"""Auth repositories.

Users are not tenant-scoped (one person may work for several operators); their *roles*
are. Anything that resolves a user into a tenant must go through `UserRoleRepository`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.core.repository import Repository
from app.modules.auth.models import AppUser, Device, OtpChallenge, RefreshToken, UserRole


class AppUserRepository(Repository[AppUser]):
    model = AppUser

    async def by_phone(self, phone: str) -> AppUser | None:
        result = await self.session.execute(select(AppUser).where(AppUser.phone == phone))
        return result.scalars().one_or_none()


class UserRoleRepository(Repository[UserRole]):
    model = UserRole

    async def for_user(self, user_id: uuid.UUID) -> list[UserRole]:
        result = await self.session.execute(select(UserRole).where(UserRole.user_id == user_id))
        return list(result.scalars().all())

    async def for_user_in_operator(
        self, user_id: uuid.UUID, operator_id: uuid.UUID
    ) -> list[UserRole]:
        result = await self.session.execute(
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .where(UserRole.operator_id == operator_id)
        )
        return list(result.scalars().all())


class RefreshTokenRepository(Repository[RefreshToken]):
    model = RefreshToken

    async def by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalars().one_or_none()


class OtpChallengeRepository(Repository[OtpChallenge]):
    model = OtpChallenge


class DeviceRepository(Repository[Device]):
    model = Device
