"""Command-line entry point for the Tyrwar XAUUSD M5 bot."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from typing import Any

from tyrwar.telemetry import TelemetryPublisher
from tyrwar.trading.bot import XAUUSDM5Bot
from tyrwar.trading.mt5_adapter import MT5Adapter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate XAUUSD M5 with RSI and SMC rules")
    parser.add_argument("--symbol", default="XAUUSD", help="Broker symbol, for example XAUUSDm")
    parser.add_argument("--volume", type=float, default=0.01)
    parser.add_argument("--continuous", action="store_true", help="Run repeated evaluation cycles")
    parser.add_argument("--poll-seconds", type=float, default=15.0)
    parser.add_argument("--publish-telemetry", action="store_true")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Request live execution; also requires TYRWAR_LIVE_TRADING acknowledgement",
    )
    return parser


def _connect(adapter: MT5Adapter) -> None:
    login_value = os.getenv("TYRWAR_MT5_LOGIN")
    adapter.connect(
        login=int(login_value) if login_value else None,
        password=os.getenv("TYRWAR_MT5_PASSWORD"),
        server=os.getenv("TYRWAR_MT5_SERVER"),
        terminal_path=os.getenv("TYRWAR_MT5_TERMINAL_PATH"),
    )


def _snapshot(adapter: MT5Adapter, result: Any, *, execute: bool) -> dict[str, Any]:
    account = adapter.account_status()
    return {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_status": "running",
        "mode": "LIVE" if execute else "PAPER/EVALUATION",
        "balance": account["balance"],
        "equity": account["equity"],
        "margin_free": account["margin_free"],
        "open_positions": account["positions"],
        "symbol": account["symbol"],
        "side": result.signal.side.value,
        "reason": result.signal.reason,
        "rsi": result.signal.rsi,
        "signal_time": (
            result.signal.signal_time.isoformat()
            if result.signal.signal_time is not None
            else None
        ),
        "executed": result.order_result is not None,
    }


def main() -> int:
    args = build_parser().parse_args()
    if args.poll_seconds <= 0:
        raise ValueError("poll-seconds must be positive")
    adapter = MT5Adapter(symbol=args.symbol, live_enabled=args.execute)
    publisher = TelemetryPublisher()
    try:
        _connect(adapter)
        bot = XAUUSDM5Bot(adapter, execute=args.execute, volume=args.volume)
        while True:
            result = bot.run_once()
            snapshot = _snapshot(adapter, result, execute=args.execute)
            print(json.dumps(snapshot, indent=2), flush=True)
            if args.publish_telemetry:
                publisher.publish(snapshot)
            if not args.continuous:
                return 0
            time.sleep(args.poll_seconds)
    finally:
        adapter.close()


if __name__ == "__main__":
    raise SystemExit(main())
