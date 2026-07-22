from fastapi.testclient import TestClient
import pytest

from tyrwar.dashboard.app import _safe_bridge_url, app


def test_dashboard_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_remote_bridge_requires_https() -> None:
    with pytest.raises(Exception):
        _safe_bridge_url("http://example.com")


def test_local_bridge_may_use_http() -> None:
    assert _safe_bridge_url("http://127.0.0.1:8090") == "http://127.0.0.1:8090"
