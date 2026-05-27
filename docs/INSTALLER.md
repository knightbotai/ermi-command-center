# Windows Installer

ERMI includes a Windows installer for collaborators who want a Desktop shortcut instead of running terminal commands.

## Install

1. Clone the repository.
2. Double-click:

```text
install\Install-ERMI.cmd
```

The installer will:

- Check for Git, Python, Node/npm, and GitHub CLI.
- Install missing prerequisites through `winget` when available.
- Install Python dependencies.
- Install frontend dependencies.
- Initialize the local archive.
- Create Desktop shortcuts.

## Shortcuts

The installer creates:

- `ERMI Command Center`
  - Starts the local API on `127.0.0.1:8765`.
  - Starts the Vite UI on `127.0.0.1:5173`.
  - Opens the app in the browser.

- `Update ERMI Command Center`
  - Runs `git pull --ff-only`.
  - Updates Python and npm dependencies.
  - Runs tests and frontend build.

## Notes

- The installer is per-user and writes shortcuts to the current user's Desktop.
- Local archive data stays in `archive/` and is ignored by git.
- If `winget` prompts for elevation, approve it to install missing system tools.

