from __future__ import annotations

import json
from pathlib import Path

from .storage import Store


def export_graph(root: Path) -> Path:
    nodes = []
    edges = []
    with Store(root / "ermi.sqlite3") as store:
        for row in store.conn.execute(
            """
            SELECT conversations.id, conversations.title, conversations.created_at,
                   conversations.project, conversations.identity,
                   chatlasso_metadata.mode, chatlasso_metadata.archetype,
                   chatlasso_metadata.status, chatlasso_metadata.regression_contradictions_found
            FROM conversations
            LEFT JOIN chatlasso_metadata ON chatlasso_metadata.conversation_id = conversations.id
            """
        ):
            nodes.append(
                {
                    "id": row["id"],
                    "label": row["title"],
                    "type": "conversation",
                    "created_at": row["created_at"],
                    "project": row["project"],
                    "identity": row["identity"],
                    "mode": row["mode"],
                    "archetype": row["archetype"],
                    "status": row["status"],
                    "flagged": bool(row["regression_contradictions_found"]),
                }
            )
            for kind in ("mode", "archetype", "status"):
                value = row[kind]
                if value:
                    node_id = f"{kind}:{value}"
                    if not any(node["id"] == node_id for node in nodes):
                        nodes.append({"id": node_id, "label": value, "type": kind})
                    edges.append({"source": row["id"], "target": node_id, "type": f"has_{kind}"})
        for row in store.conn.execute("SELECT id, conversation_id, title FROM chunks"):
            nodes.append({"id": row["id"], "label": row["title"], "type": "chunk"})
            edges.append({"source": row["conversation_id"], "target": row["id"], "type": "contains"})
        query = """
            SELECT entities.id, entities.name, entities.kind, entity_refs.conversation_id
            FROM entities
            JOIN entity_refs ON entity_refs.entity_id = entities.id
        """
        for row in store.conn.execute(query):
            entity_id = f"entity:{row['id']}"
            if not any(node["id"] == entity_id for node in nodes):
                nodes.append({"id": entity_id, "label": row["name"], "type": row["kind"]})
            edges.append({"source": row["conversation_id"], "target": entity_id, "type": "mentions"})

    target = root / "graph.json"
    target.write_text(json.dumps({"nodes": nodes, "edges": edges}, indent=2), encoding="utf-8")
    return target
