"""FastAPI dependencies: the session, the clock, and the current caller.

Everything is read from `app.state`, which the factory populated, so a test can build an
app with a `FakeClock` and a test database and every route follows.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.security import AccessTokenClaims, InvalidTokenError, decode_access_token
from app.core.settings import Settings
from app.domain.enums import Role
from app.domain.errors import DomainError
from app.modules.auth.service import InvalidCredentialsError


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One session per request, committed on success and rolled back on failure.

    Committing here rather than in every service keeps the unit of work at the request
    boundary: a handler that raises halfway cannot leave half its writes behind.
    """
    factory = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


def get_clock(request: Request) -> Clock:
    clock: Clock = request.app.state.clock
    return clock


def get_settings_dep(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


class CurrentUser:
    """The authenticated caller and the role they are acting under."""

    def __init__(self, claims: AccessTokenClaims, active_role: Role) -> None:
        self.claims = claims
        self.active_role = active_role

    @property
    def user_id(self) -> object:
        return self.claims.user_id

    @property
    def operator_id(self) -> object:
        return self.claims.operator_id

    @property
    def client_id(self) -> object:
        return self.claims.client_id


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_active_role: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    """Verify the bearer token and the active role.

    `X-Active-Role` is a *selection*, never a grant: it must match the role inside the
    signed token, so a caller cannot promote themselves by editing a header
    (`roles-and-permissions.md`: the server verifies the user holds it).
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise InvalidCredentialsError("Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    settings: Settings = request.app.state.settings
    clock: Clock = request.app.state.clock

    try:
        claims = decode_access_token(token, settings.jwt_secret.get_secret_value(), clock)
    except InvalidTokenError as exc:
        raise InvalidCredentialsError("Invalid or expired token") from exc

    if not claims.role:
        raise InvalidCredentialsError("Token carries no role")

    try:
        token_role = Role(claims.role)
    except ValueError as exc:
        raise InvalidCredentialsError("Token carries an unknown role") from exc

    if x_active_role is not None and x_active_role != str(token_role):
        raise _WrongActiveRoleError(
            "X-Active-Role does not match the role this token was issued for",
            {"active_role": x_active_role},
        )

    return CurrentUser(claims, token_role)


class _WrongActiveRoleError(DomainError):
    code = "forbidden"
    http_status = 403


SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
