"""Authenticated Windows bridge between Replit and the local MT5 terminal."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from tyrwar.trading.mt5_adapter import MT5Adapter, MT5UnavailableError
from tyrwar.trading.strategy import evaluate_signal

app = FastAPI(title="Tyrwar MT5 Bridge", docs_url=None, redoc_url=None)


class ConnectRequest(BaseModel):
    login: int = Field(gt=0)
    password: str = Field(min_length=1)
    server: str = Field(min_length=1, max_length=128)
    symbol: str = Field(default="XAUUSD", min_length=1, max_length=32)


@dataclass
class BridgeSession:
    adapter: MT5Adapter


SESSIONS: dict[str, BridgeSession] = {}


def require_bridge_key(x_tyrwar_bridge_key: Annotated[str | None, Header()] = None) -> None:
    expected = os.getenv("TYRWAR_BRIDGE_API_KEY", "")
    if not expected:
        raise HTTPException(503, "TYRWAR_BRIDGE_API_KEY is not configured")
    if x_tyrwar_bridge_key is None or not secrets.compare_digest(x_tyrwar_bridge_key, expected):
        raise HTTPException(401, "Invalid bridge key")


def require_session(
    authorization: Annotated[str | None, Header()] = None,
    _: None = Depends(require_bridge_key),
) -> BridgeSession:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bridge session")
    session = SESSIONS.get(authorization.removeprefix("Bearer "))
    if session is None:
        raise HTTPException(401, "Bridge session expired")
    return session


@app.post("/v1/connect", dependencies=[Depends(require_bridge_key)])
def connect(request: ConnectRequest) -> dict[str, str]:
    """Authenticate with MT5 and return an opaque monitoring session token."""

    adapter = MT5Adapter(symbol=request.symbol, live_enabled=False)
    try:
        adapter.connect(login=request.login, password=request.password, server=request.server)
        adapter.account_status()
    except MT5UnavailableError as exc:
        adapter.close()
        raise HTTPException(502, str(exc)) from exc
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = BridgeSession(adapter=adapter)
    return {"session_token": token, "status": "connected"}


@app.get("/v1/status")
def status(session: BridgeSession = Depends(require_session)) -> dict[str, object]:
    adapter = session.adapter
    try:
        account = adapter.account_status()
        candles = adapter.fetch_closed_m5_candles()
        signal = evaluate_signal(candles)
    except MT5UnavailableError as exc:
        raise HTTPException(502, str(exc)) from exc
    latest = candles[-1]
    account.update(
        {
            "signal": signal.side.value,
            "signal_reason": signal.reason,
            "rsi": round(signal.rsi, 2) if signal.rsi is not None else None,
            "entry": signal.entry,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "candle": latest.time.isoformat(),
            "daily_pnl": "Not available yet",
        }
    )
    return account


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
