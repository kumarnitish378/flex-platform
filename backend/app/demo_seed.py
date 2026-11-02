"""`make seed-demo`: a small, believable operator to try the app on a phone.

One operator (Rs 8 per km), one client with night safety on, one office, three zones, five cabs with
a driver each, twenty riders (odd-numbered ones are women, so the night escort gate has something
to flag), and one login per role with a fixed phone number. The numbers are listed in
`docs/runbook-phone-testing.md` and printed when the seed runs.

**Idempotent**: every row has an id derived from its name, so a second run finds the rows it made
and leaves them as they are. It never deletes anything, and it refuses to run outside dev, test
and sim - the logins it creates work with the test login.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import time
from typing import Any

from geoalchemy2.shape import from_shape
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon as ShapelyPolygon
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import SystemClock
from app.core.db import create_engine, create_session_factory
from app.core.settings import AppEnv, Settings
from app.domain.enums import Role, TrackerType, VehicleType
from app.modules.auth.models import AppUser, UserRole
from app.modules.config.service import ConfigService
from app.modules.fleet.models import Driver, Vehicle
from app.modules.people.models import Employee
from app.modules.tenancy.models import Client, ClientPolicy, Office, Operator, Zone

NAMESPACE = uuid.UUID("de30ca85-0000-4000-8000-000000000000")

OPERATOR_NAME = "Demo Cabs"
CLIENT_NAME = "Demo Corp"
RATE_PER_KM = 8.0

NIGHT_START = time(20, 0)
NIGHT_END = time(6, 0)
OFFICE = ("Demo HQ", 28.5703, 77.3218)
ZONES = (("sector_62", 28.62, 77.36), ("sector_135", 28.50, 77.38), ("sector_168", 28.46, 77.40))
CABS = (
    ("DL01DEMO01", VehicleType.sedan_4, 4),
    ("DL01DEMO02", VehicleType.sedan_4, 4),
    ("DL01DEMO03", VehicleType.sedan_4, 4),
    ("DL01DEMO04", VehicleType.sedan_4, 4),
    ("DL01DEMO05", VehicleType.suv_6, 6),
)
EMPLOYEES = 20

OPERATOR_ADMIN = "+919100000001"
SUPERVISOR = "+919100000002"
CLIENT_ADMIN = "+919100000003"


def driver_phone(number: int) -> str:
    return f"+9191000001{number:02d}"


def employee_phone(number: int) -> str:
    return f"+9191000002{number:02d}"


def is_woman(number: int) -> bool:
    """Rider 01, 03, 05 ... are women; 02, 04, 06 ... are men."""
    return number % 2 == 1


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, ":".join(str(part) for part in parts))


def _point(lat: float, lng: float) -> Any:
    return from_shape(ShapelyPoint(lng, lat), srid=4326)


def _square(lat: float, lng: float, size: float = 0.02) -> Any:
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


async def _ensure[T](session: AsyncSession, model: type[T], row_id: uuid.UUID, **fields: Any) -> T:
    """The row with this id, created if missing. An existing row is left exactly as it is."""
    found = await session.get(model, row_id)
    if found is not None:
        return found
    row = model(id=row_id, **fields)  # type: ignore[call-arg]
    session.add(row)
    await session.flush()
    return row


@dataclass(frozen=True, slots=True)
class DemoLogin:
    role: str
    name: str
    phone: str


@dataclass(slots=True)
class DemoSummary:
    operator_id: uuid.UUID
    client_id: uuid.UUID
    office_id: uuid.UUID
    logins: list[DemoLogin]
    created: dict[str, int]


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


async def seed(session: AsyncSession) -> DemoSummary:
    """Create the demo world. Safe to call any number of times."""
    before = await _counts(session)

    operator = await _ensure(session, Operator, _id("operator"), name=OPERATOR_NAME)
    client = await _ensure(
        session, Client, _id("client"), operator_id=operator.id, name=CLIENT_NAME
    )
    await _ensure(
        session,
        ClientPolicy,
        _id("policy"),
        operator_id=operator.id,
        client_id=client.id,
        night_safety_enabled=True,
        night_start=NIGHT_START,
        night_end=NIGHT_END,
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
    for name, lat, lng in ZONES:
        await _ensure(
            session,
            Zone,
            _id("zone", name),
            operator_id=operator.id,
            name=name,
            area=_square(lat, lng),
        )

    logins = [
        DemoLogin("operator_admin", "Demo Operator Admin", OPERATOR_ADMIN),
        DemoLogin("supervisor", "Demo Supervisor", SUPERVISOR),
        DemoLogin("client_admin", "Demo Client Admin", CLIENT_ADMIN),
    ]
    await _login(
        session, operator.id, Role.operator_admin, "operator_admin", logins[0].name, OPERATOR_ADMIN
    )
    await _login(session, operator.id, Role.supervisor, "supervisor", logins[1].name, SUPERVISOR)
    await _login(
        session,
        operator.id,
        Role.client_admin,
        "client_admin",
        logins[2].name,
        CLIENT_ADMIN,
        client.id,
    )

    for number, (registration, vehicle_type, seats) in enumerate(CABS, start=1):
        vehicle = await _ensure(
            session,
            Vehicle,
            _id("vehicle", registration),
            operator_id=operator.id,
            registration_no=registration,
            vehicle_type=vehicle_type,
            seat_capacity=seats,
            tracker_type=TrackerType.app,
        )
        name, phone = f"Demo Driver {number}", driver_phone(number)
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
        logins.append(DemoLogin("driver", f"{name} ({registration})", phone))

    for number in range(1, EMPLOYEES + 1):
        name, phone = f"Demo Rider {number:02d}", employee_phone(number)
        user = await _login(
            session, operator.id, Role.employee, f"employee-{number}", name, phone, client.id
        )
        base_lat, base_lng = ZONES[number % len(ZONES)][1:]
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
            home_location=_point(base_lat + number * 0.001, base_lng + number * 0.001),
            priority=5,
            gender="female" if is_woman(number) else "male",
        )
        logins.append(
            DemoLogin("employee", f"{name} ({'woman' if is_woman(number) else 'man'})", phone)
        )

    await ConfigService(session, SystemClock()).update(
        operator.id, {"billing_rate_per_km": RATE_PER_KM}
    )

    after = await _counts(session)
    return DemoSummary(
        operator_id=operator.id,
        client_id=client.id,
        office_id=office.id,
        logins=logins,
        created={name: after[name] - before[name] for name in after},
    )


async def _counts(session: AsyncSession) -> dict[str, int]:
    out: dict[str, int] = {}
    for label, model in (
        ("users", AppUser),
        ("cabs", Vehicle),
        ("drivers", Driver),
        ("employees", Employee),
        ("offices", Office),
        ("zones", Zone),
    ):
        out[label] = int(await session.scalar(select(func.count()).select_from(model)) or 0)
    return out


def refuse_outside_dev(settings: Settings) -> None:
    if settings.app_env not in (AppEnv.dev, AppEnv.sim, AppEnv.test):
        raise SystemExit(f"seed-demo refuses to run with APP_ENV={settings.app_env}")


async def main() -> None:
    settings = Settings()
    refuse_outside_dev(settings)
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    async with factory() as session:
        summary = await seed(session)
        await session.commit()
    await engine.dispose()

    print(f"Demo operator {summary.operator_id}  (rate Rs {RATE_PER_KM:g}/km, night safety on)")
    print("created this run:", ", ".join(f"{k}={v}" for k, v in summary.created.items()))
    print()
    print(f"{'role':<16}{'phone':<16}name")
    for login in summary.logins:
        print(f"{login.role:<16}{login.phone:<16}{login.name}")


if __name__ == "__main__":
    asyncio.run(main())
