from typing import List, Optional

from .models import OAuthToken


class CalendarProvider:
    async def get_weekly_events(self) -> List[dict]:
        return []


class GoogleCalendarProvider(CalendarProvider):
    def __init__(self, credentials):
        self.credentials = credentials

    async def get_weekly_events(self) -> List[dict]:
        # TODO: implement Google Calendar API fetching
        return []


class OutlookCalendarProvider(CalendarProvider):
    def __init__(self, token: OAuthToken):
        self.token = token

    async def get_weekly_events(self) -> List[dict]:
        # TODO: implement Microsoft Graph calendar fetching
        return []
