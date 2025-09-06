from fastapi.testclient import TestClient
from backend.main import app, simulator

client = TestClient(app)


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
    # Reset simulator state
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
