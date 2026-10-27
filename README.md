# SmartAlarmPi

SmartAlarmPi is a Raspberry Pi smart alarm clock backend and lightweight web UI.

## What it does
- Schedule weekly or one-time alarms via a simple web UI
- Play internet radio as the alarm source
- Generate spoken messages via `espeak-ng` now, and later ElevenLabs TTS
- Read your Google Calendar and speak a weekly summary when you stop the alarm (Outlook planned)
- Run as a local Pi service with HiFiBerry audio support

## Getting started

1. Install system packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mpg123 espeak-ng pipewire pipewire-pulse pipewire-bin wireplumber
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
- Media playback goes through PipeWire: `mpg123 -o pulse` for internet radio, `pw-play` for WAV audio, and `wpctl` for volume.
- For Raspberry Pi deployment, add the `smartalarm` user to `audio` and `gpio` groups.

## Testing

```bash
pip install -r requirements-dev.txt
pytest            # unit tests; audio, ElevenLabs and Google are faked
pytest -m live    # real API calls; skipped unless credentials are present
```

The live tests need `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` in `.env` for ElevenLabs, and
`secrets/google_client_secrets.json` plus a connected `data/smartalarm.db` for Google Calendar.

## Google Calendar setup

1. Create a Google Cloud project at https://console.cloud.google.com/
2. Enable the Google Calendar API.
3. Create OAuth 2.0 credentials and download the JSON client secret file.
4. Save it as `secrets/google_client_secrets.json` in the repository root.
5. Start the backend and visit `/oauth/auth/google` to connect your calendar.
