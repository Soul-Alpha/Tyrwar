from fastapi.testclient import TestClient

from tyrwar.dashboard.app import app


def test_dashboard_contains_secure_connection_fields() -> None:
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert 'name="login"' in response.text
    assert 'name="password" type="password"' in response.text
    assert 'name="server"' in response.text
    assert 'name="bridge_key" type="password"' in response.text
