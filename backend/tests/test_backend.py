# backend/tests/test_backend.py
import math
import pytest
from fastapi.testclient import TestClient
from backend.main import app, simulator

client = TestClient(app)


# ---------- Helpers ----------


@pytest.fixture(autouse=True)
def fast_mode():
    """Run simulator at high tick rate for tests."""
    simulator.TICKS_PER_SECOND = 200  # high frequency for speed
    yield
    simulator.TICKS_PER_SECOND = 1  # reset after test


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


# ---------- REST TESTS ----------


def test_root_and_healthz():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Odyssey ROV Backend" in resp.json()["message"]

    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_hello():
    resp = client.get("/hello")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello from FastAPI backend!"}


def test_mission_log_empty_start():
    resp = client.get("/mission-log")
    assert resp.status_code == 200
    assert resp.json() == []


def test_mission_log_after_command():
    simulator._reset_state()
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()  # initial telemetry
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )
        ws.receive_json()  # updated telemetry

    logs = simulator.get_mission_log()
    assert any("Scenario Started" in log.message for log in logs)
    assert any("Mission status changed to 'en_route'" in log.message for log in logs)


# ---------- WEBSOCKET TESTS ----------


def test_nominal_mission_success():
    simulator._reset_state()
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


def test_pressure_anomaly_failure_path():
    simulator._reset_state()
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


def test_power_fault_failure_path():
    simulator._reset_state()
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


def test_pressure_anomaly_success_path_all_stop_no_snap_no_escalation():
    """
    Operator intervenes with All-Stop after WARNING.
    - Hull returns to nominal and alert clears
    - Depth does NOT 'snap' downward
    - Scenario no longer escalates to CRITICAL / failure
    """
    simulator._reset_state()
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


def test_nominal_operator_override_respected_during_descent():
    """
    If an operator sends All-Stop during nominal descent,
    scenario logic must NOT force propulsion back on.
    """
    simulator._reset_state()
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


def test_power_fault_success_path_jettison():
    simulator._reset_state()
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


def test_nominal_mission_alert_and_log_entries():
    simulator._reset_state()
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )

        telemetry = _recv_until(
            ws, lambda d: d["alert"]["severity"] == "INFO", max_steps=1000
        )
        assert telemetry["alert"]["message"].startswith("Bioluminescent signature")

    logs = simulator.get_mission_log()
    assert any("Scenario Started" in log.message for log in logs)
    assert any("Bioluminescent signature detected" in log.message for log in logs)


def test_invalid_command_is_logged():
    simulator._reset_state()
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()
        ws.send_json({"command": "FOO_BAR", "payload": {}})
        ws.receive_json()

    logs = simulator.get_mission_log()
    assert any("Unknown command" in log.message for log in logs)


def test_multiple_clients_receive_same_telemetry():
    simulator._reset_state()
    with client.websocket_connect("/ws/telemetry") as ws1, client.websocket_connect(
        "/ws/telemetry"
    ) as ws2:
        ws1.receive_json()
        ws2.receive_json()
        ws1.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )

        t1 = _recv_until(
            ws1, lambda d: d["mission_state"]["status"] == "searching", max_steps=1000
        )
        t2 = _recv_until(
            ws2, lambda d: d["mission_state"]["status"] == "searching", max_steps=1000
        )

        assert t1["mission_state"]["status"] == t2["mission_state"]["status"]
