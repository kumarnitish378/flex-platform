"""Builders for the Phase 3 integration tests: an operator with cabs, riders and requests.

`test_semi_auto.py` builds a one-cab world inline, which was right for one cab. Pooling
needs several riders and several cabs at chosen places, so the pieces are functions here
rather than a fixture: a test composes the world it is about instead of inheriting one.

Coordinates are `(lat, lng)` throughout, matching `app.core.geo.to_point`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.geo import coords, to_point
from app.core.settings import Settings
from app.domain.enums import Direction, Urgency, VehicleType
from app.domain.modes import Mode
from app.domain.state_machines import RequestStatus, VehicleStatus
from app.modules.config.service import ConfigService
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle
from app.modules.modes.models import ModeSetting
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest
from app.modules.routing import EtaService, build_routing_provider
from app.modules.tenancy.models import Client, Office, Operator
from app.modules.tracking.models import LocationPing
from tests.builders import make_client, make_employee, make_office, make_operator, unique_phone

NOW = datetime(2026, 10, 16, 7, 0, tzinfo=UTC)
#: Sector 62, Noida (`builders.OFFICE_POINT`) as lat/lng.
OFFICE = (28.5703, 77.3218)


def near(
    lat: float, lng: float, north_km: float = 0.0, east_km: float = 0.0
) -> tuple[float, float]:
    """A point offset from another by kilometres, close enough for fixtures."""
    return lat + north_km / 111.0, lng + east_km / 98.0


@dataclass
class World:
    operator: Operator
    client: Client
    office: Office
    clock: FakeClock
    employees: list[Employee] = field(default_factory=list)
    vehicles: list[Vehicle] = field(default_factory=list)

    @property
    def operator_id(self) -> uuid.UUID:
        return self.operator.id


def eta_service(clock: FakeClock) -> EtaService:
    settings = Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        routing_provider="approx",
    )
    return EtaService(build_routing_provider(settings, clock), clock)


async def build_world(
    session: AsyncSession, clock: FakeClock, mode: Mode | None = Mode.full_auto
) -> World:
    operator = make_operator()
    session.add(operator)
    await session.flush()
    client = make_client(operator.id)
    session.add(client)
    await session.flush()
    office = make_office(operator.id, client.id)
    session.add(office)
    await session.flush()
    if mode is not None:
        session.add(
            ModeSetting(
                id=uuid.uuid4(),
                operator_id=operator.id,
                mode=str(mode),
                created_at=clock.now(),
                updated_at=clock.now(),
            )
        )
        await session.flush()
    return World(operator=operator, client=client, office=office, clock=clock)


async def set_config(session: AsyncSession, world: World, **values: object) -> None:
    await ConfigService(session, world.clock).update(world.operator_id, dict(values))


async def add_employee(
    session: AsyncSession,
    world: World,
    home: tuple[float, float],
    name: str = "Rider",
    **fields: Any,
) -> Employee:
    employee = make_employee(
        world.operator_id,
        world.client.id,
        world.office.id,
        name=name,
        phone=unique_phone(),
        **fields,
    )
    employee.home_location = to_point(*home)
    session.add(employee)
    await session.flush()
    world.employees.append(employee)
    return employee


async def add_cab(
    session: AsyncSession,
    world: World,
    at: tuple[float, float],
    *,
    seats: int = 4,
    vehicle_type: VehicleType = VehicleType.sedan_4,
    status: VehicleStatus = VehicleStatus.available,
) -> Vehicle:
    """An on-duty cab with a driver and a fresh position."""
    vehicle = Vehicle(
        id=uuid.uuid4(),
        operator_id=world.operator_id,
        registration_no=f"DL{uuid.uuid4().hex[:6].upper()}",
        vehicle_type=vehicle_type,
        seat_capacity=seats,
        status=status,
    )
    driver = Driver(
        id=uuid.uuid4(), operator_id=world.operator_id, name="Driver", phone=unique_phone()
    )
    session.add_all([vehicle, driver])
    await session.flush()
    session.add(
        DutySession(
            id=uuid.uuid4(),
            operator_id=world.operator_id,
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            started_at=world.clock.now() - timedelta(hours=1),
        )
    )
    await session.flush()
    world.vehicles.append(vehicle)
    await ping(session, world, vehicle, at)
    return vehicle


async def ping(
    session: AsyncSession, world: World, vehicle: Vehicle, at: tuple[float, float]
) -> None:
    """Report the cab's position at the current clock time."""
    session.add(
        LocationPing(
            vehicle_id=vehicle.id,
            operator_id=world.operator_id,
            recorded_at=world.clock.now(),
            received_at=world.clock.now(),
            location=to_point(*at),
            source="sim",
        )
    )
    await session.flush()


async def add_request(
    session: AsyncSession,
    world: World,
    employee: Employee,
    *,
    direction: Direction = Direction.to_office,
    status: RequestStatus = RequestStatus.queued,
    requested_in: timedelta = timedelta(0),
    **fields: Any,
) -> RideRequest:
    now = world.clock.now()
    request = RideRequest(
        id=uuid.uuid4(),
        operator_id=world.operator_id,
        client_id=world.client.id,
        employee_id=employee.id,
        direction=str(direction),
        office_id=world.office.id,
        location=to_point(*coords(employee.home_location)),
        requested_time=now + requested_in,
        urgency=str(Urgency.medium),
        status=str(status),
        queued_at=now,
        expires_at=now + timedelta(hours=2),
    )
    for name, value in fields.items():
        setattr(request, name, value)
    session.add(request)
    await session.flush()
    return request
