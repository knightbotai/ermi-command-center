# Getting Started

ERMI Command Center is a local-first cognitive archive tool for Jusstin's KnightBot project workspace.

## Requirements

- Python 3.13+
- Node.js LTS
- npm
- GitHub CLI

Optional but recommended:

- `sentence-transformers` for stronger semantic embeddings
- `pnpm` or Yarn for alternate JavaScript package workflows

## Install

For the Desktop shortcut flow on Windows, double-click:

```text
install\Install-ERMI.cmd
```

Manual setup:

```powershell
python -m pip install -e ".[dev,ml]"
npm install
```

## Run

Use two terminals.

Terminal 1:

```powershell
npm run api
```

Terminal 2:

```powershell
npm run dev:ui
```

Open:

```text
http://127.0.0.1:5173
```

## Ingest Data

From the UI, paste the absolute path to a ChatGPT `conversations.json` export and run ingest.

From the CLI:

```powershell
python -m ermi ingest C:\path\to\conversations.json
```

ERMI copies the raw source into `archive/raw` and writes derived artifacts into the vault and SQLite database.
