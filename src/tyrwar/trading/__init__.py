"""XAUUSD M5 trading components."""

from tyrwar.trading.bot import BotResult, XAUUSDM5Bot
from tyrwar.trading.models import Candle, Side, Signal, StrategyConfig
from tyrwar.trading.strategy import calculate_rsi, evaluate_signal

__all__ = [
    "BotResult",
    "Candle",
    "Side",
    "Signal",
    "StrategyConfig",
    "XAUUSDM5Bot",
    "calculate_rsi",
    "evaluate_signal",
]
