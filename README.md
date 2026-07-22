# Tyrwar

Tyrwar is an XAUUSD five-minute trading bot built around deterministic RSI confirmation and SMC-inspired liquidity-sweep and market-structure rules.

## Safety status

The bot is paper/evaluation-only by default. Live order submission requires both:

1. `--execute` on the command line; and
2. `TYRWAR_LIVE_TRADING=I_UNDERSTAND_THE_RISK` in the environment.

Start with a demo account. The strategy has not yet been validated for profitability and should not be treated as financial advice.

## Strategy

The bot evaluates completed M5 candles only. It deliberately excludes the currently forming candle.

A buy requires:

- a downside liquidity sweep on the preceding completed candle;
- a bullish break of recent structure on the latest completed candle;
- RSI at or below the configured oversold threshold;
- a valid stop below the swept low.

A sell applies the inverse conditions. Take profit defaults to 2R. The default order volume is `0.01`, but fixed-volume execution is an initial safety baseline rather than a complete account-risk model.

## Installation

Requirements:

- Python 3.11 or newer;
- Windows with a working MetaTrader 5 terminal for MT5 connectivity.

Install development tools:

```bash
python -m pip install -e ".[dev]"
```

Install the optional MT5 integration on Windows:

```bash
python -m pip install -e ".[mt5]"
```

## Usage

Evaluate the latest completed candles without placing an order:

```bash
tyrwar-bot --symbol XAUUSD
```

Some brokers use a suffix, for example:

```bash
tyrwar-bot --symbol XAUUSDm
```

Live execution is deliberately guarded:

```bash
set TYRWAR_LIVE_TRADING=I_UNDERSTAND_THE_RISK
tyrwar-bot --symbol XAUUSD --volume 0.01 --execute
```

The current command performs one evaluation cycle. Schedule it after each completed M5 candle only after demo validation and duplicate-order protection are added.

## Validation

```bash
ruff check .
ruff format --check .
pytest
```

## Structure

```text
src/tyrwar/trading/models.py       Domain models and configuration
src/tyrwar/trading/strategy.py     RSI and deterministic SMC signal logic
src/tyrwar/trading/mt5_adapter.py  MT5 market-data and guarded execution boundary
src/tyrwar/trading/bot.py          One-cycle orchestration
src/tyrwar/cli.py                  Command-line entry point
tests/                              Automated tests
.github/workflows/                  Continuous integration
```

## Required before production use

Before enabling unattended live execution, add historical backtesting, spread and slippage filters, position sizing based on account risk, daily drawdown controls, duplicate-signal protection, open-position reconciliation, session filters, persistent audit logs, and broker-specific filling-mode handling.
