from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .ingest import init_archive
from .storage import Store


def list_import_reviews(root: Path) -> list[dict[str, object]]:
    init_archive(root)
    with Store(root / "ermi.sqlite3") as store:
        rows = store.conn.execute(
            """
            SELECT import_reviews.conversation_id, import_reviews.status,
                   import_reviews.reason, import_reviews.created_at,
                   import_reviews.updated_at, conversations.title,
                   conversations.project, conversations.identity
            FROM import_reviews
            JOIN conversations ON conversations.id = import_reviews.conversation_id
            ORDER BY import_reviews.updated_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def set_import_review_status(root: Path, conversation_id: str, status: str) -> dict[str, object]:
    if status not in {"accepted", "rejected", "pending_review"}:
        raise ValueError(f"Unsupported review status: {status}")
    init_archive(root)
    now = datetime.now(timezone.utc).isoformat()
    with Store(root / "ermi.sqlite3") as store:
        row = store.conn.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        if not row:
            raise FileNotFoundError(conversation_id)
        store.conn.execute(
            "UPDATE conversations SET import_status = ? WHERE id = ?",
            (status, conversation_id),
        )
        store.conn.execute(
            """
            INSERT INTO import_reviews(conversation_id, status, reason, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET
                status = excluded.status,
                updated_at = excluded.updated_at
            """,
            (conversation_id, status, "User review update", now, now),
        )
        store.conn.commit()
    return {"conversation_id": conversation_id, "status": status}
