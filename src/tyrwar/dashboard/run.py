"""Dashboard process entry point."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "tyrwar.dashboard.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
