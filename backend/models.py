from datetime import datetime, time
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Time
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True)
    label = Column(String(128), nullable=False, default="Alarm")
    scheduled_at = Column(DateTime, nullable=False)
    enabled = Column(Boolean, default=True)
    repeat_weekly = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DayAlarm(Base):
    """The repeating alarm for one day of the week; at most one row per weekday."""

    __tablename__ = "day_alarms"

    weekday = Column(Integer, primary_key=True)  # 0 = Monday ... 6 = Sunday
    time = Column(Time, nullable=False, default=time(7, 0))
    enabled = Column(Boolean, nullable=False, default=False)
