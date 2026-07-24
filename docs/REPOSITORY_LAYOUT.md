# Tyrwar Repository Layout

## Canonical root

The Git repository root is the directory containing `pyproject.toml`, `src/`, `tests/`, `.replit`, and `README.md`.

```text
Tyrwar/
├── .github/workflows/        Continuous integration
├── docs/                     Architecture and operating documentation
├── notebooks/                Thin operator and analysis interfaces only
├── src/tyrwar/               Canonical application package
│   ├── bridge/               Authenticated MT5 monitoring bridge
│   ├── dashboard/            Replit monitoring service
│   ├── telemetry/            Outbound telemetry publisher
│   ├── trading/              Strategy, models, adapter, and bot cycle
│   └── cli.py                Shared CLI/notebook runtime entry point
├── tests/                    Automated policy and behavioural tests
├── .replit                   Replit build and run configuration
├── pyproject.toml            Package and tool configuration
└── README.md                 Primary project documentation
```

## Structural rules

1. Production logic belongs only under `src/tyrwar/`.
2. Notebooks must import the canonical package and must not reimplement strategy, execution, telemetry, or risk logic.
3. Notebook outputs and execution counts must not be committed.
4. Secrets, account credentials, runtime databases, logs, virtual environments, nested clones, and Replit workspace wrappers must not be committed.
5. `src/tyrwar/` is the Python package and is not a duplicate of the repository root.
6. A nested `Tyrwar/` repository folder or `cuddly-train/` workspace folder is non-canonical and must remain outside version control.

## Replit import rule

Import the GitHub repository directly as the Replit project. Do not clone Tyrwar into an existing Replit workspace. The Replit file browser should open at the same directory that contains `pyproject.toml` and `.replit`.
