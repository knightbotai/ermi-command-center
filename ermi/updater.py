from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ingest import init_archive
from .ops import backup_archive
from .storage import Store


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


def update_status(root: Path, channel: str = "main") -> dict[str, Any]:
    repo = resolve_repo_root(root)
    branch = normalize_channel(channel)
    current = run_command(["git", "rev-parse", "HEAD"], repo)
    current_branch = run_command(["git", "branch", "--show-current"], repo, check=False)
    remote = run_command(["git", "remote", "get-url", "origin"], repo)
    dirty = bool(run_command(["git", "status", "--porcelain"], repo).stdout.strip())
    remote_ref = run_command(["git", "ls-remote", "origin", f"refs/heads/{branch}"], repo)
    remote_commit = parse_ls_remote(remote_ref.stdout)
    current_commit = current.stdout.strip()

    ancestor = run_command(["git", "merge-base", "--is-ancestor", current_commit, remote_commit], repo, check=False)
    update_available = current_commit != remote_commit and ancestor.returncode == 0
    diverged = current_commit != remote_commit and ancestor.returncode != 0

    return {
        "channel": branch,
        "repo": str(repo),
        "remote": remote.stdout.strip(),
        "branch": current_branch.stdout.strip() or "(detached)",
        "current_commit": current_commit,
        "remote_commit": remote_commit,
        "current_short": short_commit(current_commit),
        "remote_short": short_commit(remote_commit),
        "update_available": update_available,
        "can_fast_forward": update_available,
        "diverged": diverged,
        "dirty": dirty,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "message": status_message(update_available, diverged, dirty),
    }


def install_update(root: Path, channel: str = "main") -> dict[str, Any]:
    repo = resolve_repo_root(root)
    branch = normalize_channel(channel)
    before = update_status(root, branch)
    if before["dirty"]:
        return {
            "ok": False,
            "skipped": True,
            "restart_required": False,
            "status": before,
            "log": ["Update blocked: local files have uncommitted changes. Commit or stash them before updating."],
        }
    if before["diverged"]:
        return {
            "ok": False,
            "skipped": True,
            "restart_required": False,
            "status": before,
            "log": ["Update blocked: local checkout has diverged from GitHub. Use a manual git merge or reset."],
        }
    if not before["update_available"]:
        return {
            "ok": True,
            "skipped": True,
            "restart_required": False,
            "status": before,
            "log": ["Already up to date."],
        }

    init_archive(root)
    log: list[str] = []
    backup = backup_archive(root)
    log.append(f"Backup created: {backup}")

    python = sys.executable
    npm = resolve_command("npm.cmd", ["C:\\Program Files\\nodejs\\npm.cmd"])
    commands = [
        ["git", "fetch", "origin", branch],
        ["git", "pull", "--ff-only", "origin", branch],
        [python, "-m", "pip", "install", "-e", ".[dev,ml]"],
        [npm, "install"],
        [python, "-m", "ermi", "--root", str(root), "migrate"],
        [npm, "run", "build"],
    ]

    for command in commands:
        result = run_command(command, repo, timeout=300)
        log_command(log, result)

    with Store(root / "ermi.sqlite3") as store:
        schema_version = store.schema_version()

    after = update_status(root, branch)
    return {
        "ok": True,
        "skipped": False,
        "restart_required": before["current_commit"] != after["current_commit"],
        "backup": str(backup),
        "schema_version": schema_version,
        "status": after,
        "log": log,
    }


def resolve_repo_root(root: Path) -> Path:
    candidates = [root.resolve().parent, Path.cwd().resolve(), Path(__file__).resolve().parents[1]]
    for candidate in candidates:
        if (candidate / ".git").exists():
            return candidate
    raise FileNotFoundError("Could not find ERMI git repository root.")


def normalize_channel(channel: str) -> str:
    value = (channel or "main").strip()
    if not value.replace("-", "").replace("_", "").replace("/", "").isalnum():
        raise ValueError(f"Invalid update channel: {channel}")
    return value


def resolve_command(name: str, fallbacks: list[str]) -> str:
    path = shutil.which(name)
    if path:
        return path
    for fallback in fallbacks:
        if Path(fallback).exists():
            return fallback
    raise FileNotFoundError(f"Could not find required command: {name}")


def run_command(args: list[str], cwd: Path, *, check: bool = True, timeout: int = 30) -> CommandResult:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    command = CommandResult(args, result.returncode, result.stdout, result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(format_command_failure(command))
    return command


def parse_ls_remote(output: str) -> str:
    first = output.strip().splitlines()[0] if output.strip() else ""
    if not first:
        raise RuntimeError("GitHub branch was not found.")
    return first.split()[0]


def log_command(log: list[str], result: CommandResult) -> None:
    log.append(f"$ {' '.join(result.args)}")
    for stream in (result.stdout, result.stderr):
        text = stream.strip()
        if text:
            log.extend(text.splitlines())


def format_command_failure(result: CommandResult) -> str:
    output = "\n".join(item for item in (result.stdout.strip(), result.stderr.strip()) if item)
    return f"Command failed ({result.returncode}): {' '.join(result.args)}\n{output}"


def short_commit(value: str) -> str:
    return value[:7] if value else ""


def status_message(update_available: bool, diverged: bool, dirty: bool) -> str:
    if dirty:
        return "Local files have uncommitted changes; update is blocked."
    if diverged:
        return "Local checkout differs from GitHub; manual review is needed."
    if update_available:
        return "Update available."
    return "Already up to date."
