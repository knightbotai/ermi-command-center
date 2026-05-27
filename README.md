# ERMI Command Center

Externalized Recursive Memory Infrastructure, built as a local-first MVP.

This implementation ingests ChatGPT-style `conversations.json` exports and ChatLasso SSI Markdown, preserves raw source data, creates an Obsidian-compatible Markdown vault, indexes conversations/messages/chunks/entities/SSI metadata in SQLite, generates embeddings, supports hybrid search, surfaces regression flags, and exports a lightweight graph.

## Project

ERMI is maintained as one of Jusstin's KnightBot projects.

Canonical project aliases live in [docs/ALIASES.md](docs/ALIASES.md).

## Quick Start

```powershell
python -m ermi init
python -m ermi setup --chatgpt-source C:\path\to\conversations.json --chatlasso-source C:\path\to\Obsidian\10_Data_Harvest\11_SSI_Raw --run
python -m ermi diagnostics
python -m ermi chatgpt-titles C:\path\to\conversations.json
python -m ermi ingest C:\path\to\conversations.json
python -m ermi export-chatgpt-csv C:\path\to\conversations.json
python -m ermi mine-chatgpt-code C:\path\to\conversations.json
python -m ermi chatgpt-activity C:\path\to\conversations.json
python -m ermi export-chatgpt-obsidian C:\path\to\conversations.json
python -m ermi import-chatlasso C:\path\to\Obsidian\10_Data_Harvest\11_SSI_Raw
python -m ermi watch-chatlasso C:\path\to\Obsidian\10_Data_Harvest\11_SSI_Raw --once
python -m ermi search "recursive memory architecture"
python -m ermi flags
python -m ermi timeline
python -m ermi entities
python -m ermi graph
python -m ermi backup
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

The UI provides a local command center for first-run setup, health diagnostics, ingesting exports, watched ChatLasso folders, hybrid recall, entity inspection, regression flags, import review, concept timeline, graph export, backups, archive counts, and operations logs.

The ingest panel supports both raw ChatGPT exports and ChatLasso SSI Markdown output, making ChatLasso the capture/synthesis layer and ERMI the durable recall/index layer. ChatGPT imports follow the export's `current_node` path, so regenerated/abandoned branches stay out of the main archive. ChatLasso can also POST SSI Markdown directly to ERMI at `http://127.0.0.1:8765/api/import/chatlasso-payload`. ERMI preserves ChatLasso `mode`, `archetype`, `status`, `hash_beacon`, `loss_report`, audit state, regression flags, and domain nodes as structured metadata.

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
python -m ermi --root archive migrate
npm run api
npm run dev:ui
```

See [docs/MVP_HANDOFF.md](docs/MVP_HANDOFF.md), [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md), [docs/INSTALLER.md](docs/INSTALLER.md), [docs/OPERATIONS.md](docs/OPERATIONS.md), and [CHANGELOG.md](CHANGELOG.md) for ongoing project notes.

See [docs/CHATLASSO_INTEGRATION.md](docs/CHATLASSO_INTEGRATION.md) for the joined ChatLasso -> ERMI workflow.

By default ERMI writes to:

```text
archive/
  setup.json
  raw/
  vault/
    conversations/
  ermi.sqlite3
  graph.json
  watchers.json
  backups/
```

Sample smoke-test data lives under:

```text
sample_data/
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
- ChatGPT `mapping` graphs are reconstructed from the final `current_node` path when available.
- Chunk embeddings are stored in SQLite for a simple local MVP.
- ChatLasso SSI payloads are imported as first-class memory artifacts with schema-versioned metadata.
- Hybrid search uses local embeddings plus SQLite FTS5, so exact phrases and semantic matches both matter.
- Flagged imports enter the review queue; clean imports are accepted automatically.
- Entity extraction is deliberately conservative and local. It can be replaced later with an LLM or NLP pipeline.
- The graph export is JSON for portability; NetworkX, Neo4j, or RDF can be layered on later.
