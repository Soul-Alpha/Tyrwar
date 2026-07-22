"""Deterministic RSI plus SMC-inspired signal generation."""

from __future__ import annotations

from collections.abc import Sequence

from tyrwar.trading.models import Candle, Side, Signal, StrategyConfig


def calculate_rsi(closes: Sequence[float], period: int = 14) -> float:
    """Return Wilder RSI for the latest close."""

    if len(closes) < period + 1:
        raise ValueError("not enough closes to calculate RSI")

    deltas = [current - previous for previous, current in zip(closes, closes[1:], strict=False)]
    seed = deltas[:period]
    average_gain = sum(max(delta, 0.0) for delta in seed) / period
    average_loss = sum(max(-delta, 0.0) for delta in seed) / period

    for delta in deltas[period:]:
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        average_gain = ((average_gain * (period - 1)) + gain) / period
        average_loss = ((average_loss * (period - 1)) + loss) / period

    if average_loss == 0:
        return 100.0
    relative_strength = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))


def _bullish_sweep(candles: Sequence[Candle], lookback: int) -> bool:
    current = candles[-1]
    prior = candles[-(lookback + 1) : -1]
    prior_low = min(candle.low for candle in prior)
    return current.low < prior_low and current.close > prior_low and current.close > current.open


def _bearish_sweep(candles: Sequence[Candle], lookback: int) -> bool:
    current = candles[-1]
    prior = candles[-(lookback + 1) : -1]
    prior_high = max(candle.high for candle in prior)
    return current.high > prior_high and current.close < prior_high and current.close < current.open


def _bullish_structure_break(candles: Sequence[Candle], lookback: int) -> bool:
    current = candles[-1]
    prior = candles[-(lookback + 1) : -1]
    return current.close > max(candle.high for candle in prior)


def _bearish_structure_break(candles: Sequence[Candle], lookback: int) -> bool:
    current = candles[-1]
    prior = candles[-(lookback + 1) : -1]
    return current.close < min(candle.low for candle in prior)


def evaluate_signal(candles: Sequence[Candle], config: StrategyConfig | None = None) -> Signal:
    """Evaluate the latest completed candle.

    The SMC component is deliberately deterministic: a liquidity sweep must occur on one
    of the two latest completed candles and the latest candle must confirm direction with
    a break of recent structure. RSI acts as momentum confirmation rather than a signal by itself.
    """

    config = config or StrategyConfig()
    required = max(
        config.min_candles,
        config.rsi_period + 1,
        config.sweep_lookback + 2,
        config.structure_lookback + 1,
    )
    if len(candles) < required:
        return Signal(Side.FLAT, f"insufficient candles: need {required}, received {len(candles)}")

    rsi = calculate_rsi([candle.close for candle in candles], config.rsi_period)
    latest = candles[-1]
    sweep_window = candles[:-1]

    bullish_sweep = _bullish_sweep(sweep_window, config.sweep_lookback)
    bearish_sweep = _bearish_sweep(sweep_window, config.sweep_lookback)
    bullish_break = _bullish_structure_break(candles, config.structure_lookback)
    bearish_break = _bearish_structure_break(candles, config.structure_lookback)

    if bullish_sweep and bullish_break and rsi <= config.rsi_oversold:
        sweep_low = sweep_window[-1].low
        stop_loss = sweep_low - config.stop_buffer
        risk = latest.close - stop_loss
        if risk <= 0:
            return Signal(Side.FLAT, "invalid bullish risk distance", rsi=rsi)
        return Signal(
            Side.BUY,
            "bullish liquidity sweep + bullish structure break + RSI confirmation",
            rsi=rsi,
            entry=latest.close,
            stop_loss=stop_loss,
            take_profit=latest.close + (risk * config.reward_to_risk),
            signal_time=latest.time,
        )

    if bearish_sweep and bearish_break and rsi >= config.rsi_overbought:
        sweep_high = sweep_window[-1].high
        stop_loss = sweep_high + config.stop_buffer
        risk = stop_loss - latest.close
        if risk <= 0:
            return Signal(Side.FLAT, "invalid bearish risk distance", rsi=rsi)
        return Signal(
            Side.SELL,
            "bearish liquidity sweep + bearish structure break + RSI confirmation",
            rsi=rsi,
            entry=latest.close,
            stop_loss=stop_loss,
            take_profit=latest.close - (risk * config.reward_to_risk),
            signal_time=latest.time,
        )

    return Signal(Side.FLAT, "strategy conditions not aligned", rsi=rsi)
