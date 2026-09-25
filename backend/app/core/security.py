"""Token and secret handling.

Nothing here reads the clock: expiry times are computed from a `Clock` the caller passes
in, so the simulator can age a token out in one step (CLAUDE.md hard rule 2).

What is stored, and what is not:

* Refresh tokens and OTP codes are stored **hashed**. A database dump must not let anyone
  log in. Both are high-entropy or short-lived, so SHA-256 is enough and avoids putting a
  bcrypt round in the OTP path where it would leak timing under load.
* Access tokens are not stored at all — they are verified by signature.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import jwt

from app.core.clock import Clock

ALGORITHM = "HS256"
OTP_LENGTH = 6
REFRESH_TOKEN_BYTES = 32


class InvalidTokenError(Exception):
    """Signature, expiry or shape is wrong. Deliberately says no more than that."""


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: uuid.UUID
    role: str
    operator_id: uuid.UUID | None
    client_id: uuid.UUID | None
    expires_at: datetime


def generate_otp_code() -> str:
    """A cryptographically random 6-digit code, matching the api-spec pattern."""
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def generate_refresh_token() -> str:
    """Opaque, high-entropy. Never a JWT: a refresh token must be revocable."""
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_secret(value: str) -> str:
    """One-way hash for storage."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_secret(value: str, expected_hash: str) -> bool:
    """Constant-time comparison, so a wrong OTP cannot be found by timing."""
    return hmac.compare_digest(hash_secret(value), expected_hash)


def create_access_token(
    *,
    user_id: uuid.UUID,
    role: str,
    secret: str,
    clock: Clock,
    ttl_seconds: int,
    operator_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
) -> tuple[str, datetime]:
    """Return the signed token and the moment it expires.

    The active role is inside the token, so a request cannot claim a role the user does
    not hold by setting `X-Active-Role`; that header is checked against this claim.
    """
    issued_at = clock.now()
    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "operator_id": str(operator_id) if operator_id else None,
        "client_id": str(client_id) if client_id else None,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM), expires_at


def decode_access_token(token: str, secret: str, clock: Clock) -> AccessTokenClaims:
    """Verify and unpack, or raise `InvalidTokenError`.

    **Every** time check uses the injected clock, so PyJWT's own `exp`, `iat` and `nbf`
    verification is switched off. Leaving `iat` on would compare the token against the
    real system clock: a simulator running ahead of wall-clock time mints tokens whose
    `iat` is in the future, and PyJWT rejects the lot with "not yet valid" (CLAUDE.md
    hard rule 2 - the clock is injected, including here).
    """
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            options={
                "verify_exp": False,
                "verify_iat": False,
                "verify_nbf": False,
                "require": ["sub", "role", "exp"],
            },
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    expires_at = datetime.fromtimestamp(payload["exp"], tz=clock.now().tzinfo)
    if clock.now() >= expires_at:
        raise InvalidTokenError("token expired")

    try:
        return AccessTokenClaims(
            user_id=uuid.UUID(payload["sub"]),
            role=str(payload["role"]),
            operator_id=uuid.UUID(payload["operator_id"]) if payload.get("operator_id") else None,
            client_id=uuid.UUID(payload["client_id"]) if payload.get("client_id") else None,
            expires_at=expires_at,
        )
    except (ValueError, TypeError) as exc:
        raise InvalidTokenError("malformed claims") from exc


def mask_phone_for_log(phone: str) -> str:
    """Re-exported for convenience; never log a full number."""
    from app.core.logging import mask_phone

    return mask_phone(phone)
