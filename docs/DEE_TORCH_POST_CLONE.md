# DeeTorch Post-Clone Setup

This is the shortest path for Jusstin/DeeTorch after cloning ERMI.

## One Click

From the repo root, double-click:

```text
START-HERE.cmd
```

That script:

- Installs or repairs Git, Python, Node.js, npm, and GitHub CLI when available through `winget`.
- Installs ERMI Python dependencies.
- Installs frontend dependencies.
- Initializes `archive`.
- Runs health diagnostics.
- Creates Desktop shortcuts.
- Starts ERMI API and UI.
- Opens the command center in the browser.

## First-Run Setup

To test without personal exports, paste these sample paths into `First-Run Setup`:

```text
sample_data\chatgpt\conversations.json
sample_data\chatlasso\11_SSI_Raw
```

Then click:

```text
Run First Setup
```

## Daily Shortcuts

After setup, use:

```text
ERMI Command Center
Update ERMI Command Center
```

Inside ERMI, use the `Update Center` panel to check GitHub and install updates without opening PowerShell. The updater creates a backup before pulling new code.

## Copying To DeeTorch GitHub

Recommended options:

- Fork or import `knightbotai/ermi-command-center` into `DeeTorch/ermi-command-center`.
- Keep `knightbotai` as an upstream remote if you want KnightBot updates later.

Suggested remote layout:

```powershell
git remote rename origin upstream
git remote add origin https://github.com/DeeTorch/ermi-command-center.git
git push -u origin main
git push origin v0.1.0-mvp
```

To pull KnightBot updates later:

```powershell
git fetch upstream
git merge upstream/main
```
