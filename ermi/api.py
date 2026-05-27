from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .chatlasso import import_chatlasso, import_chatlasso_payload
from .diagnostics import run_diagnostics
from .exports import activity_summary, export_chat_csv, export_obsidian_second_brain, list_chat_titles, mine_code_blocks
from .flags import list_flags
from .graph import export_graph
from .ingest import ingest_export, init_archive
from .ops import backup_archive, restore_archive
from .review import list_import_reviews, set_import_review_status
from .search import search
from .setup import load_setup, run_first_setup, save_setup
from .storage import LATEST_SCHEMA_VERSION, Store
from .timeline import concept_timeline
from .watch import add_watcher, load_watchers, scan_chatlasso_watchers


class IngestRequest(BaseModel):
    source: str


class ImportRequest(BaseModel):
    source: str


class ChatLassoPayloadRequest(BaseModel):
    title: str = "ChatLasso SSI"
    content: str


class WatchRequest(BaseModel):
    source: str


class RestoreRequest(BaseModel):
    source: str


class ExportRequest(BaseModel):
    source: str
    target: str | None = None


class SetupRequest(BaseModel):
    chatgpt_source: str = ""
    chatlasso_source: str = ""


def create_app(default_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="ERMI Command Center API")
    root = (default_root or Path("archive")).resolve()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
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
            "watchers": load_watchers(root),
        }

    @app.get("/api/schema")
    def schema() -> dict[str, object]:
        init_archive(root)
        with Store(root / "ermi.sqlite3") as store:
            return {"current": store.schema_version(), "latest": LATEST_SCHEMA_VERSION}

    @app.get("/api/setup")
    def setup_config() -> dict[str, object]:
        return {"config": load_setup(root)}

    @app.post("/api/setup")
    def save_setup_config(request: SetupRequest) -> dict[str, object]:
        return {"config": save_setup(root, request.model_dump())}

    @app.post("/api/setup/run")
    def run_setup_config(request: SetupRequest) -> dict[str, object]:
        try:
            return run_first_setup(root, request.model_dump())
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/diagnostics")
    def diagnostics() -> dict[str, object]:
        return run_diagnostics(root)

    @app.get("/api/search")
    def semantic_search(
        q: Annotated[str, Query(min_length=1)],
        limit: Annotated[int, Query(ge=1, le=25)] = 8,
        mode: str | None = None,
        status: str | None = None,
        archetype: str | None = None,
        regression: bool | None = None,
        audit_pass: bool | None = None,
        project: str | None = None,
        identity: str | None = None,
    ) -> dict[str, object]:
        filters = {
            "mode": mode,
            "status": status,
            "archetype": archetype,
            "regression": regression,
            "audit_pass": audit_pass,
            "project": project,
            "identity": identity,
        }
        return {"query": q, "filters": filters, "results": search(root, q, limit, filters)}

    @app.post("/api/ingest")
    def ingest(request: IngestRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        if not source.exists():
            raise HTTPException(status_code=404, detail=f"Source not found: {source}")
        try:
            return {"source": str(source), "stats": ingest_export(source, root)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/export/chatgpt-csv")
    def export_chatgpt_csv_endpoint(request: ExportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        target = Path(request.target).expanduser().resolve() if request.target else root / "exports" / "chat_history.csv"
        try:
            return {"target": str(target), "stats": export_chat_csv(source, target)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/export/chatgpt-code")
    def export_chatgpt_code_endpoint(request: ExportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        target = Path(request.target).expanduser().resolve() if request.target else root / "exports" / "all_extracted_code.txt"
        try:
            return {"target": str(target), "stats": mine_code_blocks(source, target)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/export/chatgpt-obsidian")
    def export_chatgpt_obsidian_endpoint(request: ExportRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        target = Path(request.target).expanduser().resolve() if request.target else root / "exports" / "chatgpt_obsidian"
        try:
            return {"target": str(target), "stats": export_obsidian_second_brain(source, target)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/export/chatgpt-titles")
    def export_chatgpt_titles(source: str) -> dict[str, object]:
        try:
            titles = list_chat_titles(Path(source).expanduser().resolve())
            return {"titles": titles, "count": len(titles)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/export/chatgpt-activity")
    def export_chatgpt_activity(source: str, limit: Annotated[int, Query(ge=1, le=50)] = 5) -> dict[str, object]:
        try:
            return {"activity": activity_summary(Path(source).expanduser().resolve(), limit)}
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

    @app.post("/api/import/chatlasso-payload")
    def import_chatlasso_payload_endpoint(request: ChatLassoPayloadRequest) -> dict[str, object]:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content is required.")
        try:
            return {"source": "payload", "stats": import_chatlasso_payload(request.title, request.content, root)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/watchers")
    def watchers() -> dict[str, object]:
        return {"chatlasso": load_watchers(root)}

    @app.post("/api/watchers/chatlasso")
    def add_chatlasso_watcher(request: WatchRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        try:
            return {"chatlasso": add_watcher(root, source)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/watchers/chatlasso/scan")
    def scan_chatlasso() -> dict[str, object]:
        try:
            return {"stats": scan_chatlasso_watchers(root), "chatlasso": load_watchers(root)}
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

    @app.get("/api/flags")
    def flags(limit: Annotated[int, Query(ge=1, le=200)] = 50) -> dict[str, object]:
        return {"flags": list_flags(root, limit)}

    @app.get("/api/timeline")
    def timeline(limit: Annotated[int, Query(ge=1, le=300)] = 100) -> dict[str, object]:
        return {"events": concept_timeline(root, limit)}

    @app.get("/api/review/imports")
    def review_imports() -> dict[str, object]:
        return {"imports": list_import_reviews(root)}

    @app.post("/api/review/imports/{conversation_id}/accept")
    def accept_import(conversation_id: str) -> dict[str, object]:
        try:
            return set_import_review_status(root, conversation_id, "accepted")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Import not found: {conversation_id}") from exc

    @app.post("/api/review/imports/{conversation_id}/reject")
    def reject_import(conversation_id: str) -> dict[str, object]:
        try:
            return set_import_review_status(root, conversation_id, "rejected")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Import not found: {conversation_id}") from exc

    @app.post("/api/backup")
    def backup() -> dict[str, object]:
        return {"path": str(backup_archive(root))}

    @app.post("/api/restore")
    def restore(request: RestoreRequest) -> dict[str, object]:
        source = Path(request.source).expanduser().resolve()
        try:
            return {"path": str(restore_archive(root, source))}
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Backup not found: {source}") from exc

    @app.post("/api/graph/export")
    def graph_export() -> dict[str, object]:
        path = export_graph(root)
        return {"path": str(path)}

    return app


def scalar(store: Store, sql: str) -> int:
    return int(store.conn.execute(sql).fetchone()[0])


app = create_app()
