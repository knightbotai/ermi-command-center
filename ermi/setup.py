from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .chatlasso import import_chatlasso
from .ingest import ingest_export, init_archive
from .watch import add_watcher, scan_chatlasso_watchers

SETUP_CONFIG = "setup.json"


def setup_path(root: Path) -> Path:
    return root / SETUP_CONFIG


def load_setup(root: Path) -> dict[str, Any]:
    path = setup_path(root)
    if not path.exists():
        return {
            "chatgpt_source": "",
            "chatlasso_source": "",
            "completed_at": None,
            "last_run": None,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_setup(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    init_archive(root)
    current = load_setup(root)
    current.update(
        {
            "chatgpt_source": str(config.get("chatgpt_source") or "").strip(),
            "chatlasso_source": str(config.get("chatlasso_source") or "").strip(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    setup_path(root).write_text(json.dumps(current, indent=2), encoding="utf-8")
    return current


def run_first_setup(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    saved = save_setup(root, config)
    stats: dict[str, Any] = {"chatgpt": None, "chatlasso": None, "watch": None}
    chatgpt_source = saved.get("chatgpt_source")
    chatlasso_source = saved.get("chatlasso_source")

    if chatgpt_source:
        source = Path(chatgpt_source).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"ChatGPT export not found: {source}")
        stats["chatgpt"] = ingest_export(source, root)

    if chatlasso_source:
        source = Path(chatlasso_source).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"ChatLasso folder not found: {source}")
        add_watcher(root, source)
        stats["chatlasso"] = import_chatlasso(source, root)
        stats["watch"] = scan_chatlasso_watchers(root)

    saved["completed_at"] = datetime.now(timezone.utc).isoformat()
    saved["last_run"] = stats
    setup_path(root).write_text(json.dumps(saved, indent=2), encoding="utf-8")
    return {"config": saved, "stats": stats}
