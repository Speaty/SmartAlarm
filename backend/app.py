from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .config import DATA_DIR, SECRET_KEY, FRONTEND_DIR
from .database import async_session, engine
from .models import Alarm, Base as ORMBase
from .scheduler import start_scheduler, schedule_alarm, remove_alarm_job, reload_alarms
from .auth_routes import router as oauth_router
from .schemas import AlarmCreate, AlarmRead, AlarmUpdate
from .alarm_controller import stop_alarm, play_schedule_summary, test_speakers
from .calendar_summary import calendar_summary_service
from .calendar_admin import router as calendar_admin_router

app = FastAPI(title="SmartAlarmPi")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.include_router(oauth_router, prefix="/oauth")
app.include_router(calendar_admin_router)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(ORMBase.metadata.create_all)
    start_scheduler()


@app.get("/alarms")
async def list_alarms():
    async with async_session() as session:
        result = await session.execute(select(Alarm))
        alarms = result.scalars().all()
    return alarms


@app.post("/alarms", response_model=AlarmRead)
async def create_alarm(payload: AlarmCreate):
    async with async_session() as session:
        alarm = Alarm(**payload.dict())
        session.add(alarm)
        await session.commit()
        await session.refresh(alarm)
    schedule_alarm(alarm)
    return alarm


@app.put("/alarms/{alarm_id}", response_model=AlarmRead)
async def update_alarm(alarm_id: int, payload: AlarmUpdate):
    async with async_session() as session:
        alarm = await session.get(Alarm, alarm_id)
        if not alarm:
            raise HTTPException(status_code=404, detail="Alarm not found")
        for key, value in payload.dict(exclude_none=True).items():
            setattr(alarm, key, value)
        await session.commit()
        await session.refresh(alarm)
    await reload_alarms()
    return alarm


@app.delete("/alarms/{alarm_id}")
async def delete_alarm(alarm_id: int):
    async with async_session() as session:
        alarm = await session.get(Alarm, alarm_id)
        if not alarm:
            raise HTTPException(status_code=404, detail="Alarm not found")
        await session.delete(alarm)
        await session.commit()
    remove_alarm_job(alarm_id)
    return {"status": "deleted", "id": alarm_id}


@app.post("/alarm/stop")
async def api_stop_alarm():
    await stop_alarm()
    return {"status": "stopped"}


@app.post("/alarm/summary")
async def api_alarm_summary():
    summary = []
    await play_schedule_summary(summary)
    return {"status": "summary_playing"}


@app.post("/alarm/test-speakers")
async def api_test_speakers():
    from .config import TEST_SPEAKER_URL

    await test_speakers(TEST_SPEAKER_URL)
    return {"status": "test_speakers_playing", "url": TEST_SPEAKER_URL}


@app.get("/calendar/summary")
async def get_calendar_summary():
    summary_text = await calendar_summary_service.get_summary()
    return {"summary": summary_text}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def read_frontend():
    index_path = DATA_DIR.parent / "frontend" / "index.html"
    return FileResponse(index_path)
