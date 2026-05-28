from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

import ermi.updater as updater
from ermi.api import create_app
from ermi.chatlasso import import_chatlasso, import_chatlasso_payload
from ermi.exports import activity_summary, export_chat_csv, export_obsidian_second_brain, mine_code_blocks
from ermi.flags import list_flags
from ermi.ingest import ingest_export, reconstruct_messages
from ermi.ops import backup_archive, known_folder, restore_archive
from ermi.review import list_import_reviews, set_import_review_status
from ermi.search import search
from ermi.setup import load_setup, run_first_setup
from ermi.storage import LATEST_SCHEMA_VERSION, Store
from ermi.timeline import concept_timeline
from ermi.watch import add_watcher, scan_chatlasso_watchers


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


def test_chatgpt_true_path_ignores_abandoned_branches_and_exports(tmp_path: Path) -> None:
    chat = {
        "id": "branchy",
        "title": "Python Project Plan",
        "create_time": 1779894000,
        "current_node": "final",
        "mapping": {
            "root": {"parent": None, "message": None},
            "prompt": {
                "parent": "root",
                "message": {
                    "id": "prompt",
                    "author": {"role": "user"},
                    "create_time": 1779894000,
                    "content": {"parts": ["Give me a Python project plan."]},
                },
            },
            "abandoned": {
                "parent": "prompt",
                "message": {
                    "id": "abandoned",
                    "author": {"role": "assistant"},
                    "create_time": 1779894100,
                    "content": {"parts": ["This abandoned answer should not be archived."]},
                },
            },
            "final": {
                "parent": "prompt",
                "message": {
                    "id": "final",
                    "author": {"role": "assistant"},
                    "create_time": 1779894200,
                    "content": {"parts": ["Use this final answer.\n```python\nprint('kept')\n```"]},
                },
            },
        },
    }
    source = tmp_path / "conversations.json"
    source.write_text(json.dumps([chat]), encoding="utf-8")

    messages = reconstruct_messages(chat)
    assert [message["id"] for message in messages] == ["prompt", "final"]
    assert "abandoned" not in "\n".join(message["content"] for message in messages)

    root = tmp_path / "archive"
    ingest_export(source, root)
    result = search(root, "abandoned answer", 1)[0]
    assert "abandoned" not in result["preview"].lower()

    csv_target = tmp_path / "chat_history.csv"
    code_target = tmp_path / "code.txt"
    obsidian_target = tmp_path / "obsidian"
    assert export_chat_csv(source, csv_target)["messages"] == 2
    assert "abandoned" not in csv_target.read_text(encoding="utf-8")
    assert mine_code_blocks(source, code_target)["code_blocks"] == 1
    assert "print('kept')" in code_target.read_text(encoding="utf-8")
    assert activity_summary(source, 1)[0]["message_count"] == 2
    assert export_obsidian_second_brain(source, obsidian_target)["files"] == 1
    assert list((obsidian_target / "Code").glob("*.md"))


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
    with Store(root / "ermi.sqlite3") as store:
        row = store.conn.execute("SELECT * FROM chatlasso_metadata").fetchone()
        conversation = store.conn.execute("SELECT source_kind, project, identity, import_status FROM conversations").fetchone()
    assert row["mode"] == "Architecture"
    assert row["archetype"] == "Prime Auditor"
    assert row["status"] == "Active"
    assert row["hash_beacon"] == "abc123"
    assert json.loads(row["domain_nodes"]) == ["ERMI", "ChatLasso", "Obsidian"]
    assert conversation["source_kind"] == "chatlasso"
    assert conversation["project"] == "ChatLasso"
    assert conversation["identity"] == "KnightBot"
    assert conversation["import_status"] == "accepted"


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


def test_watch_chatlasso_imports_only_changed_files(tmp_path: Path) -> None:
    source_dir = tmp_path / "ssi"
    source_dir.mkdir()
    source = source_dir / "watch_test.md"
    source.write_text(
        """---
type: chat_extracted_ssi
mode: Watcher
domain_nodes: ["Watcher", "ERMI"]
date_extracted: 2026-05-27T18:00:00+00:00
---

# Watcher Test

## Cognitive DNA
The watcher imports changed ChatLasso SSI files.
""",
        encoding="utf-8",
    )

    root = tmp_path / "archive"
    add_watcher(root, source_dir)

    first = scan_chatlasso_watchers(root)
    second = scan_chatlasso_watchers(root)

    assert first["watchers"] == 1
    assert first["seen"] == 1
    assert first["changed"] == 1
    assert first["imported"] == 1
    assert second["seen"] == 1
    assert second["changed"] == 0
    assert second["imported"] == 0


def test_schema_migration_adds_versioned_columns_to_existing_archive(tmp_path: Path) -> None:
    db = tmp_path / "archive" / "ermi.sqlite3"
    db.parent.mkdir()
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT,
            source_id INTEGER NOT NULL,
            markdown_path TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '[]'
        )
        """
    )
    conn.commit()
    conn.close()

    with Store(db) as store:
        columns = {row["name"] for row in store.conn.execute("PRAGMA table_info(conversations)").fetchall()}
        assert store.schema_version() == LATEST_SCHEMA_VERSION

    assert {"source_kind", "schema_version", "project", "identity", "import_status", "metadata_json"} <= columns


def test_hybrid_search_filters_regression_flags(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    stats = import_chatlasso_payload(
        "Contradiction Payload",
        """---
type: chat_extracted_ssi
mode: Architecture
archetype: Prime Auditor
status: Active
domain_nodes: ["ERMI"]
date_extracted: 2026-05-27T18:00:00+00:00
audit_pass_status: false
regression_contradictions_found: true
regression_details: ["Overturned frozen memory rule"]
loss_report: "Possible drift"
hash_beacon: "beadfeed"
---

# Contradiction Payload

## Regression Detection
- Overturned frozen memory rule

## Architectural Commits
The frozen memory rule was contradicted.
""",
        root,
    )

    assert stats["conversations"] == 1
    results = search(root, "frozen memory rule", 5, {"regression": True, "mode": "Architecture"})
    assert results
    assert results[0]["lexical_score"] >= 0
    assert results[0]["regression_contradictions_found"] is True
    assert list_flags(root)[0]["regression_contradictions_found"] is True


def test_timeline_review_backup_restore_and_api(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    import_chatlasso_payload(
        "Review Payload",
        """---
type: chat_extracted_ssi
mode: Review
archetype: DeeTorch
status: Active
domain_nodes: ["Jusstin", "ERMI"]
date_extracted: 2026-05-27T19:00:00+00:00
audit_pass_status: false
loss_report: "Needs human review"
---

# Review Payload

## Cognitive DNA
Jusstin and ERMI need a review queue.
""",
        root,
    )
    reviews = list_import_reviews(root)
    assert reviews[0]["status"] == "pending_review"
    cid = reviews[0]["conversation_id"]
    assert set_import_review_status(root, cid, "accepted")["status"] == "accepted"
    assert concept_timeline(root)[0]["mode"] == "Review"

    backup = backup_archive(root)
    restored = tmp_path / "restored"
    restore_archive(restored, backup)
    assert (restored / "ermi.sqlite3").exists()

    client = TestClient(create_app(root))
    assert client.get("/api/schema").json()["latest"] == LATEST_SCHEMA_VERSION
    assert client.get("/api/timeline").json()["events"]
    assert "flags" in client.get("/api/flags").json()
    assert client.get("/api/review/imports").json()["imports"]
    assert known_folder(root, "vault") == (root / "vault").resolve()


def test_timeline_rows_produce_unique_ui_keys_for_repeated_concepts(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    import_chatlasso_payload(
        "Repeated ERMI Payload",
        """---
type: chat_extracted_ssi
mode: Review
status: Active
domain_nodes: ["ERMI", "ERMI"]
date_extracted: 2026-05-27T21:00:00+00:00
---

# Repeated ERMI Payload

## Cognitive DNA
ERMI should keep ERMI timeline rows stable when ERMI appears as both metadata and extracted text.
""",
        root,
    )

    events = concept_timeline(root)
    ui_keys = [
        ":".join(
            [
                str(item.get("conversation_id") or "seed"),
                str(item.get("concept") or item.get("title") or "event"),
                str(item.get("kind") or "kind"),
                str(item.get("event_at") or "undated"),
                str(index),
            ]
        )
        for index, item in enumerate(events)
    ]

    assert len(ui_keys) == len(set(ui_keys))
    assert any(item["concept"] == "ERMI" and item["kind"] == "system" for item in events)
    assert any(item["concept"] == "ERMI" and item["kind"] == "concept" for item in events)


def test_first_run_setup_and_diagnostics_api(tmp_path: Path) -> None:
    source = tmp_path / "conversations.json"
    source.write_text(
        json.dumps(
            [
                {
                    "id": "setup_conv",
                    "title": "Setup Memory",
                    "create_time": 1779894000,
                    "current_node": "m2",
                    "mapping": {
                        "root": {"parent": None, "message": None},
                        "m1": {
                            "parent": "root",
                            "message": {
                                "id": "m1",
                                "author": {"role": "user"},
                                "create_time": 1779894000,
                                "content": {"parts": ["Set up ERMI."]},
                            },
                        },
                        "m2": {
                            "parent": "m1",
                            "message": {
                                "id": "m2",
                                "author": {"role": "assistant"},
                                "create_time": 1779897600,
                                "content": {"parts": ["ERMI setup is complete."]},
                            },
                        },
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    ssi_dir = tmp_path / "ssi"
    ssi_dir.mkdir()
    (ssi_dir / "setup_ssi.md").write_text(
        """---
type: chat_extracted_ssi
mode: Setup
domain_nodes: ["ERMI"]
date_extracted: 2026-05-27T20:00:00+00:00
hash_beacon: "setup"
---

# Setup SSI

## Cognitive DNA
Setup should be boring and reliable.
""",
        encoding="utf-8",
    )

    root = tmp_path / "archive"
    result = run_first_setup(root, {"chatgpt_source": str(source), "chatlasso_source": str(ssi_dir)})

    assert result["stats"]["chatgpt"]["conversations"] == 1
    assert result["stats"]["chatlasso"]["conversations"] == 1
    assert load_setup(root)["completed_at"]

    client = TestClient(create_app(root))
    setup_response = client.get("/api/setup").json()
    assert setup_response["config"]["chatgpt_source"] == str(source)
    diagnostics = client.get("/api/diagnostics").json()
    assert diagnostics["healthy"] is True
    assert {item["name"] for item in diagnostics["checks"]} >= {"Python", "SQLite", "Schema", "Archive writable"}


def test_update_status_and_install_use_fast_forward_with_backup(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    root = repo / "archive"
    (repo / ".git").mkdir(parents=True)
    root.mkdir()
    commands: list[list[str]] = []
    state = {"commit": "aaaa111111111111111111111111111111111111"}

    def fake_run_command(args, cwd, *, check=True, timeout=30):
        commands.append(args)
        if args == ["git", "rev-parse", "HEAD"]:
            return updater.CommandResult(args, 0, f"{state['commit']}\n", "")
        if args == ["git", "branch", "--show-current"]:
            return updater.CommandResult(args, 0, "main\n", "")
        if args == ["git", "remote", "get-url", "origin"]:
            return updater.CommandResult(args, 0, "https://github.com/knightbotai/ermi-command-center.git\n", "")
        if args == ["git", "status", "--porcelain"]:
            return updater.CommandResult(args, 0, "", "")
        if args == ["git", "ls-remote", "origin", "refs/heads/main"]:
            return updater.CommandResult(args, 0, "bbbb222222222222222222222222222222222222\trefs/heads/main\n", "")
        if args[:3] == ["git", "merge-base", "--is-ancestor"]:
            return updater.CommandResult(args, 0, "", "")
        if args[:4] == ["git", "pull", "--ff-only", "origin"]:
            state["commit"] = "bbbb222222222222222222222222222222222222"
            return updater.CommandResult(args, 0, "Fast-forward\n", "")
        return updater.CommandResult(args, 0, "ok\n", "")

    monkeypatch.setattr(updater, "run_command", fake_run_command)
    monkeypatch.setattr(updater, "resolve_command", lambda _name, _fallbacks: "npm.cmd")

    status = updater.update_status(root)
    assert status["update_available"] is True
    assert status["current_short"] == "aaaa111"
    assert status["remote_short"] == "bbbb222"

    result = updater.install_update(root)
    assert result["ok"] is True
    assert result["restart_required"] is True
    assert Path(result["backup"]).exists()
    assert ["git", "pull", "--ff-only", "origin", "main"] in commands
    assert any(command[-1] == "build" for command in commands)
