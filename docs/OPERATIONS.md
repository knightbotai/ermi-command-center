# Operations

## Local Services

Desktop shortcut:

```text
ERMI Command Center
```

The shortcut runs `install/Launch-ERMI.ps1`, starts the API/UI if needed, and opens the browser.

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

## Desktop Installer

Installer entrypoint:

```text
install\Install-ERMI.cmd
```

PowerShell scripts:

- `install/Install-ERMI.ps1`: installs prerequisites/dependencies and creates shortcuts.
- `install/Launch-ERMI.ps1`: starts API/UI and opens the app.
- `install/Update-ERMI.ps1`: pulls latest changes, updates dependencies, and verifies the build.

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
