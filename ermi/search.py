from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .embeddings import cosine, get_embedder
from .storage import Store


def search(
    root: Path,
    query: str,
    limit: int = 5,
    filters: dict[str, str | bool | None] | None = None,
) -> list[dict[str, object]]:
    filters = filters or {}
    query_vector = get_embedder().embed(query)
    lexical = lexical_scores(root, query)
    results: list[dict[str, object]] = []
    with Store(root / "ermi.sqlite3") as store:
        rows = store.conn.execute(
            """
            SELECT chunks.id, chunks.conversation_id, chunks.title, chunks.text, chunks.embedding,
                   chunks.tags, conversations.markdown_path, conversations.project,
                   conversations.identity, conversations.import_status,
                   chatlasso_metadata.mode, chatlasso_metadata.archetype,
                   chatlasso_metadata.status AS ssi_status,
                   chatlasso_metadata.audit_pass_status,
                   chatlasso_metadata.regression_contradictions_found
            FROM chunks
            JOIN conversations ON conversations.id = chunks.conversation_id
            LEFT JOIN chatlasso_metadata ON chatlasso_metadata.conversation_id = conversations.id
            """
        ).fetchall()
    for row in rows:
        if not row_matches_filters(row, filters):
            continue
        score = cosine(query_vector, json.loads(row["embedding"]))
        lexical_score = lexical.get(row["id"], lexical_fallback(query, row["title"], row["text"]))
        combined = (score * 0.7) + (lexical_score * 0.3)
        results.append(
            {
                "score": combined,
                "semantic_score": score,
                "lexical_score": lexical_score,
                "chunk_id": row["id"],
                "conversation_id": row["conversation_id"],
                "title": row["title"],
                "markdown_path": row["markdown_path"],
                "preview": preview(row["text"]),
                "tags": json.loads(row["tags"] or "[]"),
                "project": row["project"],
                "identity": row["identity"],
                "import_status": row["import_status"],
                "mode": row["mode"],
                "archetype": row["archetype"],
                "status": row["ssi_status"],
                "audit_pass_status": none_or_bool(row["audit_pass_status"]),
                "regression_contradictions_found": bool(row["regression_contradictions_found"]),
            }
        )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]


def lexical_scores(root: Path, query: str) -> dict[str, float]:
    if not query.strip():
        return {}
    try:
        with Store(root / "ermi.sqlite3") as store:
            rows = store.conn.execute(
                """
                SELECT chunk_id, bm25(chunks_fts) AS rank
                FROM chunks_fts
                WHERE chunks_fts MATCH ?
                ORDER BY rank
                LIMIT 100
                """,
                (fts_query(query),),
            ).fetchall()
    except Exception:
        return {}
    if not rows:
        return {}
    worst = max(abs(float(row["rank"])) for row in rows) or 1.0
    return {row["chunk_id"]: max(0.0, 1.0 - (abs(float(row["rank"])) / worst)) for row in rows}


def fts_query(query: str) -> str:
    tokens = [token.replace('"', "") for token in query.split() if token.strip()]
    return " OR ".join(f'"{token}"' for token in tokens) or '""'


def lexical_fallback(query: str, title: str, text: str) -> float:
    tokens = {token.lower() for token in query.split() if token.strip()}
    if not tokens:
        return 0.0
    haystack = f"{title} {text}".lower()
    hits = sum(1 for token in tokens if token in haystack)
    return hits / len(tokens)


def row_matches_filters(row: Any, filters: dict[str, str | bool | None]) -> bool:
    comparisons = {
        "mode": row["mode"],
        "status": row["ssi_status"],
        "archetype": row["archetype"],
        "project": row["project"],
        "identity": row["identity"],
    }
    for key, current in comparisons.items():
        expected = filters.get(key)
        if expected and str(current or "").lower() != str(expected).lower():
            return False
    regression = filters.get("regression")
    if regression is not None and bool(row["regression_contradictions_found"]) != bool(regression):
        return False
    audit_pass = filters.get("audit_pass")
    if audit_pass is not None and none_or_bool(row["audit_pass_status"]) != bool(audit_pass):
        return False
    return True


def none_or_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def preview(text: str, length: int = 240) -> str:
    compact = " ".join(text.split())
    if len(compact) <= length:
        return compact
    return compact[: length - 3].rstrip() + "..."
