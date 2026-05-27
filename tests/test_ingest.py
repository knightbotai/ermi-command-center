from __future__ import annotations

import json
from pathlib import Path

from ermi.chatlasso import import_chatlasso, import_chatlasso_payload
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


def test_import_chatlasso_ssi(tmp_path: Path) -> None:
    source = tmp_path / "memory_architecture_SSI.md"
    source.write_text(
        """---
type: chat_extracted_ssi
mode: Architecture
archetype: Prime Auditor
status: Active
domain_nodes: ["ERMI", "ChatLasso", "Obsidian"]
date_extracted: 2026-05-27T15:00:00+00:00
loss_report: "None"
hash_beacon: "abc123"
---

# ERMI and ChatLasso Integration

## Cognitive DNA
- ChatLasso captures live LLM conversations.
- ERMI stores durable recursive memory.

## Architectural Commits
- ChatLasso SSI payloads must import into ERMI.
- Obsidian output remains immutable source material.

## Open Vectors
- Build a seamless importer and graph bridge.
""",
        encoding="utf-8",
    )

    root = tmp_path / "archive"
    stats = import_chatlasso(source, root)

    assert stats["conversations"] == 1
    assert stats["chunks"] == 4
    assert stats["entities"] >= 3
    assert list((root / "raw" / "chatlasso").glob("*.md"))
    assert list((root / "vault" / "chatlasso" / "2026").glob("*.md"))
    result = search(root, "live LLM conversations durable memory", 1)[0]
    assert result["chunk_id"].startswith("chatlasso_")


def test_import_chatlasso_payload(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    stats = import_chatlasso_payload(
        "Direct ERMI Payload",
        """---
type: chat_extracted_ssi
mode: Direct Bridge
domain_nodes: ["ChatLasso", "ERMI"]
date_extracted: 2026-05-27T16:00:00+00:00
---

# Direct ERMI Payload

## Architectural Commits
ChatLasso can send SSI Markdown directly into ERMI without a filesystem path.
""",
        root,
    )

    assert stats["conversations"] == 1
    assert list((root / "raw" / "chatlasso_payloads").glob("*.md"))
    assert search(root, "without a filesystem path", 1)[0]["chunk_id"].startswith("chatlasso_")
