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

## Replit monitoring dashboard

The dashboard is designed for Replit, while the MT5 connection remains on a Windows machine or Windows VPS running the MetaTrader 5 terminal.

Architecture:

```text
Browser -> Replit dashboard -> HTTPS MT5 bridge -> local MetaTrader 5 terminal
```

This separation is required because the official MetaTrader5 Python integration communicates directly with the installed MT5 terminal and its published wheels are Windows builds.

### Replit

1. Import this GitHub repository into Replit.
2. Select the `feature/xauusd-m5-rsi-smc` branch until the pull request is merged.
3. Replit uses the included `.replit` configuration to install the package and start the dashboard on `0.0.0.0:$PORT`.
4. Publish it as an Autoscale deployment for interactive monitoring, or Reserved VM when predictable always-on dashboard availability is required.

The dashboard contains connection fields for:

- secure bridge URL;
- bridge API key;
- MT5 account number;
- MT5 password;
- broker server;
- broker symbol.

The MT5 password is forwarded to the bridge for authentication and is not stored in the dashboard session or written to disk. The bridge returns an opaque monitoring session token.

### Windows MT5 bridge

On the Windows host running MetaTrader 5:

```powershell
python -m pip install -e ".[mt5]"
$env:TYRWAR_BRIDGE_API_KEY="replace-with-a-long-random-secret"
tyrwar-bridge
```

The bridge binds to `127.0.0.1:8090` by default. For a remote Replit deployment, expose it only through an authenticated HTTPS reverse proxy or secure tunnel. Do not expose the raw bridge port directly to the public internet.

The current bridge is monitoring-only. It exposes account status, XAUUSD open-position count, completed-candle time, RSI, and the latest strategy signal. It does not expose a remote order-placement endpoint.

## Validation

```bash
ruff check .
ruff format --check .
pytest
```

## Structure

```text
src/tyrwar/trading/               Strategy, models, MT5 adapter, and bot cycle
src/tyrwar/dashboard/app.py       Replit monitoring dashboard
src/tyrwar/dashboard/run.py       Replit/Uvicorn process runner
src/tyrwar/bridge/app.py          Authenticated Windows MT5 monitoring bridge
src/tyrwar/bridge/run.py          Windows bridge process runner
src/tyrwar/cli.py                 Trading command-line entry point
tests/                            Automated tests
.github/workflows/                Continuous integration
```

## Required before production use

Before enabling unattended live execution, add historical backtesting, spread and slippage filters, position sizing based on account risk, daily drawdown controls, duplicate-signal protection, open-position reconciliation, session filters, persistent audit logs, and broker-specific filling-mode handling.

The monitoring connection state is currently held in memory. Replit deployments may restart or scale down, so users may need to reconnect. Persistent operational history should be stored in a database rather than the deployment filesystem.
