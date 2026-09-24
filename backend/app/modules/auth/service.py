"""Authentication use cases (B03).

Security rules come from `non-functional.md`:
  * phone + OTP login, access token 15 min, refresh token 30 days, rotated on use,
    revocable;
  * OTP requests limited to 3 per 10 minutes per phone.

Two decisions worth stating, because they are easy to get wrong:

**An unknown phone gets the same answer as a known one.** The contract allows 404 on
`/auth/otp/request`, and that turns the endpoint into a directory: anyone could discover
which numbers belong to an operator's staff and riders. The service always reports
success and simply does not send a code. See `_send_if_known`.

**Verification failures are indistinguishable.** Wrong code, expired code, no challenge
and locked out all raise the same error, so an attacker learns nothing about which part
was wrong.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from http import HTTPStatus

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger, mask_phone
from app.core.security import (
    create_access_token,
    generate_otp_code,
    generate_refresh_token,
    hash_secret,
    verify_secret,
)
from app.core.settings import Settings
from app.domain.enums import Role, UserStatus
from app.domain.errors import DomainError, NotFound, RateLimited, ValidationFailed
from app.modules.auth.models import AppUser, Device, OtpChallenge, RefreshToken, UserRole
from app.modules.auth.otp import OtpSender
from app.modules.auth.permissions import permissions_for

logger = get_logger(__name__)

# non-functional.md, Security: "OTP requests 3/10 min per phone".
OTP_RATE_LIMIT = 3
OTP_RATE_WINDOW = timedelta(minutes=10)
OTP_TTL = timedelta(minutes=5)
# Attempts against a single challenge before it is burned.
OTP_MAX_ATTEMPTS = 5


class InvalidCredentialsError(DomainError):
    """Deliberately vague: wrong code, expired, missing and locked out are one error.

    401 rather than 403: the caller is unauthenticated, not forbidden from a resource.
    """

    code = "unauthorized"
    http_status = HTTPStatus.UNAUTHORIZED


@dataclass(frozen=True, slots=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True, slots=True)
class RoleView:
    role: Role
    operator_id: uuid.UUID | None
    client_id: uuid.UUID | None
    employee_id: uuid.UUID | None
    driver_id: uuid.UUID | None
    permissions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MeView:
    user_id: uuid.UUID
    name: str
    phone: str
    roles: tuple[RoleView, ...]


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        settings: Settings,
        otp_sender: OtpSender,
    ) -> None:
        self.session = session
        self.clock = clock
        self.settings = settings
        self.otp_sender = otp_sender

    # --- OTP ----------------------------------------------------------------

    async def request_otp(self, phone: str) -> None:
        """Send a code if the phone belongs to a user. Rate limited per phone."""
        await self._enforce_otp_rate_limit(phone)
        await self._send_if_known(phone)

    async def _enforce_otp_rate_limit(self, phone: str) -> None:
        since = self.clock.now() - OTP_RATE_WINDOW
        result = await self.session.execute(
            select(OtpChallenge).where(
                OtpChallenge.phone == phone, OtpChallenge.created_at >= since
            )
        )
        recent = result.scalars().all()
        if len(recent) >= OTP_RATE_LIMIT:
            logger.info("otp_rate_limited", phone=mask_phone(phone), recent=len(recent))
            raise RateLimited(
                "Too many OTP requests. Try again later.",
                {"retry_after_seconds": int(OTP_RATE_WINDOW.total_seconds())},
            )

    async def _send_if_known(self, phone: str) -> None:
        """Create and send a challenge only for a known, active user.

        An unknown number is silently ignored so this endpoint cannot be used to
        enumerate staff and riders.
        """
        user = await self._user_by_phone(phone)
        if user is None or user.status != UserStatus.active:
            logger.info("otp_requested_for_unknown_phone", phone=mask_phone(phone))
            return

        code = generate_otp_code()
        self.session.add(
            OtpChallenge(
                phone=phone,
                code_hash=hash_secret(code),
                expires_at=self.clock.now() + OTP_TTL,
            )
        )
        await self.session.flush()
        await self.otp_sender.send(phone, code)
        logger.info("otp_sent", phone=mask_phone(phone))

    async def verify_otp(
        self, phone: str, code: str, device_info: str | None = None
    ) -> IssuedTokens:
        """Consume a challenge and issue tokens, or raise `InvalidCredentialsError`."""
        challenge = await self._latest_open_challenge(phone)
        if challenge is None:
            raise InvalidCredentialsError("Invalid phone or code")

        if challenge.attempts >= OTP_MAX_ATTEMPTS:
            logger.info("otp_locked_out", phone=mask_phone(phone))
            raise InvalidCredentialsError("Invalid phone or code")

        if not verify_secret(code, challenge.code_hash):
            # Count the failure before returning, so repeated guesses burn the challenge.
            challenge.attempts += 1
            await self.session.flush()
            logger.info("otp_verify_failed", phone=mask_phone(phone), attempts=challenge.attempts)
            raise InvalidCredentialsError("Invalid phone or code")

        user = await self._user_by_phone(phone)
        if user is None or user.status != UserStatus.active:
            raise InvalidCredentialsError("Invalid phone or code")

        challenge.consumed_at = self.clock.now()
        user.last_login_at = self.clock.now()
        await self.session.flush()

        logger.info("login_succeeded", user_id=str(user.id), phone=mask_phone(phone))
        return await self._issue_tokens(user, device_info)

    async def _latest_open_challenge(self, phone: str) -> OtpChallenge | None:
        now = self.clock.now()
        result = await self.session.execute(
            select(OtpChallenge)
            .where(OtpChallenge.phone == phone)
            .where(OtpChallenge.consumed_at.is_(None))
            .where(OtpChallenge.expires_at > now)
            .order_by(OtpChallenge.created_at.desc())
        )
        return result.scalars().first()

    # --- tokens -------------------------------------------------------------

    async def _issue_tokens(self, user: AppUser, device_info: str | None) -> IssuedTokens:
        role_view = await self._default_role(user.id)
        access_token, expires_at = create_access_token(
            user_id=user.id,
            role=str(role_view.role) if role_view else "",
            secret=self.settings.jwt_secret.get_secret_value(),
            clock=self.clock,
            ttl_seconds=self.settings.access_token_ttl_seconds,
            operator_id=role_view.operator_id if role_view else None,
            client_id=role_view.client_id if role_view else None,
        )

        refresh_value = generate_refresh_token()
        self.session.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_secret(refresh_value),
                expires_at=self.clock.now() + timedelta(days=self.settings.refresh_token_ttl_days),
                device_info=device_info,
            )
        )
        await self.session.flush()

        return IssuedTokens(
            access_token=access_token,
            refresh_token=refresh_value,
            expires_in=int((expires_at - self.clock.now()).total_seconds()),
        )

    async def refresh(self, refresh_token: str) -> IssuedTokens:
        """Rotate: the presented token is revoked and a new one issued."""
        stored = await self._live_refresh_token(refresh_token)
        if stored is None:
            raise InvalidCredentialsError("Invalid refresh token")

        user = await self.session.get(AppUser, stored.user_id)
        if user is None or user.status != UserStatus.active:
            raise InvalidCredentialsError("Invalid refresh token")

        stored.revoked_at = self.clock.now()
        await self.session.flush()
        return await self._issue_tokens(user, stored.device_info)

    async def logout(self, refresh_token: str) -> None:
        """Revoke one refresh token. Unknown tokens are accepted silently."""
        stored = await self._live_refresh_token(refresh_token)
        if stored is not None:
            stored.revoked_at = self.clock.now()
            await self.session.flush()

    async def _live_refresh_token(self, value: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == hash_secret(value))
            .where(RefreshToken.revoked_at.is_(None))
            .where(RefreshToken.expires_at > self.clock.now())
        )
        return result.scalars().one_or_none()

    # --- identity -----------------------------------------------------------

    async def me(self, user_id: uuid.UUID) -> MeView:
        user = await self.session.get(AppUser, user_id)
        if user is None:
            raise NotFound("User not found", {"id": str(user_id)})

        roles = await self._roles_for(user_id)
        return MeView(
            user_id=user.id,
            name=user.name,
            phone=user.phone,
            roles=tuple(roles),
        )

    async def _roles_for(self, user_id: uuid.UUID) -> list[RoleView]:
        result = await self.session.execute(
            select(UserRole).where(UserRole.user_id == user_id).order_by(UserRole.role)
        )
        return [
            RoleView(
                role=Role(row.role),
                operator_id=row.operator_id,
                client_id=row.client_id,
                employee_id=row.employee_id,
                driver_id=row.driver_id,
                permissions=tuple(sorted(str(p) for p in permissions_for(Role(row.role)))),
            )
            for row in result.scalars().all()
        ]

    async def _default_role(self, user_id: uuid.UUID) -> RoleView | None:
        roles = await self._roles_for(user_id)
        return roles[0] if roles else None

    async def _user_by_phone(self, phone: str) -> AppUser | None:
        result = await self.session.execute(select(AppUser).where(AppUser.phone == phone))
        return result.scalars().one_or_none()

    # --- devices ------------------------------------------------------------

    async def register_device(
        self, user_id: uuid.UUID, platform: str, push_token: str, app_version: str
    ) -> None:
        """Upsert by push token.

        The same handset can be handed to another driver, so a token that already exists
        is re-pointed at the current user rather than rejected — otherwise push would
        keep going to the previous owner.
        """
        if not push_token:
            raise ValidationFailed("push_token is required")

        result = await self.session.execute(select(Device).where(Device.push_token == push_token))
        device = result.scalars().one_or_none()
        now: datetime = self.clock.now()

        if device is None:
            self.session.add(
                Device(
                    user_id=user_id,
                    platform=platform,
                    push_token=push_token,
                    app_version=app_version,
                    last_seen_at=now,
                )
            )
        else:
            device.user_id = user_id
            device.platform = platform
            device.app_version = app_version
            device.last_seen_at = now
        await self.session.flush()
