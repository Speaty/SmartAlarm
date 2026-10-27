# SmartAlarmPi

SmartAlarmPi is a Raspberry Pi smart alarm clock backend and lightweight web UI.

## What it does
- Schedule weekly or one-time alarms via a simple web UI
- Play internet radio as the alarm source
- Generate spoken messages via `espeak-ng` now, and later ElevenLabs TTS
- Read your calendar (any iCal feed: Google, Outlook, Apple) and speak a weekly summary when you stop the alarm
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
pytest            # unit tests; audio, ElevenLabs and the calendar are faked
pytest -m live    # real API calls; skipped unless credentials are present
```

The live tests need `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` in `.env` for ElevenLabs, and
`CALENDAR_ICAL_URLS` for the calendar.

## Calendar setup

The schedule summary reads your calendar from its secret iCal address, so there is no sign-in or
Google Cloud project to set up.

1. In Google Calendar on the web, open **Settings**, pick your calendar under
   **Settings for my calendars**, and go to **Integrate calendar**.
2. Copy the **Secret address in iCal format** (it ends in `basic.ics`).
3. Put it in `.env` on the Pi and restart the service:

   ```
   CALENDAR_ICAL_URLS=https://calendar.google.com/calendar/ical/.../private-.../basic.ics
   ```

   For several calendars, separate the URLs with commas. Outlook ("Publish calendar" → ICS link)
   and Apple Calendar (public/shared calendar link) addresses work the same way.
4. Check it: **Refresh Summary** in the web UI should list the next seven days, and
   `pytest -m live -rs` runs the live calendar test.

Treat the secret address like a password: anyone with it can read that calendar. If it leaks,
use **Reset** next to it in Google Calendar and update `.env`.
