"""`/ws` (`websocket-protocol.md`) - the realtime endpoint (B13).

The socket handler and nothing else: authentication is `app/core/security.py`, the rules
are `channels.py`, the facts are `service.py`, and the fan-out is `hub.py`. What is left
here is the conversation - authenticate, subscribe, relay, close - which is the part worth
reading in one screen.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.logging import get_logger
from app.core.security import InvalidTokenError, decode_access_token
from app.domain.enums import Role
from app.modules.auth.permissions import has_permission
from app.modules.realtime.channels import (
    Channel,
    Refusal,
    Subscriber,
    TripChannel,
    may_subscribe,
    parse,
    permission_for,
)
from app.modules.realtime.hub import Connection
from app.modules.realtime.service import MembershipService

logger = get_logger(__name__)

router = APIRouter()

#: `websocket-protocol.md` section 1.
AUTH_DEADLINE_SECONDS = 10.0
CLOSE_UNAUTHENTICATED = 4401
CLOSE_BAD_FRAME = 4408

#: One subscribe frame may name several channels; a login screen asks for a handful.
MAX_CHANNELS_PER_FRAME = 50


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    subscriber = await _authenticate(websocket)
    if subscriber is None:
        return

    hub = websocket.app.state.hub
    connection = Connection(send=websocket.send_json)
    logger.info("ws_connected", user_id=str(subscriber.user_id), role=subscriber.role)

    try:
        await _converse(websocket, subscriber, hub, connection)
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(connection)
        logger.info("ws_disconnected", user_id=str(subscriber.user_id))


async def _authenticate(websocket: WebSocket) -> Subscriber | None:
    """Header first, then an `auth` frame for browsers. Never the query string.

    A token in a URL ends up in proxy logs, browser history and `Referer` headers, so the
    query-string form other products offer is deliberately not accepted here.
    """
    settings = websocket.app.state.settings
    clock = websocket.app.state.clock

    header = websocket.headers.get("authorization")
    payload: dict[str, Any] | None = None
    if header is None:
        try:
            async with asyncio.timeout(AUTH_DEADLINE_SECONDS):
                payload = await websocket.receive_json()
        except (TimeoutError, WebSocketDisconnect, ValueError):
            await _close(websocket, CLOSE_UNAUTHENTICATED, "authentication timed out")
            return None
        if not isinstance(payload, dict) or payload.get("type") != "auth":
            await _close(websocket, CLOSE_UNAUTHENTICATED, "first frame must be auth")
            return None
        header = f"Bearer {payload.get('token')}"

    if not header.lower().startswith("bearer "):
        await _close(websocket, CLOSE_UNAUTHENTICATED, "expected a bearer token")
        return None

    try:
        claims = decode_access_token(
            header.split(" ", 1)[1], settings.jwt_secret.get_secret_value(), clock
        )
    except InvalidTokenError:
        await _close(websocket, CLOSE_UNAUTHENTICATED, "invalid or expired token")
        return None

    requested_role = (payload or {}).get("active_role") or websocket.headers.get("x-active-role")
    role = str(requested_role) if requested_role else claims.role
    if role != claims.role or role not in set(Role):
        # Same rule as X-Active-Role on REST: you may only act as a role you hold.
        await _close(websocket, CLOSE_UNAUTHENTICATED, "that role is not on this token")
        return None

    return Subscriber(
        user_id=claims.user_id,
        role=role,
        operator_id=claims.operator_id,
        client_id=claims.client_id,
    )


async def _converse(
    websocket: WebSocket, subscriber: Subscriber, hub: Any, connection: Connection
) -> None:
    while True:
        try:
            frame = await websocket.receive_json()
        except ValueError:
            await _close(websocket, CLOSE_BAD_FRAME, "frames must be JSON objects")
            return

        if not isinstance(frame, dict):
            await _close(websocket, CLOSE_BAD_FRAME, "frames must be JSON objects")
            return

        kind = frame.get("type")
        if kind == "subscribe":
            await _handle_subscribe(websocket, subscriber, hub, connection, frame)
        elif kind == "unsubscribe":
            for name in _names(frame):
                await hub.unsubscribe(connection, name)
            await websocket.send_json({"type": "unsubscribed", "channels": _names(frame)})
        elif kind == "ping":
            await websocket.send_json({"type": "pong"})
        # Unknown types are ignored, so a newer client can talk to an older server.


async def _handle_subscribe(
    websocket: WebSocket,
    subscriber: Subscriber,
    hub: Any,
    connection: Connection,
    frame: dict[str, Any],
) -> None:
    """Answer once for the whole frame, listing what was taken and what was refused.

    One refused channel neither closes the connection nor loses the others: a client
    asking for six channels on login should not lose the five it may read because a trip
    ended a second ago.
    """
    accepted: list[str] = []
    refused: list[dict[str, str]] = []

    for name in _names(frame):
        channel = parse(name)
        if channel is None:
            refused.append({"channel": name, "reason": str(Refusal.unknown_channel)})
            continue

        reason = await _decide(websocket, subscriber, channel)
        if reason is not None:
            refused.append({"channel": name, "reason": str(reason)})
            continue

        await hub.subscribe(connection, name)
        accepted.append(name)

    if refused:
        logger.info(
            "ws_subscription_refused",
            user_id=str(subscriber.user_id),
            refused=[entry["channel"] for entry in refused],
        )
    await websocket.send_json({"type": "subscribed", "channels": accepted, "refused": refused})


async def _decide(websocket: WebSocket, subscriber: Subscriber, channel: Channel) -> Refusal | None:
    permission = permission_for(channel)
    allowed = permission is None or has_permission(Role(subscriber.role), permission)

    membership = None
    if isinstance(channel, TripChannel):
        # Resolved through app.state so a socket test can supply the membership without a
        # database on its event loop; the query itself is tested directly in
        # tests/integration/test_trip_membership.py.
        build = getattr(websocket.app.state, "membership", MembershipService)
        factory = websocket.app.state.session_factory
        async with factory() as session:
            membership = await build(session).trip_membership(channel.trip_id, subscriber)

    return may_subscribe(channel, subscriber, allowed, membership)


def _names(frame: dict[str, Any]) -> list[str]:
    raw = frame.get("channels")
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    return [name for name in raw if isinstance(name, str)][:MAX_CHANNELS_PER_FRAME]


async def _close(websocket: WebSocket, code: int, reason: str) -> None:
    with contextlib.suppress(Exception):
        if websocket.client_state is WebSocketState.CONNECTED:
            await websocket.send_json({"type": "error", "code": code, "message": reason})
        await websocket.close(code=code, reason=reason)
