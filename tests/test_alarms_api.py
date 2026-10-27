from backend.scheduler import scheduler

FUTURE = "2099-01-05T07:30:00"  # a Monday


def job_for(alarm_id):
    return scheduler.get_job(f"alarm-{alarm_id}")


async def create(client, **overrides):
    body = {"label": "Morning", "scheduled_at": FUTURE, **overrides}
    response = await client.post("/alarms", json=body)
    assert response.status_code == 200, response.text
    return response.json()


async def test_create_alarm_returns_it_and_schedules_a_job(client):
    alarm = await create(client)

    assert alarm["label"] == "Morning"
    assert alarm["enabled"] is True
    assert alarm["repeat_weekly"] is True
    assert job_for(alarm["id"]) is not None


async def test_list_alarms(client):
    await create(client, label="One")
    await create(client, label="Two")

    response = await client.get("/alarms")

    assert response.status_code == 200
    assert [a["label"] for a in response.json()] == ["One", "Two"]


async def test_create_disabled_alarm_is_not_scheduled(client):
    alarm = await create(client, enabled=False)

    assert job_for(alarm["id"]) is None


async def test_partial_update_changes_only_sent_fields(client):
    alarm = await create(client, label="Old")

    response = await client.put(f"/alarms/{alarm['id']}", json={"label": "New"})

    assert response.status_code == 200
    updated = response.json()
    assert updated["label"] == "New"
    assert updated["scheduled_at"] == alarm["scheduled_at"]
    assert updated["repeat_weekly"] == alarm["repeat_weekly"]


async def test_disabling_an_alarm_removes_its_job(client):
    alarm = await create(client)

    await client.put(f"/alarms/{alarm['id']}", json={"enabled": False})

    assert job_for(alarm["id"]) is None


async def test_reenabling_an_alarm_schedules_it_again(client):
    alarm = await create(client, enabled=False)

    await client.put(f"/alarms/{alarm['id']}", json={"enabled": True})

    assert job_for(alarm["id"]) is not None


async def test_update_rejects_explicit_null(client):
    alarm = await create(client)

    response = await client.put(f"/alarms/{alarm['id']}", json={"label": None})

    assert response.status_code == 422


async def test_update_missing_alarm_is_404(client):
    response = await client.put("/alarms/999", json={"label": "x"})

    assert response.status_code == 404


async def test_delete_alarm_removes_row_and_job(client):
    alarm = await create(client)

    response = await client.delete(f"/alarms/{alarm['id']}")

    assert response.status_code == 200
    assert job_for(alarm["id"]) is None
    assert (await client.get("/alarms")).json() == []


async def test_delete_missing_alarm_is_404(client):
    response = await client.delete("/alarms/999")

    assert response.status_code == 404
