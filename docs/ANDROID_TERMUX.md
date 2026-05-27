# Android / Termux MVP

ERMI can run on Android today through Termux as a local mobile command center.

## What Works

- Python FastAPI backend.
- React/Vite command center UI.
- SQLite archive.
- ChatGPT export ingestion.
- ChatLasso SSI folder/file import if files are accessible to Termux.
- Search, diagnostics, backup, timeline, flags, and review queue.

## Install Termux

Use the current Termux app from F-Droid or the official Termux distribution. Avoid stale Play Store builds.

## Setup

In Termux:

```bash
termux-setup-storage
pkg update -y
pkg install -y git
git clone https://github.com/knightbotai/ermi-command-center.git
cd ermi-command-center
bash install/termux-install.sh
```

## Launch

```bash
cd ermi-command-center
bash install/termux-launch.sh
```

Then open:

```text
http://127.0.0.1:5173
```

The launch script tries `termux-open-url` when available.

## Android File Paths

After `termux-setup-storage`, common Android folders appear under:

```text
~/storage/downloads
~/storage/shared
```

Example ChatGPT export path:

```text
~/storage/downloads/conversations.json
```

## Sideload APK Path

ERMI now includes a Capacitor-based sideload APK lane. It bundles the ERMI UI into an Android WebView and talks to the local Termux backend at:

```text
http://127.0.0.1:8765
```

This avoids Google Play entirely. Install the APK with Android's normal package installer or an APK installer you trust.

## Build APK On Windows

From the repo root:

```powershell
.\install\Build-AndroidApk.ps1 -InstallTooling
```

The script installs or locates:

- Temurin JDK 21.
- Android SDK command-line tools from the official Android Developers distribution.
- Android SDK Platform 36, Build Tools, and Platform Tools.
- Capacitor Android dependencies.

The APK output path is:

```text
android\app\build\outputs\apk\debug\app-debug.apk
```

A checksum is written beside it:

```text
android\app\build\outputs\apk\debug\app-debug.apk.sha256.txt
```

Install it on Android, then start ERMI in Termux:

```bash
cd ermi-command-center
bash install/termux-launch.sh
```

Open the ERMI APK. It should connect to the Termux API running on `127.0.0.1:8765`.

## APK Architecture

Current APK MVP:

- Capacitor Android shell.
- Bundled ERMI React UI.
- API base set by `.env.android`.
- Backend still runs in Termux.

Future bundled-backend APK:

- Package Python or port backend to a mobile-friendly runtime.
- Store SQLite archive in app-private storage.
- Add Android share-sheet import for ChatGPT exports and SSI Markdown.
- Add file picker for Downloads and Obsidian folders.

The current sideload APK is intentionally simple: it gives you a tappable Android app without app-store signing or Google Play distribution.

## Self-Contained APK Options

Bundling literal Termux is not the cleanest product path. Termux is open source, but it is its own Android application plus package ecosystem, and its plugin/app model depends on matching signatures. Forking or embedding it would make ERMI inherit a lot of unrelated terminal-app complexity.

Cleaner self-contained routes:

1. **Chaquopy backend inside Android**
   - Embed Python in the Android app.
   - Run ERMI FastAPI or a smaller ASGI/server layer inside the APK.
   - Keep the existing React WebView UI.
   - Best fit for a sideload APK prototype.

2. **BeeWare / Briefcase**
   - Package Python as a native Android project.
   - Better if ERMI becomes a Python-first Android app.
   - More restructuring than the current WebView shell.

3. **Kotlin service rewrite**
   - Port the small backend API to Kotlin.
   - Keep SQLite and bundled WebView UI.
   - Most native long-term, highest rewrite cost.

Recommended next Android milestone:

```text
Capacitor APK shell -> Chaquopy embedded ERMI backend -> signed sideload APK
```

That gives a self-contained APK without needing Google Play. It still needs normal Android sideload signing, but that can be done with a local debug/release keystore rather than a paid store account.
