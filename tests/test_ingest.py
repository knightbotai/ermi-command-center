from __future__ import annotations

import json
from pathlib import Path

from ermi.ingest import ingest_export
from ermi.search import search


def test_ingest_chatgpt_export(tmp_path: Path) -> None:
    source = tmp_path / "conversations.json"
    source.write_text(
        json.dumps(
            [
                {
                    "id": "conv_1",
                    "title": "Recursive Memory Architecture",
                    "create_time": 1779894000,
                    "update_time": 1779897600,
                    "mapping": {
                        "root": {"id": "root", "parent": None, "children": ["m1"], "message": None},
                        "m1": {
                            "parent": "root",
                            "children": ["m2"],
                            "message": {
                                "id": "m1",
                                "author": {"role": "user"},
                                "create_time": 1779894000,
                                "content": {"parts": ["Design ERMI as a recursive memory system."]},
                            },
                        },
                        "m2": {
                            "parent": "m1",
                            "children": [],
                            "message": {
                                "id": "m2",
                                "author": {"role": "assistant"},
                                "create_time": 1779897600,
                                "content": {"parts": ["Use SQLite, chunks, embeddings, and graph relationships."]},
                            },
                        },
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    root = tmp_path / "archive"
    stats = ingest_export(source, root)

    assert stats["conversations"] == 1
    assert stats["messages"] == 2
    assert stats["chunks"] == 1
    assert (root / "ermi.sqlite3").exists()
    assert list((root / "vault" / "conversations" / "2026").glob("*.md"))
    assert search(root, "graph memory system", 1)[0]["chunk_id"] == "conv_1:chunk:0001"

