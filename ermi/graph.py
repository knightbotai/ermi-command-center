from __future__ import annotations

import json
from pathlib import Path

from .storage import Store


def export_graph(root: Path) -> Path:
    nodes = []
    edges = []
    seen_node_ids = set()
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
            seen_node_ids.add(row["id"])
            for kind in ("mode", "archetype", "status"):
                value = row[kind]
                if value:
                    node_id = f"{kind}:{value}"
                    if node_id not in seen_node_ids:
                        nodes.append({"id": node_id, "label": value, "type": kind})
                        seen_node_ids.add(node_id)
                    edges.append({"source": row["id"], "target": node_id, "type": f"has_{kind}"})
        for row in store.conn.execute("SELECT id, conversation_id, title FROM chunks"):
            nodes.append({"id": row["id"], "label": row["title"], "type": "chunk"})
            seen_node_ids.add(row["id"])
            edges.append({"source": row["conversation_id"], "target": row["id"], "type": "contains"})
        query = """
            SELECT entities.id, entities.name, entities.kind, entity_refs.conversation_id
            FROM entities
            JOIN entity_refs ON entity_refs.entity_id = entities.id
        """
        for row in store.conn.execute(query):
            entity_id = f"entity:{row['id']}"
            if entity_id not in seen_node_ids:
                nodes.append({"id": entity_id, "label": row["name"], "type": row["kind"]})
                seen_node_ids.add(entity_id)
            edges.append({"source": row["conversation_id"], "target": entity_id, "type": "mentions"})

    target = root / "graph.json"
    target.write_text(json.dumps({"nodes": nodes, "edges": edges}, indent=2), encoding="utf-8")
    return target
