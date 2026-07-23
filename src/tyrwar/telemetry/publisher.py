"""Authenticated outbound HTTPS telemetry publisher."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PublishResult:
    """Observable result of one telemetry publication attempt."""

    sent: bool
    message: str


class TelemetryPublisher:
    """Publish read-only runtime snapshots to a remote dashboard endpoint."""

    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        self.url = (url or os.getenv("TYRWAR_TELEMETRY_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("TYRWAR_TELEMETRY_KEY", "")

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.api_key)

    @property
    def configuration_status(self) -> str:
        if self.enabled:
            return f"configured for {self.url}"
        missing = []
        if not self.url:
            missing.append("TYRWAR_TELEMETRY_URL")
        if not self.api_key:
            missing.append("TYRWAR_TELEMETRY_KEY")
        return f"disabled; missing {', '.join(missing)}"

    def publish(self, snapshot: dict[str, Any]) -> PublishResult:
        """Publish a snapshot without allowing dashboard failures to stop trading."""
        if not self.enabled:
            return PublishResult(False, self.configuration_status)
        if not self.url.startswith("https://") and not self.url.startswith("http://127.0.0.1"):
            message = "remote telemetry URL must use HTTPS"
            LOGGER.error(message)
            return PublishResult(False, message)
        try:
            response = httpx.post(
                f"{self.url}/api/telemetry",
                json=snapshot,
                headers={"X-Tyrwar-Telemetry-Key": self.api_key},
                timeout=10.0,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            message = f"telemetry publish failed: {exc}"
            LOGGER.warning(message)
            return PublishResult(False, message)
        return PublishResult(True, "telemetry accepted")
