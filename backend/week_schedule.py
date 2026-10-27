from datetime import time
from typing import List

from fastapi import APIRouter, HTTPException, Path
from sqlalchemy import select

from .database import async_session
from .models import DayAlarm
from .scheduler import schedule_day
from .schemas import DayAlarmRead, DayAlarmUpdate

router = APIRouter()

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DEFAULT_TIME = time(7, 0)


def default_day(weekday: int) -> DayAlarm:
    return DayAlarm(weekday=weekday, time=DEFAULT_TIME, enabled=False)


def to_read(day: DayAlarm) -> DayAlarmRead:
    return DayAlarmRead(
        weekday=day.weekday,
        day=DAY_NAMES[day.weekday],
        time=day.time.strftime("%H:%M"),
        enabled=day.enabled,
    )


@router.get("/schedule", response_model=List[DayAlarmRead])
async def read_schedule():
    """All seven days, Monday first. Days never set are off at the default time."""
    async with async_session() as session:
        result = await session.execute(select(DayAlarm))
        stored = {day.weekday: day for day in result.scalars().all()}
    return [to_read(stored.get(weekday) or default_day(weekday)) for weekday in range(7)]


@router.put("/schedule/{weekday}", response_model=DayAlarmRead)
async def update_day(payload: DayAlarmUpdate, weekday: int = Path(..., ge=0, le=6)):
    async with async_session() as session:
        day = await session.get(DayAlarm, weekday)
        if day is None:
            day = default_day(weekday)
            session.add(day)
        for key, value in payload.model_dump(exclude_unset=True).items():
            if value is None:
                raise HTTPException(status_code=422, detail=f"{key} cannot be null")
            setattr(day, key, value)
        await session.commit()
        await session.refresh(day)
    schedule_day(day)
    return to_read(day)
