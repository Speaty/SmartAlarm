import logging
from typing import List

from .calendar_sync import summarize_events
from .google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)


class CalendarSummaryService:
    def __init__(self):
        self.events: List[dict] = []
        self.google_service = GoogleCalendarService()

    async def refresh_events(self) -> List[dict]:
        """Fetch fresh events, keeping the cached ones if the fetch fails or returns nothing."""
        try:
            events = await self.google_service.get_weekly_events()
        except Exception:
            logger.exception("Failed to fetch Google Calendar events; using cached events")
            return self.events
        if events:
            self.events = events
        return self.events

    async def get_summary(self) -> str:
        await self.refresh_events()
        return summarize_events(self.events)


calendar_summary_service = CalendarSummaryService()
