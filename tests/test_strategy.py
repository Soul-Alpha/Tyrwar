from datetime import datetime, timezone

import pytest

from tyrwar.trading.models import Candle, Side, StrategyConfig
from tyrwar.trading.mt5_adapter import MT5Adapter
from tyrwar.trading.strategy import calculate_rsi, evaluate_signal


def candle(close: float) -> Candle:
    return Candle(
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        open=close,
        high=close + 0.5,
        low=close - 0.5,
        close=close,
    )


def test_rsi_reaches_100_when_prices_only_rise() -> None:
    assert calculate_rsi([float(value) for value in range(1, 17)], period=14) == 100.0


def test_strategy_refuses_incomplete_history() -> None:
    signal = evaluate_signal([candle(3000.0)] * 10)
    assert signal.side is Side.FLAT
    assert "insufficient candles" in signal.reason


def test_strategy_is_restricted_to_m5() -> None:
    with pytest.raises(ValueError, match="M5"):
        StrategyConfig(timeframe="H1")


def test_live_order_requires_explicit_acknowledgement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TYRWAR_LIVE_TRADING", raising=False)
    adapter = MT5Adapter(live_enabled=True)
    with pytest.raises(PermissionError, match="live trading is disabled"):
        adapter.place_market_order(
            evaluate_signal([candle(3000.0)] * 60),
        )
