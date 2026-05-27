from __future__ import annotations

import json
from pathlib import Path

from .ingest import init_archive
from .storage import Store


def list_flags(root: Path, limit: int = 50) -> list[dict[str, object]]:
    init_archive(root)
    with Store(root / "ermi.sqlite3") as store:
        rows = store.conn.execute(
            """
            SELECT conversations.id, conversations.title, conversations.project,
                   conversations.identity, conversations.import_status,
                   chatlasso_metadata.mode, chatlasso_metadata.archetype,
                   chatlasso_metadata.status, chatlasso_metadata.audit_pass_status,
                   chatlasso_metadata.loss_report,
                   chatlasso_metadata.regression_contradictions_found,
                   chatlasso_metadata.regression_details
            FROM conversations
            JOIN chatlasso_metadata ON chatlasso_metadata.conversation_id = conversations.id
            WHERE chatlasso_metadata.regression_contradictions_found = 1
               OR chatlasso_metadata.audit_pass_status = 0
               OR conversations.import_status = 'pending_review'
            ORDER BY conversations.updated_at DESC, conversations.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            **dict(row),
            "audit_pass_status": None if row["audit_pass_status"] is None else bool(row["audit_pass_status"]),
            "regression_contradictions_found": bool(row["regression_contradictions_found"]),
            "regression_details": json.loads(row["regression_details"] or "[]"),
        }
        for row in rows
    ]
