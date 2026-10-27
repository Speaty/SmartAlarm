import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PIPEWIRE_SINK = os.getenv("PIPEWIRE_SINK", "@DEFAULT_AUDIO_SINK@")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR / 'smartalarm.db'}")
# Comma-separated secret iCal feed URLs (Google: Settings > your calendar > Integrate calendar)
CALENDAR_ICAL_URLS = [u.strip() for u in os.getenv("CALENDAR_ICAL_URLS", "").split(",") if u.strip()]
FRONTEND_DIR = BASE_DIR.parent / "frontend"

DEFAULT_ALARM_VOLUME = int(os.getenv("DEFAULT_ALARM_VOLUME", "70"))
# Radio and speech levels (0-100) within the speaker volume
DEFAULT_MUSIC_LEVEL = int(os.getenv("DEFAULT_MUSIC_LEVEL", "100"))
DEFAULT_VOICE_LEVEL = int(os.getenv("DEFAULT_VOICE_LEVEL", "100"))
ALARM_RADIO_URL = os.getenv("ALARM_RADIO_URL", "http://stream-relay-geo.ntslive.net/stream")
TEST_SPEAKER_URL = os.getenv("TEST_SPEAKER_URL", "http://stream-relay-geo.ntslive.net/stream")

TIMEZONE = os.getenv("TIMEZONE", "Europe/London")
