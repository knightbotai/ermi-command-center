#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ""
echo "==> ERMI Termux setup"
echo "Root: $ROOT"

pkg update -y
pkg install -y git python nodejs-lts clang make rust openssl libffi

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "$ROOT[dev]"

cd "$ROOT"
npm install
python -m ermi --root archive init
python -m ermi --root archive diagnostics || true

cat <<EOF

ERMI Termux setup complete.

Start ERMI with:
  bash install/termux-launch.sh

Then open Android Chrome to:
  http://127.0.0.1:5173
EOF
