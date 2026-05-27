# Architecture

ERMI follows the roadmap from the Externalized Recursive Memory Infrastructure spec.

## Current MVP Layers

1. Raw archive
   - Preserves original source exports in `archive/raw`.
   - Raw files are copied with a content hash in the filename.

2. Markdown vault
   - Writes Obsidian-compatible conversation files.
   - Includes frontmatter for title, timestamps, tags, participants, and embedding status.

3. SQLite index
   - Stores sources, conversations, messages, chunks, entities, and entity references.
   - Keeps derived data rebuildable from raw source.

4. Embeddings
   - Uses `sentence-transformers` when available.
   - Falls back to deterministic local hashing embeddings so the system remains offline-capable.

5. Retrieval
   - Provides semantic search over chunks.
   - Returns score, title, preview, and vault file path.

6. Graph export
   - Exports a portable `graph.json` with conversation, chunk, and entity nodes.

7. Command center
   - FastAPI backend serves local operations.
   - React/Vite frontend provides the visual command surface.

8. ChatLasso bridge
   - Imports ChatLasso SSI Markdown files as first-class ERMI memory artifacts.
   - Preserves raw SSI files under `archive/raw/chatlasso`.
   - Writes canonical ERMI vault copies under `archive/vault/chatlasso`.
   - Chunks SSI headings, embeds sections, and indexes domain nodes/entities.

## Next Architecture Targets

- File picker and watched folder ingestion.
- Dedicated graph visualization.
- Direct ChatLasso export-to-ERMI handoff.
- Richer entity extraction and relationship typing.
- ChromaDB/LanceDB or pgvector backing store.
- Periodic synthesis and concept evolution tracking.
