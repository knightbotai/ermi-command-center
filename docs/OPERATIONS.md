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

If a fresh PowerShell window cannot find Python or npm, use the installed defaults:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m pytest -q
$env:Path = "C:\Program Files\nodejs;$env:Path"; npm run build
```

## ChatLasso Import

CLI:

```powershell
python -m ermi import-chatlasso C:\path\to\10_Data_Harvest\11_SSI_Raw
```

Watched-folder scan:

```powershell
python -m ermi watch-chatlasso C:\path\to\10_Data_Harvest\11_SSI_Raw --once
```

Continuous watcher:

```powershell
python -m ermi watch-chatlasso C:\path\to\10_Data_Harvest\11_SSI_Raw --interval 15
```

UI:

1. Open `ERMI Command Center`.
2. In `Ingest`, select `ChatLasso SSI`.
3. Paste a single `.md` file path or the folder where ChatLasso writes SSI files.
4. Click `Import SSI`.

For recurring imports, use `Watched Folders`, paste the ChatLasso SSI folder, and click `Scan Now`.

## Schema, Flags, Timeline, Review

```powershell
python -m ermi --root archive migrate
python -m ermi --root archive flags
python -m ermi --root archive timeline
python -m ermi --root archive review
```

Flagged ChatLasso imports enter `pending_review` when ERMI sees a regression contradiction, failed audit status, or missing hash beacon. Use the command center review buttons or:

```powershell
python -m ermi --root archive accept-import <conversation_id>
python -m ermi --root archive reject-import <conversation_id>
```

## Backup / Restore

```powershell
python -m ermi --root archive backup
python -m ermi --root archive restore C:\path\to\archive\backups\ermi-backup-YYYYMMDD-HHMMSS
```

Backups include SQLite, raw source files, vault Markdown, watcher config, graph export, and a changelog snapshot when present.

## Desktop Installer

Installer entrypoint:

```text
install\Install-ERMI.cmd
```

PowerShell scripts:

- `install/Install-ERMI.ps1`: installs prerequisites/dependencies and creates shortcuts.
- `install/Launch-ERMI.ps1`: starts API/UI and opens the app.
- `install/Update-ERMI.ps1`: pulls latest changes, updates dependencies, runs migrations, and verifies the build.

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
