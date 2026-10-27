from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VolumeSet(BaseModel):
    volume: int = Field(..., ge=0, le=100)


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
