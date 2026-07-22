from fastapi.testclient import TestClient

from tyrwar.bridge.app import app


def test_bridge_requires_configured_api_key(monkeypatch) -> None:
    monkeypatch.delenv("TYRWAR_BRIDGE_API_KEY", raising=False)
    response = TestClient(app).get("/v1/status")
    assert response.status_code == 503
