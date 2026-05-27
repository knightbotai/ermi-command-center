# Contributing

This repository is maintained as a KnightBot project for Jusstin.

## Development Loop

```powershell
python -m pip install -e ".[dev,ml]"
npm install
python -m pytest -q
npm run build
```

## Commit Expectations

- Keep raw archives, SQLite databases, generated screenshots, logs, and dependency folders out of git.
- Update `CHANGELOG.md` when behavior, commands, UI, or setup changes.
- Update docs when user-facing workflows change.
