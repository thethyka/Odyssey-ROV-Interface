import pytest
from fastapi.testclient import TestClient
from backend.main import app, simulator

client = TestClient(app)


@pytest.fixture(autouse=True)
def fast_mode():
    # Make descents/ascents instant
    simulator.DESCENT_RATE = 1000.0
    simulator.ASCENT_RATE = 1000.0

    # Lower thresholds
    simulator.PRESSURE_WARNING_THRESHOLD = 50
    simulator.PRESSURE_CRITICAL_THRESHOLD = 100

    yield

    # Reset after test
    simulator.DESCENT_RATE = 25.0
    simulator.ASCENT_RATE = 20.0
    simulator.PRESSURE_WARNING_THRESHOLD = (
        simulator.TARGET_DEPTH * simulator.PRESSURE_PER_METER * 1.1
    )
    simulator.PRESSURE_CRITICAL_THRESHOLD = (
        simulator.TARGET_DEPTH * simulator.PRESSURE_PER_METER * 1.2
    )


def _recv_until(ws, condition, max_steps=200):
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


@pytest.fixture(autouse=True)
def speed_up_simulator():
    """Patch simulator for faster tests (faster depth/pressure changes)."""
    simulator.DESCENT_RATE = 500.0
    simulator.ASCENT_RATE = 500.0
    yield
    simulator.DESCENT_RATE = 25.0
    simulator.ASCENT_RATE = 20.0


def test_nominal_mission_success():
    simulator._reset_state()
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.receive_json()  # standby

        ws.send_json(
            {"command": "START_SIMULATION", "payload": {"scenario": "nominal"}}
        )
        _recv_until(ws, lambda d: d["mission_state"]["status"] == "searching")

        ws.send_json({"command": "DEPLOY_ARM"})
        ws.send_json({"command": "COLLECT_SAMPLE"})

        result = _recv_until(
            ws,
            lambda d: d["mission_state"]["status"] == "mission_success",
            max_steps=200,
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
            max_steps=500,
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
            max_steps=1000,
        )
        assert result["mission_state"]["status"] == "mission_failure_lost_signal"
