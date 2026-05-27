from __future__ import annotations

import json
from pathlib import Path

from .embeddings import cosine, get_embedder
from .storage import Store


def search(root: Path, query: str, limit: int = 5) -> list[dict[str, object]]:
    query_vector = get_embedder().embed(query)
    results = []
    with Store(root / "ermi.sqlite3") as store:
        rows = store.conn.execute(
            """
            SELECT chunks.id, chunks.title, chunks.text, chunks.embedding,
                   conversations.markdown_path
            FROM chunks
            JOIN conversations ON conversations.id = chunks.conversation_id
            """
        ).fetchall()
    for row in rows:
        score = cosine(query_vector, json.loads(row["embedding"]))
        results.append(
            {
                "score": score,
                "chunk_id": row["id"],
                "title": row["title"],
                "markdown_path": row["markdown_path"],
                "preview": preview(row["text"]),
            }
        )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]


def preview(text: str, length: int = 240) -> str:
    compact = " ".join(text.split())
    if len(compact) <= length:
        return compact
    return compact[: length - 3].rstrip() + "..."

