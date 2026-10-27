from datetime import time

import pytest
from apscheduler.triggers.cron import CronTrigger

from backend import alarm_controller
from backend.database import async_session
from backend.models import DayAlarm
from backend.scheduler import day_alarm_handler, load_alarms, scheduler


def day_job(weekday):
    return scheduler.get_job(f"day-{weekday}")


def cron_fields(trigger: CronTrigger) -> dict:
    return {f.name: str(f) for f in trigger.fields}


async def put_day(client, weekday, **body):
    return await client.put(f"/schedule/{weekday}", json=body)


async def test_schedule_lists_all_seven_days_off_by_default(client):
    response = await client.get("/schedule")

    week = response.json()
    assert [d["day"] for d in week] == [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
    assert all(d["time"] == "07:00" and d["enabled"] is False for d in week)


async def test_turning_a_day_on_schedules_a_weekly_job(client):
    response = await put_day(client, 2, enabled=True, time="06:45")

    assert response.json() == {"weekday": 2, "day": "Wednesday", "time": "06:45", "enabled": True}
    fields = cron_fields(day_job(2).trigger)
    assert fields["day_of_week"] == "2"
    assert fields["hour"] == "6"
    assert fields["minute"] == "45"


async def test_turning_a_day_on_keeps_default_time(client):
    response = await put_day(client, 0, enabled=True)

    assert response.json()["time"] == "07:00"
    assert day_job(0) is not None


async def test_setting_time_on_an_off_day_saves_it_without_scheduling(client):
    response = await put_day(client, 4, time="09:30")

    assert response.json()["time"] == "09:30"
    assert response.json()["enabled"] is False
    assert day_job(4) is None


async def test_changing_time_reschedules(client):
    await put_day(client, 1, enabled=True, time="07:00")

    await put_day(client, 1, time="08:15")

    fields = cron_fields(day_job(1).trigger)
    assert (fields["hour"], fields["minute"]) == ("8", "15")


async def test_turning_a_day_off_removes_job_and_keeps_time(client):
    await put_day(client, 5, enabled=True, time="10:00")

    response = await put_day(client, 5, enabled=False)

    assert day_job(5) is None
    assert response.json()["time"] == "10:00"


async def test_changes_show_up_in_schedule(client):
    await put_day(client, 6, enabled=True, time="11:00")

    sunday = (await client.get("/schedule")).json()[6]

    assert sunday == {"weekday": 6, "day": "Sunday", "time": "11:00", "enabled": True}


async def test_days_are_independent(client):
    await put_day(client, 0, enabled=True, time="06:00")
    await put_day(client, 1, enabled=True, time="07:30")

    await put_day(client, 0, enabled=False)

    assert day_job(0) is None
    assert day_job(1) is not None


@pytest.mark.parametrize("weekday", [-1, 7])
async def test_invalid_weekday_is_rejected(client, weekday):
    response = await put_day(client, weekday, enabled=True)

    assert response.status_code == 422


@pytest.mark.parametrize("bad_time", ["", "25:00", "seven"])
async def test_invalid_time_is_rejected(client, bad_time):
    response = await put_day(client, 0, time=bad_time)

    assert response.status_code == 422


@pytest.mark.parametrize("field", ["time", "enabled"])
async def test_null_is_rejected(client, field):
    response = await put_day(client, 0, **{field: None})

    assert response.status_code == 422


async def test_load_alarms_schedules_enabled_days_only():
    async with async_session() as session:
        session.add_all([
            DayAlarm(weekday=0, time=time(6, 30), enabled=True),
            DayAlarm(weekday=3, time=time(8, 0), enabled=False),
        ])
        await session.commit()

    await load_alarms()

    assert day_job(0) is not None
    assert day_job(3) is None


async def test_day_alarm_rings(player):
    await day_alarm_handler(0)

    player.start_radio.assert_awaited_once()
    assert "stop button" in player.play_message.await_args.args[0]
    assert alarm_controller.is_ringing()


async def test_one_off_alarms_still_work_alongside_days(client):
    await put_day(client, 0, enabled=True)

    response = await client.post(
        "/alarms", json={"label": "Flight", "scheduled_at": "2099-03-01T04:00", "repeat_weekly": False}
    )

    assert response.status_code == 200
    assert scheduler.get_job(f"alarm-{response.json()['id']}") is not None
    assert day_job(0) is not None
