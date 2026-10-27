import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import requests
from google.oauth2.credentials import Credentials

from backend import google_calendar
from backend.calendar_summary import CalendarSummaryService, calendar_summary_service
from backend.calendar_sync import get_weekly_google_events, summarize_events
from backend.google_calendar import GoogleCalendarService
from backend.token_store import get_token, save_token
from tests.fakes import FakeResponse, RecordingHTTP

EVENTS = [
    {"start": {"dateTime": "2099-01-05T09:00:00Z"}, "summary": "Standup"},
    {"start": {"date": "2099-01-06"}, "summary": "Holiday"},
]


# --- summarize_events -------------------------------------------------------


def test_summary_with_no_events():
    assert "no events" in summarize_events([])


def test_summary_lists_events_with_start_times():
    text = summarize_events(EVENTS)

    assert "2099-01-05T09:00:00Z: Standup" in text
    assert "2099-01-06: Holiday" in text  # all-day events use `date`


def test_summary_caps_at_five_events():
    events = [{"start": {"date": "2099-01-01"}, "summary": f"E{i}"} for i in range(8)]

    text = summarize_events(events)

    assert "E4" in text
    assert "E5" not in text


def test_summary_handles_untitled_event():
    assert "Untitled event" in summarize_events([{"start": {"date": "2099-01-01"}}])


# --- Google Calendar HTTP fetch ---------------------------------------------


async def test_google_fetch_requests_next_seven_days(monkeypatch):
    get = RecordingHTTP(FakeResponse(json_data={"items": EVENTS}))
    monkeypatch.setattr(requests, "get", get)

    events = await get_weekly_google_events(Credentials(token="access-1"))

    assert events == EVENTS
    url, kwargs = get.calls[0]
    assert url == "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    assert kwargs["headers"]["Authorization"] == "Bearer access-1"
    params = kwargs["params"]
    assert params["singleEvents"] == "true"
    assert params["orderBy"] == "startTime"
    start = datetime.fromisoformat(params["timeMin"].rstrip("Z"))
    end = datetime.fromisoformat(params["timeMax"].rstrip("Z"))
    assert end - start == timedelta(days=7)


async def test_google_fetch_with_no_items_returns_empty(monkeypatch):
    monkeypatch.setattr(requests, "get", RecordingHTTP(FakeResponse(json_data={})))

    assert await get_weekly_google_events(Credentials(token="t")) == []


async def test_google_fetch_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(requests, "get", RecordingHTTP(FakeResponse(status_code=401)))

    with pytest.raises(requests.HTTPError):
        await get_weekly_google_events(Credentials(token="t"))


# --- GoogleCalendarService (token handling) ---------------------------------


@pytest.fixture
def service(tmp_path):
    secrets = tmp_path / "client_secrets.json"
    secrets.write_text(json.dumps({"installed": {"client_id": "cid", "client_secret": "csecret"}}))
    svc = GoogleCalendarService()
    svc.client_secrets_file = secrets
    return svc


@pytest.fixture
def fetched(monkeypatch):
    """Capture the credentials the service fetches events with."""
    seen = []

    async def fake_fetch(creds):
        seen.append(creds)
        return EVENTS

    monkeypatch.setattr(google_calendar, "get_weekly_google_events", fake_fetch)
    return seen


async def test_service_without_stored_token_returns_no_events(service, fetched):
    assert await service.get_weekly_events() == []
    assert fetched == []


async def test_service_uses_stored_token(service, fetched):
    await save_token("google", "access-1", "refresh-1", "scope", datetime.utcnow() + timedelta(hours=1))

    events = await service.get_weekly_events()

    assert events == EVENTS
    assert fetched[0].token == "access-1"
    assert fetched[0].client_id == "cid"


async def test_service_refreshes_expired_token_and_stores_it(service, fetched, monkeypatch):
    await save_token("google", "stale", "refresh-1", "scope", datetime.utcnow() - timedelta(minutes=5))
    new_expiry = datetime.utcnow() + timedelta(hours=1)

    def fake_refresh(self, request):
        self.token = "fresh"
        self.expiry = new_expiry

    monkeypatch.setattr(Credentials, "refresh", fake_refresh)

    await service.get_weekly_events()

    assert fetched[0].token == "fresh"
    stored = await get_token("google")
    assert stored.access_token == "fresh"
    assert stored.refresh_token == "refresh-1"
    assert stored.expires_at == new_expiry


async def test_service_does_not_refresh_valid_token(service, fetched, monkeypatch):
    await save_token("google", "access-1", "refresh-1", "scope", datetime.utcnow() + timedelta(hours=1))
    refresh = AsyncMock()
    monkeypatch.setattr(Credentials, "refresh", lambda self, request: refresh())

    await service.get_weekly_events()

    refresh.assert_not_called()


async def test_service_missing_client_secrets_raises(service):
    await save_token("google", "a", "r", "scope")
    service.client_secrets_file = Path("does/not/exist.json")

    with pytest.raises(FileNotFoundError):
        await service.get_weekly_events()


async def test_save_token_updates_existing_row():
    await save_token("google", "a1", "r1", "s")
    await save_token("google", "a2", "r2", "s")

    stored = await get_token("google")
    assert (stored.access_token, stored.refresh_token) == ("a2", "r2")


# --- CalendarSummaryService (caching / fallback) ----------------------------


@pytest.fixture
def summary_service():
    svc = CalendarSummaryService()
    svc.google_service = AsyncMock()
    return svc


async def test_summary_service_fetches_fresh_events(summary_service):
    summary_service.google_service.get_weekly_events.return_value = EVENTS

    assert "Standup" in await summary_service.get_summary()


async def test_summary_service_refreshes_every_time(summary_service):
    summary_service.google_service.get_weekly_events.side_effect = [
        [{"start": {"date": "2099-01-01"}, "summary": "First"}],
        [{"start": {"date": "2099-01-01"}, "summary": "Second"}],
    ]

    await summary_service.get_summary()

    assert "Second" in await summary_service.get_summary()


async def test_summary_service_falls_back_to_cache_when_google_fails(summary_service):
    summary_service.google_service.get_weekly_events.side_effect = [
        EVENTS,
        requests.ConnectionError("offline"),
    ]
    await summary_service.get_summary()

    assert "Standup" in await summary_service.get_summary()


async def test_summary_service_keeps_cache_when_google_returns_nothing(summary_service):
    summary_service.google_service.get_weekly_events.side_effect = [EVENTS, []]
    await summary_service.get_summary()

    assert "Standup" in await summary_service.get_summary()


# --- HTTP endpoints ----------------------------------------------------------


async def test_calendar_summary_endpoint(client):
    calendar_summary_service.google_service.get_weekly_events.return_value = EVENTS

    response = await client.get("/calendar/summary")

    assert "Standup" in response.json()["summary"]


async def test_sample_events_endpoint_feeds_summary(client):
    await client.post("/calendar/events/sample")

    response = await client.get("/calendar/summary")

    assert "Morning standup" in response.json()["summary"]


# --- Live --------------------------------------------------------------------


@pytest.mark.live
async def test_live_google_calendar_fetch():
    real_db = Path(__file__).resolve().parent.parent / "data" / "smartalarm.db"
    service = GoogleCalendarService()
    if not service.client_secrets_file.exists() or not real_db.exists():
        pytest.skip("needs secrets/google_client_secrets.json and a connected data/smartalarm.db")
    with sqlite3.connect(real_db) as conn:
        row = conn.execute(
            "SELECT access_token, refresh_token, scopes, expires_at FROM oauth_tokens "
            "WHERE provider = 'google'"
        ).fetchone()
    if not row:
        pytest.skip("connect Google Calendar via /oauth/auth/google first")
    expires_at = datetime.fromisoformat(row[3]) if row[3] else None
    await save_token("google", row[0], row[1], row[2], expires_at)

    events = await service.get_weekly_events()

    assert isinstance(events, list)
    for event in events:
        assert "start" in event
    print(summarize_events(events))
