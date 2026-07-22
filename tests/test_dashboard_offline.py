from fastapi.testclient import TestClient

from tyrwar.dashboard.app import app


def test_dashboard_status_is_offline_without_session() -> None:
    response = TestClient(app).get("/api/status")
    assert response.status_code == 200
    assert response.json()["connected"] == "Offline"
