#!/usr/bin/env bash
set -euo pipefail

echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mpg123 espeak-ng alsa-utils

if python3 -m venv venv 2>/dev/null; then
  source venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
else
  echo "python3 venv support is unavailable; falling back to user install."
  python3 -m pip install --user --upgrade pip
  python3 -m pip install --user -r requirements.txt
fi

mkdir -p data

cat <<'EOF'
Installation complete.
Run the app with: source venv/bin/activate && uvicorn backend.app:app --host 0.0.0.0 --port 5000
EOF
