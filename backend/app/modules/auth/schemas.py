"""Request and response models for `/auth/*` and `/devices`.

These mirror `api-spec.yaml` exactly — field names, patterns and required-ness. A
contract test (B-later) compares the generated OpenAPI against the spec, so a drift here
fails the build rather than the app.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DevicePlatform, Role

# api-spec.yaml `Phone`.
PHONE_PATTERN = r"^\+[1-9][0-9]{7,14}$"
OTP_CODE_PATTERN = r"^[0-9]{6}$"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OtpRequest(Strict):
    phone: str = Field(pattern=PHONE_PATTERN, examples=["+919812345678"])


class OtpVerify(Strict):
    phone: str = Field(pattern=PHONE_PATTERN)
    code: str = Field(pattern=OTP_CODE_PATTERN)


class RefreshRequest(Strict):
    refresh_token: str = Field(min_length=1)


class TokenPair(Strict):
    access_token: str
    refresh_token: str
    expires_in: int = Field(description="seconds")


class RoleEntry(Strict):
    role: Role
    operator_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    employee_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    permissions: list[str] = Field(default_factory=list)


class Me(Strict):
    user_id: uuid.UUID
    name: str
    phone: str
    roles: list[RoleEntry] = Field(default_factory=list)


class DeviceRegister(Strict):
    platform: DevicePlatform
    push_token: str = Field(min_length=1, max_length=500)
    app_version: str = Field(min_length=1, max_length=50)
