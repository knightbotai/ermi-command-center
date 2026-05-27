from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    imported_at TEXT NOT NULL,
    sha256 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT,
    updated_at TEXT,
    source_id INTEGER NOT NULL,
    markdown_path TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    source_kind TEXT NOT NULL DEFAULT 'chatgpt',
    schema_version INTEGER NOT NULL DEFAULT 1,
    project TEXT NOT NULL DEFAULT 'ERMI',
    identity TEXT NOT NULL DEFAULT 'KnightBot',
    import_status TEXT NOT NULL DEFAULT 'accepted',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    parent_id TEXT,
    author TEXT NOT NULL,
    created_at TEXT,
    content TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    embedding TEXT NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    score REAL NOT NULL,
    UNIQUE(name, kind)
);

CREATE TABLE IF NOT EXISTS entity_refs (
    entity_id INTEGER NOT NULL,
    conversation_id TEXT NOT NULL,
    chunk_id TEXT,
    count INTEGER NOT NULL,
    PRIMARY KEY(entity_id, conversation_id, chunk_id),
    FOREIGN KEY(entity_id) REFERENCES entities(id)
);

CREATE TABLE IF NOT EXISTS chatlasso_metadata (
    conversation_id TEXT PRIMARY KEY,
    mode TEXT,
    archetype TEXT,
    status TEXT,
    domain_nodes TEXT NOT NULL DEFAULT '[]',
    date_extracted TEXT,
    audit_pass_status INTEGER,
    hash_beacon TEXT,
    loss_report TEXT,
    regression_contradictions_found INTEGER NOT NULL DEFAULT 0,
    regression_details TEXT NOT NULL DEFAULT '[]',
    source_path TEXT,
    source_hash TEXT,
    raw_metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS import_reviews (
    conversation_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'accepted',
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    chunk_id UNINDEXED,
    conversation_id UNINDEXED,
    title,
    text,
    tags
);
"""

LATEST_SCHEMA_VERSION = 2


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.migrate()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def upsert_source(self, path: str, imported_at: str, sha256: str) -> int:
        self.conn.execute(
            "INSERT OR IGNORE INTO sources(path, imported_at, sha256) VALUES (?, ?, ?)",
            (path, imported_at, sha256),
        )
        self.conn.execute(
            "UPDATE sources SET imported_at = ?, sha256 = ? WHERE path = ?",
            (imported_at, sha256, path),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT id FROM sources WHERE path = ?", (path,)).fetchone()
        return int(row["id"])

    def migrate(self) -> None:
        from datetime import datetime, timezone

        columns = {row["name"] for row in self.conn.execute("PRAGMA table_info(conversations)").fetchall()}
        additions = {
            "source_kind": "TEXT NOT NULL DEFAULT 'chatgpt'",
            "schema_version": "INTEGER NOT NULL DEFAULT 1",
            "project": "TEXT NOT NULL DEFAULT 'ERMI'",
            "identity": "TEXT NOT NULL DEFAULT 'KnightBot'",
            "import_status": "TEXT NOT NULL DEFAULT 'accepted'",
            "metadata_json": "TEXT NOT NULL DEFAULT '{}'",
        }
        for name, definition in additions.items():
            if name not in columns:
                self.conn.execute(f"ALTER TABLE conversations ADD COLUMN {name} {definition}")

        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (LATEST_SCHEMA_VERSION, now),
        )
        self.conn.commit()

    def schema_version(self) -> int:
        row = self.conn.execute("SELECT max(version) AS version FROM schema_migrations").fetchone()
        return int(row["version"] or 1)

    def replace_conversation(self, conversation: dict[str, Any]) -> None:
        cid = conversation["id"]
        self.conn.execute("DELETE FROM entity_refs WHERE conversation_id = ?", (cid,))
        self.conn.execute("DELETE FROM chunks WHERE conversation_id = ?", (cid,))
        self.conn.execute("DELETE FROM messages WHERE conversation_id = ?", (cid,))
        self.conn.execute("DELETE FROM chunks_fts WHERE conversation_id = ?", (cid,))
        metadata = conversation.get("chatlasso_metadata") or {}
        import_status = conversation.get("import_status") or import_status_for(metadata)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO conversations
            (id, title, created_at, updated_at, source_id, markdown_path, tags,
             source_kind, schema_version, project, identity, import_status, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                conversation["title"],
                conversation.get("created_at"),
                conversation.get("updated_at"),
                conversation["source_id"],
                conversation["markdown_path"],
                json.dumps(conversation.get("tags", [])),
                conversation.get("source_kind", "chatgpt"),
                LATEST_SCHEMA_VERSION,
                conversation.get("project", "ERMI"),
                conversation.get("identity", "KnightBot"),
                import_status,
                json.dumps(metadata),
            ),
        )
        self.conn.executemany(
            """
            INSERT INTO messages
            (id, conversation_id, parent_id, author, created_at, content, ordinal, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    message["id"],
                    cid,
                    message.get("parent_id"),
                    message["author"],
                    message.get("created_at"),
                    message["content"],
                    index,
                    json.dumps(message.get("metadata", {})),
                )
                for index, message in enumerate(conversation["messages"])
            ],
        )
        self.conn.executemany(
            """
            INSERT INTO chunks
            (id, conversation_id, title, text, ordinal, tags, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    chunk["id"],
                    cid,
                    chunk["title"],
                    chunk["text"],
                    index,
                    json.dumps(chunk.get("tags", [])),
                    json.dumps(chunk["embedding"]),
                )
                for index, chunk in enumerate(conversation["chunks"])
            ],
        )
        self.conn.executemany(
            """
            INSERT INTO chunks_fts(chunk_id, conversation_id, title, text, tags)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    chunk["id"],
                    cid,
                    chunk["title"],
                    chunk["text"],
                    " ".join(chunk.get("tags", [])),
                )
                for chunk in conversation["chunks"]
            ],
        )
        if conversation.get("source_kind") == "chatlasso":
            self.replace_chatlasso_metadata(cid, metadata)
        self.replace_import_review(cid, import_status, review_reason(metadata))
        for entity in conversation.get("entities", []):
            self.conn.execute(
                """
                INSERT INTO entities(name, kind, score) VALUES (?, ?, ?)
                ON CONFLICT(name, kind) DO UPDATE SET score = max(score, excluded.score)
                """,
                (entity["name"], entity["kind"], entity["score"]),
            )
            entity_id = self.conn.execute(
                "SELECT id FROM entities WHERE name = ? AND kind = ?",
                (entity["name"], entity["kind"]),
            ).fetchone()["id"]
            self.conn.execute(
                """
                INSERT OR REPLACE INTO entity_refs(entity_id, conversation_id, chunk_id, count)
                VALUES (?, ?, ?, ?)
                """,
                (entity_id, cid, None, int(entity["score"])),
            )
        self.conn.commit()

    def replace_chatlasso_metadata(self, conversation_id: str, metadata: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO chatlasso_metadata
            (conversation_id, mode, archetype, status, domain_nodes, date_extracted,
             audit_pass_status, hash_beacon, loss_report, regression_contradictions_found,
             regression_details, source_path, source_hash, raw_metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                metadata.get("mode"),
                metadata.get("archetype"),
                metadata.get("status"),
                json.dumps(metadata.get("domain_nodes", [])),
                metadata.get("date_extracted"),
                bool_to_int(metadata.get("audit_pass_status")),
                metadata.get("hash_beacon"),
                metadata.get("loss_report"),
                1 if metadata.get("regression_contradictions_found") else 0,
                json.dumps(metadata.get("regression_details", [])),
                metadata.get("source_path"),
                metadata.get("source_hash"),
                json.dumps(metadata),
            ),
        )

    def replace_import_review(self, conversation_id: str, status: str, reason: str) -> None:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO import_reviews(conversation_id, status, reason, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET
                status = excluded.status,
                reason = excluded.reason,
                updated_at = excluded.updated_at
            """,
            (conversation_id, status, reason, now, now),
        )


def bool_to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    lowered = str(value).strip().lower()
    if lowered in {"true", "yes", "pass", "passed", "1"}:
        return 1
    if lowered in {"false", "no", "fail", "failed", "warn", "0"}:
        return 0
    return None


def import_status_for(metadata: dict[str, Any]) -> str:
    if metadata.get("regression_contradictions_found"):
        return "pending_review"
    audit = bool_to_int(metadata.get("audit_pass_status"))
    if audit == 0:
        return "pending_review"
    if metadata and not metadata.get("hash_beacon"):
        return "pending_review"
    return "accepted"


def review_reason(metadata: dict[str, Any]) -> str:
    reasons = []
    if metadata.get("regression_contradictions_found"):
        reasons.append("Regression contradiction detected")
    if bool_to_int(metadata.get("audit_pass_status")) == 0:
        reasons.append("Audit pass status is false")
    if metadata and not metadata.get("hash_beacon"):
        reasons.append("Missing hash beacon")
    return "; ".join(reasons)
