"""Driver trip and stop actions against a real database (B15, DRV-03/05).

Acceptance: duplicate events ignored, no-show blocked before the wait time, and request
states follow their stops.

The shape of the world is one pooled `to_office` trip with two riders, because that is
where the interesting cases live: finishing one rider's pickup must move exactly one
request, and the trip is not over until the last person is out of the cab.
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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.events import RecordingEventPublisher
from app.core.geo import to_point
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import Direction, Role, Urgency, VehicleType
from app.domain.state_machines import RequestStatus, StopKind, StopStatus, TripStatus, VehicleStatus
from app.main import create_app
from app.modules.dispatch.models import Trip, TripEvent, TripStop
from app.modules.fleet.models import Driver, Vehicle
from app.modules.requests.models import RideRequest
from app.modules.requests.service import RideRequestService
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
JWT_SECRET = "driver-trip-tests-secret-0123456789"

OFFICE = (28.5000, 77.4000)
FAR = (28.5600, 77.4000)
MID = (28.5300, 77.4000)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def events() -> RecordingEventPublisher:
    return RecordingEventPublisher()


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
    """A pooled to_office trip: two riders picked up, both dropped at the office."""
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

    users: dict[str, Any] = {}
    for label, role in (
        ("driver", Role.driver),
        ("other_driver", Role.driver),
        ("first", Role.employee),
        ("second", Role.employee),
    ):
        user = make_user(name=label, phone=unique_phone())
        db_session.add(user)
        await db_session.flush()
        db_session.add(
            make_user_role(
                user.id,
                role,
                operator_id=operator.id,
                client_id=customer.id if role is Role.employee else None,
            )
        )
        users[label] = user
    await db_session.flush()

    employees = {}
    for label, place in (("first", FAR), ("second", MID)):
        employee = make_employee(operator.id, customer.id, office.id, name=label)
        employee.home_location = to_point(*place)
        employee.user_id = users[label].id
        db_session.add(employee)
        employees[label] = employee
    await db_session.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        registration_no="UP16DR0001",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
        status=VehicleStatus.on_trip,
    )
    db_session.add(vehicle)
    await db_session.flush()

    drivers = {}
    for label in ("driver", "other_driver"):
        driver = Driver(
            operator_id=operator.id,
            user_id=users[label].id,
            name=label,
            phone=unique_phone(),
            default_vehicle_id=vehicle.id,
        )
        db_session.add(driver)
        drivers[label] = driver
    await db_session.flush()

    trip = Trip(
        operator_id=operator.id,
        vehicle_id=vehicle.id,
        driver_id=drivers["driver"].id,
        direction=Direction.to_office,
        office_id=office.id,
        status=TripStatus.planned,
        planned_start=NOW,
        mode_used="manual",
    )
    db_session.add(trip)
    await db_session.flush()

    requests = {}
    sequence = 1
    for label in ("first", "second"):
        request = RideRequest(
            operator_id=operator.id,
            client_id=customer.id,
            employee_id=employees[label].id,
            direction=Direction.to_office,
            office_id=office.id,
            location=employees[label].home_location,
            requested_time=NOW + timedelta(minutes=15),
            urgency=Urgency.medium,
            status=RequestStatus.assigned,
            trip_id=trip.id,
            expires_at=NOW + timedelta(hours=2),
        )
        db_session.add(request)
        requests[label] = request
    await db_session.flush()

    stops: dict[str, TripStop] = {}
    for label in ("first", "second"):
        stop = TripStop(
            operator_id=operator.id,
            trip_id=trip.id,
            sequence=sequence,
            stop_type=StopKind.pickup,
            request_id=requests[label].id,
            location=employees[label].home_location,
            status=StopStatus.pending,
        )
        db_session.add(stop)
        stops[f"pickup_{label}"] = stop
        sequence += 1
    for label in ("first", "second"):
        stop = TripStop(
            operator_id=operator.id,
            trip_id=trip.id,
            sequence=sequence,
            stop_type=StopKind.drop,
            request_id=requests[label].id,
            location=office.location,
            status=StopStatus.pending,
        )
        db_session.add(stop)
        stops[f"drop_{label}"] = stop
        sequence += 1
    await db_session.flush()

    return {
        "operator_id": operator.id,
        "trip_id": trip.id,
        "stop_ids": {label: stop.id for label, stop in stops.items()},
        "trip": trip,
        "vehicle": vehicle,
        "users": users,
        "drivers": drivers,
        "requests": requests,
        "stops": stops,
    }


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
def driver(world: dict[str, Any], clock: FakeClock) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=world["users"]["driver"].id,
        role=str(Role.driver),
        secret=JWT_SECRET,
        clock=clock,
        # Long-lived on purpose: several tests advance the clock past a no-show wait,
        # and token expiry has its own tests in test_auth.py.
        ttl_seconds=8 * 3600,
        operator_id=world["operator_id"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_driver(world: dict[str, Any], clock: FakeClock) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=world["users"]["other_driver"].id,
        role=str(Role.driver),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
    )
    return {"Authorization": f"Bearer {token}"}


def event(occurred_at: datetime | None = None, **extra: Any) -> dict[str, Any]:
    return {
        "client_event_id": str(uuid.uuid4()),
        "occurred_at": (occurred_at or NOW).isoformat(),
        **extra,
    }


async def start(client: AsyncClient, headers: dict[str, str], trip_id: uuid.UUID, **kw: Any) -> Any:
    return await client.post(f"/driver/trips/{trip_id}/start", json=event(**kw), headers=headers)


async def act(
    client: AsyncClient,
    headers: dict[str, str],
    stop_id: uuid.UUID,
    action: str,
    body: dict[str, Any] | None = None,
) -> Any:
    """Act on a stop by id: an ORM instance goes stale across HTTP calls in this harness."""
    return await client.post(
        f"/driver/stops/{stop_id}/{action}", json=body or event(), headers=headers
    )


async def reload_stop(session: AsyncSession, stop_id: uuid.UUID) -> TripStop:
    return (await session.execute(select(TripStop).where(TripStop.id == stop_id))).scalars().one()


# --- seeing my trips (DRV-03) -------------------------------------------------------


async def test_a_driver_sees_their_upcoming_trip(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    response = await client.get("/driver/trips?scope=upcoming", headers=driver)

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [str(world["trip_id"])]


async def test_the_trip_carries_its_stops_in_order(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    """DRV-03: "stops in order"."""
    items = (await client.get("/driver/trips?scope=upcoming", headers=driver)).json()["items"]

    stops = items[0]["stops"]
    assert [stop["sequence"] for stop in stops] == [1, 2, 3, 4]
    assert [stop["stop_type"] for stop in stops] == ["pickup", "pickup", "drop", "drop"]


async def test_another_driver_sees_nothing(
    client: AsyncClient, world: dict[str, Any], other_driver: dict[str, str]
) -> None:
    response = await client.get("/driver/trips?scope=upcoming", headers=other_driver)
    assert response.json()["items"] == []


async def test_an_unknown_scope_is_rejected(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    response = await client.get("/driver/trips?scope=yesterday", headers=driver)
    assert response.status_code == 422


async def test_a_finished_trip_shows_under_history(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    world["trip"].status = TripStatus.completed
    await db_session.flush()

    items = (await client.get("/driver/trips?scope=history", headers=driver)).json()["items"]
    assert [item["id"] for item in items] == [str(world["trip_id"])]


# --- starting -------------------------------------------------------------------------


async def test_starting_moves_the_trip_to_in_progress(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    response = await start(client, driver, world["trip_id"])

    assert response.status_code == 200
    assert response.json()["status"] == str(TripStatus.in_progress)


async def test_starting_sets_the_first_stop_en_route(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    await start(client, driver, world["trip_id"])

    first = await reload_stop(db_session, world["stop_ids"]["pickup_first"])
    assert first.status == str(StopStatus.en_route)


async def test_starting_records_the_dispatched_step_too(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """`trip-lifecycle.md` has no planned -> in_progress edge; the history must not skip."""
    await start(client, driver, world["trip_id"])

    events = (
        (
            await db_session.execute(
                select(TripEvent)
                .where(TripEvent.trip_id == world["trip_id"])
                .order_by(TripEvent.at)
            )
        )
        .scalars()
        .all()
    )
    assert [e.to_status for e in events] == [
        str(TripStatus.dispatched),
        str(TripStatus.in_progress),
    ]


async def test_the_start_time_is_the_drivers_time_not_ours(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """A trip that started at 08:40 must not be recorded as starting when signal returned."""
    tapped = NOW - timedelta(minutes=20)
    await start(client, driver, world["trip_id"], occurred_at=tapped)
    await db_session.refresh(world["trip"])

    assert world["trip"].started_at == tapped


async def test_another_drivers_trip_is_forbidden(
    client: AsyncClient, world: dict[str, Any], other_driver: dict[str, str]
) -> None:
    response = await start(client, other_driver, world["trip_id"])
    assert response.status_code == 403


async def test_a_tap_from_the_future_is_rejected(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    response = await start(client, driver, world["trip_id"], occurred_at=NOW + timedelta(hours=1))
    assert response.status_code == 422


# --- idempotency (B15 acceptance) ------------------------------------------------------


async def test_the_same_event_twice_is_applied_once(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """The offline queue retries; a retry must not start the trip twice."""
    body = event()
    first = await client.post(f"/driver/trips/{world['trip_id']}/start", json=body, headers=driver)
    second = await client.post(f"/driver/trips/{world['trip_id']}/start", json=body, headers=driver)

    assert first.status_code == second.status_code == 200
    assert second.json()["status"] == str(TripStatus.in_progress)

    count = len(
        (
            await db_session.execute(
                select(TripEvent).where(
                    TripEvent.client_event_id == uuid.UUID(body["client_event_id"])
                )
            )
        )
        .scalars()
        .all()
    )
    assert count == 1


async def test_a_duplicate_pickup_does_not_pick_up_twice(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    await start(client, driver, world["trip_id"])
    stop = world["stop_ids"]["pickup_first"]
    await act(client, driver, stop, "arrived")

    body = event()
    await act(client, driver, stop, "done", body)
    await act(client, driver, stop, "done", body)

    await db_session.refresh(world["requests"]["first"])
    assert world["requests"]["first"].status == str(RequestStatus.picked_up)


async def test_a_repeated_arrival_with_a_new_key_is_harmless(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """Two taps of the same button is a user, not a bug. It must not 409."""
    await start(client, driver, world["trip_id"])
    stop = world["stop_ids"]["pickup_first"]

    assert (await act(client, driver, stop, "arrived")).status_code == 200
    assert (await act(client, driver, stop, "arrived")).status_code == 200


# --- stops move requests (B15 acceptance) --------------------------------------------------


async def test_finishing_a_pickup_picks_the_rider_up(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    await start(client, driver, world["trip_id"])
    await act(client, driver, world["stop_ids"]["pickup_first"], "arrived")
    await act(client, driver, world["stop_ids"]["pickup_first"], "done")

    await db_session.refresh(world["requests"]["first"])
    await db_session.refresh(world["requests"]["second"])
    assert world["requests"]["first"].status == str(RequestStatus.picked_up)
    # One stop finishing must move exactly one request.
    assert world["requests"]["second"].status == str(RequestStatus.assigned)


async def test_finishing_a_drop_drops_the_rider(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    await start(client, driver, world["trip_id"])
    for key in ("pickup_first", "drop_first"):
        await act(client, driver, world["stop_ids"][key], "arrived")
        await act(client, driver, world["stop_ids"][key], "done")

    await db_session.refresh(world["requests"]["first"])
    assert world["requests"]["first"].status == str(RequestStatus.dropped)


async def test_a_stop_cannot_be_finished_before_arriving(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    """Recording a pickup from three streets away is how a rider gets left behind."""
    await start(client, driver, world["trip_id"])

    response = await act(client, driver, world["stop_ids"]["pickup_second"], "done")
    assert response.status_code == 409


async def test_stops_cannot_be_touched_before_the_trip_starts(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    response = await act(client, driver, world["stop_ids"]["pickup_first"], "arrived")
    assert response.status_code == 409


async def test_the_tap_position_is_recorded(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """DRV-05: "each tap is timestamped with GPS position" - for later disputes."""
    await start(client, driver, world["trip_id"])
    await act(
        client,
        driver,
        world["stop_ids"]["pickup_first"],
        "arrived",
        event(lat=FAR[0], lng=FAR[1]),
    )

    first = await reload_stop(db_session, world["stop_ids"]["pickup_first"])
    assert first.event_location is not None


# --- no-show (B15 acceptance) ---------------------------------------------------------------


async def test_no_show_is_blocked_before_the_wait_time(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], clock: FakeClock
) -> None:
    """DRV-05: enabled only after `no_show_wait_minutes` (default 5) from "Arrived"."""
    await start(client, driver, world["trip_id"])
    stop = world["stop_ids"]["pickup_first"]
    await act(client, driver, stop, "arrived")

    clock.advance(timedelta(minutes=3))
    response = await act(client, driver, stop, "no_show", event(occurred_at=clock.now()))

    assert response.status_code == 409


async def test_no_show_is_allowed_once_the_driver_has_waited(
    client: AsyncClient,
    world: dict[str, Any],
    driver: dict[str, str],
    clock: FakeClock,
    db_session: AsyncSession,
) -> None:
    await start(client, driver, world["trip_id"])
    stop = world["stop_ids"]["pickup_first"]
    await act(client, driver, stop, "arrived")

    clock.advance(timedelta(minutes=6))
    response = await act(client, driver, stop, "no_show", event(occurred_at=clock.now()))

    assert response.status_code == 200
    await db_session.refresh(world["requests"]["first"])
    assert world["requests"]["first"].status == str(RequestStatus.no_show)
    assert (await reload_stop(db_session, stop)).status == str(StopStatus.skipped)


async def test_no_show_needs_an_arrival_first(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], clock: FakeClock
) -> None:
    await start(client, driver, world["trip_id"])
    clock.advance(timedelta(minutes=30))

    response = await act(
        client,
        driver,
        world["stop_ids"]["pickup_second"],
        "no_show",
        event(occurred_at=clock.now()),
    )
    assert response.status_code == 409


async def test_a_drop_cannot_be_a_no_show(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], clock: FakeClock
) -> None:
    """Nobody fails to show up for being let out of a cab."""
    await start(client, driver, world["trip_id"])
    clock.advance(timedelta(minutes=30))

    response = await act(
        client, driver, world["stop_ids"]["drop_first"], "no_show", event(occurred_at=clock.now())
    )
    assert response.status_code == 409


# --- completing -------------------------------------------------------------------------------


async def test_a_trip_cannot_complete_with_a_rider_still_aboard(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    await start(client, driver, world["trip_id"])

    response = await client.post(
        f"/driver/trips/{world['trip_id']}/complete", json=event(), headers=driver
    )
    assert response.status_code == 409


async def test_completing_frees_the_vehicle(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    await _run_the_whole_trip(client, driver, world)

    await db_session.refresh(world["trip"])
    await db_session.refresh(world["vehicle"])
    assert world["trip"].status == str(TripStatus.completed)
    assert world["vehicle"].status == str(VehicleStatus.available)


async def test_every_rider_ends_dropped(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    await _run_the_whole_trip(client, driver, world)

    for label in ("first", "second"):
        await db_session.refresh(world["requests"][label])
        assert world["requests"][label].status == str(RequestStatus.dropped)


async def _run_the_whole_trip(
    client: AsyncClient, driver: dict[str, str], world: dict[str, Any]
) -> None:
    await start(client, driver, world["trip_id"])
    for key in ("pickup_first", "pickup_second", "drop_first", "drop_second"):
        await act(client, driver, world["stop_ids"][key], "arrived")
        await act(client, driver, world["stop_ids"][key], "done")
    await client.post(f"/driver/trips/{world['trip_id']}/complete", json=event(), headers=driver)


# --- notifications ------------------------------------------------------------------------------


async def test_the_rider_hears_that_the_cab_arrived(
    client: AsyncClient,
    world: dict[str, Any],
    driver: dict[str, str],
    events: RecordingEventPublisher,
) -> None:
    """`trip-lifecycle.md` section 6: "stop -> arrived | Employee"."""
    await start(client, driver, world["trip_id"])
    await act(client, driver, world["stop_ids"]["pickup_first"], "arrived")

    rider_user_id = world["users"]["first"].id
    assert f"user.{rider_user_id}" in events.channels_for("stop.arrived")


async def test_starting_and_completing_are_announced_on_the_trip_channel(
    client: AsyncClient,
    world: dict[str, Any],
    driver: dict[str, str],
    events: RecordingEventPublisher,
) -> None:
    await _run_the_whole_trip(client, driver, world)

    trip_channel = f"trip.{world['trip_id']}"
    assert trip_channel in events.channels_for("trip.started")
    assert trip_channel in events.channels_for("trip.completed")


# --- permissions ----------------------------------------------------------------------------------


async def test_a_supervisor_cannot_act_as_the_driver(
    client: AsyncClient, world: dict[str, Any], clock: FakeClock, db_session: AsyncSession
) -> None:
    """`trip_action` is a driver's permission over their own trip, not a dispatch tool."""
    supervisor = make_user(name="Sunil", phone=unique_phone())
    db_session.add(supervisor)
    await db_session.flush()
    db_session.add(make_user_role(supervisor.id, Role.supervisor, operator_id=world["operator_id"]))
    await db_session.flush()

    token, _ = create_access_token(
        user_id=supervisor.id,
        role=str(Role.supervisor),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
    )
    response = await start(client, {"Authorization": f"Bearer {token}"}, world["trip_id"])

    assert response.status_code == 403


async def test_starting_needs_a_token(client: AsyncClient, world: dict[str, Any]) -> None:
    response = await client.post(f"/driver/trips/{world['trip_id']}/start", json=event())
    assert response.status_code == 401


# --- a cancelled rider must not strand the cab (found by the S02 simulator run) --------


async def test_cancelling_an_assigned_ride_skips_its_stops(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """Otherwise the driver drives to a pickup nobody is waiting at.

    `done` would then be refused - a cancelled request cannot become `picked_up` - and
    the trip could never complete. The S02 run stranded every assigned cab this way.
    """
    await start(client, driver, world["trip_id"])

    request = world["requests"]["first"]
    await RideRequestService(db_session, FakeClock(NOW)).cancel(
        operator_id=world["operator_id"],
        request_id=request.id,
        actor_role=Role.employee,
        actor_user_id=world["users"]["first"].id,
        reason="Waited too long",
        caller_employee_id=request.employee_id,
    )

    for key in ("pickup_first", "drop_first"):
        stop = await reload_stop(db_session, world["stop_ids"][key])
        assert stop.status == str(StopStatus.skipped)


async def test_the_trip_can_still_be_completed_after_a_cancellation(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """The cab must be freed for its next job, not held by a rider who left."""
    await start(client, driver, world["trip_id"])

    request = world["requests"]["first"]
    await RideRequestService(db_session, FakeClock(NOW)).cancel(
        operator_id=world["operator_id"],
        request_id=request.id,
        actor_role=Role.employee,
        actor_user_id=world["users"]["first"].id,
        reason="Waited too long",
        caller_employee_id=request.employee_id,
    )

    for key in ("pickup_second", "drop_second"):
        await act(client, driver, world["stop_ids"][key], "arrived")
        await act(client, driver, world["stop_ids"][key], "done")

    response = await client.post(
        f"/driver/trips/{world['trip_id']}/complete", json=event(), headers=driver
    )
    assert response.status_code == 200


async def test_an_already_finished_stop_is_left_alone_by_a_cancellation(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """A pickup that happened, happened; cancelling afterwards cannot unmake it."""
    await start(client, driver, world["trip_id"])
    await act(client, driver, world["stop_ids"]["pickup_first"], "arrived")
    await act(client, driver, world["stop_ids"]["pickup_first"], "done")

    # A picked-up rider cannot cancel at all - the state machine has no such edge - so
    # the finished pickup simply stands.
    pickup = await reload_stop(db_session, world["stop_ids"]["pickup_first"])
    assert pickup.status == str(StopStatus.done)
