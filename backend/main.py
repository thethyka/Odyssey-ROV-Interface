import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db_session
from .logs import LogEntry
from .repository import EventLogRepository
from .simulation_manager import SimulationManager, TooManySessionsError
from .simulator import RovSimulator


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sim_manager = SimulationManager()
    yield
    for session_id in list(app.state.sim_manager._sessions):
        await app.state.sim_manager.destroy_session(session_id)


app = FastAPI(lifespan=lifespan)
simulator = RovSimulator()


class EventLogOut(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    severity: str
    message: str
    mission_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class MissionSummaryOut(BaseModel):
    mission_id: uuid.UUID
    event_count: int
    first_event_at: datetime
    last_event_at: datetime

    model_config = ConfigDict(from_attributes=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"message": "Odyssey ROV Backend is running"}


@app.get("/healthz")
async def health():
    return {"status": "ok"}


@app.get("/mission-log", response_model=list[LogEntry])
async def get_mission_log():
    """Expose mission log over REST (for demo until gRPC is wired).

    TODO(#27): now disconnected from real sessions since each websocket
    connection has its own RovSimulator (see simulation_manager.py). This
    always returns []. Needs a session-scoped redesign.
    """
    return simulator.get_mission_log()


@app.get("/hello")
async def say_hello():
    return {"message": "Hello from FastAPI backend!"}


@app.get("/api/v1/events", response_model=list[EventLogOut])
async def list_events(
    severity: str | None = None,
    mission_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """List persisted WARNING/CRITICAL mission events, optionally filtered."""
    repo = EventLogRepository(db)
    return await repo.list_events(severity=severity, mission_id=mission_id)


@app.get("/api/v1/missions", response_model=list[MissionSummaryOut])
async def list_missions(db: AsyncSession = Depends(get_db_session)):
    """List past missions with summary stats derived from persisted events."""
    repo = EventLogRepository(db)
    return await repo.list_missions()


@app.websocket("/ws/telemetry")
async def telemetry_ws(ws: WebSocket):
    await ws.accept()
    sim_manager: SimulationManager = ws.app.state.sim_manager

    try:
        session = await sim_manager.create_session(ws)
    except TooManySessionsError:
        await ws.close(code=1013, reason="Server at capacity")
        return

    try:
        while True:
            msg = await ws.receive_json()
            await session.command_queue.put(msg)
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        await sim_manager.destroy_session(session.session_id)
        await ws.close()
