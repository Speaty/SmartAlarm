import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

# Point the app at a throwaway database before any backend module reads config.
_TEST_DIR = Path(tempfile.mkdtemp(prefix="smartalarm-tests-"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_TEST_DIR / 'test.db').as_posix()}"

import httpx
import pytest

from backend import alarm_controller, tts_engine
from backend.app import app
from backend.audio_player import player as shared_player
from backend.calendar_summary import calendar_summary_service
from backend.database import engine
from backend.models import Base
from backend.scheduler import scheduler


@pytest.fixture(autouse=True)
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    """Keep tests isolated from each other and from any real .env credentials."""
    monkeypatch.setattr(tts_engine, "ELEVENLABS_API_KEY", None)
    monkeypatch.setattr(tts_engine, "ELEVENLABS_VOICE_ID", None)
    monkeypatch.setattr(alarm_controller, "_ringing", False)
    calendar_summary_service.events = []
    scheduler.remove_all_jobs()
    yield
    scheduler.remove_all_jobs()


@pytest.fixture(autouse=True)
def player(monkeypatch):
    """Stub the shared audio player so no test shells out to mpg123/pw-play/espeak."""
    for name in ("start_radio", "stop_radio", "play_message", "play_wav", "set_volume", "set_music_level"):
        monkeypatch.setattr(shared_player, name, AsyncMock())
    monkeypatch.setattr(shared_player, "volume", 70)
    monkeypatch.setattr(shared_player, "music_level", 100)
    monkeypatch.setattr(shared_player, "voice_level", 100)
    return shared_player


@pytest.fixture(autouse=True)
def calendar(monkeypatch):
    """Stub the calendar feed; tests set `.return_value` to supply events."""
    fetch = AsyncMock(return_value=[])
    monkeypatch.setattr(calendar_summary_service, "fetch_events", fetch)
    return fetch


@pytest.fixture
async def client():
    # ASGITransport skips the startup event, so the scheduler is never started:
    # jobs stay pending and can be inspected without firing.
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

