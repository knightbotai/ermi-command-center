from __future__ import annotations

import json
from pathlib import Path

from .ingest import init_archive
from .storage import Store


def concept_timeline(root: Path, limit: int = 100) -> list[dict[str, object]]:
    init_archive(root)
    with Store(root / "ermi.sqlite3") as store:
        rows = store.conn.execute(
            """
            SELECT DISTINCT conversations.id AS conversation_id, conversations.title,
                   coalesce(chatlasso_metadata.date_extracted, conversations.created_at) AS event_at,
                   conversations.project, conversations.identity,
                   chatlasso_metadata.mode, chatlasso_metadata.archetype,
                   chatlasso_metadata.status, chatlasso_metadata.regression_contradictions_found,
                   entities.name AS concept, entities.kind
            FROM conversations
            LEFT JOIN chatlasso_metadata ON chatlasso_metadata.conversation_id = conversations.id
            LEFT JOIN entity_refs ON entity_refs.conversation_id = conversations.id
            LEFT JOIN entities ON entities.id = entity_refs.entity_id
            ORDER BY event_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            **dict(row),
            "regression_contradictions_found": bool(row["regression_contradictions_found"]),
        }
        for row in rows
    ]
