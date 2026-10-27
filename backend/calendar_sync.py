import asyncio
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events
import requests

from .config import CALENDAR_ICAL_URLS, TIMEZONE


MAX_SPOKEN_EVENTS = 5


def summarize_events(events: List[dict], now: Optional[datetime] = None) -> str:
    if not events:
        return "You have no events scheduled for the next seven days. Enjoy your morning."

    tz = ZoneInfo(TIMEZONE)
    today = (now or datetime.now(tz)).astimezone(tz).date()
    lines = ["Your upcoming schedule for the week is as follows:"]
    for event in events[:MAX_SPOKEN_EVENTS]:
        summary = event.get("summary", "Untitled event")
        lines.append(f"{spoken_when(event.get('start', {}), today, tz)}: {summary}.")
    remaining = len(events) - MAX_SPOKEN_EVENTS
    if remaining > 0:
        lines.append(f"And {remaining} more.")
    return " ".join(lines)


def spoken_when(start: dict, today: date, tz: ZoneInfo) -> str:
    """Describe an event start the way you'd say it: "Tomorrow at 9:30 AM", "Wednesday, all day"."""
    if start.get("dateTime"):
        moment = datetime.fromisoformat(start["dateTime"])
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=tz)
        moment = moment.astimezone(tz)
        return f"{spoken_day(moment.date(), today)} at {spoken_time(moment)}"
    if start.get("date"):
        return f"{spoken_day(date.fromisoformat(start['date']), today)}, all day"
    return "Sometime soon"


def spoken_day(day: date, today: date) -> str:
    days_ahead = (day - today).days
    if days_ahead == 0:
        return "Today"
    if days_ahead == 1:
        return "Tomorrow"
    if 2 <= days_ahead <= 6:
        return day.strftime("%A")
    if days_ahead == 7:
        return f"Next {day.strftime('%A')}"
    return f"{day.strftime('%A')} the {ordinal(day.day)} of {day.strftime('%B')}"


def spoken_time(moment: datetime) -> str:
    hour = moment.hour % 12 or 12
    suffix = "AM" if moment.hour < 12 else "PM"
    if moment.minute:
        return f"{hour}:{moment.minute:02d} {suffix}"
    return f"{hour} {suffix}"


def ordinal(n: int) -> str:
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


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
