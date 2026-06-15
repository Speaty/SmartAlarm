from datetime import datetime, timedelta
from typing import List

import requests
from .models import OAuthToken


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
    now = datetime.utcnow().isoformat() + "Z"
    week_later = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
    url = (
        "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        f"?timeMin={now}&timeMax={week_later}&singleEvents=true&orderBy=startTime"
    )
    token = credentials.token
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("items", [])


async def get_weekly_outlook_events(access_token: str) -> List[dict]:
    now = datetime.utcnow().isoformat() + "Z"
    week_later = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
    url = (
        "https://graph.microsoft.com/v1.0/me/calendarView"
        f"?startDateTime={now}&endDateTime={week_later}"
        "&$orderby=start/dateTime"
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("value", [])
