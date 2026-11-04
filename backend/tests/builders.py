"""Plain builders for test entities (`testing-strategy.md` §4).

Deliberately functions rather than a factory library: they take an explicit
`operator_id`, which makes every tenant-isolation test say out loud which tenant a row
belongs to.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from geoalchemy2.shape import from_shape
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon as ShapelyPolygon

from app.domain.enums import DevicePlatform, Role
from app.modules.auth.models import AppUser, Device, OtpChallenge, RefreshToken, UserRole
from app.modules.people.models import Employee, SavedPlace
from app.modules.tenancy.models import Client, ClientPolicy, Office, Operator, Zone

# Sector 62 and Sector 135, Noida - the fixture pair used across the docs.
OFFICE_POINT = (77.3218, 28.5703)
HOME_POINT = (77.3910, 28.5123)


def point(lng: float, lat: float) -> object:
    return from_shape(ShapelyPoint(lng, lat), srid=4326)


def square(lng: float, lat: float, size: float = 0.01) -> object:
    return from_shape(
        ShapelyPolygon(
            [
                (lng, lat),
                (lng + size, lat),
                (lng + size, lat + size),
                (lng, lat + size),
                (lng, lat),
            ]
        ),
        srid=4326,
    )


def unique_phone() -> str:
    """A distinct E.164 number, so uniqueness constraints do not collide across tests."""
    return f"+91{uuid.uuid4().int % 10**10:010d}"


def make_operator(name: str = "Acme Cabs") -> Operator:
    return Operator(id=uuid.uuid4(), name=name)


def make_client(operator_id: uuid.UUID, name: str = "Client A") -> Client:
    return Client(id=uuid.uuid4(), operator_id=operator_id, name=name)


def make_office(operator_id: uuid.UUID, client_id: uuid.UUID, name: str = "B200") -> Office:
    return Office(
        id=uuid.uuid4(),
        operator_id=operator_id,
        client_id=client_id,
        name=name,
        location=point(*OFFICE_POINT),
    )


def make_client_policy(operator_id: uuid.UUID, client_id: uuid.UUID) -> ClientPolicy:
    return ClientPolicy(id=uuid.uuid4(), operator_id=operator_id, client_id=client_id)


def make_zone(operator_id: uuid.UUID, name: str = "sector_62") -> Zone:
    return Zone(id=uuid.uuid4(), operator_id=operator_id, name=name, area=square(77.32, 28.57))


def make_employee(
    operator_id: uuid.UUID,
    client_id: uuid.UUID,
    office_id: uuid.UUID,
    name: str = "Asha",
    phone: str | None = None,
    **kwargs: object,
) -> Employee:
    return Employee(
        id=uuid.uuid4(),
        operator_id=operator_id,
        client_id=client_id,
        office_id=office_id,
        name=name,
        phone=phone or unique_phone(),
        home_location=point(*HOME_POINT),
        **kwargs,
    )


def make_saved_place(
    operator_id: uuid.UUID, employee_id: uuid.UUID, label: str = "Home"
) -> SavedPlace:
    return SavedPlace(
        id=uuid.uuid4(),
        operator_id=operator_id,
        employee_id=employee_id,
        label=label,
        location=point(*HOME_POINT),
    )


def make_user(name: str = "Asha", phone: str | None = None) -> AppUser:
    return AppUser(id=uuid.uuid4(), name=name, phone=phone or unique_phone())


def make_user_role(
    user_id: uuid.UUID,
    role: Role = Role.supervisor,
    operator_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
) -> UserRole:
    return UserRole(
        id=uuid.uuid4(),
        user_id=user_id,
        role=role,
        operator_id=operator_id,
        client_id=client_id,
    )


def make_refresh_token(
    user_id: uuid.UUID, token_hash: str | None = None, ttl_days: int = 30
) -> RefreshToken:
    return RefreshToken(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash=token_hash or uuid.uuid4().hex,
        expires_at=datetime.now(UTC) + timedelta(days=ttl_days),
    )


def make_otp_challenge(phone: str | None = None, ttl_minutes: int = 5) -> OtpChallenge:
    return OtpChallenge(
        id=uuid.uuid4(),
        phone=phone or unique_phone(),
        code_hash=uuid.uuid4().hex,
        expires_at=datetime.now(UTC) + timedelta(minutes=ttl_minutes),
    )


def make_device(user_id: uuid.UUID, token: str | None = None) -> Device:
    return Device(
        id=uuid.uuid4(),
        user_id=user_id,
        platform=DevicePlatform.android,
        push_token=token or uuid.uuid4().hex,
    )
