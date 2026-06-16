import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PIPEWIRE_SINK = os.getenv("PIPEWIRE_SINK", "@DEFAULT_AUDIO_SINK@")
MPD_HOST = os.getenv("MPD_HOST", "localhost")
MPD_PORT = int(os.getenv("MPD_PORT", "6600"))
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "alloy")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR / 'smartalarm.db'}")
GOOGLE_CLIENT_SECRETS = BASE_DIR.parent / "secrets" / "google_client_secrets.json"
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
OUTLOOK_SCOPES = ["https://graph.microsoft.com/Calendars.Read"]
OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY", "changeme_local_secret")
FRONTEND_DIR = BASE_DIR.parent / "frontend"

DEFAULT_ALARM_VOLUME = int(os.getenv("DEFAULT_ALARM_VOLUME", "70"))
ALARM_RADIO_URL = os.getenv("ALARM_RADIO_URL", "http://stream-relay-geo.ntslive.net/stream")
TEST_SPEAKER_URL = os.getenv("TEST_SPEAKER_URL", "http://stream-relay-geo.ntslive.net/stream")

TIMEZONE = os.getenv("TIMEZONE", "Europe/London")
