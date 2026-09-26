"""The dispatch board and manual assignment against a real database (B14).

Acceptance: assigning notifies employee and driver, adding to a full vehicle is rejected,
and the worked scenarios of SUP-02/SUP-03 behave as the stories describe.

The world here is deliberately geographic: one office, riders at 1 km, 3 km and 7 km, and
vehicles parked at known points, so "the nearest cab" and "on the way" mean something a
person can check on a map rather than something only the test knows.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.events import RecordingEventPublisher
from app.core.geo import to_point
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import Direction, Role, Urgency, VehicleType
from app.domain.errors import Conflict
from app.domain.state_machines import (
    Actor,
    RequestStatus,
    StopKind,
    StopStatus,
    TripStatus,
    VehicleStatus,
)
from app.main import create_app
from app.modules.dispatch.models import Trip, TripEvent, TripStop
from app.modules.dispatch.service import DispatchService
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle
from app.modules.requests.models import RideRequest
from app.modules.routing.approx import ApproxRoutingProvider
from app.modules.routing.service import EtaService
from app.modules.tracking.models import LocationPing
from tests.builders import (
    make_client,
    make_employee,
    make_office,
    make_operator,
    make_user,
    make_user_role,
    unique_phone,
)

NOW = datetime(2026, 9, 25, 9, 0, tzinfo=UTC)
JWT_SECRET = "dispatch-tests-secret-0123456789abc"

OFFICE = (28.5000, 77.4000)
NEAR = (28.5100, 77.4000)  # ~1.1 km from the office
MID = (28.5300, 77.4000)  # ~3.3 km
FAR = (28.5600, 77.4000)  # ~6.7 km


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def events() -> RecordingEventPublisher:
    return RecordingEventPublisher()


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
    """One operator, one client, one office, three employees and two cabs on duty."""
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()

    customer = make_client(operator.id)
    db_session.add(customer)
    await db_session.flush()

    office = make_office(operator.id, customer.id)
    office.location = to_point(*OFFICE)
    db_session.add(office)
    await db_session.flush()

    employees = {}
    for label, place in (("near", NEAR), ("mid", MID), ("far", FAR)):
        employee = make_employee(operator.id, customer.id, office.id, name=label.title())
        employee.home_location = to_point(*place)
        db_session.add(employee)
        employees[label] = employee
    await db_session.flush()

    supervisor = make_user(name="Sunil", phone=unique_phone())
    db_session.add(supervisor)
    await db_session.flush()
    db_session.add(make_user_role(supervisor.id, Role.supervisor, operator_id=operator.id))

    vehicles = {}
    drivers = {}
    for label, capacity, place in (("alpha", 4, NEAR), ("bravo", 4, FAR)):
        vehicle = Vehicle(
            operator_id=operator.id,
            registration_no=f"UP16{label[:2].upper()}0001",
            vehicle_type=VehicleType.sedan_4,
            seat_capacity=capacity,
            status=VehicleStatus.available,
        )
        db_session.add(vehicle)
        await db_session.flush()

        driver_user = make_user(name=f"Driver {label}", phone=unique_phone())
        db_session.add(driver_user)
        await db_session.flush()
        db_session.add(make_user_role(driver_user.id, Role.driver, operator_id=operator.id))

        driver = Driver(
            operator_id=operator.id,
            user_id=driver_user.id,
            name=f"Driver {label}",
            phone=unique_phone(),
            default_vehicle_id=vehicle.id,
        )
        db_session.add(driver)
        await db_session.flush()

        db_session.add(
            DutySession(
                operator_id=operator.id,
                driver_id=driver.id,
                vehicle_id=vehicle.id,
                started_at=NOW - timedelta(hours=1),
            )
        )
        db_session.add(
            LocationPing(
                operator_id=operator.id,
                vehicle_id=vehicle.id,
                recorded_at=NOW - timedelta(seconds=5),
                received_at=NOW - timedelta(seconds=5),
                location=to_point(*place),
                source="sim",
            )
        )
        vehicles[label] = vehicle
        drivers[label] = driver
    await db_session.flush()

    return {
        "operator_id": operator.id,
        "client_id": customer.id,
        "office_id": office.id,
        "employees": employees,
        "vehicles": vehicles,
        "drivers": drivers,
        "supervisor_user_id": supervisor.id,
    }


async def make_request(
    db_session: AsyncSession,
    world: dict[str, Any],
    who: str = "mid",
    direction: Direction = Direction.to_office,
    status: RequestStatus = RequestStatus.queued,
    **extra: Any,
) -> RideRequest:
    employee = world["employees"][who]
    request = RideRequest(
        operator_id=world["operator_id"],
        client_id=world["client_id"],
        employee_id=employee.id,
        direction=direction,
        office_id=world["office_id"],
        location=employee.home_location,
        requested_time=NOW + timedelta(minutes=5),
        urgency=Urgency.medium,
        status=status,
        expires_at=NOW + timedelta(hours=2),
        **extra,
    )
    db_session.add(request)
    await db_session.flush()
    return request


@pytest_asyncio.fixture
async def app(
    database_ready: bool,
    db_session: AsyncSession,
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> AsyncIterator[FastAPI]:
    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
        routing_provider="approx",
    )
    application = create_app(settings=settings, clock=clock)
    application.state.events = events

    class _Factory:
        def __call__(self) -> object:
            return _NoClose(db_session)

    application.state.session_factory = _Factory()
    yield application


class _NoClose:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


@pytest.fixture
def supervisor(world: dict[str, Any], clock: FakeClock) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=world["supervisor_user_id"],
        role=str(Role.supervisor),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
    )
    return {"Authorization": f"Bearer {token}"}


# --- the board (SUP-02) ------------------------------------------------------------


async def test_the_queue_lists_open_requests_oldest_first(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    first = await make_request(db_session, world, "far")
    second = await make_request(db_session, world, "near")

    response = await client.get("/dispatch/requests", headers=supervisor)

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [str(first.id), str(second.id)]


async def test_the_queue_can_be_filtered_by_status(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    await make_request(db_session, world, "far", status=RequestStatus.queued)
    cancelled = await make_request(db_session, world, "near", status=RequestStatus.cancelled)

    response = await client.get("/dispatch/requests?status=cancelled", headers=supervisor)

    ids = [item["id"] for item in response.json()["items"]]
    assert ids == [str(cancelled.id)]


async def test_a_cancelled_request_is_not_on_the_board_by_default(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    await make_request(db_session, world, "near", status=RequestStatus.cancelled)

    response = await client.get("/dispatch/requests", headers=supervisor)
    assert response.json()["items"] == []


async def test_the_queue_is_scoped_to_the_operator(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """Another operator's queue is not a thing this supervisor can see at all."""
    other = make_operator("Rival Cabs")
    db_session.add(other)
    await db_session.flush()
    other_client = make_client(other.id)
    db_session.add(other_client)
    await db_session.flush()
    other_office = make_office(other.id, other_client.id)
    db_session.add(other_office)
    await db_session.flush()
    other_employee = make_employee(other.id, other_client.id, other_office.id)
    db_session.add(other_employee)
    await db_session.flush()
    db_session.add(
        RideRequest(
            operator_id=other.id,
            client_id=other_client.id,
            employee_id=other_employee.id,
            direction=Direction.to_office,
            office_id=other_office.id,
            location=other_employee.home_location,
            requested_time=NOW,
            status=RequestStatus.queued,
            expires_at=NOW + timedelta(hours=2),
        )
    )
    await db_session.flush()

    response = await client.get("/dispatch/requests", headers=supervisor)
    assert response.json()["items"] == []


# --- the live map (SUP-01) ----------------------------------------------------------


async def test_vehicles_report_their_last_position(
    client: AsyncClient, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    response = await client.get("/dispatch/vehicles", headers=supervisor)

    assert response.status_code == 200
    items = {item["registration_no"]: item for item in response.json()["items"]}
    assert len(items) == 2
    alpha = items[world["vehicles"]["alpha"].registration_no]
    assert alpha["position"]["lat"] == pytest.approx(NEAR[0], abs=1e-6)
    assert alpha["stale"] is False
    assert alpha["seats_free"] == 4


async def test_a_vehicle_with_an_old_ping_is_stale(
    client: AsyncClient, world: dict[str, Any], supervisor: dict[str, str], clock: FakeClock
) -> None:
    """`stale_gps_seconds` default is 60; a supervisor must see the difference."""
    clock.advance(timedelta(minutes=2))

    response = await client.get("/dispatch/vehicles", headers=supervisor)
    assert all(item["stale"] for item in response.json()["items"])


async def test_a_vehicle_that_never_pinged_has_no_position(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    db_session.add(
        Vehicle(
            operator_id=world["operator_id"],
            registration_no="UP16ZZ9999",
            vehicle_type=VehicleType.sedan_4,
            seat_capacity=4,
            status=VehicleStatus.off_duty,
        )
    )
    await db_session.flush()

    response = await client.get("/dispatch/vehicles", headers=supervisor)
    silent = next(
        item for item in response.json()["items"] if item["registration_no"] == "UP16ZZ9999"
    )
    assert silent["position"] is None
    assert silent["stale"] is True


# --- candidates ------------------------------------------------------------------------


async def test_candidates_are_returned_nearest_first(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    request = await make_request(db_session, world, "near")

    response = await client.get(f"/dispatch/requests/{request.id}/candidates", headers=supervisor)

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    # The cab parked at NEAR is on the rider's doorstep; the one at FAR is 6 km away.
    assert items[0]["registration_no"] == world["vehicles"]["alpha"].registration_no
    assert items[0]["eta_to_pickup_seconds"] < items[1]["eta_to_pickup_seconds"]


async def test_a_candidate_reports_seats_and_the_trip_it_would_join(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    request = await make_request(db_session, world, "near")

    items = (
        await client.get(f"/dispatch/requests/{request.id}/candidates", headers=supervisor)
    ).json()["items"]

    assert items[0]["seats_free_after"] == 3
    assert items[0]["new_trip"] is True
    assert items[0]["trip_id"] is None


async def test_candidates_flag_an_approximate_eta(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """Tests run on the `approx` provider, and the client must be told (ADR-0010)."""
    request = await make_request(db_session, world, "near")

    items = (
        await client.get(f"/dispatch/requests/{request.id}/candidates", headers=supervisor)
    ).json()["items"]

    assert all(item["eta_approximate"] is True for item in items)


async def test_an_off_duty_vehicle_is_not_a_candidate(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    world["vehicles"]["bravo"].status = VehicleStatus.off_duty
    await db_session.flush()
    request = await make_request(db_session, world, "near")

    items = (
        await client.get(f"/dispatch/requests/{request.id}/candidates", headers=supervisor)
    ).json()["items"]

    assert [item["registration_no"] for item in items] == [
        world["vehicles"]["alpha"].registration_no
    ]


async def test_candidates_for_another_operators_request_are_a_404(
    client: AsyncClient, supervisor: dict[str, str]
) -> None:
    response = await client.get(f"/dispatch/requests/{uuid.uuid4()}/candidates", headers=supervisor)
    assert response.status_code == 404


async def test_a_vip_rider_sees_the_violation_on_a_normal_cab(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    world["employees"]["near"].is_vip = True
    await db_session.flush()
    request = await make_request(db_session, world, "near")

    items = (
        await client.get(f"/dispatch/requests/{request.id}/candidates", headers=supervisor)
    ).json()["items"]

    assert all("vip_needs_vip_vehicle" in item["violations"] for item in items)


# --- manual assignment (SUP-03) ---------------------------------------------------------


def _service(session: AsyncSession, clock: FakeClock) -> DispatchService:
    """The service with the offline `approx` provider, for the few service-level tests."""
    return DispatchService(session, clock, EtaService(ApproxRoutingProvider(clock), clock))


async def assign(
    client: AsyncClient,
    supervisor: dict[str, str],
    request: RideRequest,
    vehicle: Vehicle,
    **extra: Any,
) -> Any:
    body = {"request_id": str(request.id), "vehicle_id": str(vehicle.id), **extra}
    return await client.post("/dispatch/assign", json=body, headers=supervisor)


async def test_assigning_creates_a_trip_with_stops(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    request = await make_request(db_session, world, "mid")

    response = await assign(client, supervisor, request, world["vehicles"]["alpha"])

    assert response.status_code == 200
    trip = response.json()
    assert trip["status"] == str(TripStatus.planned)
    assert trip["mode_used"] == "manual"
    assert [stop["stop_type"] for stop in trip["stops"]] == [
        str(StopKind.pickup),
        str(StopKind.drop),
    ]
    assert trip["stops"][0]["sequence"] == 1
    assert trip["stops"][1]["sequence"] == 2


async def test_assigning_moves_the_request_and_the_vehicle(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    request = await make_request(db_session, world, "mid")

    await assign(client, supervisor, request, world["vehicles"]["alpha"])
    await db_session.refresh(request)
    await db_session.refresh(world["vehicles"]["alpha"])

    assert request.status == str(RequestStatus.assigned)
    assert request.trip_id is not None
    assert world["vehicles"]["alpha"].status == str(VehicleStatus.on_trip)


async def test_assigning_notifies_the_employee_and_the_driver(
    client: AsyncClient,
    db_session: AsyncSession,
    world: dict[str, Any],
    supervisor: dict[str, str],
    events: RecordingEventPublisher,
) -> None:
    """B14 acceptance, SUP-03: both sides hear about it."""
    employee_user = make_user(name="Rider", phone=unique_phone())
    db_session.add(employee_user)
    await db_session.flush()
    world["employees"]["mid"].user_id = employee_user.id
    await db_session.flush()

    request = await make_request(db_session, world, "mid")
    await assign(client, supervisor, request, world["vehicles"]["alpha"])

    assert "request.assigned" in events.names()
    assert "trip.assigned" in events.names()
    driver_user_id = world["drivers"]["alpha"].user_id
    assert f"user.{driver_user_id}" in events.channels_for("trip.assigned")
    assert f"user.{employee_user.id}" in events.channels_for("request.assigned")


async def test_the_assignment_is_recorded_as_an_event(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    request = await make_request(db_session, world, "mid")
    await assign(client, supervisor, request, world["vehicles"]["alpha"], note="phoned in")

    event = (await db_session.execute(select(TripEvent))).scalars().one()
    data = event.data or {}
    assert event.to_status == str(TripStatus.planned)
    assert data["action"] == "trip_created"
    assert data["request_id"] == str(request.id)
    assert event.at == NOW


async def test_accepted_violations_are_recorded(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """ADR-0011: an override against the rules must stay visible afterwards."""
    world["employees"]["mid"].is_vip = True
    await db_session.flush()
    request = await make_request(db_session, world, "mid")

    await assign(client, supervisor, request, world["vehicles"]["alpha"])

    event = (await db_session.execute(select(TripEvent))).scalars().one()
    assert "vip_needs_vip_vehicle" in (event.data or {})["violations_accepted"]


async def test_a_second_rider_joins_the_existing_trip(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    first = await make_request(db_session, world, "far")
    created = (await assign(client, supervisor, first, world["vehicles"]["alpha"])).json()

    second = await make_request(db_session, world, "mid")
    response = await assign(
        client, supervisor, second, world["vehicles"]["alpha"], trip_id=created["id"]
    )

    assert response.status_code == 200
    trip = response.json()
    assert trip["id"] == created["id"]
    assert len(trip["stops"]) == 4
    assert await db_session.scalar(select(func.count()).select_from(Trip)) == 1


async def test_the_new_rider_is_sequenced_by_least_added_time(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """The rider at MID is on the way in from FAR, so they are picked up second."""
    far = await make_request(db_session, world, "far")
    created = (await assign(client, supervisor, far, world["vehicles"]["alpha"])).json()

    mid = await make_request(db_session, world, "mid")
    trip = (
        await assign(client, supervisor, mid, world["vehicles"]["alpha"], trip_id=created["id"])
    ).json()

    pickups = [stop for stop in trip["stops"] if stop["stop_type"] == str(StopKind.pickup)]
    assert [stop["request_id"] for stop in pickups] == [str(far.id), str(mid.id)]


async def test_joining_a_trip_reports_the_added_minutes(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """SUP-03: "the system shows the added minutes for existing riders"."""
    far = await make_request(db_session, world, "far")
    await assign(client, supervisor, far, world["vehicles"]["alpha"])

    mid = await make_request(db_session, world, "mid")
    items = (
        await client.get(f"/dispatch/requests/{mid.id}/candidates", headers=supervisor)
    ).json()["items"]

    joining = next(item for item in items if item["trip_id"] is not None)
    assert joining["new_trip"] is False
    assert [entry["request_id"] for entry in joining["added_minutes_existing"]] == [str(far.id)]


async def test_adding_to_a_full_vehicle_is_rejected(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """B14 acceptance. Capacity is the one hard rule that refuses (ADR-0011)."""
    vehicle = world["vehicles"]["alpha"]
    vehicle.seat_capacity = 1
    await db_session.flush()

    first = await make_request(db_session, world, "far")
    created = (await assign(client, supervisor, first, vehicle)).json()

    second = await make_request(db_session, world, "mid")
    response = await assign(client, supervisor, second, vehicle, trip_id=created["id"])

    assert response.status_code == 409
    assert "seat" in response.json()["message"].lower()


async def test_a_rejected_assignment_leaves_the_request_queued(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock
) -> None:
    """A refusal must change nothing at all, not "almost nothing".

    Driven through the service rather than HTTP: a refused request rolls its whole
    session back, which in this harness would take the fixture data with it and leave
    nothing to assert against.
    """
    service = _service(db_session, clock)
    vehicle = world["vehicles"]["alpha"]
    vehicle.seat_capacity = 1
    await db_session.flush()

    first = await make_request(db_session, world, "far")
    trip = await service.assign(
        operator_id=world["operator_id"],
        request_id=first.id,
        vehicle_id=vehicle.id,
        actor=Actor.supervisor,
        actor_user_id=world["supervisor_user_id"],
    )

    second = await make_request(db_session, world, "mid")
    with pytest.raises(Conflict):
        await service.assign(
            operator_id=world["operator_id"],
            request_id=second.id,
            vehicle_id=vehicle.id,
            actor=Actor.supervisor,
            actor_user_id=world["supervisor_user_id"],
            trip_id=trip.id,
        )

    assert second.status == str(RequestStatus.queued)
    assert second.trip_id is None
    assert len(await service.stops_of(trip.id)) == 2


async def test_an_already_assigned_request_cannot_be_assigned_again(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    request = await make_request(db_session, world, "mid")
    await assign(client, supervisor, request, world["vehicles"]["alpha"])

    response = await assign(client, supervisor, request, world["vehicles"]["bravo"])
    assert response.status_code == 409


async def test_assigning_a_vehicle_with_no_driver_on_duty_is_rejected(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """A trip needs a driver; `trip.driver_id` is not nullable for a reason."""
    parked = Vehicle(
        operator_id=world["operator_id"],
        registration_no="UP16QQ0001",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
        status=VehicleStatus.available,
    )
    db_session.add(parked)
    await db_session.flush()

    request = await make_request(db_session, world, "mid")
    response = await assign(client, supervisor, request, parked)

    assert response.status_code == 409
    assert "driver" in response.json()["message"].lower()


async def test_another_operators_vehicle_is_a_404(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    other = make_operator("Rival Cabs")
    db_session.add(other)
    await db_session.flush()
    stranger = Vehicle(
        operator_id=other.id,
        registration_no="DL01AA0001",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
        status=VehicleStatus.available,
    )
    db_session.add(stranger)
    await db_session.flush()

    request = await make_request(db_session, world, "mid")
    response = await assign(client, supervisor, request, stranger)

    assert response.status_code == 404


async def test_a_trip_belonging_to_another_vehicle_is_refused(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    first = await make_request(db_session, world, "far")
    created = (await assign(client, supervisor, first, world["vehicles"]["alpha"])).json()

    second = await make_request(db_session, world, "mid")
    response = await assign(
        client, supervisor, second, world["vehicles"]["bravo"], trip_id=created["id"]
    )

    assert response.status_code == 409


async def test_a_from_office_trip_collects_at_the_office(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    request = await make_request(db_session, world, "mid", direction=Direction.from_office)

    trip = (await assign(client, supervisor, request, world["vehicles"]["alpha"])).json()

    pickup, drop = trip["stops"]
    assert pickup["location"]["lat"] == pytest.approx(OFFICE[0], abs=1e-6)
    assert drop["location"]["lat"] == pytest.approx(MID[0], abs=1e-6)


async def test_stops_carry_an_eta(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    request = await make_request(db_session, world, "mid")

    trip = (await assign(client, supervisor, request, world["vehicles"]["alpha"])).json()

    assert trip["stops"][0]["planned_eta"] is not None
    assert trip["stops"][0]["eta_approximate"] is True


async def test_a_no_sharing_request_makes_the_trip_exclusive(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    request = await make_request(db_session, world, "mid", no_sharing=True)

    trip = (await assign(client, supervisor, request, world["vehicles"]["alpha"])).json()
    assert trip["pooling_blocked"] is True


async def test_an_existing_stop_that_already_happened_is_not_rewritten(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """A driver who has arrived somewhere cannot have that undone by a later insertion."""
    far = await make_request(db_session, world, "far")
    created = (await assign(client, supervisor, far, world["vehicles"]["alpha"])).json()

    pickup = await db_session.scalar(
        select(TripStop)
        .where(TripStop.trip_id == uuid.UUID(created["id"]))
        .where(TripStop.stop_type == str(StopKind.pickup))
    )
    assert pickup is not None
    pickup.status = StopStatus.arrived
    pickup.arrived_at = NOW
    await db_session.flush()
    kept_id = pickup.id

    mid = await make_request(db_session, world, "mid")
    await assign(client, supervisor, mid, world["vehicles"]["alpha"], trip_id=created["id"])
    await db_session.refresh(pickup)

    assert pickup.id == kept_id
    assert pickup.status == str(StopStatus.arrived)
    assert pickup.arrived_at == NOW


# --- automation pause (SUP-05) ------------------------------------------------------


async def test_automation_starts_unpaused(
    client: AsyncClient, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    response = await client.get("/dispatch/automation", headers=supervisor)
    assert response.json() == {"automation_paused": False}


async def test_a_supervisor_can_pause_automation(
    client: AsyncClient, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    response = await client.put(
        "/dispatch/automation",
        json={"automation_paused": True, "reason_code": "safety"},
        headers=supervisor,
    )

    assert response.status_code == 200
    assert response.json() == {"automation_paused": True}
    assert (await client.get("/dispatch/automation", headers=supervisor)).json() == {
        "automation_paused": True
    }


async def test_pausing_tells_every_supervisor(
    client: AsyncClient,
    world: dict[str, Any],
    supervisor: dict[str, str],
    events: RecordingEventPublisher,
) -> None:
    """SUP-05: "the pause is visible to all supervisors"."""
    await client.put(
        "/dispatch/automation",
        json={"automation_paused": True, "reason_code": "safety"},
        headers=supervisor,
    )

    assert f"operator.{world['operator_id']}.requests" in events.channels_for("automation.changed")


async def test_pausing_requires_a_reason(
    client: AsyncClient, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    response = await client.put(
        "/dispatch/automation", json={"automation_paused": True}, headers=supervisor
    )
    assert response.status_code == 422


async def test_the_pause_does_not_leak_between_operators(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    other = make_operator("Rival Cabs")
    db_session.add(other)
    await db_session.flush()

    await client.put(
        "/dispatch/automation",
        json={"automation_paused": True, "reason_code": "safety"},
        headers=supervisor,
    )
    await db_session.refresh(other)

    assert other.automation_paused is False


# --- permissions -----------------------------------------------------------------------


@pytest.fixture
def driver_headers(world: dict[str, Any], clock: FakeClock) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=world["drivers"]["alpha"].user_id,
        role=str(Role.driver),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
    )
    return {"Authorization": f"Bearer {token}"}


async def test_a_driver_cannot_see_the_dispatch_queue(
    client: AsyncClient, driver_headers: dict[str, str]
) -> None:
    response = await client.get("/dispatch/requests", headers=driver_headers)
    assert response.status_code == 403


async def test_a_driver_cannot_assign(
    client: AsyncClient,
    db_session: AsyncSession,
    world: dict[str, Any],
    driver_headers: dict[str, str],
) -> None:
    request = await make_request(db_session, world, "mid")

    response = await client.post(
        "/dispatch/assign",
        json={"request_id": str(request.id), "vehicle_id": str(world["vehicles"]["alpha"].id)},
        headers=driver_headers,
    )
    assert response.status_code == 403


async def test_assigning_needs_a_token(client: AsyncClient) -> None:
    response = await client.post(
        "/dispatch/assign",
        json={"request_id": str(uuid.uuid4()), "vehicle_id": str(uuid.uuid4())},
    )
    assert response.status_code == 401


async def test_adding_a_rider_keeps_the_existing_stop_ids(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """A driver already holds these ids; changing them 404s their next tap.

    Found by the S02 simulator run, where a driver's `arrived` came back "Stop not found"
    because another rider had been added to the trip meanwhile. A re-sequenced stop is
    the same stop.
    """
    far = await make_request(db_session, world, "far")
    created = (await assign(client, supervisor, far, world["vehicles"]["alpha"])).json()
    before = {stop["id"] for stop in created["stops"]}

    mid = await make_request(db_session, world, "mid")
    after = (
        await assign(client, supervisor, mid, world["vehicles"]["alpha"], trip_id=created["id"])
    ).json()

    assert before <= {stop["id"] for stop in after["stops"]}


async def test_the_sequence_still_has_no_gaps_or_duplicates_after_an_insertion(
    client: AsyncClient, db_session: AsyncSession, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """`(trip_id, sequence)` is unique, so re-ordering in place must not collide."""
    far = await make_request(db_session, world, "far")
    created = (await assign(client, supervisor, far, world["vehicles"]["alpha"])).json()

    mid = await make_request(db_session, world, "mid")
    trip = (
        await assign(client, supervisor, mid, world["vehicles"]["alpha"], trip_id=created["id"])
    ).json()

    sequences = [stop["sequence"] for stop in trip["stops"]]
    assert sequences == list(range(1, len(sequences) + 1))
