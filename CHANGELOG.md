# Changelog

All notable changes to ERMI Command Center will be documented here.

## [0.1.0] - 2026-05-27

### Added

- ChatLasso SSI Markdown importer for files or folders.
- Command center ingest mode toggle for ChatGPT exports versus ChatLasso SSI payloads.
- ChatLasso integration documentation for the combined capture -> archive -> recall workflow.
- Local ERMI Python package with CLI commands for archive initialization, ingestion, semantic search, entity listing, and graph export.
- Immutable raw archive preservation under `archive/raw`.
- Obsidian-compatible Markdown vault export under `archive/vault/conversations`.
- SQLite storage for sources, conversations, messages, chunks, entities, and entity references.
- Deterministic fallback embedder plus optional `sentence-transformers` embedding support.
- FastAPI backend exposing status, ingest, search, entities, and graph endpoints.
- React/Vite command center UI with semantic search, ingest controls, entity panel, graph overview, archive counts, and operations log.
- Project documentation for KnightBot/Jusstin handoff and local operations.
- Canonical alias map for KnightBot, Jusstin, and Codee.
- Windows single-click installer and Desktop shortcuts for launching/updating ERMI Command Center.

### Verified

- Python test suite passes with `pytest`.
- Frontend production build passes with Vite.
- Local API and UI respond on `127.0.0.1`.
