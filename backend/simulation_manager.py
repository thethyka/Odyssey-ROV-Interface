# backend/simulation_manager.py
import asyncio
import uuid

from fastapi import WebSocket

from backend.database import async_session_factory
from backend.logs import LogEntry, LogLevel
from backend.repository import EventLogRepository
from backend.simulator import RovSimulator

# Severities that get persisted to the event_log table.
PERSISTED_SEVERITIES = {LogLevel.WARNING, LogLevel.CRITICAL}


class TooManySessionsError(Exception):
    """Raised when the server is already running MAX_CONCURRENT_SESSIONS sessions."""


class SimulationSession:
    """One visitor's isolated simulation: its own simulator, its own tick task."""

    def __init__(self, session_id: str, simulator: RovSimulator, ws: WebSocket):
        self.session_id = session_id
        self.mission_id = uuid.UUID(session_id)
        self.simulator = simulator
        self.ws = ws
        self.task: asyncio.Task | None = None
        self.command_queue: asyncio.Queue = asyncio.Queue()
        self.pending_events: list[LogEntry] = []


class SimulationManager:
    """Owns the lifecycle of all active simulation sessions."""

    MAX_CONCURRENT_SESSIONS = 50

    def __init__(self):
        self._sessions: dict[str, SimulationSession] = {}

    async def create_session(self, ws: WebSocket) -> SimulationSession:
        if len(self._sessions) >= self.MAX_CONCURRENT_SESSIONS:
            raise TooManySessionsError()

        session_id = str(uuid.uuid4())
        sim = RovSimulator()
        session = SimulationSession(session_id, sim, ws)
        sim.on_event = session.pending_events.append
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
                await self._persist_events(session)

                await asyncio.sleep(1 / sim.TICKS_PER_SECOND)
        except asyncio.CancelledError:
            pass
        except Exception:
            # Client disconnected mid-send; the receive loop (dish #1) will
            # detect this independently and call destroy_session.
            pass

    async def _persist_events(self, session: SimulationSession):
        """Persist any newly emitted WARNING/CRITICAL events to the event_log table."""
        if not session.pending_events:
            return

        events = list(session.pending_events)
        session.pending_events.clear()
        to_persist = [e for e in events if e.level in PERSISTED_SEVERITIES]
        if not to_persist:
            return

        # Shielded so a session cancellation (tab closed mid-write) can't abort
        # an in-flight commit and leave the connection in an open transaction.
        await asyncio.shield(self._write_events(session.mission_id, to_persist))

    async def _write_events(self, mission_id: uuid.UUID, entries: list[LogEntry]):
        async with async_session_factory() as db_session:
            repo = EventLogRepository(db_session)
            for entry in entries:
                await repo.insert(
                    timestamp=entry.timestamp,
                    severity=entry.level.value,
                    message=entry.message,
                    mission_id=mission_id,
                )

    @property
    def active_session_count(self) -> int:
        return len(self._sessions)
