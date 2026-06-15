import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from .audio_player import AudioPlayer
from .database import async_session
from .models import Alarm

scheduler = AsyncIOScheduler(timezone="UTC")
player = AudioPlayer()


def schedule_alarm(alarm: Alarm):
    try:
        trigger = CronTrigger.from_crontab(alarm.cron)
    except ValueError:
        return

    job_id = f"alarm-{alarm.id}"
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
