# ChatLasso Integration

ChatLasso and ERMI are designed to work as one full memory pipeline.

## Roles

ChatLasso is the capture and synthesis layer:

- Extracts live LLM conversations from browser DOMs.
- Runs SSI synthesis through Gemini, Ollama, or LM Studio.
- Produces structured SSI Markdown.
- Syncs outputs into Obsidian.

ERMI is the archive and recall layer:

- Preserves raw SSI Markdown.
- Writes canonical vault copies.
- Chunks SSI sections.
- Generates embeddings.
- Indexes entities/domain nodes.
- Provides semantic search, graph export, and local command-center operations.

## Data Flow

```text
Live LLM session
  -> ChatLasso bookmarklet / relay
  -> SSI synthesis
  -> Obsidian 10_Data_Harvest/11_SSI_Raw
  -> ERMI import-chatlasso
  -> SQLite + embeddings + vault/chatlasso
  -> semantic recall + graph export
```

## CLI Import

```powershell
python -m ermi import-chatlasso C:\path\to\10_Data_Harvest\11_SSI_Raw
```

You can also import a single `.md` file:

```powershell
python -m ermi import-chatlasso C:\path\to\example_SSI.md
```

## Command Center Import

1. Start ERMI.
2. In the ingest panel, select `ChatLasso SSI`.
3. Paste a file or folder path.
4. Click `Import SSI`.

## Mapping

| ChatLasso SSI | ERMI |
| --- | --- |
| Original Markdown | `archive/raw/chatlasso` |
| Canonical copy | `archive/vault/chatlasso` |
| Headings | Semantic chunks |
| `domain_nodes` | Concept entities |
| SSI body | Searchable memory text |
| Filename/title | Conversation title |

## Next Seamless Step

ChatLasso can call ERMI directly after SSI export, removing the manual path paste:

```text
ChatLasso Send to ERMI -> POST http://127.0.0.1:8765/api/import/chatlasso-payload
```

The payload shape is:

```json
{
  "title": "SSI title",
  "content": "full SSI Markdown"
}
```

ERMI preserves that payload under `archive/raw/chatlasso_payloads` and indexes it as a ChatLasso memory.
