"""The OTP-free test login (owner decision 4): existing users only, test environments only."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import decode_access_token
from app.core.settings import AppEnv, Settings
from app.domain.enums import Role, UserStatus
from app.main import create_app
from tests.builders import make_operator, make_user, make_user_role, unique_phone
from tests.integration.test_auth import JWT_SECRET, NOW, _NoCloseSession

pytestmark = pytest.mark.requires_db


class _BoundFactory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def __call__(self) -> object:
        return _NoCloseSession(self._session)


def _settings(env: str, enabled: bool) -> Settings:
    return Settings(
        app_env=env,
        auth_test_login=enabled,
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
    )


async def _client(db_session: AsyncSession, env: str, enabled: bool) -> AsyncIterator[AsyncClient]:
    app: FastAPI = create_app(settings=_settings(env, enabled), clock=FakeClock(NOW))
    app.state.session_factory = _BoundFactory(db_session)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api/v1"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def enabled(database_ready: bool, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async for client in _client(db_session, "dev", True):
        yield client


@pytest_asyncio.fixture
async def disabled(database_ready: bool, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async for client in _client(db_session, "dev", False):
        yield client


async def _user(
    db_session: AsyncSession, role: Role, status: UserStatus = UserStatus.active
) -> str:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    phone = unique_phone()
    user = make_user(phone=phone)
    user.status = status
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, role, operator_id=operator.id))
    await db_session.flush()
    return phone


async def test_an_existing_user_gets_their_real_role(
    enabled: AsyncClient, db_session: AsyncSession
) -> None:
    phone = await _user(db_session, Role.supervisor)

    response = await enabled.post("/auth/test-login", json={"phone": phone})

    assert response.status_code == 200, response.text
    claims = decode_access_token(response.json()["access_token"], JWT_SECRET, FakeClock(NOW))
    assert claims.role == "supervisor"
    me = await enabled.get(
        "/auth/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"}
    )
    assert [r["role"] for r in me.json()["roles"]] == ["supervisor"]


async def test_an_unknown_phone_is_refused_and_no_user_is_created(enabled: AsyncClient) -> None:
    response = await enabled.post("/auth/test-login", json={"phone": unique_phone()})

    assert response.status_code == 401


async def test_a_suspended_user_is_refused(enabled: AsyncClient, db_session: AsyncSession) -> None:
    phone = await _user(db_session, Role.driver, UserStatus.suspended)

    assert (await enabled.post("/auth/test-login", json={"phone": phone})).status_code == 401


async def test_it_does_not_exist_unless_switched_on(
    disabled: AsyncClient, db_session: AsyncSession
) -> None:
    phone = await _user(db_session, Role.supervisor)

    response = await disabled.post("/auth/test-login", json={"phone": phone})

    assert response.status_code == 404


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_the_app_refuses_to_start_with_it_on_outside_test_environments(env: str) -> None:
    with pytest.raises(ValidationError, match="AUTH_TEST_LOGIN"):
        Settings(
            app_env=env,
            auth_test_login=True,
            database_url="postgresql+asyncpg://t:t@localhost:5432/t",
            jwt_secret="x" * 40,
            osm_contact_email="ops@example.com",
        )


@pytest.mark.parametrize("env", [AppEnv.dev, AppEnv.test, AppEnv.sim])
def test_it_may_be_enabled_in_dev_test_and_sim(env: AppEnv) -> None:
    assert _settings(env.value, True).auth_test_login is True


def test_it_is_off_by_default() -> None:
    assert Settings().auth_test_login is False
