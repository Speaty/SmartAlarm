import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select
from .audio_player import player
from .config import TIMEZONE
from .database import async_session
from .models import Alarm

scheduler = AsyncIOScheduler(timezone=TIMEZONE)


def schedule_alarm(alarm: Alarm):
    """Schedule an alarm. If `repeat_weekly` is True, schedule a weekly cron at the
    time and weekday of `scheduled_at`. Otherwise schedule a one-time `DateTrigger`.
    """
    if not alarm.scheduled_at:
        return

    job_id = f"alarm-{alarm.id}"

    # Ensure scheduled_at is a datetime
    dt: datetime = alarm.scheduled_at

    if alarm.repeat_weekly:
        # APScheduler expects day_of_week as 0-6 (mon-sun) or names; use weekday()
        trigger = CronTrigger(
            day_of_week=dt.weekday(),
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            timezone=TIMEZONE,
        )
    else:
        trigger = DateTrigger(run_date=dt, timezone=TIMEZONE)

    scheduler.add_job(
        alarm_handler,
        trigger,
        args=[alarm.id, alarm.label],
        id=job_id,
        replace_existing=True,
    )


async def load_alarms():
    async with async_session() as session:
        result = await session.execute(select(Alarm).where(Alarm.enabled == True))
        alarms = result.scalars().all()

    for alarm in alarms:
        schedule_alarm(alarm)


async def reload_alarms():
    scheduler.remove_all_jobs()
    await load_alarms()


def remove_alarm_job(alarm_id: int):
    job_id = f"alarm-{alarm_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


async def alarm_handler(alarm_id: int, label: str):
    await player.start_radio()
    await player.play_message(
        f"Alarm {label} is ringing. Tap the stop button to dismiss and hear your schedule summary."
    )


def start_scheduler():
    scheduler.start()
    asyncio.create_task(load_alarms())
