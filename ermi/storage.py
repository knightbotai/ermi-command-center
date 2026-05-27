from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA journal_mode = WAL;

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
"""


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

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

    def replace_conversation(self, conversation: dict[str, Any]) -> None:
        cid = conversation["id"]
        self.conn.execute("DELETE FROM entity_refs WHERE conversation_id = ?", (cid,))
        self.conn.execute("DELETE FROM chunks WHERE conversation_id = ?", (cid,))
        self.conn.execute("DELETE FROM messages WHERE conversation_id = ?", (cid,))
        self.conn.execute(
            """
            INSERT OR REPLACE INTO conversations
            (id, title, created_at, updated_at, source_id, markdown_path, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                conversation["title"],
                conversation.get("created_at"),
                conversation.get("updated_at"),
                conversation["source_id"],
                conversation["markdown_path"],
                json.dumps(conversation.get("tags", [])),
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

