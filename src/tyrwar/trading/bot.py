"""Orchestration for one evaluation cycle of the XAUUSD M5 bot."""

from __future__ import annotations

from dataclasses import dataclass

from tyrwar.trading.models import Signal, StrategyConfig
from tyrwar.trading.mt5_adapter import MT5Adapter
from tyrwar.trading.strategy import evaluate_signal


@dataclass(frozen=True)
class BotResult:
    """Outcome of one completed bot cycle."""

    signal: Signal
    order_result: object | None = None


class XAUUSDM5Bot:
    """Evaluate completed XAUUSD M5 candles and optionally execute a guarded order."""

    def __init__(
        self,
        adapter: MT5Adapter,
        config: StrategyConfig | None = None,
        *,
        execute: bool = False,
        volume: float = 0.01,
    ) -> None:
        if volume <= 0:
            raise ValueError("volume must be positive")
        self.adapter = adapter
        self.config = config or StrategyConfig(symbol=adapter.symbol)
        self.execute = execute
        self.volume = volume

    def run_once(self) -> BotResult:
        candles = self.adapter.fetch_closed_m5_candles()
        signal = evaluate_signal(candles, self.config)
        if not self.execute or not signal.actionable:
            return BotResult(signal=signal)
        return BotResult(
            signal=signal,
            order_result=self.adapter.place_market_order(signal, volume=self.volume),
        )
