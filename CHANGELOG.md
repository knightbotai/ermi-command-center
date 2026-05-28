# Changelog

All notable changes to ERMI Command Center will be documented here.

## [0.1.0] - 2026-05-27

### Added

- Inno Setup project for building a traditional Windows setup wizard executable.
- Installer branding assets and generated bitmap/icon pipeline.
- Optional code-signing build script lane for `.pfx` certificates and `signtool.exe`.
- Certificate-store thumbprint signing support for Windows code-signing certificates.
- Internal dev self-signing mode with public certificate export for controlled test machines.
- SHA-256 checksum generation for installer release artifacts.
- Verified Windows SDK signing tools and internal dev-signed installer generation on the local build machine.
- Signed Windows installer walkthrough documentation.
- Android/Termux install and launch scripts for mobile local MVP use.
- Capacitor Android project and build script for a sideload APK UI shell that connects to the local Termux backend.
- Fixed duplicate Concept Evolution Timeline rows that caused repeated React key warnings after ChatLasso imports.
- In-app Update Center for checking GitHub, creating a backup, fast-forward updating, running migrations, rebuilding the UI, and reporting update logs.
- Root-level `START-HERE.cmd` for one-click post-clone setup, diagnostics, shortcut creation, launch, and browser open.
- DeeTorch post-clone setup guide with one-click usage and optional GitHub remote handoff notes.
- MVP handoff guide with install, setup, sample-data, daily-use, update, and recovery notes.
- Sample ChatGPT and ChatLasso data for smoke testing without personal exports.
- Actionable diagnostic fix hints in API and command-center health checks.
- Open-folder shortcuts for archive, vault, backups, exports, and sample data.
- Pre-update backup step in the Windows updater.
- First-run setup profile for saving ChatGPT export and ChatLasso SSI folder paths.
- One-click setup runner that performs initial ChatGPT ingest, ChatLasso import, watcher registration, and scan.
- MVP health diagnostics for Python, Node, npm, SQLite, schema, archive writes, watch folders, backups, and Git remote.
- Command center setup and diagnostics panels.
- True-path ChatGPT export reconstruction using `current_node`, preventing abandoned regenerated branches from entering the archive.
- ChatGPT export utility commands for title health checks, CSV export, assistant code-block mining, activity summaries, and categorized Obsidian-ready Markdown export.
- API endpoints for ChatGPT CSV/code/Obsidian exports, title listing, and activity summaries.
- ChatLasso watched-folder registration and scan/import workflow.
- SQLite schema versioning with additive migrations for existing local archives.
- Dedicated ChatLasso SSI metadata storage for mode, archetype, status, domain nodes, audit status, hash beacon, loss report, regression flags, source path, and source hash.
- Hybrid search combining embedding similarity with SQLite FTS5 lexical recall and structured filters.
- Regression/contradiction flags API and command-center flag panel.
- Concept evolution timeline API and command-center timeline panel.
- Richer graph export with ChatLasso mode/archetype/status nodes plus command-center graph preview.
- Import review queue with accept/reject actions for flagged or malformed imports.
- Project and identity segmentation defaults for ERMI, ChatLasso, KnightBot, and Jusstin/DeeTorch.
- Backup/restore CLI and API support for local archive recovery.
- Hardened installer, launcher, updater, and frontend scripts for Windows PATH issues.
- ChatLasso SSI Markdown importer for files or folders.
- Direct ChatLasso payload import endpoint for browser-to-ERMI handoff.
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
