"""Push providers (B16).

A port with three adapters, chosen by `PUSH_PROVIDER`, the same shape as the routing and
OTP providers so switching one is configuration rather than code.

* `log` - writes the message to the structured log. The default, and what the tests run
  against: a notification test that needs a real device is a test nobody runs.
* `ntfy` - an HTTP POST per token to a self-hosted ntfy server. No account, no SDK, no
  credentials, which is why it can be implemented and exercised now.
* `fcm` - **not implemented**. It needs a Google service account, and the choice between
  FCM and ntfy is still open (OQ-20). Selecting it fails loudly at startup rather than
  silently dropping every notification, which is the failure mode that matters: nobody
  notices missing pushes until a rider is standing outside at 7am.

Sending is best-effort. A push that fails must never roll back the trip it was announcing.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import httpx

from app.core.logging import get_logger
from app.core.settings import PushProvider, Settings

logger = get_logger(__name__)

#: A phone that has not been seen in this long is probably a reinstalled or lost device.
#: Pushing to it wastes a request and, on some providers, earns a rate penalty.
STALE_DEVICE_DAYS = 90

REQUEST_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True, slots=True)
class PushMessage:
    """One message for one device."""

    token: str
    title: str
    body: str
    data: dict[str, Any]
    high_priority: bool = False
    notification_id: uuid.UUID | None = None


@runtime_checkable
class PushSender(Protocol):
    """Where a push goes. Swapped for a recorder in tests."""

    name: str

    async def send(self, message: PushMessage) -> bool:
        """True if the provider accepted it. Never raises."""
        ...


class LogPushSender:
    """Writes the push to the log. The default, and what `make test` runs against."""

    name = "log"

    async def send(self, message: PushMessage) -> bool:
        logger.info(
            "push_sent",
            provider=self.name,
            # The token identifies a device, so only its shape is logged.
            token_tail=message.token[-6:] if len(message.token) > 6 else "short",
            title=message.title,
            body=message.body,
            high_priority=message.high_priority,
        )
        return True


class NtfyPushSender:
    """POSTs to a self-hosted ntfy topic (one topic per device token)."""

    name = "ntfy"

    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    async def send(self, message: PushMessage) -> bool:
        headers = {
            "Title": message.title,
            "Priority": "high" if message.high_priority else "default",
        }
        try:
            client = self._client or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
            response = await client.post(
                f"{self._base_url}/{message.token}", content=message.body, headers=headers
            )
            if self._client is None:
                await client.aclose()
        except Exception as exc:  # noqa: BLE001 - a failed push must not fail the trip
            logger.warning("push_failed", provider=self.name, error=type(exc).__name__)
            return False

        if response.status_code >= 400:
            logger.warning("push_rejected", provider=self.name, status=response.status_code)
            return False
        return True


class RecordingPushSender:
    """Keeps messages in a list. For tests that assert who was told what."""

    name = "recording"

    def __init__(self) -> None:
        self.messages: list[PushMessage] = []

    async def send(self, message: PushMessage) -> bool:
        self.messages.append(message)
        return True

    def titles(self) -> list[str]:
        return [message.title for message in self.messages]

    def tokens(self) -> list[str]:
        return [message.token for message in self.messages]


def build_push_sender(settings: Settings) -> PushSender:
    """One place decides the provider, so switching it is configuration (ADR-0002 style)."""
    provider = PushProvider(settings.push_provider)
    if provider is PushProvider.log:
        return LogPushSender()
    if provider is PushProvider.ntfy:
        if not settings.ntfy_url:
            raise ValueError("PUSH_PROVIDER=ntfy needs NTFY_URL")
        return NtfyPushSender(settings.ntfy_url)
    raise NotImplementedError(
        "FCM is not implemented: it needs a Google service account, and the choice "
        "between FCM and a self-hosted ntfy is still open (OQ-20). Use PUSH_PROVIDER=log "
        "in dev or PUSH_PROVIDER=ntfy with NTFY_URL set."
    )
