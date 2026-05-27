# ERMI Command Center

Externalized Recursive Memory Infrastructure, built as a local-first MVP.

This implementation ingests ChatGPT-style `conversations.json` exports, preserves raw source data, creates an Obsidian-compatible Markdown vault, indexes conversations/messages/chunks/entities in SQLite, generates embeddings, supports semantic search, and exports a lightweight graph.

## Project

ERMI is maintained as one of Jusstin's KnightBot projects.

Canonical project aliases live in [docs/ALIASES.md](docs/ALIASES.md).

## Quick Start

```powershell
python -m ermi init
python -m ermi ingest C:\path\to\conversations.json
python -m ermi import-chatlasso C:\path\to\Obsidian\10_Data_Harvest\11_SSI_Raw
python -m ermi search "recursive memory architecture"
python -m ermi entities
python -m ermi graph
```

## Command Center UI

Run the local API and frontend in two terminals:

```powershell
npm run api
npm run dev:ui
```

Then open:

```text
http://127.0.0.1:5173
```

The UI provides a local command center for ingesting exports, semantic recall, entity inspection, graph export, archive counts, and operations logs.

The ingest panel supports both raw ChatGPT exports and ChatLasso SSI Markdown output, making ChatLasso the capture/synthesis layer and ERMI the durable recall/index layer.

## Windows Desktop Installer

After cloning the repo on Windows, double-click:

```text
install\Install-ERMI.cmd
```

The installer checks core prerequisites, installs ERMI dependencies, initializes the local archive, and creates two Desktop shortcuts:

- `ERMI Command Center`
- `Update ERMI Command Center`

## Update Workflow

```powershell
git pull
npm install
python -m pip install -e ".[dev,ml]"
npm run api
npm run dev:ui
```

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md), [docs/INSTALLER.md](docs/INSTALLER.md), [docs/OPERATIONS.md](docs/OPERATIONS.md), and [CHANGELOG.md](CHANGELOG.md) for ongoing project notes.

See [docs/CHATLASSO_INTEGRATION.md](docs/CHATLASSO_INTEGRATION.md) for the joined ChatLasso -> ERMI workflow.

By default ERMI writes to:

```text
archive/
  raw/
  vault/
    conversations/
  ermi.sqlite3
  graph.json
```

## Optional ML Embeddings

Without optional packages, ERMI uses a deterministic local hashing embedder so the system works offline immediately. For stronger semantic retrieval, install:

```powershell
pip install -e .[ml]
```

Then re-run ingestion so chunk embeddings are regenerated with `sentence-transformers`.

## Design Notes

- Raw source files are copied, never overwritten.
- Markdown and database rows are derived artifacts and can be rebuilt.
- Chunk embeddings are stored in SQLite for a simple local MVP.
- ChatLasso SSI payloads are imported as first-class memory artifacts.
- Entity extraction is deliberately conservative and local. It can be replaced later with an LLM or NLP pipeline.
- The graph export is JSON for portability; NetworkX, Neo4j, or RDF can be layered on later.
