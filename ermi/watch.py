from __future__ import annotations

import json
import time
from pathlib import Path
from threading import Event

from .chatlasso import discover_markdown, import_chatlasso
from .ingest import init_archive, sha256

WATCH_CONFIG = "watchers.json"
WATCH_STATE = "watch_state.json"


def config_path(root: Path) -> Path:
    return root / WATCH_CONFIG


def state_path(root: Path) -> Path:
    return root / WATCH_STATE


def load_watchers(root: Path) -> list[str]:
    path = config_path(root)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [item for item in data.get("chatlasso", []) if isinstance(item, str)]


def save_watchers(root: Path, watchers: list[str]) -> None:
    init_archive(root)
    unique = []
    for item in watchers:
        resolved = str(Path(item).expanduser().resolve())
        if resolved not in unique:
            unique.append(resolved)
    config_path(root).write_text(json.dumps({"chatlasso": unique}, indent=2), encoding="utf-8")


def add_watcher(root: Path, source: Path) -> list[str]:
    if not source.exists():
        raise FileNotFoundError(source)
    watchers = load_watchers(root)
    watchers.append(str(source.expanduser().resolve()))
    save_watchers(root, watchers)
    return load_watchers(root)


def load_state(root: Path) -> dict[str, str]:
    path = state_path(root)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in data.items()}


def save_state(root: Path, state: dict[str, str]) -> None:
    init_archive(root)
    state_path(root).write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def scan_chatlasso_watchers(root: Path) -> dict[str, int]:
    init_archive(root)
    watchers = load_watchers(root)
    state = load_state(root)
    totals = {"watchers": len(watchers), "seen": 0, "changed": 0, "imported": 0, "chunks": 0, "entities": 0}

    for watched in watchers:
        source = Path(watched)
        if not source.exists():
            continue
        for file_path in discover_markdown(source):
            key = str(file_path.resolve())
            digest = sha256(file_path)
            totals["seen"] += 1
            if state.get(key) == digest:
                continue
            stats = import_chatlasso(file_path, root)
            state[key] = digest
            totals["changed"] += 1
            totals["imported"] += stats["conversations"]
            totals["chunks"] += stats["chunks"]
            totals["entities"] += stats["entities"]

    save_state(root, state)
    return totals


def watch_chatlasso(root: Path, interval: int = 15, stop_event: Event | None = None) -> None:
    stop_event = stop_event or Event()
    while not stop_event.is_set():
        scan_chatlasso_watchers(root)
        stop_event.wait(interval)

