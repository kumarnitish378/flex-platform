"""Zones, and the derivation they exist for (B27).

`employee.zone_id` is never set by a caller - not by the API, not by the CSV import.
It is derived from the home location, which means two separate things have to stay
true: a home written now lands in the right zone, and a zone drawn or redrawn now
re-derives the homes that already existed.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon as ShapelyPolygon
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.geo import ring, to_point, to_polygon
from app.domain.enums import Direction, Role
from app.domain.errors import Conflict, NotFound, ValidationFailed
from app.domain.modes import Mode, ModeReason
from app.modules.modes.models import ModeSetting
from app.modules.modes.service import ModeService
from app.modules.people.service import EmployeeService
from app.modules.requests.models import RideRequest
from app.modules.zones.service import ZoneService
from tests.builders import make_client, make_employee, make_office, make_operator, unique_phone

pytestmark = pytest.mark.requires_db

NOW = datetime(2026, 10, 17, 7, 0, tzinfo=UTC)

#: A one-degree-tenth square with corners that are easy to reason about: the zone runs
#: from 28.50 to 28.60 north and 77.30 to 77.40 east.
SQUARE = [(28.50, 77.30), (28.50, 77.40), (28.60, 77.40), (28.60, 77.30)]
INSIDE = (28.55, 77.35)
OUTSIDE = (28.70, 77.35)
#: Exactly on the southern edge. `ST_Contains` says no; `ST_Covers` says yes.
ON_THE_BOUNDARY = (28.50, 77.35)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    corporate = make_client(operator.id)
    db_session.add(corporate)
    await db_session.flush()
    office = make_office(operator.id, corporate.id)
    db_session.add(office)
    await db_session.flush()
    return {"operator": operator, "client": corporate, "office": office}


@pytest.fixture
def zones(db_session: AsyncSession, clock: FakeClock) -> ZoneService:
    return ZoneService(db_session, clock)


@pytest.fixture
def employees(db_session: AsyncSession, clock: FakeClock) -> EmployeeService:
    return EmployeeService(db_session, clock)


async def add_employee(
    db_session: AsyncSession, world: dict[str, Any], at: tuple[float, float], name: str = "Asha"
) -> Any:
    employee = make_employee(
        world["operator"].id,
        world["client"].id,
        world["office"].id,
        name=name,
        phone=unique_phone(),
    )
    employee.home_location = to_point(*at)
    db_session.add(employee)
    await db_session.flush()
    return employee


# --- point in polygon ------------------------------------------------------------


@pytest.mark.parametrize(
    ("home", "covered"),
    [(INSIDE, True), (OUTSIDE, False), (ON_THE_BOUNDARY, True)],
    ids=["inside", "outside", "on the boundary"],
)
async def test_a_home_inside_outside_and_on_the_boundary(
    db_session: AsyncSession,
    world: dict[str, Any],
    zones: ZoneService,
    home: tuple[float, float],
    covered: bool,
) -> None:
    """The boundary case is a decision, not an accident.

    `ST_Contains` excludes a point on the edge, which would drop a rider into the crack
    between two adjacent zones sharing that edge. `ST_Covers` includes it.
    """
    zone, _ = await zones.create(world["operator"].id, "sector_62", SQUARE)
    found = await zones.zone_of(world["operator"].id, *home)
    assert found == (zone.id if covered else None)


async def test_an_operator_with_no_zones_has_no_zone_for_anyone(
    world: dict[str, Any], zones: ZoneService
) -> None:
    """`None` is an ordinary answer: Phase 1 ran that way from end to end."""
    assert await zones.zone_of(world["operator"].id, *INSIDE) is None


async def test_an_inactive_zone_covers_nobody(world: dict[str, Any], zones: ZoneService) -> None:
    zone, _ = await zones.create(world["operator"].id, "sector_62", SQUARE, active=False)
    assert await zones.zone_of(world["operator"].id, *INSIDE) is None
    await zones.update(world["operator"].id, zone.id, active=True)
    assert await zones.zone_of(world["operator"].id, *INSIDE) == zone.id


async def test_overlapping_zones_resolve_to_the_smaller_one(
    world: dict[str, Any], zones: ZoneService
) -> None:
    """An operator drawing "Sector 62" inside "Noida" is being reasonable, and the more
    specific answer is the useful one. Created larger-first and smaller-first to prove
    the answer does not depend on insertion order."""
    inner = [(28.54, 77.34), (28.54, 77.36), (28.56, 77.36), (28.56, 77.34)]
    big, _ = await zones.create(world["operator"].id, "noida", SQUARE)
    small, _ = await zones.create(world["operator"].id, "sector_62", inner)
    assert await zones.zone_of(world["operator"].id, *INSIDE) == small.id

    await zones.delete(world["operator"].id, small.id)
    await zones.delete(world["operator"].id, big.id)
    small_again, _ = await zones.create(world["operator"].id, "sector_62", inner)
    await zones.create(world["operator"].id, "noida", SQUARE)
    assert await zones.zone_of(world["operator"].id, *INSIDE) == small_again.id


async def test_a_zone_is_scoped_to_its_operator(
    db_session: AsyncSession, world: dict[str, Any], zones: ZoneService
) -> None:
    other = make_operator(name="Other Cabs")
    db_session.add(other)
    await db_session.flush()
    await zones.create(world["operator"].id, "sector_62", SQUARE)
    assert await zones.zone_of(other.id, *INSIDE) is None


# --- drawing a zone -----------------------------------------------------------------


async def test_a_ring_sent_closed_and_open_describe_the_same_zone(
    world: dict[str, Any], zones: ZoneService
) -> None:
    """A map-drawing tool produces one and a GeoJSON export the other."""
    closed, _ = await zones.create(world["operator"].id, "closed", [*SQUARE, SQUARE[0]])
    opened, _ = await zones.create(world["operator"].id, "open", SQUARE)
    assert ring(closed.area) == ring(opened.area)


async def test_an_outline_that_crosses_itself_is_refused_not_repaired() -> None:
    """`buffer(0)` would return one of the two lobes, and which one is a guess."""
    bowtie = [(28.50, 77.30), (28.60, 77.40), (28.60, 77.30), (28.50, 77.40)]
    with pytest.raises(ValidationFailed) as excinfo:
        to_polygon(bowtie)
    assert "crosses itself" in str(excinfo.value)


async def test_a_ring_with_fewer_than_three_corners_is_refused() -> None:
    with pytest.raises(ValidationFailed):
        to_polygon([(28.50, 77.30), (28.60, 77.40), (28.50, 77.30)])


async def test_two_zones_cannot_share_a_name(world: dict[str, Any], zones: ZoneService) -> None:
    await zones.create(world["operator"].id, "sector_62", SQUARE)
    with pytest.raises(Conflict):
        await zones.create(world["operator"].id, "sector_62", SQUARE)


# --- derivation on the employee paths -------------------------------------------------


async def test_an_employee_created_in_a_zone_is_derived_into_it(
    world: dict[str, Any], zones: ZoneService, employees: EmployeeService
) -> None:
    zone, _ = await zones.create(world["operator"].id, "sector_62", SQUARE)
    employee = await employees.create_employee(
        world["operator"].id,
        world["client"].id,
        {
            "name": "Asha",
            "phone": unique_phone(),
            "office_id": world["office"].id,
            "home_location": to_point(*INSIDE),
        },
        caller_client_id=None,
    )
    assert employee.zone_id == zone.id


async def test_an_employee_who_moves_house_moves_zone(
    db_session: AsyncSession,
    world: dict[str, Any],
    zones: ZoneService,
    employees: EmployeeService,
) -> None:
    north = [(28.60, 77.30), (28.60, 77.40), (28.70, 77.40), (28.70, 77.30)]
    south, _ = await zones.create(world["operator"].id, "south", SQUARE)
    far_north, _ = await zones.create(world["operator"].id, "north", north)

    employee = await add_employee(db_session, world, INSIDE)
    await zones.rederive(world["operator"].id)
    # `rederive` is one UPDATE statement, so the identity map does not hear about it.
    await db_session.refresh(employee)
    assert employee.zone_id == south.id

    await employees.update_employee(
        world["operator"].id,
        employee.id,
        {"home_location": to_point(28.65, 77.35)},
        caller_client_id=None,
    )
    assert employee.zone_id == far_north.id


async def test_moving_out_of_every_zone_clears_the_derivation(
    db_session: AsyncSession,
    world: dict[str, Any],
    zones: ZoneService,
    employees: EmployeeService,
) -> None:
    zone, _ = await zones.create(world["operator"].id, "sector_62", SQUARE)
    employee = await add_employee(db_session, world, INSIDE)
    await zones.rederive(world["operator"].id)
    await db_session.refresh(employee)
    assert employee.zone_id == zone.id

    await employees.update_employee(
        world["operator"].id,
        employee.id,
        {"home_location": to_point(*OUTSIDE)},
        caller_client_id=None,
    )
    assert employee.zone_id is None


# --- the backfill: a zone drawn after the people ---------------------------------------


async def test_drawing_a_zone_derives_the_employees_who_already_existed(
    db_session: AsyncSession, world: dict[str, Any], zones: ZoneService
) -> None:
    """The whole point. A zone drawn today has to know who lives in it today, not from
    the next CSV upload onwards - a freshly drawn zone reporting zero employees is the
    kind of wrong that looks like a working feature."""
    inside = await add_employee(db_session, world, INSIDE, name="Asha")
    outside = await add_employee(db_session, world, OUTSIDE, name="Rahul")
    assert inside.zone_id is None

    zone, count = await zones.create(world["operator"].id, "sector_62", SQUARE)

    await db_session.refresh(inside)
    await db_session.refresh(outside)
    assert inside.zone_id == zone.id
    assert outside.zone_id is None
    assert count == 1


async def test_redrawing_a_zone_re_derives_who_is_in_it(
    db_session: AsyncSession, world: dict[str, Any], zones: ZoneService
) -> None:
    employee = await add_employee(db_session, world, (28.65, 77.35))
    zone, _ = await zones.create(world["operator"].id, "sector_62", SQUARE)
    await db_session.refresh(employee)
    assert employee.zone_id is None

    wider = [(28.50, 77.30), (28.50, 77.40), (28.70, 77.40), (28.70, 77.30)]
    _, count = await zones.update(world["operator"].id, zone.id, boundary=wider)
    await db_session.refresh(employee)
    assert employee.zone_id == zone.id
    assert count == 1


async def test_deactivating_a_zone_empties_it(
    db_session: AsyncSession, world: dict[str, Any], zones: ZoneService
) -> None:
    employee = await add_employee(db_session, world, INSIDE)
    zone, _ = await zones.create(world["operator"].id, "sector_62", SQUARE)
    await db_session.refresh(employee)
    assert employee.zone_id == zone.id

    _, count = await zones.update(world["operator"].id, zone.id, active=False)
    await db_session.refresh(employee)
    assert employee.zone_id is None
    assert count == 0


async def test_deleting_a_zone_a_mode_setting_uses_is_refused(
    db_session: AsyncSession, world: dict[str, Any], zones: ZoneService
) -> None:
    """`mode_setting.zone_id` is ON DELETE SET NULL, so the database would allow it
    silently - and the rule would quietly widen from one zone to every zone."""
    zone, _ = await zones.create(world["operator"].id, "sector_62", SQUARE)
    db_session.add(
        ModeSetting(
            id=uuid.uuid4(),
            operator_id=world["operator"].id,
            zone_id=zone.id,
            mode=str(Mode.semi_auto),
            created_at=NOW,
            updated_at=NOW,
        )
    )
    await db_session.flush()

    with pytest.raises(Conflict) as excinfo:
        await zones.delete(world["operator"].id, zone.id)
    assert "mode setting" in str(excinfo.value).lower()


async def test_deleting_an_unused_zone_clears_its_employees(
    db_session: AsyncSession, world: dict[str, Any], zones: ZoneService
) -> None:
    employee = await add_employee(db_session, world, INSIDE)
    zone, _ = await zones.create(world["operator"].id, "sector_62", SQUARE)
    await db_session.refresh(employee)
    assert employee.zone_id == zone.id

    await zones.delete(world["operator"].id, zone.id)
    await db_session.refresh(employee)
    assert employee.zone_id is None
    with pytest.raises(NotFound):
        await zones.update(world["operator"].id, zone.id, name="gone")


# --- what zones are for: a zone-scoped mode setting now resolves ------------------------


async def test_a_zone_scoped_mode_setting_resolves_now_that_zones_are_derived(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, zones: ZoneService
) -> None:
    """B24 built the precedence and B27 makes level 6 reachable. Until now a
    zone-scoped rule could be written and could never match, because every employee's
    `zone_id` was null."""
    zone, _ = await zones.create(world["operator"].id, "sector_62", SQUARE)
    # Added straight to the session rather than through `EmployeeService`, so the
    # derivation has to come from the zone side - which is the path an operator who
    # imported their people before drawing a zone actually takes.
    employee = await add_employee(db_session, world, INSIDE)
    await zones.rederive(world["operator"].id)
    await db_session.refresh(employee)
    assert employee.zone_id == zone.id

    db_session.add(
        ModeSetting(
            id=uuid.uuid4(),
            operator_id=world["operator"].id,
            zone_id=zone.id,
            mode=str(Mode.semi_auto),
            created_at=NOW,
            updated_at=NOW,
        )
    )
    request = RideRequest(
        id=uuid.uuid4(),
        operator_id=world["operator"].id,
        client_id=world["client"].id,
        employee_id=employee.id,
        direction=str(Direction.to_office),
        office_id=world["office"].id,
        location=to_point(*INSIDE),
        requested_time=NOW,
        urgency="medium",
        status="queued",
        queued_at=NOW,
        expires_at=NOW,
    )
    db_session.add(request)
    await db_session.flush()

    resolution = await ModeService(db_session, clock).resolve_for_request(request)
    assert resolution.mode is Mode.semi_auto
    assert resolution.reason is ModeReason.zone


# --- the geometry helpers round-trip ------------------------------------------------


def test_a_polygon_read_back_has_the_corners_it_was_given() -> None:
    """lat/lng versus x/y is exactly the detail that gets flipped in a copy."""
    assert ring(to_polygon(SQUARE)) == SQUARE


def test_a_polygon_written_by_hand_reads_back_the_same_way() -> None:
    """Guards the other direction: `tests.builders.square` and the fixtures elsewhere
    build polygons with shapely directly, in (lng, lat) order."""
    by_hand = from_shape(
        ShapelyPolygon([(77.30, 28.50), (77.40, 28.50), (77.40, 28.60), (77.30, 28.60)]),
        srid=4326,
    )
    assert ring(by_hand) == SQUARE


def test_the_employee_role_cannot_manage_zones() -> None:
    """Server-side authorisation, hard rule 3: hiding the screen is not security."""
    from app.modules.auth.permissions import Permission, permissions_for

    assert Permission.zone_manage in permissions_for(Role.operator_admin)
    assert Permission.zone_manage not in permissions_for(Role.employee)
