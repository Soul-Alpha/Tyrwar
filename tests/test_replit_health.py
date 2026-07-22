from fastapi.testclient import TestClient

from tyrwar.dashboard.app import app


def test_replit_health_contract() -> None:
    response = TestClient(app).get("/health")
    assert response.headers["content-type"].startswith("application/json")
