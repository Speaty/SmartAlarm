from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlarmCreate(BaseModel):
    label: str
    scheduled_at: datetime
    enabled: bool = True
    repeat_weekly: bool = True


class AlarmUpdate(BaseModel):
    label: Optional[str]
    scheduled_at: Optional[datetime]
    enabled: Optional[bool]
    repeat_weekly: Optional[bool]


class AlarmRead(BaseModel):
    id: int
    label: str
    scheduled_at: datetime
    enabled: bool
    repeat_weekly: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
