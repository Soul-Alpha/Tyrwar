"""Windows MT5 bridge process entry point."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "tyrwar.bridge.app:app",
        host=os.getenv("TYRWAR_BRIDGE_HOST", "127.0.0.1"),
        port=int(os.getenv("TYRWAR_BRIDGE_PORT", "8090")),
    )


if __name__ == "__main__":
    main()
