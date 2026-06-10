# backend/simulation_manager.py
import asyncio
import uuid
from typing import Dict, Optional

from fastapi import WebSocket

from backend.simulator import RovSimulator


class TooManySessionsError(Exception):
    """Raised when the server is already running MAX_CONCURRENT_SESSIONS sessions."""


class SimulationSession:
    """One visitor's isolated simulation: its own simulator, its own tick task."""

    def __init__(self, session_id: str, simulator: RovSimulator, ws: WebSocket):
        self.session_id = session_id
        self.simulator = simulator
        self.ws = ws
        self.task: Optional[asyncio.Task] = None
        self.command_queue: asyncio.Queue = asyncio.Queue()


class SimulationManager:
    """Owns the lifecycle of all active simulation sessions."""

    MAX_CONCURRENT_SESSIONS = 50

    def __init__(self):
        self._sessions: Dict[str, SimulationSession] = {}

    async def create_session(self, ws: WebSocket) -> SimulationSession:
        if len(self._sessions) >= self.MAX_CONCURRENT_SESSIONS:
            raise TooManySessionsError()

        session_id = str(uuid.uuid4())
        sim = RovSimulator()
        session = SimulationSession(session_id, sim, ws)
        session.task = asyncio.create_task(self._run_loop(session))
        self._sessions[session_id] = session
        return session

    async def destroy_session(self, session_id: str):
        session = self._sessions.pop(session_id, None)
        if session and session.task:
            session.task.cancel()

    async def _run_loop(self, session: SimulationSession):
        """Tick loop for a single session: drain commands, advance sim, send telemetry."""
        sim = session.simulator
        try:
            while True:
                while not session.command_queue.empty():
                    cmd = session.command_queue.get_nowait()
                    sim.handle_command(cmd)

                sim.update()
                telemetry = sim.get_telemetry()
                await session.ws.send_json(telemetry.model_dump())

                await asyncio.sleep(1 / sim.TICKS_PER_SECOND)
        except asyncio.CancelledError:
            pass
        except Exception:
            # Client disconnected mid-send; the receive loop (dish #1) will
            # detect this independently and call destroy_session.
            pass

    @property
    def active_session_count(self) -> int:
        return len(self._sessions)
