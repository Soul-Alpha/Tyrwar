"""Domain models for the XAUUSD M5 trading bot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Side(str, Enum):
    """Trade direction."""

    BUY = "buy"
    SELL = "sell"
    FLAT = "flat"


@dataclass(frozen=True)
class Candle:
    """A completed OHLCV candle."""

    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        if self.low > self.high:
            raise ValueError("candle low cannot exceed high")
        if not self.low <= self.open <= self.high:
            raise ValueError("candle open must be inside the candle range")
        if not self.low <= self.close <= self.high:
            raise ValueError("candle close must be inside the candle range")


@dataclass(frozen=True)
class StrategyConfig:
    """Configuration for the RSI and SMC-inspired strategy."""

    symbol: str = "XAUUSD"
    timeframe: str = "M5"
    rsi_period: int = 14
    rsi_oversold: float = 35.0
    rsi_overbought: float = 65.0
    sweep_lookback: int = 8
    structure_lookback: int = 5
    stop_buffer: float = 0.30
    reward_to_risk: float = 2.0
    min_candles: int = 60

    def __post_init__(self) -> None:
        if self.timeframe != "M5":
            raise ValueError("this strategy is restricted to the M5 timeframe")
        if self.rsi_period < 2:
            raise ValueError("rsi_period must be at least 2")
        if not 0 < self.rsi_oversold < self.rsi_overbought < 100:
            raise ValueError("RSI thresholds must satisfy 0 < oversold < overbought < 100")
        if self.sweep_lookback < 2 or self.structure_lookback < 2:
            raise ValueError("lookback values must be at least 2")
        if self.stop_buffer <= 0 or self.reward_to_risk <= 0:
            raise ValueError("risk parameters must be positive")


@dataclass(frozen=True)
class Signal:
    """A fully evaluated strategy decision."""

    side: Side
    reason: str
    rsi: float | None = None
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    signal_time: datetime | None = None

    @property
    def actionable(self) -> bool:
        return self.side in {Side.BUY, Side.SELL}
