from datetime import datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest
import requests

from backend import calendar_sync
from backend.calendar_summary import CalendarSummaryService
from backend.calendar_sync import download_feed, get_weekly_events, summarize_events
from tests.fakes import FakeResponse, RecordingHTTP

LONDON = ZoneInfo("Europe/London")
NOW = datetime(2099, 1, 5, 8, 0, tzinfo=LONDON)  # Monday 08:00


def feed(*events: str) -> bytes:
    body = "".join(f"BEGIN:VEVENT\r\n{e.strip()}\r\nEND:VEVENT\r\n" for e in events)
    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//EN\r\n" + body + "END:VCALENDAR\r\n"
    ).encode()


def vevent(uid, summary, dtstart, extra=""):
    lines = [f"UID:{uid}", f"SUMMARY:{summary}", dtstart, "DTSTAMP:20990101T000000Z"]
    if extra:
        lines.append(extra)
    return "\r\n".join(lines)


STANDUP = vevent("1", "Standup", "DTSTART:20990105T090000Z")
HOLIDAY = vevent("2", "Holiday", "DTSTART;VALUE=DATE:20990106")
GYM_WEEKLY = vevent(
    "3", "Gym", "DTSTART;TZID=Europe/London:20981202T180000", "RRULE:FREQ=WEEKLY"
)  # Tuesdays
NEW_YORK_CALL = vevent("4", "NY call", "DTSTART;TZID=America/New_York:20990107T090000")
FLOATING = vevent("5", "Dentist", "DTSTART:20990108T070000")
YESTERDAY = vevent("6", "Past", "DTSTART:20990104T090000Z")
NEXT_MONTH = vevent("7", "Later", "DTSTART:20990201T090000Z")


@pytest.fixture
def feeds(monkeypatch):
    """Serve iCal feeds by URL instead of hitting the network."""
    served = {}

    def fake_download(url):
        return served[url]

    monkeypatch.setattr(calendar_sync, "download_feed", fake_download)
    return served


def summaries(events):
    return [e["summary"] for e in events]


# --- parsing the next seven days ---------------------------------------------


async def test_timed_event_is_returned_in_local_time(feeds):
    feeds["u"] = feed(STANDUP)

    events = await get_weekly_events(["u"], now=NOW)

    assert events == [{"start": {"dateTime": "2099-01-05T09:00:00+00:00"}, "summary": "Standup"}]


async def test_all_day_event_uses_date(feeds):
    feeds["u"] = feed(HOLIDAY)

    events = await get_weekly_events(["u"], now=NOW)

    assert events == [{"start": {"date": "2099-01-06"}, "summary": "Holiday"}]


async def test_weekly_recurring_event_expands_to_this_weeks_occurrence(feeds):
    feeds["u"] = feed(GYM_WEEKLY)

    events = await get_weekly_events(["u"], now=NOW)

    assert events == [{"start": {"dateTime": "2099-01-06T18:00:00+00:00"}, "summary": "Gym"}]


async def test_event_in_other_timezone_is_converted_to_local(feeds):
    feeds["u"] = feed(NEW_YORK_CALL)

    events = await get_weekly_events(["u"], now=NOW)

    assert events[0]["start"]["dateTime"] == "2099-01-07T14:00:00+00:00"


async def test_floating_time_is_treated_as_local(feeds):
    feeds["u"] = feed(FLOATING)

    events = await get_weekly_events(["u"], now=NOW)

    assert events[0]["start"]["dateTime"] == "2099-01-08T07:00:00+00:00"


async def test_events_outside_the_week_are_excluded(feeds):
    feeds["u"] = feed(YESTERDAY, STANDUP, NEXT_MONTH)

    events = await get_weekly_events(["u"], now=NOW)

    assert summaries(events) == ["Standup"]


async def test_untitled_event(feeds):
    feeds["u"] = feed("UID:9\r\nDTSTART:20990105T120000Z\r\nDTSTAMP:20990101T000000Z")

    events = await get_weekly_events(["u"], now=NOW)

    assert summaries(events) == ["Untitled event"]


async def test_multiple_feeds_are_merged_and_sorted(feeds):
    feeds["work"] = feed(NEW_YORK_CALL, STANDUP)  # Thu, Mon
    feeds["home"] = feed(HOLIDAY, GYM_WEEKLY)  # Tue all-day, Tue 18:00

    events = await get_weekly_events(["work", "home"], now=NOW)

    assert summaries(events) == ["Standup", "Holiday", "Gym", "NY call"]


async def test_no_feeds_configured_returns_none(feeds):
    assert await get_weekly_events([], now=NOW) is None


async def test_uses_configured_urls_by_default(feeds, monkeypatch):
    monkeypatch.setattr(calendar_sync, "CALENDAR_ICAL_URLS", ["configured"])
    feeds["configured"] = feed(STANDUP)

    events = await get_weekly_events(now=NOW)

    assert summaries(events) == ["Standup"]


async def test_bad_feed_raises(feeds):
    feeds["u"] = b"<html>not a calendar</html>"

    with pytest.raises(ValueError):
        await get_weekly_events(["u"], now=NOW)


# --- downloading --------------------------------------------------------------


def test_download_returns_body_with_timeout(monkeypatch):
    get = RecordingHTTP(FakeResponse(content=b"ICS"))
    monkeypatch.setattr(requests, "get", get)

    assert download_feed("https://example.com/basic.ics") == b"ICS"
    url, kwargs = get.calls[0]
    assert url == "https://example.com/basic.ics"
    assert kwargs["timeout"] > 0


def test_download_rewrites_webcal_to_https(monkeypatch):
    get = RecordingHTTP(FakeResponse(content=b"ICS"))
    monkeypatch.setattr(requests, "get", get)

    download_feed("webcal://example.com/basic.ics")

    assert get.calls[0][0] == "https://example.com/basic.ics"


def test_download_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(requests, "get", RecordingHTTP(FakeResponse(status_code=404)))

    with pytest.raises(requests.HTTPError):
        download_feed("https://example.com/basic.ics")


# --- summarize_events -----------------------------------------------------------


def test_summary_with_no_events():
    assert "no events" in summarize_events([])


def test_summary_lists_events_with_start_times():
    text = summarize_events(
        [
            {"start": {"dateTime": "2099-01-05T09:00:00+00:00"}, "summary": "Standup"},
            {"start": {"date": "2099-01-06"}, "summary": "Holiday"},
        ]
    )

    assert "2099-01-05T09:00:00+00:00: Standup" in text
    assert "2099-01-06: Holiday" in text


def test_summary_caps_at_five_events():
    events = [{"start": {"date": "2099-01-01"}, "summary": f"E{i}"} for i in range(8)]

    text = summarize_events(events)

    assert "E4" in text
    assert "E5" not in text


# --- CalendarSummaryService (caching / fallback) ----------------------------------

A = [{"start": {"date": "2099-01-01"}, "summary": "First"}]
B = [{"start": {"date": "2099-01-01"}, "summary": "Second"}]


@pytest.fixture
def service():
    svc = CalendarSummaryService()
    svc.fetch_events = AsyncMock()
    return svc


async def test_service_refreshes_every_time(service):
    service.fetch_events.side_effect = [A, B]

    await service.get_summary()

    assert "Second" in await service.get_summary()


async def test_service_falls_back_to_cache_when_fetch_fails(service):
    service.fetch_events.side_effect = [A, requests.ConnectionError("offline")]
    await service.get_summary()

    assert "First" in await service.get_summary()


async def test_service_keeps_cache_when_no_feed_configured(service):
    service.events = A
    service.fetch_events.return_value = None

    assert "First" in await service.get_summary()


async def test_service_empty_week_replaces_cache(service):
    service.fetch_events.side_effect = [A, []]
    await service.get_summary()

    assert "no events" in await service.get_summary()


# --- HTTP endpoints ---------------------------------------------------------------


async def test_calendar_summary_endpoint(client, calendar):
    calendar.return_value = A

    response = await client.get("/calendar/summary")

    assert "First" in response.json()["summary"]


async def test_sample_events_endpoint_feeds_summary_when_no_feed_configured(client, calendar):
    calendar.return_value = None
    await client.post("/calendar/events/sample")

    response = await client.get("/calendar/summary")

    assert "Morning standup" in response.json()["summary"]


# --- Live -------------------------------------------------------------------------


@pytest.mark.live
async def test_live_ical_feed():
    if not calendar_sync.CALENDAR_ICAL_URLS:
        pytest.skip("set CALENDAR_ICAL_URLS in .env to run")

    events = await get_weekly_events()

    assert isinstance(events, list)
    for event in events:
        assert event["start"].get("dateTime") or event["start"].get("date")
    print(summarize_events(events))
