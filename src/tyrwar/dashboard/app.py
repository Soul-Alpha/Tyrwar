"""Replit-ready FastAPI dashboard for Tyrwar monitoring.

The dashboard never connects to MetaTrader 5 directly. It exchanges credentials and
monitoring requests with a separately hosted Windows bridge beside the MT5 terminal.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse


@dataclass
class DashboardSession:
    bridge_url: str
    bridge_key: str
    bridge_session: str
    account: str
    server: str
    symbol: str
    last_status: dict[str, Any] = field(default_factory=dict)


SESSIONS: dict[str, DashboardSession] = {}
app = FastAPI(title="Tyrwar Bot Monitor", docs_url=None, redoc_url=None)


def _safe_bridge_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise HTTPException(400, "Bridge URL must be a valid HTTP(S) URL")
    if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise HTTPException(400, "A remote bridge must use HTTPS")
    return value.rstrip("/")


def _page(message: str = "") -> str:
    notice = f'<div class="notice">{message}</div>' if message else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tyrwar Monitor</title>
<style>
:root{{--bg:#071018;--panel:#101c28;--line:#273746;--text:#e8f1f7;--muted:#91a4b5;--good:#34d399;--warn:#fbbf24;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,Arial,sans-serif}}
main{{max-width:1100px;margin:auto;padding:24px}} h1{{margin:0 0 6px}} .sub{{color:var(--muted);margin-bottom:22px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}} .card,.panel{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}}
.metric{{font-size:1.55rem;font-weight:700;margin-top:8px}} .label{{color:var(--muted);font-size:.82rem;text-transform:uppercase}}
.panel{{margin-top:16px}} form{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}} label{{font-size:.85rem;color:var(--muted)}}
input{{width:100%;margin-top:5px;padding:11px;border:1px solid var(--line);border-radius:8px;background:#09141e;color:var(--text)}}
button{{padding:12px 18px;border:0;border-radius:9px;background:var(--good);font-weight:700;cursor:pointer}} .wide{{grid-column:1/-1}}
.notice{{background:#3b2f0b;border:1px solid #80671a;padding:12px;border-radius:9px;margin-bottom:16px}} .status{{white-space:pre-wrap;color:var(--muted)}}
@media(max-width:760px){{.grid{{grid-template-columns:repeat(2,1fr)}}form{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1>Tyrwar · XAUUSD M5</h1><div class="sub">RSI + deterministic SMC monitoring console</div>{notice}
<div class="grid">
<div class="card"><div class="label">Bridge</div><div class="metric" id="connected">Offline</div></div>
<div class="card"><div class="label">Last signal</div><div class="metric" id="signal">—</div></div>
<div class="card"><div class="label">RSI</div><div class="metric" id="rsi">—</div></div>
<div class="card"><div class="label">Open positions</div><div class="metric" id="positions">—</div></div>
<div class="card"><div class="label">Balance</div><div class="metric" id="balance">—</div></div>
<div class="card"><div class="label">Equity</div><div class="metric" id="equity">—</div></div>
<div class="card"><div class="label">Daily P/L</div><div class="metric" id="daily_pnl">—</div></div>
<div class="card"><div class="label">Last candle</div><div class="metric" id="candle">—</div></div>
</div>
<section class="panel"><h2>Connect trade platform</h2>
<p class="sub">Credentials are sent directly to your Windows MT5 bridge and are not written to disk by this dashboard.</p>
<form method="post" action="/connect">
<div><label>Bridge URL<input name="bridge_url" placeholder="https://your-secure-bridge.example.com" required></label></div>
<div><label>Bridge API key<input name="bridge_key" type="password" autocomplete="off" required></label></div>
<div><label>MT5 account number<input name="login" inputmode="numeric" autocomplete="off" required></label></div>
<div><label>MT5 password<input name="password" type="password" autocomplete="new-password" required></label></div>
<div><label>Broker server<input name="server" placeholder="Broker-Server" required></label></div>
<div><label>Symbol<input name="symbol" value="XAUUSD" required></label></div>
<div class="wide"><button type="submit">Connect securely</button></div>
</form></section>
<section class="panel"><h2>Operational status</h2><div class="status" id="detail">No bridge session.</div></section>
<script>
async function poll(){{try{{const r=await fetch('/api/status');const d=await r.json();
for(const k of ['connected','signal','rsi','positions','balance','equity','daily_pnl','candle']){{if(d[k]!==undefined)document.getElementById(k).textContent=d[k]??'—';}}
document.getElementById('detail').textContent=JSON.stringify(d,null,2);}}catch(e){{document.getElementById('detail').textContent=String(e)}}}}
poll();setInterval(poll,10000);
</script></main></body></html>"""


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return HTMLResponse(_page())


@app.post("/connect", response_class=HTMLResponse)
async def connect(
    request: Request,
    bridge_url: str = Form(...),
    bridge_key: str = Form(...),
    login: str = Form(...),
    password: str = Form(...),
    server: str = Form(...),
    symbol: str = Form("XAUUSD"),
) -> HTMLResponse:
    safe_url = _safe_bridge_url(bridge_url)
    payload = {"login": int(login), "password": password, "server": server, "symbol": symbol}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{safe_url}/v1/connect",
                json=payload,
                headers={"X-Tyrwar-Bridge-Key": bridge_key},
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, f"Bridge connection failed: {exc}") from exc
    bridge_session = str(data.get("session_token", ""))
    if not bridge_session:
        raise HTTPException(502, "Bridge did not return a session token")
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = DashboardSession(
        bridge_url=safe_url,
        bridge_key=bridge_key,
        bridge_session=bridge_session,
        account=login,
        server=server,
        symbol=symbol,
    )
    response = HTMLResponse(_page("Connected. Password discarded after bridge authentication."))
    response.set_cookie("tyrwar_session", session_id, httponly=True, secure=True, samesite="strict")
    return response


@app.get("/api/status")
async def status(request: Request) -> JSONResponse:
    session = SESSIONS.get(request.cookies.get("tyrwar_session", ""))
    if session is None:
        return JSONResponse({"connected": "Offline", "message": "Connect the MT5 bridge."})
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{session.bridge_url}/v1/status",
                headers={
                    "X-Tyrwar-Bridge-Key": session.bridge_key,
                    "Authorization": f"Bearer {session.bridge_session}",
                },
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        data = {"connected": "Degraded", "message": str(exc)}
    session.last_status = data
    return JSONResponse(data)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
