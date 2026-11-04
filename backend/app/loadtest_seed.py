"""Data for `make loadtest`: a pilot-sized operator, 35 cabs, 300 riders, 2 supervisors.

Separate from the demo operator on purpose: the demo world is five cabs for a human with a
phone, this one is the size of the pilot and exists to be driven by a script
(`scripts/loadtest.py`). Same seeding as `demo_seed` - ids derived from names, so a second run
creates nothing and a developer's other data is never touched - and the same guard: dev, test
and sim only.

Riders live within `RIDER_RADIUS_M` of the office on a deterministic spread, so every run has the
same map. Phones are fixed and printed:

    operator admin   +919230000003        supervisors   +919230000001, +919230000002
    drivers          +9192100000NN        riders        +9192200000NNN   (NN 01..35, NNN 001..300)
"""

from __future__ import annotations

import asyncio
import math
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import SystemClock
from app.core.db import create_engine, create_session_factory
from app.core.settings import Settings
from app.demo_seed import _ensure, _point, refuse_outside_dev  # noqa: PLC2701
from app.domain.enums import Role, TrackerType, VehicleType
from app.modules.auth.models import AppUser, UserRole
from app.modules.config.service import ConfigService
from app.modules.fleet.models import Driver, Vehicle
from app.modules.people.models import Employee
from app.modules.tenancy.models import Client, ClientPolicy, Office, Operator

NAMESPACE = uuid.UUID("10ad7e57-0000-4000-8000-000000000000")

OPERATOR_NAME = "Load Test Cabs"
CLIENT_NAME = "Load Test Corp"
OFFICE = ("Load Test HQ", 28.5703, 77.3218)
CABS = 35
RIDERS = 300
RIDER_RADIUS_M = 6000.0
MIN_RIDER_DISTANCE_M = 800.0

OPERATOR_ADMIN = "+919230000003"
SUPERVISORS = ("+919230000001", "+919230000002")

EARTH = 6_371_000.0
GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))


def driver_phone(number: int) -> str:
    return f"+9192100{number:05d}"


def rider_phone(number: int) -> str:
    return f"+9192200{number:05d}"


def registration(number: int) -> str:
    return f"DL01LT{number:04d}"


def rider_home(number: int) -> tuple[float, float]:
    """Rider `number` (1-based) on a sunflower spread between 0.8 km and 6 km of the office.

    Deterministic, so two runs - and two machines - load the same map. Equal-area spacing means
    the request pins are spread like real homes rather than piled on the office.
    """
    fraction = (number - 0.5) / RIDERS
    radius = math.sqrt(
        MIN_RIDER_DISTANCE_M**2 + fraction * (RIDER_RADIUS_M**2 - MIN_RIDER_DISTANCE_M**2)
    )
    angle = number * GOLDEN_ANGLE
    north, east = radius * math.cos(angle), radius * math.sin(angle)
    lat = OFFICE[1] + math.degrees(north / EARTH)
    lng = OFFICE[2] + math.degrees(east / (EARTH * math.cos(math.radians(OFFICE[1]))))
    return lat, lng


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, ":".join(str(part) for part in parts))


@dataclass(slots=True)
class LoadWorld:
    operator_id: uuid.UUID
    client_id: uuid.UUID
    created: int


async def _login(
    session: AsyncSession,
    operator_id: uuid.UUID,
    role: Role,
    key: str,
    name: str,
    phone: str,
    client_id: uuid.UUID | None = None,
) -> AppUser:
    user = await _ensure(session, AppUser, _id("user", key), phone=phone, name=name)
    await _ensure(
        session,
        UserRole,
        _id("role", key),
        user_id=user.id,
        role=role,
        operator_id=operator_id,
        client_id=client_id,
    )
    return user


async def seed(session: AsyncSession) -> LoadWorld:
    """Create the load-test world. Safe to call any number of times."""
    operator = await _ensure(session, Operator, _id("operator"), name=OPERATOR_NAME)
    client = await _ensure(
        session, Client, _id("client"), operator_id=operator.id, name=CLIENT_NAME
    )
    # Pooling off for the supervisor-driven run: one request, one cab, so the load measured is the
    # API and the GPS pipeline, not the pooling arithmetic (the optimizer has its own scenarios).
    await _ensure(
        session,
        ClientPolicy,
        _id("policy"),
        operator_id=operator.id,
        client_id=client.id,
        pooling_allowed=False,
    )
    office = await _ensure(
        session,
        Office,
        _id("office"),
        operator_id=operator.id,
        client_id=client.id,
        name=OFFICE[0],
        location=_point(OFFICE[1], OFFICE[2]),
    )

    await _login(
        session, operator.id, Role.operator_admin, "admin", "Load Test Admin", OPERATOR_ADMIN
    )
    for number, phone in enumerate(SUPERVISORS, start=1):
        await _login(
            session,
            operator.id,
            Role.supervisor,
            f"sup-{number}",
            f"Load Supervisor {number}",
            phone,
        )

    for number in range(1, CABS + 1):
        vehicle = await _ensure(
            session,
            Vehicle,
            _id("vehicle", number),
            operator_id=operator.id,
            registration_no=registration(number),
            vehicle_type=VehicleType.sedan_4,
            seat_capacity=4,
            tracker_type=TrackerType.app,
        )
        name, phone = f"Load Driver {number:02d}", driver_phone(number)
        user = await _login(session, operator.id, Role.driver, f"driver-{number}", name, phone)
        await _ensure(
            session,
            Driver,
            _id("driver", number),
            operator_id=operator.id,
            user_id=user.id,
            name=name,
            phone=phone,
            default_vehicle_id=vehicle.id,
        )

    for number in range(1, RIDERS + 1):
        name, phone = f"Load Rider {number:03d}", rider_phone(number)
        user = await _login(
            session, operator.id, Role.employee, f"rider-{number}", name, phone, client.id
        )
        lat, lng = rider_home(number)
        await _ensure(
            session,
            Employee,
            _id("employee", number),
            operator_id=operator.id,
            client_id=client.id,
            user_id=user.id,
            name=name,
            phone=phone,
            office_id=office.id,
            home_location=_point(lat, lng),
            priority=5,
            gender="female" if number % 2 else "male",
        )

    # Manual mode is the Phase 1 default and what the pilot starts in; nothing to set. The rate
    # is set so the billing report has something to multiply.
    await ConfigService(session, SystemClock()).update(operator.id, {"billing_rate_per_km": 8.0})
    return LoadWorld(operator.id, client.id, CABS + RIDERS)


async def main() -> None:
    settings = Settings()
    refuse_outside_dev(settings)
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    async with factory() as session:
        world: Any = await seed(session)
        await session.commit()
    await engine.dispose()
    print(f"Load-test operator {world.operator_id}: {CABS} cabs, {RIDERS} riders, 2 supervisors")


if __name__ == "__main__":
    asyncio.run(main())
