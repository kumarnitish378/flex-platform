"""Push providers (B16).

The interesting property is that **nothing here raises**: a failed push must never roll
back the trip it was announcing.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.core.settings import PushProvider, Settings
from app.modules.notifications.push import (
    LogPushSender,
    NtfyPushSender,
    PushMessage,
    RecordingPushSender,
    build_push_sender,
)


def message(**extra: Any) -> PushMessage:
    body: dict[str, Any] = {
        "token": "device-token-abcdef",
        "title": "Cab assigned",
        "body": "Cab UP16AB1234 is on the way.",
        "data": {"trip_id": "t1"},
    }
    body.update(extra)
    return PushMessage(**body)


# --- the log provider -------------------------------------------------------------


async def test_the_log_provider_accepts_everything() -> None:
    assert await LogPushSender().send(message()) is True


async def test_the_log_provider_does_not_log_the_whole_token(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A push token identifies a device; only its shape belongs in a log."""
    await LogPushSender().send(message(token="secret-token-value-123456"))

    captured = capsys.readouterr().out
    assert "secret-token-value-123456" not in captured
    assert "123456" in captured


# --- ntfy ---------------------------------------------------------------------------


async def test_ntfy_posts_to_the_topic() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["title"] = request.headers.get("Title")
        seen["priority"] = request.headers.get("Priority")
        seen["body"] = request.content.decode()
        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    sender = NtfyPushSender("https://ntfy.example/", client=client)

    assert await sender.send(message()) is True
    assert seen["url"] == "https://ntfy.example/device-token-abcdef"
    assert seen["title"] == "Cab assigned"
    assert seen["priority"] == "default"
    await client.aclose()


async def test_ntfy_marks_an_emergency_high_priority() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["priority"] = request.headers.get("Priority")
        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    await NtfyPushSender("https://ntfy.example", client=client).send(message(high_priority=True))

    assert seen["priority"] == "high"
    await client.aclose()


async def test_a_rejected_push_is_reported_not_raised() -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(507)))
    assert await NtfyPushSender("https://ntfy.example", client=client).send(message()) is False
    await client.aclose()


async def test_a_dead_server_is_reported_not_raised() -> None:
    """The whole point: the trip is already assigned, and must stay assigned."""

    def explode(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to host")

    client = httpx.AsyncClient(transport=httpx.MockTransport(explode))
    assert await NtfyPushSender("https://ntfy.example", client=client).send(message()) is False
    await client.aclose()


# --- choosing one -------------------------------------------------------------------


def settings(**extra: Any) -> Settings:
    base: dict[str, Any] = {
        "app_env": "dev",
        "database_url": "postgresql+asyncpg://test:test@localhost:5432/test",
        "jwt_secret": "push-tests-secret-0123456789abcdef",
    }
    base.update(extra)
    return Settings(**base)


def test_log_is_the_default() -> None:
    assert build_push_sender(settings()).name == "log"


def test_ntfy_is_selectable() -> None:
    chosen = build_push_sender(
        settings(push_provider=PushProvider.ntfy, ntfy_url="https://ntfy.example")
    )
    assert chosen.name == "ntfy"


def test_ntfy_without_a_url_is_refused_loudly() -> None:
    with pytest.raises(ValueError, match="NTFY_URL"):
        build_push_sender(settings(push_provider=PushProvider.ntfy))


def test_fcm_says_what_is_missing() -> None:
    """Silently dropping every push is the failure nobody notices until 7am."""
    with pytest.raises(NotImplementedError, match="OQ-20"):
        build_push_sender(settings(push_provider=PushProvider.fcm))


async def test_the_recording_sender_keeps_what_it_was_given() -> None:
    sender = RecordingPushSender()
    await sender.send(message())

    assert sender.titles() == ["Cab assigned"]
    assert sender.tokens() == ["device-token-abcdef"]
