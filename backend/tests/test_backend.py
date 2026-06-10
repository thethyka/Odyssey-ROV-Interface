# backend/tests/test_backend.py
import time

import pytest
from fastapi import WebSocketDisconnect

from backend.simulation_manager import SimulationManager

# ---------- Helpers ----------


def _recv_until(ws, condition, max_steps=2000):
    """
    Drain telemetry until condition(data) is True or max_steps exceeded.
    Returns the matching telemetry packet.
    """
    last = None
    for _ in range(max_steps):
        last = ws.receive_json()
        if condition(last):
            return last
    raise AssertionError("Condition not met in telemetry stream", last)


def _recv_n(ws, n):
    """Receive exactly n frames, return the last one."""
    last = None
    for _ in range(n):
        last = ws.receive_json()
    return last


def _only_session_simulator(client):
    """Grab the RovSimulator for the (single) currently active session.

    Must be called while the websocket connection is still open --
    destroy_session removes the session from the manager on disconnect.
    """
    sessions = list(client.app.state.sim_manager._sessions.values())
    assert len(sessions) == 1
    return sessions[0].simulator


# ---------- REST TESTS ----------


def test_root_and_healthz(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Odyssey ROV Backend" in resp.json()["message"]

    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_hello(client):
    resp = client.get("/hello")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello from FastAPI backend!"}


def test_mission_log_empty_start(client):
    resp = client.get("/mission-log")
    assert resp.status_code == 200
    assert resp.json() == []


def test_mission_log_after_command(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()  # initial telemetry
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )
        ws.receive_json()  # updated telemetry

        sim = _only_session_simulator(client)

    logs = sim.get_mission_log()
    assert any("Scenario Started" in log.message for log in logs)
    assert any("Mission status changed to 'en_route'" in log.message for log in logs)


# ---------- WEBSOCKET TESTS ----------


def test_nominal_mission_success(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )
        _recv_until(ws, lambda d: d["mission_state"]["status"] == "searching")

        ws.send_json({"command": "DEPLOY_ARM"})
        ws.send_json({"command": "COLLECT_SAMPLE"})

        # First confirm it enters returning phase
        returning = _recv_until(
            ws,
            lambda d: d["mission_state"]["status"] == "returning",
            max_steps=1000,
        )
        assert returning["mission_state"]["status"] == "returning"

        # Now wait longer for ascent to complete
        result = _recv_until(
            ws,
            lambda d: d["mission_state"]["status"] == "mission_success",
            max_steps=5000,  # increased from 1000
        )
        assert result["mission_state"]["status"] == "mission_success"


def test_pressure_anomaly_failure_path(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "pressure_anomaly"}}
        )

        result = _recv_until(
            ws,
            lambda d: d["mission_state"]["status"] == "mission_failure_hull_breach",
            max_steps=1500,
        )
        assert result["mission_state"]["status"] == "mission_failure_hull_breach"


def test_power_fault_failure_path(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "power_fault"}}
        )

        result = _recv_until(
            ws,
            lambda d: d["mission_state"]["status"] == "mission_failure_lost_signal",
            max_steps=3000,
        )
        assert result["mission_state"]["status"] == "mission_failure_lost_signal"


def test_pressure_anomaly_success_path_all_stop_no_snap_no_escalation(client):
    """
    Operator intervenes with All-Stop after WARNING.
    - Hull returns to nominal and alert clears
    - Depth does NOT 'snap' downward
    - Scenario no longer escalates to CRITICAL / failure
    """
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "pressure_anomaly"}}
        )

        # Wait until warning triggers and capture depth at that moment
        at_warning = _recv_until(
            ws, lambda d: d["alert"]["severity"] == "WARNING", max_steps=500
        )
        depth_at_warning = at_warning["rov_state"]["environment"]["depth_meters"]

        # Operator sends All Stop
        ws.send_json(
            {"command": "SET_PROPULSION_STATE", "payload": {"status": "inactive"}}
        )

        # Expect hull back to nominal and alert cleared (no depth snap)
        nominal = _recv_until(
            ws, lambda d: d["rov_state"]["hull_integrity"]["status"] == "nominal"
        )
        depth_after = nominal["rov_state"]["environment"]["depth_meters"]
        assert nominal["alert"]["active"] is False
        assert nominal["rov_state"]["propulsion"]["status"] == "inactive"

        # No snap downwards (allow tiny float noise)
        assert depth_after + 1e-6 >= depth_at_warning

        # No further escalation despite continuing ticks
        for _ in range(200):
            frame = ws.receive_json()
            assert frame["rov_state"]["hull_integrity"]["status"] != "critical"
            assert frame["mission_state"]["status"] != "mission_failure_hull_breach"


def test_nominal_operator_override_respected_during_descent(client):
    """
    If an operator sends All-Stop during nominal descent,
    scenario logic must NOT force propulsion back on.
    """
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )

        # Ensure we're actually descending
        start = _recv_until(ws, lambda d: d["mission_state"]["status"] == "en_route")
        d0 = start["rov_state"]["environment"]["depth_meters"]

        # Operator hits all-stop
        ws.send_json(
            {"command": "SET_PROPULSION_STATE", "payload": {"status": "inactive"}}
        )

        # After many ticks, propulsion should remain inactive and depth should not increase
        after = _recv_n(ws, 200)
        d1 = after["rov_state"]["environment"]["depth_meters"]
        assert after["rov_state"]["propulsion"]["status"] == "inactive"
        # No further descent (allow tiny epsilon for float rounding)
        assert d1 <= d0 + 1e-6
        # Mission stays en_route (won't reach target depth)
        assert after["mission_state"]["status"] == "en_route"


def test_power_fault_success_path_jettison(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "power_fault"}}
        )

        _recv_until(ws, lambda d: d["alert"]["severity"] == "CRITICAL", max_steps=500)
        ws.send_json({"command": "JETTISON_PACKAGE"})

        result = _recv_until(
            ws, lambda d: d["mission_state"]["status"] == "emergency_ascent"
        )
        assert result["mission_state"]["status"] == "emergency_ascent"
        # Alert should be cleared by jettison according to updated sim
        assert result["alert"]["active"] is False

        final = _recv_until(
            ws,
            lambda d: d["mission_state"]["status"] == "mission_success",
            max_steps=1500,
        )
        assert final["mission_state"]["status"] == "mission_success"


def test_nominal_mission_alert_and_log_entries(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )

        telemetry = _recv_until(
            ws, lambda d: d["alert"]["severity"] == "INFO", max_steps=1000
        )
        assert telemetry["alert"]["message"].startswith("Bioluminescent signature")

        sim = _only_session_simulator(client)

    logs = sim.get_mission_log()
    assert any("Scenario Started" in log.message for log in logs)
    assert any("Bioluminescent signature detected" in log.message for log in logs)


def test_invalid_command_is_logged(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json({"command": "FOO_BAR", "payload": {}})
        ws.receive_json()

        sim = _only_session_simulator(client)

    logs = sim.get_mission_log()
    assert any("Unknown command" in log.message for log in logs)


# ---------- SESSION ISOLATION TESTS (T1-1) ----------


def test_each_connection_gets_an_isolated_simulator(client):
    """Two tabs open: each runs its own scenario, neither affects the other."""
    with client.websocket_connect("/ws/telemetry") as ws1, client.websocket_connect(
        "/ws/telemetry"
    ) as ws2:
        ws1.receive_json()
        ws2.receive_json()

        assert client.app.state.sim_manager.active_session_count == 2

        # Only ws1 starts its mission
        ws1.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )
        t1 = _recv_until(ws1, lambda d: d["mission_state"]["status"] == "en_route")
        assert t1["rov_state"]["environment"]["depth_meters"] > 0

        # ws2 never received START_SIMULATION -- must remain in standby,
        # at depth 0, completely unaffected by ws1's progress.
        t2 = ws2.receive_json()
        assert t2["mission_state"]["status"] == "standby"
        assert t2["rov_state"]["environment"]["depth_meters"] == 0

    # Both sessions cleaned up on disconnect
    assert client.app.state.sim_manager.active_session_count == 0


def test_two_concurrent_sessions_each_tick_at_one_x_speed(client):
    """The original bug: N clients caused N updates per real tick.

    With two sessions running simultaneously, ws1's depth must still advance
    by exactly DESCENT_RATE per *received frame* -- not 2x DESCENT_RATE,
    which is what a shared simulator would produce.
    """
    DESCENT_RATE = 25.0  # RovSimulator.DESCENT_RATE

    with client.websocket_connect("/ws/telemetry") as ws1, client.websocket_connect(
        "/ws/telemetry"
    ) as ws2:
        ws1.receive_json()
        ws2.receive_json()

        ws1.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )
        ws2.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )

        prev_depth = ws1.receive_json()["rov_state"]["environment"]["depth_meters"]
        for _ in range(10):
            depth = ws1.receive_json()["rov_state"]["environment"]["depth_meters"]
            assert depth - prev_depth == pytest.approx(DESCENT_RATE)
            prev_depth = depth


def test_session_task_cancelled_on_disconnect(client):
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        session = next(iter(client.app.state.sim_manager._sessions.values()))
        task = session.task

    # task.cancel() only requests cancellation; give the event loop a moment
    # to actually process it.
    for _ in range(50):
        if task.done():
            break
        time.sleep(0.01)

    # _run_loop catches CancelledError to exit gracefully, so the task
    # finishes normally (done=True, cancelled=False) rather than ending
    # in the "cancelled" state -- that's the correct, clean shutdown.
    assert task.done()
    assert task.exception() is None


def test_server_rejects_connections_beyond_max_sessions(client, monkeypatch):
    monkeypatch.setattr(SimulationManager, "MAX_CONCURRENT_SESSIONS", 1)

    with client.websocket_connect("/ws/telemetry") as ws1:
        ws1.receive_json()
        assert client.app.state.sim_manager.active_session_count == 1

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/telemetry") as ws2:
                ws2.receive_json()
