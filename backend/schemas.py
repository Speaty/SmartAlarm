from datetime import datetime, time as TimeOfDay
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VolumeSet(BaseModel):
    """Any subset of the speaker volume and the music/voice levels within it."""

    volume: Optional[int] = Field(None, ge=0, le=100)
    music: Optional[int] = Field(None, ge=0, le=100)
    voice: Optional[int] = Field(None, ge=0, le=100)


class DayAlarmUpdate(BaseModel):
    time: Optional[TimeOfDay] = None
    enabled: Optional[bool] = None


class DayAlarmRead(BaseModel):
    weekday: int
    day: str
    time: str  # "HH:MM", local time
    enabled: bool


class AlarmCreate(BaseModel):
    label: str
    scheduled_at: datetime
    enabled: bool = True
    repeat_weekly: bool = True


class AlarmUpdate(BaseModel):
    label: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    enabled: Optional[bool] = None
    repeat_weekly: Optional[bool] = None


class AlarmRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    scheduled_at: datetime
    enabled: bool
    repeat_weekly: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
