# backend/tests/test_persistence.py
import asyncio
import time
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.config import settings
from backend.repository import EventLogRepository

from .test_backend import _recv_n, _recv_until

# ---------- Helpers ----------


def _query_events(*, mission_id: uuid.UUID | None = None, severity: str | None = None):
    async def _query():
        # Short-lived engine: the app's global engine is bound to its own
        # event loop, which differs from the loop `asyncio.run` creates here.
        engine = create_async_engine(settings.database_url, poolclass=NullPool)
        try:
            async with async_sessionmaker(engine)() as session:
                repo = EventLogRepository(session)
                return await repo.list_events(severity=severity, mission_id=mission_id)
        finally:
            await engine.dispose()

    return asyncio.run(_query())


def _wait_for_events(*, mission_id: uuid.UUID, severity: str, min_count=1, timeout=2.0):
    deadline = time.monotonic() + timeout
    events = []
    while time.monotonic() < deadline:
        events = _query_events(mission_id=mission_id, severity=severity)
        if len(events) >= min_count:
            return events
        time.sleep(0.05)
    raise AssertionError(f"expected >= {min_count} '{severity}' events, got {len(events)}")


# ---------- Tests ----------


def test_critical_event_is_persisted_with_mission_id(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "pressure_anomaly"}}
        )

        _recv_until(ws, lambda d: d["alert"]["severity"] == "CRITICAL", max_steps=1500)
        _recv_n(ws, 2)  # let the persist step for this tick complete before disconnecting

        session = next(iter(client.app.state.sim_manager._sessions.values()))
        mission_id = session.mission_id

    events = _wait_for_events(mission_id=mission_id, severity="CRITICAL")
    assert all(e.mission_id == mission_id for e in events)
    assert all(e.severity == "CRITICAL" for e in events)


def test_info_events_are_not_persisted(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )
        _recv_until(ws, lambda d: d["alert"]["severity"] == "INFO", max_steps=1000)

        session = next(iter(client.app.state.sim_manager._sessions.values()))
        mission_id = session.mission_id

    time.sleep(0.2)
    assert _query_events(mission_id=mission_id) == []


def test_events_endpoint_filters_by_severity_and_mission(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "pressure_anomaly"}}
        )
        _recv_until(ws, lambda d: d["alert"]["severity"] == "WARNING", max_steps=500)
        _recv_n(ws, 2)  # let the persist step for this tick complete before disconnecting

        session = next(iter(client.app.state.sim_manager._sessions.values()))
        mission_id = session.mission_id

    _wait_for_events(mission_id=mission_id, severity="WARNING")

    resp = client.get("/api/v1/events", params={"severity": "WARNING"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert all(e["severity"] == "WARNING" for e in body)

    resp = client.get("/api/v1/events", params={"mission_id": str(mission_id)})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert all(e["mission_id"] == str(mission_id) for e in body)

    other_mission_id = uuid.uuid4()
    resp = client.get("/api/v1/events", params={"mission_id": str(other_mission_id)})
    assert resp.status_code == 200
    assert resp.json() == []


def test_missions_endpoint_summarizes_persisted_events(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "pressure_anomaly"}}
        )
        _recv_until(ws, lambda d: d["alert"]["severity"] == "WARNING", max_steps=500)
        _recv_n(ws, 2)  # let the persist step for this tick complete before disconnecting

        session = next(iter(client.app.state.sim_manager._sessions.values()))
        mission_id = session.mission_id

    _wait_for_events(mission_id=mission_id, severity="WARNING")

    resp = client.get("/api/v1/missions")
    assert resp.status_code == 200
    missions = {m["mission_id"]: m for m in resp.json()}
    assert str(mission_id) in missions
    summary = missions[str(mission_id)]
    assert summary["event_count"] >= 1
    assert summary["first_event_at"] <= summary["last_event_at"]
