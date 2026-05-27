#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${ERMI_API_PORT:-8765}"
UI_PORT="${ERMI_UI_PORT:-5173}"

cd "$ROOT"

echo "==> Starting ERMI API on 127.0.0.1:$API_PORT"
python -m ermi.server --root archive --host 127.0.0.1 --port "$API_PORT" &
API_PID=$!

echo "==> Starting ERMI UI on 127.0.0.1:$UI_PORT"
npm run dev:ui -- --host 127.0.0.1 --port "$UI_PORT" &
UI_PID=$!

cleanup() {
  kill "$API_PID" "$UI_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

sleep 5

if command -v termux-open-url >/dev/null 2>&1; then
  termux-open-url "http://127.0.0.1:$UI_PORT"
else
  echo "Open http://127.0.0.1:$UI_PORT in Android Chrome."
fi

wait
