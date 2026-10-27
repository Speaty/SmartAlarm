from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
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

