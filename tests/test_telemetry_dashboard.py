from fastapi.testclient import TestClient

from tyrwar.dashboard.app import LATEST, app


def test_telemetry_requires_configured_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TYRWAR_TELEMETRY_DB_PATH", str(tmp_path / "telemetry.db"))
    monkeypatch.delenv("TYRWAR_TELEMETRY_KEY", raising=False)
    LATEST.clear()
    response = TestClient(app).post("/api/telemetry", json={"mode": "PAPER/EVALUATION"})
    assert response.status_code == 503


def test_telemetry_ingestion_is_read_only_authenticated_and_persistent(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("TYRWAR_TELEMETRY_KEY", "secret")
    monkeypatch.setenv("TYRWAR_TELEMETRY_DB_PATH", str(tmp_path / "telemetry.db"))
    LATEST.clear()
    payload = {
        "checked_at_utc": "2099-01-01T00:00:00+00:00",
        "mode": "PAPER/EVALUATION",
        "balance": 50.0,
        "equity": 50.0,
        "open_positions": 0,
        "side": "flat",
        "reason": "strategy conditions not aligned",
        "rsi": 41.4,
        "executed": False,
        "account": "must-not-be-stored",
    }
    client = TestClient(app)
    accepted = client.post(
        "/api/telemetry",
        json=payload,
        headers={"X-Tyrwar-Telemetry-Key": "secret"},
    )
    assert accepted.status_code == 200

    LATEST.clear()  # Simulate a dashboard process restart.
    status = client.get("/api/status").json()
    assert status["connection"] == "Online"
    assert status["balance"] == 50.0
    assert "account" not in status
