"""Read-only Replit dashboard receiving outbound Tyrwar telemetry."""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from typing import Any, Annotated

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="Tyrwar Bot Monitor", docs_url=None, redoc_url=None)
LATEST: dict[str, Any] = {}


def _require_key(x_tyrwar_telemetry_key: Annotated[str | None, Header()] = None) -> None:
    expected = os.getenv("TYRWAR_TELEMETRY_KEY", "")
    if not expected:
        raise HTTPException(503, "TYRWAR_TELEMETRY_KEY is not configured")
    if x_tyrwar_telemetry_key is None or not secrets.compare_digest(
        x_tyrwar_telemetry_key, expected
    ):
        raise HTTPException(401, "Invalid telemetry key")


def _age_seconds(snapshot: dict[str, Any]) -> float | None:
    value = snapshot.get("checked_at_utc")
    if not isinstance(value, str):
        return None
    try:
        checked = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0.0, (datetime.now(timezone.utc) - checked).total_seconds())


@app.post("/api/telemetry")
def ingest(
    snapshot: dict[str, Any],
    x_tyrwar_telemetry_key: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    _require_key(x_tyrwar_telemetry_key)
    allowed = {
        "checked_at_utc",
        "mode",
        "balance",
        "equity",
        "margin_free",
        "open_positions",
        "symbol",
        "side",
        "reason",
        "rsi",
        "signal_time",
        "executed",
        "feature_store_observations",
        "runtime_status",
    }
    LATEST.clear()
    LATEST.update({key: value for key, value in snapshot.items() if key in allowed})
    return {"status": "accepted"}


@app.get("/api/status")
def status() -> JSONResponse:
    if not LATEST:
        return JSONResponse({"connection": "Offline", "message": "No telemetry received."})
    data = dict(LATEST)
    age = _age_seconds(data)
    stale_after = int(os.getenv("TYRWAR_STALE_AFTER_SECONDS", "90"))
    data["heartbeat_age_seconds"] = round(age, 1) if age is not None else None
    data["connection"] = "Stale" if age is None or age > stale_after else "Online"
    return JSONResponse(data)


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tyrwar Monitor</title><style>
:root{--bg:#071018;--panel:#101c28;--line:#273746;--text:#e8f1f7;--muted:#91a4b5;--good:#34d399}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Arial,sans-serif}
main{max-width:1100px;margin:auto;padding:24px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.card,.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}.panel{margin-top:16px}
.label{color:var(--muted);font-size:.8rem;text-transform:uppercase}.metric{font-size:1.5rem;font-weight:700;margin-top:8px}
pre{white-space:pre-wrap;color:var(--muted)}@media(max-width:760px){.grid{grid-template-columns:repeat(2,1fr)}}
</style></head><body><main><h1>Tyrwar · XAUUSD M5</h1><p>Read-only outbound telemetry dashboard</p>
<div class="grid">
<div class="card"><div class="label">Connection</div><div class="metric" id="connection">Offline</div></div>
<div class="card"><div class="label">Mode</div><div class="metric" id="mode">—</div></div>
<div class="card"><div class="label">Balance</div><div class="metric" id="balance">—</div></div>
<div class="card"><div class="label">Equity</div><div class="metric" id="equity">—</div></div>
<div class="card"><div class="label">Signal</div><div class="metric" id="side">—</div></div>
<div class="card"><div class="label">RSI</div><div class="metric" id="rsi">—</div></div>
<div class="card"><div class="label">Positions</div><div class="metric" id="open_positions">—</div></div>
<div class="card"><div class="label">Heartbeat age</div><div class="metric" id="heartbeat_age_seconds">—</div></div>
</div><section class="panel"><h2>Operational status</h2><pre id="detail">No telemetry received.</pre></section>
<script>async function poll(){try{const r=await fetch('/api/status');const d=await r.json();
for(const k of ['connection','mode','balance','equity','side','rsi','open_positions','heartbeat_age_seconds']){
if(d[k]!==undefined)document.getElementById(k).textContent=d[k]??'—'}document.getElementById('detail').textContent=JSON.stringify(d,null,2)}
catch(e){document.getElementById('detail').textContent=String(e)}}poll();setInterval(poll,10000)</script></main></body></html>""")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
