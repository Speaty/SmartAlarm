import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

AUDIO_DEVICE = os.getenv("AUDIO_DEVICE", "plughw:2,0")
AUDIO_MIXER_DEVICE = os.getenv("AUDIO_MIXER_DEVICE", "hw:2")
MPD_HOST = os.getenv("MPD_HOST", "localhost")
MPD_PORT = int(os.getenv("MPD_PORT", "6600"))
ALSA_MIXER = os.getenv("ALSA_MIXER", "Master")
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

DEFAULT_ALARM_VOLUME = int(os.getenv("DEFAULT_ALARM_VOLUME", "85"))
ALARM_RADIO_URL = os.getenv("ALARM_RADIO_URL", "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service")
TEST_SPEAKER_URL = os.getenv("TEST_SPEAKER_URL", "http://stream-relay-geo.ntslive.net/stream")

TIMEZONE = os.getenv("TIMEZONE", "UTC")
