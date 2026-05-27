from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .chatlasso import import_chatlasso
from .graph import export_graph
from .ingest import ingest_export, init_archive
from .search import search
from .storage import Store


class IngestRequest(BaseModel):
    source: str


class ImportRequest(BaseModel):
    source: str


def create_app(default_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="ERMI Command Center API")
    root = (default_root or Path("archive")).resolve()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/status")
    def status() -> dict[str, object]:
        init_archive(root)
        with Store(root / "ermi.sqlite3") as store:
            counts = {
                "conversations": scalar(store, "SELECT count(*) FROM conversations"),
                "messages": scalar(store, "SELECT count(*) FROM messages"),
                "chunks": scalar(store, "SELECT count(*) FROM chunks"),
                "entities": scalar(store, "SELECT count(*) FROM entities"),
                "sources": scalar(store, "SELECT count(*) FROM sources"),
            }
            last_source = store.conn.execute(
                "SELECT imported_at, path FROM sources ORDER BY imported_at DESC LIMIT 1"
            ).fetchone()
        return {
            "archiveRoot": str(root),
            "database": str(root / "ermi.sqlite3"),
            "healthy": True,
            "counts": counts,
            "lastIngest": dict(last_source) if last_source else None,
        }

    @app.get("/api/search")
    def semantic_search(
        q: Annotated[str, Query(min_length=1)],
        limit: Annotated[int, Query(ge=1, le=25)] = 8,
    ) -> dict[str, object]:
        return {"query": q, "results": search(root, q, limit)}

    @app.post("/api/ingest")
    def ingest(request: IngestRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        if not source.exists():
            raise HTTPException(status_code=404, detail=f"Source not found: {source}")
        try:
            return {"source": str(source), "stats": ingest_export(source, root)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/import/chatlasso")
    def import_chatlasso_endpoint(request: ImportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        if not source.exists():
            raise HTTPException(status_code=404, detail=f"Source not found: {source}")
        try:
            return {"source": str(source), "stats": import_chatlasso(source, root)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/entities")
    def entities(limit: Annotated[int, Query(ge=1, le=200)] = 50) -> dict[str, object]:
        init_archive(root)
        with Store(root / "ermi.sqlite3") as store:
            rows = store.conn.execute(
                "SELECT name, kind, score FROM entities ORDER BY score DESC, name LIMIT ?",
                (limit,),
            ).fetchall()
        return {"entities": [dict(row) for row in rows]}

    @app.get("/api/graph")
    def graph() -> dict[str, object]:
        init_archive(root)
        path = export_graph(root)
        return json.loads(path.read_text(encoding="utf-8"))

    @app.post("/api/graph/export")
    def graph_export() -> dict[str, object]:
        path = export_graph(root)
        return {"path": str(path)}

    return app


def scalar(store: Store, sql: str) -> int:
    return int(store.conn.execute(sql).fetchone()[0])


app = create_app()
