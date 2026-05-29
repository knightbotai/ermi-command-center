from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

from .ingest import init_archive
from .storage import LATEST_SCHEMA_VERSION, Store
from .watch import load_watchers


def run_diagnostics(root: Path) -> dict[str, Any]:
    init_archive(root)
    checks = [
        python_check(),
        command_check("node", ["C:\\Program Files\\nodejs\\node.exe"]),
        command_check("npm", ["C:\\Program Files\\nodejs\\npm.cmd"]),
        sqlite_check(root),
        archive_write_check(root),
        schema_check(root),
        watcher_check(root),
        backup_check(root),
        git_remote_check(),
    ]
    return {"healthy": all(item["ok"] for item in checks), "checks": checks}


def python_check() -> dict[str, Any]:
    return {
        "name": "Python",
        "ok": True,
        "detail": sys.executable,
        "version": sys.version.split()[0],
        "fix": "Python is available.",
    }


def command_check(name: str, fallbacks: list[str]) -> dict[str, Any]:
    path = shutil.which(name)
    if not path:
        path = next((item for item in fallbacks if Path(item).exists()), None)
    return {
        "name": name,
        "ok": bool(path),
        "detail": path or f"{name} not found",
        "fix": (
            f"{name} is available." if path else "Run install\\Install-ERMI.cmd to install or repair prerequisites."
        ),
    }


def sqlite_check(root: Path) -> dict[str, Any]:
    try:
        with sqlite3.connect(root / "ermi.sqlite3") as conn:
            conn.execute("SELECT 1").fetchone()
        return {"name": "SQLite", "ok": True, "detail": str(root / "ermi.sqlite3"), "fix": "SQLite is reachable."}
    except Exception as exc:
        return {
            "name": "SQLite",
            "ok": False,
            "detail": str(exc),
            "fix": "Run python -m ermi --root archive init, then retry diagnostics.",
        }


def archive_write_check(root: Path) -> dict[str, Any]:
    try:
        probe = root / ".ermi-write-check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return {"name": "Archive writable", "ok": True, "detail": str(root), "fix": "Archive path is writable."}
    except Exception as exc:
        return {
            "name": "Archive writable",
            "ok": False,
            "detail": str(exc),
            "fix": "Move ERMI to a writable folder or run PowerShell with access to this archive path.",
        }


def schema_check(root: Path) -> dict[str, Any]:
    try:
        with Store(root / "ermi.sqlite3") as store:
            current = store.schema_version()
        return {
            "name": "Schema",
            "ok": current == LATEST_SCHEMA_VERSION,
            "detail": f"{current}/{LATEST_SCHEMA_VERSION}",
            "fix": (
                "Schema is current."
                if current == LATEST_SCHEMA_VERSION
                else "Run python -m ermi --root archive migrate."
            ),
        }
    except Exception as exc:
        return {"name": "Schema", "ok": False, "detail": str(exc), "fix": "Run python -m ermi --root archive migrate."}


def watcher_check(root: Path) -> dict[str, Any]:
    watchers = load_watchers(root)
    missing = [item for item in watchers if not Path(item).exists()]
    return {
        "name": "Watch folders",
        "ok": not missing,
        "detail": f"{len(watchers)} configured, {len(missing)} missing",
        "fix": (
            "Watched folders are reachable."
            if not missing
            else "Remove or re-add missing watched folders in the command center."
        ),
    }


def backup_check(root: Path) -> dict[str, Any]:
    backup_root = root / "backups"
    count = len(list(backup_root.glob("ermi-backup-*"))) if backup_root.exists() else 0
    return {
        "name": "Backups",
        "ok": True,
        "detail": f"{count} backup folders",
        "fix": "Backups are present." if count else "Click Backup before important imports or updates.",
    }


def git_remote_check() -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {"name": "Git remote", "ok": True, "detail": result.stdout.strip(), "fix": "Git remote is configured."}
    except Exception as exc:
        return {
            "name": "Git remote",
            "ok": False,
            "detail": str(exc),
            "fix": "Run git remote add origin https://github.com/knightbotai/ermi-command-center.git.",
        }
