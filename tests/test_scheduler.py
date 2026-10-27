from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from backend import alarm_controller
from backend.database import async_session
from backend.models import Alarm
from backend.scheduler import alarm_handler, load_alarms, schedule_alarm, scheduler


async def add_alarm(**fields) -> Alarm:
    defaults = {"label": "Morning", "scheduled_at": datetime(2099, 1, 5, 7, 30)}
    async with async_session() as session:
        alarm = Alarm(**{**defaults, **fields})
        session.add(alarm)
        await session.commit()
        await session.refresh(alarm)
    return alarm


async def get_alarm(alarm_id) -> Alarm:
    async with async_session() as session:
        return await session.get(Alarm, alarm_id)


def job_for(alarm):
    return scheduler.get_job(f"alarm-{alarm.id}")


def cron_fields(trigger: CronTrigger) -> dict:
    return {f.name: str(f) for f in trigger.fields}


async def test_weekly_alarm_uses_cron_on_same_weekday_and_time():
    alarm = await add_alarm(repeat_weekly=True)  # 2099-01-05 is a Monday

    schedule_alarm(alarm)

    trigger = job_for(alarm).trigger
    assert isinstance(trigger, CronTrigger)
    fields = cron_fields(trigger)
    assert fields["day_of_week"] == "0"
    assert fields["hour"] == "7"
    assert fields["minute"] == "30"


async def test_weekly_alarm_in_the_past_is_still_scheduled():
    alarm = await add_alarm(repeat_weekly=True, scheduled_at=datetime(2000, 1, 3, 6, 0))

    schedule_alarm(alarm)

    assert job_for(alarm) is not None


async def test_one_off_future_alarm_uses_date_trigger():
    alarm = await add_alarm(repeat_weekly=False)

    schedule_alarm(alarm)

    trigger = job_for(alarm).trigger
    assert isinstance(trigger, DateTrigger)
    assert trigger.run_date.replace(tzinfo=None) == datetime(2099, 1, 5, 7, 30)


async def test_one_off_alarm_in_the_past_is_not_scheduled():
    alarm = await add_alarm(repeat_weekly=False, scheduled_at=datetime(2000, 1, 1, 7, 0))

    schedule_alarm(alarm)

    assert job_for(alarm) is None


async def test_disabled_alarm_is_not_scheduled():
    alarm = await add_alarm(enabled=False)

    schedule_alarm(alarm)

    assert job_for(alarm) is None


async def test_scheduling_a_disabled_alarm_removes_existing_job():
    alarm = await add_alarm()
    schedule_alarm(alarm)

    alarm.enabled = False
    schedule_alarm(alarm)

    assert job_for(alarm) is None


async def test_load_alarms_schedules_only_enabled_ones():
    on = await add_alarm(label="on")
    off = await add_alarm(label="off", enabled=False)

    await load_alarms()

    assert job_for(on) is not None
    assert job_for(off) is None


async def test_handler_rings_and_announces_label(player):
    alarm = await add_alarm(label="Gym")

    await alarm_handler(alarm.id, alarm.label, True)

    player.start_radio.assert_awaited_once()
    assert "Gym" in player.play_message.await_args.args[0]
    assert alarm_controller.is_ringing()


async def test_one_off_alarm_disables_itself_when_it_fires():
    alarm = await add_alarm(repeat_weekly=False)

    await alarm_handler(alarm.id, alarm.label, False)

    assert (await get_alarm(alarm.id)).enabled is False


async def test_weekly_alarm_stays_enabled_after_firing():
    alarm = await add_alarm(repeat_weekly=True)

    await alarm_handler(alarm.id, alarm.label, True)

    assert (await get_alarm(alarm.id)).enabled is True
