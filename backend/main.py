from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .simulator import RovSimulator
from .logs import LogEntry
from .simulation_manager import SimulationManager, TooManySessionsError


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sim_manager = SimulationManager()
    yield
    for session_id in list(app.state.sim_manager._sessions):
        await app.state.sim_manager.destroy_session(session_id)


app = FastAPI(lifespan=lifespan)
simulator = RovSimulator()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


@app.get("/mission-log", response_model=List[LogEntry])
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
