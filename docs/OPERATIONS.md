# Operations

## Local Services

API:

```powershell
npm run api
```

UI:

```powershell
npm run dev:ui
```

Default URLs:

- UI: `http://127.0.0.1:5173`
- API: `http://127.0.0.1:8765`

## Verification

```powershell
python -m pytest -q
npm run build
```

## GitHub Publishing

The active GitHub owner is `knightbotai`.

Recommended repository name:

```text
ermi-command-center
```

Recommended description:

```text
Local-first Externalized Recursive Memory Infrastructure command center for Jusstin's KnightBot projects.
```

After GitHub CLI authentication:

```powershell
gh repo create knightbotai/ermi-command-center --private --description "Local-first Externalized Recursive Memory Infrastructure command center for Jusstin's KnightBot projects." --source . --remote origin --push
```

If the repository already exists:

```powershell
git remote add origin https://github.com/knightbotai/ermi-command-center.git
git push -u origin main
```

## Release Hygiene

- Update `CHANGELOG.md` for each meaningful iteration.
- Keep generated archives, databases, logs, screenshots, and `node_modules` out of git.
- Run tests and frontend build before pushing.
