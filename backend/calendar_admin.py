from fastapi import APIRouter

from .calendar_summary import calendar_summary_service

router = APIRouter()


@router.post("/calendar/events/sample")
async def load_sample_events():
    calendar_summary_service.events = [
        {"start": {"dateTime": "2026-06-16T09:00:00"}, "summary": "Morning standup"},
        {"start": {"dateTime": "2026-06-16T13:00:00"}, "summary": "Project planning"},
        {"start": {"dateTime": "2026-06-17T10:30:00"}, "summary": "Doctor appointment"},
    ]
    return {"status": "loaded"}
