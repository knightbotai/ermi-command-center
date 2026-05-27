# ERMI MVP Handoff

ERMI Command Center is ready for local MVP use.

## Install

Double-click:

```text
install\Install-ERMI.cmd
```

This installs prerequisites, Python dependencies, frontend dependencies, initializes `archive`, and creates Desktop shortcuts.

## Launch

Use the Desktop shortcut:

```text
ERMI Command Center
```

The app opens at:

```text
http://127.0.0.1:5173
```

## First Setup

In `First-Run Setup`, enter:

- `ChatGPT Export`: path to `conversations.json`
- `ChatLasso SSI Folder`: path to `10_Data_Harvest\11_SSI_Raw`

Click `Run First Setup`.

ERMI will ingest ChatGPT, import ChatLasso SSI, register the ChatLasso folder for scans, and refresh the dashboard.

## Test With Sample Data

Use these paths if you want to verify the app before using personal data:

```text
sample_data\chatgpt\conversations.json
sample_data\chatlasso\11_SSI_Raw
```

## Daily Use

- Search from `Semantic Search`.
- Add ChatLasso folders in `Watched Folders`.
- Click `Scan Now` after ChatLasso writes new SSI files.
- Review flagged imports in `Import Review Queue`.
- Click `Backup` before major changes.
- Click `Run Diagnostics` if anything feels off.

## Update

Use the Desktop shortcut:

```text
Update ERMI Command Center
```

The updater creates a backup before pulling the latest code, updates dependencies, runs migrations, and verifies tests/build.

## Recovery

Backups are written under:

```text
archive\backups
```

Restore from PowerShell:

```powershell
python -m ermi --root archive restore C:\path\to\archive\backups\ermi-backup-YYYYMMDD-HHMMSS
```
