import asyncio
from datetime import datetime, timedelta
from typing import List

import requests


def summarize_events(events: List[dict]) -> str:
    if not events:
        return "You have no events scheduled for the next seven days. Enjoy your morning."

    lines = ["Your upcoming schedule for the week is as follows:"]
    for event in events[:5]:
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        summary = event.get("summary", "Untitled event")
        lines.append(f"{start}: {summary}")
    return " ".join(lines)


async def get_weekly_google_events(credentials) -> List[dict]:
    now = datetime.utcnow()
    params = {
        "timeMin": now.isoformat() + "Z",
        "timeMax": (now + timedelta(days=7)).isoformat() + "Z",
        "singleEvents": "true",
        "orderBy": "startTime",
    }
    headers = {"Authorization": f"Bearer {credentials.token}"}
    response = await asyncio.to_thread(
        requests.get,
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        params=params,
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("items", [])
