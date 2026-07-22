from fastapi.testclient import TestClient

from tyrwar.bridge.app import app


def test_bridge_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
