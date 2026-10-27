import logging
from typing import List

from .calendar_sync import get_weekly_events, summarize_events

logger = logging.getLogger(__name__)


class CalendarSummaryService:
    def __init__(self):
        self.events: List[dict] = []
        self.fetch_events = get_weekly_events

    async def refresh_events(self) -> List[dict]:
        """Fetch fresh events, keeping the cached ones if the fetch fails or no feed is configured."""
        try:
            events = await self.fetch_events()
        except Exception:
            logger.exception("Failed to fetch calendar events; using cached events")
            return self.events
        if events is not None:
            self.events = events
        return self.events

    async def get_summary(self) -> str:
        await self.refresh_events()
        return summarize_events(self.events)


calendar_summary_service = CalendarSummaryService()
