# Replit deployment checklist

1. Import `Soul-Alpha/Tyrwar` into Replit.
2. Install with `python -m pip install -e .`.
3. Run `python -m tyrwar.dashboard.run`.
4. Publish as Autoscale for an interactive dashboard, or Reserved VM for predictable availability.
5. Confirm `/health` returns `{\"status\": \"ok\"}`.
6. Run `tyrwar-bridge` on a Windows MT5 host with `TYRWAR_BRIDGE_API_KEY` configured.
7. Place the bridge behind HTTPS and enter its URL, API key, MT5 login, password, server, and symbol in the dashboard.

Never commit broker credentials or the bridge API key to GitHub. The Replit deployment is the monitoring tier; MetaTrader 5 remains on the Windows execution host.
