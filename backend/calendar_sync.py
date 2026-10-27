import asyncio
from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events
import requests

from .config import CALENDAR_ICAL_URLS, TIMEZONE


def summarize_events(events: List[dict]) -> str:
    if not events:
        return "You have no events scheduled for the next seven days. Enjoy your morning."

    lines = ["Your upcoming schedule for the week is as follows:"]
    for event in events[:5]:
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        summary = event.get("summary", "Untitled event")
        lines.append(f"{start}: {summary}")
    return " ".join(lines)


async def get_weekly_events(
    urls: Optional[List[str]] = None, now: Optional[datetime] = None
) -> Optional[List[dict]]:
    """Fetch the next seven days of events from each iCal feed, merged and sorted by start.

    Returns None when no feed is configured.
    """
    urls = CALENDAR_ICAL_URLS if urls is None else urls
    if not urls:
        return None
    tz = ZoneInfo(TIMEZONE)
    now = now or datetime.now(tz)
    end = now + timedelta(days=7)

    events: List[Tuple[datetime, dict]] = []
    for url in urls:
        ics = await asyncio.to_thread(download_feed, url)
        events.extend(parse_events(ics, now, end, tz))
    events.sort(key=lambda pair: pair[0])
    return [event for _, event in events]


def download_feed(url: str) -> bytes:
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.content


def parse_events(ics: bytes, start: datetime, end: datetime, tz: ZoneInfo) -> List[Tuple[datetime, dict]]:
    """Expand recurring events in [start, end) into (sort key, event dict) pairs.

    Event dicts use the `{"start": {"dateTime" | "date": ...}, "summary": ...}` shape
    that `summarize_events` reads.
    """
    calendar = icalendar.Calendar.from_ical(ics)
    results = []
    for component in recurring_ical_events.of(calendar).between(start, end):
        dtstart = component.get("DTSTART").dt
        summary = str(component.get("SUMMARY", "Untitled event"))
        if isinstance(dtstart, datetime):
            if dtstart.tzinfo is None:  # "floating" time: treat as local
                dtstart = dtstart.replace(tzinfo=tz)
            local = dtstart.astimezone(tz)
            results.append((local, {"start": {"dateTime": local.isoformat()}, "summary": summary}))
        else:  # all-day event
            sort_key = datetime.combine(dtstart, time.min, tz)
            results.append((sort_key, {"start": {"date": dtstart.isoformat()}, "summary": summary}))
    return results
