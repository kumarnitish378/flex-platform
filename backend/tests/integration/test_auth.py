"""Auth end to end (B03).

Acceptance: success, wrong OTP, lockout, rate limit, refresh rotation, revoked token.
Everything runs against real PostgreSQL with a controllable clock, so expiry and the
rate-limit window are tested by advancing time rather than by waiting.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import decode_access_token
from app.domain.enums import Role, UserStatus
from app.main import create_app
from app.modules.auth.models import Device, OtpChallenge, RefreshToken
from app.modules.auth.otp import RecordingOtpSender
from app.modules.auth.permissions import Permission
from app.modules.auth.service import OTP_MAX_ATTEMPTS, OTP_RATE_LIMIT
from tests.builders import make_client, make_operator, make_user, make_user_role, unique_phone

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
# At least 32 bytes: the same rule production enforces (RFC 7518 §3.2).
JWT_SECRET = "test-secret-for-auth-tests-0123456789abcdef"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def otp_sender() -> RecordingOtpSender:
    return RecordingOtpSender()


@pytest_asyncio.fixture
async def app(
    database_ready: bool, db_session: AsyncSession, clock: FakeClock, otp_sender: RecordingOtpSender
) -> AsyncIterator[FastAPI]:
    """An app whose session factory returns the test's transaction-bound session.

    Binding the app to the same session means the request sees rows the test created and
    the whole thing is still rolled back at the end.
    """
    from app.core.settings import Settings

    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
        access_token_ttl_seconds=900,
        refresh_token_ttl_days=30,
    )
    application = create_app(settings=settings, clock=clock)
    application.state.otp_sender = otp_sender

    class _BoundFactory:
        """Hands every request the test's session and never closes it."""

        def __call__(self) -> object:
            return _NoCloseSession(db_session)

    application.state.session_factory = _BoundFactory()
    yield application


class _NoCloseSession:
    """Async-context wrapper so `async with factory() as session` reuses one session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def user_phone(db_session: AsyncSession) -> str:
    """A registered supervisor."""
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()

    phone = unique_phone()
    user = make_user(phone=phone)
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.supervisor, operator_id=operator.id))
    await db_session.flush()
    return phone


async def login(client: AsyncClient, otp_sender: RecordingOtpSender, phone: str) -> tuple[str, str]:
    """Complete the OTP flow; return (access, refresh)."""
    assert (await client.post("/auth/otp/request", json={"phone": phone})).status_code == 202
    code = otp_sender.last_code_for(phone)
    assert code is not None
    response = await client.post("/auth/otp/verify", json={"phone": phone, "code": code})
    assert response.status_code == 200, response.text
    body = response.json()
    return body["access_token"], body["refresh_token"]


# --- happy path --------------------------------------------------------------


async def test_login_issues_a_token_pair(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    access, refresh = await login(client, otp_sender, user_phone)
    assert access and refresh
    assert access != refresh


async def test_expires_in_matches_the_configured_ttl(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    await client.post("/auth/otp/request", json={"phone": user_phone})
    code = otp_sender.last_code_for(user_phone)
    body = (await client.post("/auth/otp/verify", json={"phone": user_phone, "code": code})).json()
    assert body["expires_in"] == 900


async def test_access_token_carries_the_role(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str, clock: FakeClock
) -> None:
    access, _ = await login(client, otp_sender, user_phone)
    claims = decode_access_token(access, JWT_SECRET, clock)
    assert claims.role == "supervisor"
    assert claims.operator_id is not None


async def test_otp_code_is_six_digits(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    await client.post("/auth/otp/request", json={"phone": user_phone})
    code = otp_sender.last_code_for(user_phone)
    assert code is not None and len(code) == 6 and code.isdigit()


async def test_the_code_is_never_stored_in_clear(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str, db_session: AsyncSession
) -> None:
    await client.post("/auth/otp/request", json={"phone": user_phone})
    code = otp_sender.last_code_for(user_phone)
    stored = (
        (await db_session.execute(select(OtpChallenge).where(OtpChallenge.phone == user_phone)))
        .scalars()
        .all()
    )
    assert stored
    assert all(challenge.code_hash != code for challenge in stored)


async def test_refresh_token_is_never_stored_in_clear(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str, db_session: AsyncSession
) -> None:
    _, refresh = await login(client, otp_sender, user_phone)
    rows = (await db_session.execute(select(RefreshToken))).scalars().all()
    assert rows
    assert all(row.token_hash != refresh for row in rows)


# --- failures ----------------------------------------------------------------


async def test_wrong_code_is_rejected(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    await client.post("/auth/otp/request", json={"phone": user_phone})
    response = await client.post("/auth/otp/verify", json={"phone": user_phone, "code": "000000"})
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


async def test_verify_without_a_challenge_is_rejected(client: AsyncClient, user_phone: str) -> None:
    response = await client.post("/auth/otp/verify", json={"phone": user_phone, "code": "123456"})
    assert response.status_code == 401


async def test_unknown_phone_and_wrong_code_are_indistinguishable(
    client: AsyncClient, user_phone: str
) -> None:
    """An attacker must not learn which half of the pair was wrong."""
    unknown = await client.post(
        "/auth/otp/verify", json={"phone": unique_phone(), "code": "123456"}
    )
    known = await client.post("/auth/otp/verify", json={"phone": user_phone, "code": "123456"})
    assert unknown.status_code == known.status_code == 401
    assert unknown.json() == known.json()


async def test_unknown_phone_still_gets_202(client: AsyncClient) -> None:
    """OQ-24: a 404 here would make the endpoint a directory of staff and riders."""
    response = await client.post("/auth/otp/request", json={"phone": unique_phone()})
    assert response.status_code == 202


async def test_no_code_is_sent_to_an_unknown_phone(
    client: AsyncClient, otp_sender: RecordingOtpSender
) -> None:
    stranger = unique_phone()
    await client.post("/auth/otp/request", json={"phone": stranger})
    assert otp_sender.last_code_for(stranger) is None


async def test_expired_code_is_rejected(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str, clock: FakeClock
) -> None:
    await client.post("/auth/otp/request", json={"phone": user_phone})
    code = otp_sender.last_code_for(user_phone)
    clock.advance(timedelta(minutes=6))

    response = await client.post("/auth/otp/verify", json={"phone": user_phone, "code": code})
    assert response.status_code == 401


async def test_suspended_user_cannot_log_in(
    client: AsyncClient, otp_sender: RecordingOtpSender, db_session: AsyncSession
) -> None:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    phone = unique_phone()
    user = make_user(phone=phone)
    user.status = UserStatus.suspended
    db_session.add(user)
    await db_session.flush()

    await client.post("/auth/otp/request", json={"phone": phone})
    assert otp_sender.last_code_for(phone) is None


async def test_malformed_phone_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/auth/otp/request", json={"phone": "9812345678"})
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_malformed_code_is_rejected(client: AsyncClient, user_phone: str) -> None:
    response = await client.post("/auth/otp/verify", json={"phone": user_phone, "code": "12ab56"})
    assert response.status_code == 422


# --- lockout and rate limiting ----------------------------------------------


async def test_lockout_after_repeated_wrong_codes(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    await client.post("/auth/otp/request", json={"phone": user_phone})
    real_code = otp_sender.last_code_for(user_phone)
    assert real_code is not None

    for _ in range(OTP_MAX_ATTEMPTS):
        assert (
            await client.post("/auth/otp/verify", json={"phone": user_phone, "code": "000000"})
        ).status_code == 401

    # Even the correct code no longer works: the challenge is burned.
    response = await client.post("/auth/otp/verify", json={"phone": user_phone, "code": real_code})
    assert response.status_code == 401


async def test_rate_limit_is_three_per_ten_minutes(client: AsyncClient, user_phone: str) -> None:
    for _ in range(OTP_RATE_LIMIT):
        assert (
            await client.post("/auth/otp/request", json={"phone": user_phone})
        ).status_code == 202

    response = await client.post("/auth/otp/request", json={"phone": user_phone})
    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"


async def test_rate_limit_window_rolls_off(
    client: AsyncClient, user_phone: str, clock: FakeClock
) -> None:
    for _ in range(OTP_RATE_LIMIT):
        await client.post("/auth/otp/request", json={"phone": user_phone})
    assert (await client.post("/auth/otp/request", json={"phone": user_phone})).status_code == 429

    clock.advance(timedelta(minutes=11))
    assert (await client.post("/auth/otp/request", json={"phone": user_phone})).status_code == 202


async def test_rate_limit_is_per_phone(client: AsyncClient, user_phone: str) -> None:
    for _ in range(OTP_RATE_LIMIT):
        await client.post("/auth/otp/request", json={"phone": user_phone})
    assert (await client.post("/auth/otp/request", json={"phone": user_phone})).status_code == 429
    # A different number is unaffected.
    assert (
        await client.post("/auth/otp/request", json={"phone": unique_phone()})
    ).status_code == 202


# --- refresh rotation ---------------------------------------------------------


async def test_refresh_returns_a_new_pair(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    _, refresh = await login(client, otp_sender, user_phone)
    response = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    body = response.json()
    assert body["refresh_token"] != refresh, "the refresh token must rotate"


async def test_the_old_refresh_token_stops_working(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    """Rotation is worthless if the previous token still works."""
    _, refresh = await login(client, otp_sender, user_phone)
    await client.post("/auth/refresh", json={"refresh_token": refresh})

    replay = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert replay.status_code == 401


async def test_unknown_refresh_token_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh", json={"refresh_token": "not-a-token"})
    assert response.status_code == 401


async def test_expired_refresh_token_is_rejected(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str, clock: FakeClock
) -> None:
    _, refresh = await login(client, otp_sender, user_phone)
    clock.advance(timedelta(days=31))
    response = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 401


async def test_logout_revokes_the_refresh_token(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    access, refresh = await login(client, otp_sender, user_phone)
    headers = {"Authorization": f"Bearer {access}"}

    assert (
        await client.post("/auth/logout", json={"refresh_token": refresh}, headers=headers)
    ).status_code == 204
    assert (await client.post("/auth/refresh", json={"refresh_token": refresh})).status_code == 401


async def test_logout_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/auth/logout", json={"refresh_token": "x"})
    assert response.status_code == 401


# --- /auth/me -----------------------------------------------------------------


async def test_me_returns_identity_and_permissions(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    access, _ = await login(client, otp_sender, user_phone)
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})

    assert response.status_code == 200
    body = response.json()
    assert body["phone"] == user_phone
    assert len(body["roles"]) == 1

    role = body["roles"][0]
    assert role["role"] == "supervisor"
    assert role["operator_id"] is not None
    assert role["client_id"] is None
    assert str(Permission.assign) in role["permissions"]
    assert str(Permission.vehicle_manage) not in role["permissions"], (
        "a supervisor manages vehicle status only, not the vehicle record"
    )


async def test_me_requires_a_token(client: AsyncClient) -> None:
    assert (await client.get("/auth/me")).status_code == 401


async def test_me_rejects_a_forged_token(client: AsyncClient) -> None:
    from app.core.security import create_access_token

    forged, _ = create_access_token(
        user_id=uuid.uuid4(),
        role="operator_admin",
        secret="the-wrong-secret-but-long-enough-0123456789",
        clock=FakeClock(NOW),
        ttl_seconds=900,
    )
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


async def test_me_rejects_an_expired_token(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str, clock: FakeClock
) -> None:
    access, _ = await login(client, otp_sender, user_phone)
    clock.advance(timedelta(minutes=16))
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert response.status_code == 401


async def test_active_role_header_must_match_the_token(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    """X-Active-Role is a selection, not a grant."""
    access, _ = await login(client, otp_sender, user_phone)
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access}", "X-Active-Role": "operator_admin"},
    )
    assert response.status_code == 403


async def test_matching_active_role_header_is_accepted(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    access, _ = await login(client, otp_sender, user_phone)
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access}", "X-Active-Role": "supervisor"},
    )
    assert response.status_code == 200


async def test_me_lists_every_role_a_user_holds(
    client: AsyncClient,
    otp_sender: RecordingOtpSender,
    db_session: AsyncSession,
) -> None:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    corporate = make_client(operator.id)
    db_session.add(corporate)
    await db_session.flush()

    phone = unique_phone()
    user = make_user(phone=phone)
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.supervisor, operator_id=operator.id))
    db_session.add(
        make_user_role(user.id, Role.employee, operator_id=operator.id, client_id=corporate.id)
    )
    await db_session.flush()

    access, _ = await login(client, otp_sender, phone)
    body = (await client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})).json()
    assert {role["role"] for role in body["roles"]} == {"supervisor", "employee"}


# --- devices ------------------------------------------------------------------


async def test_device_registration(
    client: AsyncClient,
    otp_sender: RecordingOtpSender,
    user_phone: str,
    db_session: AsyncSession,
) -> None:
    access, _ = await login(client, otp_sender, user_phone)
    response = await client.post(
        "/devices",
        json={"platform": "android", "push_token": "token-abc", "app_version": "0.1.0"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert response.status_code == 204

    device = (
        (await db_session.execute(select(Device).where(Device.push_token == "token-abc")))
        .scalars()
        .one()
    )
    assert device.app_version == "0.1.0"
    assert device.last_seen_at is not None


async def test_registering_the_same_token_twice_updates_it(
    client: AsyncClient,
    otp_sender: RecordingOtpSender,
    user_phone: str,
    db_session: AsyncSession,
) -> None:
    """A handset passed to another driver must not keep pushing to the old owner."""
    access, _ = await login(client, otp_sender, user_phone)
    headers = {"Authorization": f"Bearer {access}"}

    await client.post(
        "/devices",
        json={"platform": "android", "push_token": "shared", "app_version": "0.1.0"},
        headers=headers,
    )
    response = await client.post(
        "/devices",
        json={"platform": "android", "push_token": "shared", "app_version": "0.2.0"},
        headers=headers,
    )
    assert response.status_code == 204

    devices = (
        (await db_session.execute(select(Device).where(Device.push_token == "shared")))
        .scalars()
        .all()
    )
    assert len(devices) == 1
    assert devices[0].app_version == "0.2.0"


async def test_device_registration_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/devices",
        json={"platform": "android", "push_token": "x", "app_version": "1"},
    )
    assert response.status_code == 401


async def test_unknown_platform_is_rejected(
    client: AsyncClient, otp_sender: RecordingOtpSender, user_phone: str
) -> None:
    access, _ = await login(client, otp_sender, user_phone)
    response = await client.post(
        "/devices",
        json={"platform": "symbian", "push_token": "x", "app_version": "1"},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert response.status_code == 422
