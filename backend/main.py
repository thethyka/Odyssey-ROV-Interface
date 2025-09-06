from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import asyncio

from .simulator import RovSimulator
from .logs import LogEntry
from backend.simulator import RovSimulator
from backend.logs import LogEntry

app = FastAPI()
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
    """Expose mission log over REST (for demo until gRPC is wired)."""
    return simulator.get_mission_log()


@app.get("/hello")
async def say_hello():
    return {"message": "Hello from FastAPI backend!"}


@app.websocket("/ws/telemetry")
async def telemetry_ws(ws: WebSocket):
    """
    Bi-directional WebSocket for telemetry & operator commands.
    - Frontend can send JSON commands { "command": ..., "payload": ... }
    - Backend pushes telemetry snapshots at 1Hz
    """
    await ws.accept()
    try:
        while True:
            # Push telemetry
            telemetry = simulator.get_telemetry()
            await ws.send_json(telemetry.model_dump())

            # Non-blocking check for incoming command
            try:
                msg = await asyncio.wait_for(ws.receive_json(), timeout=1.0)
                simulator.handle_command(msg)
            except asyncio.TimeoutError:
                pass

            # Advance simulator 1 tick
            simulator.update()

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        await ws.close()
