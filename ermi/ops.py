from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .ingest import init_archive


def backup_archive(root: Path, target: Path | None = None) -> Path:
    init_archive(root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target = target or (root / "backups" / f"ermi-backup-{stamp}")
    target.mkdir(parents=True, exist_ok=True)
    for name in ("ermi.sqlite3", "graph.json", "watchers.json", "watch_state.json"):
        source = root / name
        if source.exists():
            shutil.copy2(source, target / name)
    for folder in ("raw", "vault"):
        source = root / folder
        if source.exists():
            shutil.copytree(source, target / folder, dirs_exist_ok=True)
    changelog = Path("CHANGELOG.md")
    if changelog.exists():
        shutil.copy2(changelog, target / "CHANGELOG.md")
    return target


def restore_archive(root: Path, source: Path) -> Path:
    if not source.exists():
        raise FileNotFoundError(source)
    init_archive(root)
    for name in ("ermi.sqlite3", "graph.json", "watchers.json", "watch_state.json"):
        backup_file = source / name
        if backup_file.exists():
            shutil.copy2(backup_file, root / name)
    for folder in ("raw", "vault"):
        backup_folder = source / folder
        if backup_folder.exists():
            shutil.copytree(backup_folder, root / folder, dirs_exist_ok=True)
    return root


def known_folder(root: Path, name: str) -> Path:
    folders = {
        "archive": root,
        "raw": root / "raw",
        "vault": root / "vault",
        "backups": root / "backups",
        "exports": root / "exports",
        "samples": Path("sample_data").resolve(),
    }
    if name not in folders:
        raise ValueError(f"Unknown folder shortcut: {name}")
    return folders[name].resolve()


def open_folder(root: Path, name: str | None = None, path: Path | None = None) -> Path:
    target = path.expanduser().resolve() if path else known_folder(root, name or "archive")
    target.mkdir(parents=True, exist_ok=True)
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", str(target)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])
    return target
