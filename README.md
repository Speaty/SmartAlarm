# SmartAlarmPi

SmartAlarmPi is a Raspberry Pi smart alarm clock backend and lightweight web UI.

## What it does
- Schedule weekly or one-time alarms via a simple web UI
- Play internet radio as the alarm source
- Generate spoken messages via `espeak-ng` now, and later ElevenLabs TTS
- Provide hooks for Google Calendar and Outlook integration
- Run as a local Pi service with HiFiBerry audio support

## Getting started

1. Install system packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mpg123 espeak-ng alsa-utils
```

2. Install Python dependencies

3. Initialize the database:

```bash
python scripts/init_db.py
```

4. Run the backend:

```bash
source venv/bin/activate
uvicorn backend.app:app --host 0.0.0.0 --port 5000
```

5. Open the UI in your browser:

```
http://localhost:5000/
```

## Project layout

- `backend/` — FastAPI app, scheduler, audio and TTS helpers
- `frontend/` — single-page alarm UI
- `config/` — systemd service file and deployment configuration
- `scripts/` — install and setup helpers
- `data/` — runtime SQLite databases and generated audio

## Notes

- The current MVP uses `espeak-ng` for local TTS.
- Media playback uses `mpg123` for internet radio and `aplay` for WAV audio.
- For Raspberry Pi deployment, add the `smartalarm` user to `audio` and `gpio` groups.

## Google Calendar setup

1. Create a Google Cloud project at https://console.cloud.google.com/
2. Enable the Google Calendar API.
3. Create OAuth 2.0 credentials and download the JSON client secret file.
4. Save it as `secrets/google_client_secrets.json` in the repository root.
5. Start the backend and visit `/oauth/auth/google` to connect your calendar.
