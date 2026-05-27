from __future__ import annotations

import shutil
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
