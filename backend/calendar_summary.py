from typing import List

from .calendar_sync import summarize_events
from .google_calendar import GoogleCalendarService


class CalendarSummaryService:
    def __init__(self):
        self.events: List[dict] = []
        self.google_service = GoogleCalendarService()

    async def refresh_events(self) -> List[dict]:
        events = await self.google_service.get_weekly_events()
        if events:
            self.events = events
        return self.events

    async def get_summary(self) -> str:
        if not self.events:
            await self.refresh_events()
        return summarize_events(self.events)


calendar_summary_service = CalendarSummaryService()
