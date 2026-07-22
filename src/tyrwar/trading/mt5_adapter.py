"""MetaTrader 5 adapter with live trading disabled by default."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from tyrwar.trading.models import Candle, Side, Signal


class MT5UnavailableError(RuntimeError):
    """Raised when MetaTrader 5 cannot be imported or connected."""


class MT5Adapter:
    """Small boundary around the optional MetaTrader5 package."""

    def __init__(self, symbol: str = "XAUUSD", *, live_enabled: bool = False) -> None:
        self.symbol = symbol
        self.live_enabled = live_enabled
        self._mt5: Any | None = None

    def connect(self) -> None:
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise MT5UnavailableError(
                "MetaTrader5 is not installed; install the mt5 extra on Windows"
            ) from exc

        if not mt5.initialize():
            raise MT5UnavailableError(f"MT5 initialize failed: {mt5.last_error()}")
        if not mt5.symbol_select(self.symbol, True):
            mt5.shutdown()
            raise MT5UnavailableError(f"unable to select symbol {self.symbol}")
        self._mt5 = mt5

    def close(self) -> None:
        if self._mt5 is not None:
            self._mt5.shutdown()
            self._mt5 = None

    def fetch_closed_m5_candles(self, count: int = 250) -> list[Candle]:
        """Fetch completed M5 candles, deliberately excluding the open candle at index zero."""

        mt5 = self._require_connection()
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M5, 1, count)
        if rates is None:
            raise MT5UnavailableError(f"MT5 candle fetch failed: {mt5.last_error()}")
        return [
            Candle(
                time=datetime.fromtimestamp(int(rate["time"]), tz=timezone.utc),
                open=float(rate["open"]),
                high=float(rate["high"]),
                low=float(rate["low"]),
                close=float(rate["close"]),
                volume=float(rate["tick_volume"]),
            )
            for rate in rates
        ]

    def place_market_order(self, signal: Signal, volume: float = 0.01) -> Any:
        """Place a guarded market order after explicit live-mode opt-in."""

        if not self.live_enabled or os.getenv("TYRWAR_LIVE_TRADING") != "I_UNDERSTAND_THE_RISK":
            raise PermissionError(
                "live trading is disabled; enable the adapter and set TYRWAR_LIVE_TRADING"
            )
        if not signal.actionable or signal.entry is None:
            raise ValueError("an actionable signal is required")
        if signal.stop_loss is None or signal.take_profit is None:
            raise ValueError("signal must include stop loss and take profit")
        if volume <= 0:
            raise ValueError("volume must be positive")

        mt5 = self._require_connection()
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            raise MT5UnavailableError(f"MT5 tick fetch failed: {mt5.last_error()}")

        is_buy = signal.side is Side.BUY
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL,
            "price": float(tick.ask if is_buy else tick.bid),
            "sl": signal.stop_loss,
            "tp": signal.take_profit,
            "deviation": 20,
            "magic": 260722,
            "comment": "tyrwar-rsi-smc-m5",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        checked = mt5.order_check(request)
        if checked is None:
            raise MT5UnavailableError(f"MT5 order check failed: {mt5.last_error()}")
        result = mt5.order_send(request)
        if result is None:
            raise MT5UnavailableError(f"MT5 order send failed: {mt5.last_error()}")
        return result

    def _require_connection(self) -> Any:
        if self._mt5 is None:
            raise MT5UnavailableError("MT5 adapter is not connected")
        return self._mt5
