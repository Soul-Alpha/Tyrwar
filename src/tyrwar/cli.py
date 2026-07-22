"""Command-line entry point for the Tyrwar XAUUSD M5 bot."""

from __future__ import annotations

import argparse
import json

from tyrwar.trading.bot import XAUUSDM5Bot
from tyrwar.trading.mt5_adapter import MT5Adapter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate XAUUSD M5 with RSI and SMC rules")
    parser.add_argument("--symbol", default="XAUUSD", help="Broker symbol, for example XAUUSDm")
    parser.add_argument("--volume", type=float, default=0.01)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Request live execution; also requires TYRWAR_LIVE_TRADING acknowledgement",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    adapter = MT5Adapter(symbol=args.symbol, live_enabled=args.execute)
    try:
        adapter.connect()
        result = XAUUSDM5Bot(
            adapter,
            execute=args.execute,
            volume=args.volume,
        ).run_once()
        print(
            json.dumps(
                {
                    "side": result.signal.side.value,
                    "reason": result.signal.reason,
                    "rsi": result.signal.rsi,
                    "entry": result.signal.entry,
                    "stop_loss": result.signal.stop_loss,
                    "take_profit": result.signal.take_profit,
                    "signal_time": (
                        result.signal.signal_time.isoformat()
                        if result.signal.signal_time is not None
                        else None
                    ),
                    "executed": result.order_result is not None,
                },
                indent=2,
            )
        )
        return 0
    finally:
        adapter.close()


if __name__ == "__main__":
    raise SystemExit(main())
