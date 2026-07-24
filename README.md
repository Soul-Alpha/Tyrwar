# Tyrwar

Tyrwar is an XAUUSD five-minute trading system built around deterministic RSI confirmation and SMC-inspired liquidity-sweep and market-structure rules.

## Safety status

Tyrwar is evaluation-only by default. Live order submission requires both `--execute` and `TYRWAR_LIVE_TRADING=I_UNDERSTAND_THE_RISK`. Use a demo account until the complete validation and capital-governance programme is satisfied.

## Canonical architecture

```text
Windows MT5 runtime -> authenticated telemetry -> Replit dashboard -> browser
```

Production logic has one authoritative location: `src/tyrwar/`.

```text
.github/workflows/        Continuous integration
docs/                     Architecture and operating documentation
notebooks/                Thin operator interfaces; no trading logic
src/tyrwar/bridge/        Authenticated MT5 monitoring bridge
src/tyrwar/dashboard/     Replit dashboard and persistent latest telemetry
src/tyrwar/telemetry/     Resilient telemetry publisher
src/tyrwar/trading/       Strategy, models, MT5 adapter, and bot cycle
src/tyrwar/cli.py         Shared CLI and notebook runtime
tests/                    Behavioural and repository-policy tests
```

See `docs/REPOSITORY_LAYOUT.md` for the structural contract. A Replit wrapper such as `cuddly-train/` or a nested clone such as `Tyrwar/Tyrwar/` is not part of the canonical repository.

## Installation

Requirements:

- Python 3.11 or newer;
- Windows and a working MetaTrader 5 terminal for MT5 connectivity.

```bash
python -m pip install -e ".[dev,mt5]"
```

## Evaluation usage

```bash
tyrwar-bot --symbol XAUUSDm
```

Telemetry starts automatically when both variables are present:

```text
TYRWAR_TELEMETRY_URL=https://your-replit-deployment.replit.app
TYRWAR_TELEMETRY_KEY=<shared-secret>
```

Telemetry failure is non-fatal and is reported in each runtime snapshot.

## Edith notebook

`notebooks/edith.ipynb` is a governed operator interface. It imports `run_tyrwar()` from the canonical package and contains no independent strategy, order-management, credentials, or telemetry implementation.

Run the one-cycle evaluation cell before starting continuous evaluation. Notebook outputs and execution counts must not be committed.

## Replit

Import this GitHub repository directly into Replit. The Replit workspace root must be the directory containing `.replit`, `pyproject.toml`, `src/`, and `tests/`. Do not clone Tyrwar inside an existing Replit project.

The included `.replit` file installs the package and starts the dashboard. The latest accepted telemetry snapshot is persisted so a process restart does not erase the last known state.

## Validation

```bash
ruff check .
ruff format --check .
pytest
```

Repository tests enforce the notebook policy and prevent executable duplication from being reintroduced.

## Production readiness

Before unattended live execution, Tyrwar still requires institutional backtesting, spread and slippage modelling, account-risk position sizing, daily drawdown controls, duplicate-signal protection, open-position reconciliation, session controls, durable audit history, and broker-specific execution validation.
