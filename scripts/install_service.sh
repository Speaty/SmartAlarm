#!/usr/bin/env bash
# Install SmartAlarm as a systemd *user* service: it starts at boot and restarts after a crash.
# It runs as you (not root) so it can reach your PipeWire audio session.
#
# Run with the app's virtualenv activated:
#   source <venv>/bin/activate && ./scripts/install_service.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UVICORN="$(command -v uvicorn || true)"

if [[ -z "${VIRTUAL_ENV:-}" || -z "$UVICORN" ]]; then
  echo "Activate the app's virtualenv first (the one you run uvicorn from), then re-run." >&2
  exit 1
fi

if pgrep -f "uvicorn backend.app:app" >/dev/null && ! systemctl --user is-active --quiet smartalarm.service; then
  echo "A manually started uvicorn is already using the app. Stop it first (Ctrl+C, or: pkill -f 'uvicorn backend.app'), then re-run." >&2
  exit 1
fi

UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"
cat > "$UNIT_DIR/smartalarm.service" <<EOF
[Unit]
Description=SmartAlarm
Wants=pipewire.service pipewire-pulse.service wireplumber.service
After=pipewire.service pipewire-pulse.service wireplumber.service

[Service]
WorkingDirectory=$REPO_DIR
ExecStart=$UVICORN backend.app:app --host 0.0.0.0 --port 5000
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF
echo "Wrote $UNIT_DIR/smartalarm.service"

# Start this user's services (including PipeWire) at boot, without anyone logging in.
sudo loginctl enable-linger "$USER"

systemctl --user daemon-reload
systemctl --user enable --now smartalarm.service
systemctl --user --no-pager status smartalarm.service

cat <<EOF

SmartAlarm is running as a user service and will start at boot.
  Logs:     journalctl --user -u smartalarm -f
  Restart:  systemctl --user restart smartalarm   (after git pull)
  Stop:     systemctl --user stop smartalarm
EOF
