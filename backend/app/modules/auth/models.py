"""Users, roles, tokens, OTP challenges and devices (`data-model.md`, Tenancy and users).

`app_user` is deliberately **not** tenant-scoped: one person can hold roles at more than
one operator (and `platform_admin` belongs to none). Tenancy lives on `user_role`, which
is why every authorisation check reads the active role rather than the user.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Entity
from app.domain.enums import DevicePlatform, Role, UserStatus

# E.164, matching the `Phone` schema in api-spec.yaml.
PHONE_PATTERN = r"^\+[1-9][0-9]{7,14}$"


class AppUser(Entity):
    """A person who can log in. Identified by phone; there is no password."""

    __tablename__ = "app_user"
    __table_args__ = (
        UniqueConstraint("phone", name="uq_app_user_phone"),
        CheckConstraint(f"phone ~ '{PHONE_PATTERN}'", name="ck_app_user_phone_e164"),
    )

    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(UserStatus, native_enum=False, length=20), nullable=False, default=UserStatus.active
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserRole(Entity):
    """One role a user holds, and the scope it applies to.

    `operator_id` is nullable only for `platform_admin`; `client_id` is set for
    `client_admin` and `employee`. Both rules are CHECK constraints rather than
    application-only logic, because a wrong row here is a cross-tenant data leak.
    """

    __tablename__ = "user_role"
    __table_args__ = (
        # NULLS NOT DISTINCT is load-bearing. client_id is NULL for every supervisor,
        # driver and operator_admin grant, and a default unique constraint treats NULLs
        # as distinct - so it would allow unlimited duplicate role grants for exactly
        # the most common roles. Postgres 15+ required.
        UniqueConstraint(
            "user_id",
            "role",
            "operator_id",
            "client_id",
            name="uq_user_role_scope",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint(
            "(role = 'platform_admin' AND operator_id IS NULL)"
            " OR (role <> 'platform_admin' AND operator_id IS NOT NULL)",
            name="ck_user_role_operator_scope",
        ),
        CheckConstraint(
            "(role IN ('client_admin', 'employee') AND client_id IS NOT NULL)"
            " OR (role NOT IN ('client_admin', 'employee') AND client_id IS NULL)",
            name="ck_user_role_client_scope",
        ),
        Index("ix_user_role_user", "user_id"),
        Index("ix_user_role_operator_role", "operator_id", "role"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(Enum(Role, native_enum=False, length=20), nullable=False)
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("operator.id", ondelete="CASCADE")
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client.id", ondelete="CASCADE")
    )
    # Filled once the matching profile exists; a driver or employee row may be created
    # before the person ever logs in.
    employee_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    driver_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))


class RefreshToken(Entity):
    """A rotating refresh token. Only the hash is stored, never the token itself."""

    __tablename__ = "refresh_token"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_refresh_token_hash"),
        Index("ix_refresh_token_user", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    device_info: Mapped[str | None] = mapped_column(String(300))


class OtpChallenge(Entity):
    """A pending OTP. Only the hash is stored; `attempts` drives lockout (B03)."""

    __tablename__ = "otp_challenge"
    __table_args__ = (
        Index("ix_otp_challenge_phone", "phone"),
        CheckConstraint("attempts >= 0", name="ck_otp_attempts_non_negative"),
    )

    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Device(Entity):
    """A device registered for push notifications."""

    __tablename__ = "device"
    __table_args__ = (
        UniqueConstraint("push_token", name="uq_device_push_token"),
        Index("ix_device_user", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(
        Enum(DevicePlatform, native_enum=False, length=20), nullable=False
    )
    push_token: Mapped[str] = mapped_column(String(500), nullable=False)
    app_version: Mapped[str | None] = mapped_column(String(50))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
