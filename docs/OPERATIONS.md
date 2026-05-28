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

## MVP First-Run Setup

In the command center, fill in `First-Run Setup`:

- `ChatGPT Export`: path to `conversations.json`
- `ChatLasso SSI Folder`: path to `10_Data_Harvest\11_SSI_Raw`

Then click `Run First Setup`. ERMI saves the paths, ingests the ChatGPT export, imports the ChatLasso folder, registers it as a watched folder, scans once, and refreshes the dashboard.

CLI equivalent:

```powershell
python -m ermi --root archive setup --chatgpt-source C:\path\to\conversations.json --chatlasso-source C:\path\to\10_Data_Harvest\11_SSI_Raw --run
```

Saved setup lives at:

```text
archive\setup.json
```

## Health Diagnostics

UI:

```text
Quick Actions -> Run Diagnostics
```

CLI:

```powershell
python -m ermi --root archive diagnostics
```

Diagnostics check Python, Node, npm, SQLite, archive writability, schema version, watched folders, backups, and Git remote.
Each diagnostic includes a fix hint when attention is needed.

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

## ChatGPT Export Utilities

ERMI can use the raw `conversations.json` graph for more than ingestion. These utilities follow the `current_node` path so abandoned regenerations do not pollute the derived outputs.

```powershell
python -m ermi chatgpt-titles C:\path\to\conversations.json
python -m ermi export-chatgpt-csv C:\path\to\conversations.json
python -m ermi mine-chatgpt-code C:\path\to\conversations.json
python -m ermi chatgpt-activity C:\path\to\conversations.json --limit 10
python -m ermi export-chatgpt-obsidian C:\path\to\conversations.json --target archive\exports\chatgpt_obsidian
```

Default outputs:

- `archive/exports/chat_history.csv`
- `archive/exports/all_extracted_code.txt`
- `archive/exports/chatgpt_obsidian`

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
The Windows updater creates a backup automatically before pulling new code.

## In-App Updates

Use the Command Center `Update Center` panel:

1. Choose `KnightBot main`.
2. Click `Check GitHub`.
3. Click `Install Update` when an update is available.
4. Relaunch ERMI after a successful install so backend code changes are loaded.

The in-app updater uses fast-forward-only git updates. It creates a backup, pulls from GitHub, updates Python/npm dependencies, runs migrations, rebuilds the UI, and shows the update log. If Justin has local code changes or a diverged checkout, it blocks the update and asks for manual git review instead of overwriting anything.

## Desktop Installer

Installer entrypoint:

```text
install\Install-ERMI.cmd
```

PowerShell scripts:

- `install/Install-ERMI.ps1`: installs prerequisites/dependencies and creates shortcuts.
- `install/Launch-ERMI.ps1`: starts API/UI and opens the app.
- `install/Update-ERMI.ps1`: pulls latest changes, updates dependencies, runs migrations, and verifies the build.
- `docs/MVP_HANDOFF.md`: shortest handoff path for installation, setup, sample data, daily use, updates, and recovery.

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
