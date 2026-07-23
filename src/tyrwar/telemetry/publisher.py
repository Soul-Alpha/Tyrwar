"""Authenticated outbound HTTPS telemetry publisher."""

from __future__ import annotations

import os
from typing import Any

import httpx


class TelemetryPublisher:
    """Publish read-only runtime snapshots to a remote dashboard endpoint."""

    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        self.url = (url or os.getenv("TYRWAR_TELEMETRY_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("TYRWAR_TELEMETRY_KEY", "")

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.api_key)

    def publish(self, snapshot: dict[str, Any]) -> None:
        if not self.enabled:
            return
        if not self.url.startswith("https://") and not self.url.startswith("http://127.0.0.1"):
            raise ValueError("remote telemetry URL must use HTTPS")
        response = httpx.post(
            f"{self.url}/api/telemetry",
            json=snapshot,
            headers={"X-Tyrwar-Telemetry-Key": self.api_key},
            timeout=10.0,
            follow_redirects=False,
        )
        response.raise_for_status()
