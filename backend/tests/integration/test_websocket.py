"""The `/ws` endpoint end to end (B13, `websocket-protocol.md`).

Acceptance: an employee receives only their own trip channel, a supervisor receives the
operator channels, and an unauthorised subscription is rejected.

Driven through Starlette's test client over a real socket with real tokens and a real
database, because the thing worth proving is that the authorisation actually runs on the
connection - not that a function returns the right enum, which `test_channels.py` covers.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.geo import to_point
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import Direction, Role, Urgency, VehicleType
from app.domain.state_machines import RequestStatus, TripStatus, VehicleStatus
from app.main import create_app
from app.modules.dispatch.models import Trip
from app.modules.fleet.models import Driver, Vehicle
from app.modules.realtime.channels import Refusal, Subscriber, TripMembership
from app.modules.requests.models import RideRequest
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
JWT_SECRET = "websocket-tests-secret-0123456789ab"

OFFICE = (28.5000, 77.4000)
HOME = (28.5300, 77.4000)

WS_URL = "/api/v1/ws"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
    """One trip with one rider and one driver, plus a supervisor and a bystander."""
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
        ("supervisor", Role.supervisor),
        ("rider", Role.employee),
        ("bystander", Role.employee),
        ("driver", Role.driver),
        ("other_driver", Role.driver),
        ("client_admin", Role.client_admin),
    ):
        user = make_user(name=label, phone=unique_phone())
        db_session.add(user)
        await db_session.flush()
        db_session.add(
            make_user_role(
                user.id,
                role,
                operator_id=operator.id,
                client_id=customer.id if role in {Role.employee, Role.client_admin} else None,
            )
        )
        users[label] = user
    await db_session.flush()

    employees = {}
    for label in ("rider", "bystander"):
        employee = make_employee(operator.id, customer.id, office.id, name=label)
        employee.home_location = to_point(*HOME)
        employee.user_id = users[label].id
        db_session.add(employee)
        employees[label] = employee
    await db_session.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        registration_no="UP16WS0001",
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

    request = RideRequest(
        operator_id=operator.id,
        client_id=customer.id,
        employee_id=employees["rider"].id,
        direction=Direction.to_office,
        office_id=office.id,
        location=employees["rider"].home_location,
        requested_time=NOW + timedelta(minutes=10),
        urgency=Urgency.medium,
        status=RequestStatus.assigned,
        trip_id=trip.id,
        expires_at=NOW + timedelta(hours=2),
    )
    db_session.add(request)
    await db_session.flush()

    return {
        "operator_id": operator.id,
        "client_id": customer.id,
        "trip_id": trip.id,
        "users": users,
        "employees": employees,
        "request": request,
    }


@pytest_asyncio.fixture
async def app(
    database_ready: bool,
    db_session: AsyncSession,
    clock: FakeClock,
    memberships: Memberships,
) -> AsyncIterator[FastAPI]:
    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
        routing_provider="approx",
    )
    application = create_app(settings=settings, clock=clock)

    class _Factory:
        def __call__(self) -> object:
            return _NoClose(db_session)

    application.state.session_factory = _Factory()
    # No Redis: the hub still fans out locally, which is what these tests exercise. The
    # Redis path is covered in tests/unit/test_hub.py.
    application.state.hub._redis = None
    # Membership is supplied rather than queried. TestClient runs the app on its own
    # event loop, and the shared test session belongs to pytest-asyncio's, so a real
    # query here fails on the loop rather than on anything about the product. The query
    # itself is tested against the database in test_trip_membership.py, and the rule in
    # tests/unit/test_channels.py; this file is about the socket.
    application.state.membership = _stub_membership(memberships)
    yield application


Memberships = dict[tuple[uuid.UUID, uuid.UUID], TripMembership]


@pytest.fixture
def memberships() -> Memberships:
    """`(trip_id, user_id) -> membership`. Anything absent is "not on this trip"."""
    return {}


def _stub_membership(table: Memberships) -> Any:
    class _Stub:
        def __init__(self, _session: object) -> None:
            pass

        async def trip_membership(
            self, trip_id: uuid.UUID, subscriber: Subscriber
        ) -> TripMembership | None:
            return table.get((trip_id, subscriber.user_id))

    return _Stub


class _NoClose:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


@pytest.fixture
def web(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def token_for(world: dict[str, Any], label: str, role: Role, clock: FakeClock) -> str:
    token, _ = create_access_token(
        user_id=world["users"][label].id,
        role=str(role),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
        client_id=world["client_id"] if role in {Role.employee, Role.client_admin} else None,
    )
    return token


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def subscribe(socket: Any, *channels: str) -> dict[str, Any]:
    socket.send_json({"type": "subscribe", "channels": list(channels)})
    reply: dict[str, Any] = socket.receive_json()
    return reply


def refusal_reasons(reply: dict[str, Any]) -> list[str]:
    return [entry["reason"] for entry in reply["refused"]]


def _in_app_loop(web: TestClient, call: Any, *args: Any) -> Any:
    """Run a coroutine on the loop the app is running on, as a worker would.

    TestClient drives the app from its own portal; publishing from the test's thread
    would touch the hub from the wrong loop.
    """
    portal = web.portal
    assert portal is not None, "TestClient must be entered before using its portal"
    return portal.call(call, *args)


# --- authentication -------------------------------------------------------------------


def test_a_token_in_the_header_connects(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    token = token_for(world, "supervisor", Role.supervisor, clock)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        socket.send_json({"type": "ping"})
        assert socket.receive_json() == {"type": "pong"}


def test_a_browser_can_authenticate_with_a_first_frame(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """Browsers cannot set headers on a WebSocket upgrade, hence the `auth` frame."""
    token = token_for(world, "supervisor", Role.supervisor, clock)

    with web.websocket_connect(WS_URL) as socket:
        socket.send_json({"type": "auth", "token": token, "active_role": "supervisor"})
        socket.send_json({"type": "ping"})
        assert socket.receive_json() == {"type": "pong"}


def test_no_token_is_closed(web: TestClient, world: dict[str, Any]) -> None:
    with web.websocket_connect(WS_URL) as socket:
        socket.send_json({"type": "subscribe", "channels": ["user.x"]})
        assert socket.receive_json()["type"] == "error"


def test_a_garbage_token_is_closed(web: TestClient, world: dict[str, Any]) -> None:
    with web.websocket_connect(WS_URL, headers=auth_header("not-a-token")) as socket:
        message = socket.receive_json()
        assert message["type"] == "error"
        assert message["code"] == 4401


def test_an_expired_token_is_closed(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """The socket must not outlive the credential that opened it."""
    token = token_for(world, "supervisor", Role.supervisor, clock)
    clock.advance(timedelta(minutes=20))

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        assert socket.receive_json()["code"] == 4401


def test_a_role_not_on_the_token_is_refused(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """Asking to act as operator_admin with an employee token is not a thing."""
    token = token_for(world, "rider", Role.employee, clock)

    with web.websocket_connect(
        WS_URL, headers={**auth_header(token), "X-Active-Role": "operator_admin"}
    ) as socket:
        assert socket.receive_json()["code"] == 4401


def test_a_token_in_the_query_string_is_not_accepted(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """Deliberate: a URL ends up in proxy logs and browser history."""
    token = token_for(world, "supervisor", Role.supervisor, clock)

    with web.websocket_connect(f"{WS_URL}?token={token}") as socket:
        assert socket.receive_json()["code"] == 4401


# --- the supervisor's channels -----------------------------------------------------------


def test_a_supervisor_receives_the_operator_channels(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """B13 acceptance."""
    token = token_for(world, "supervisor", Role.supervisor, clock)
    operator_id = world["operator_id"]

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(
            socket,
            f"operator.{operator_id}.vehicles",
            f"operator.{operator_id}.requests",
            f"operator.{operator_id}.alerts",
        )

    assert reply["refused"] == []
    assert len(reply["channels"]) == 3


def test_a_supervisor_receives_any_trip_of_their_operator(
    web: TestClient, world: dict[str, Any], clock: FakeClock, memberships: Memberships
) -> None:
    token = token_for(world, "supervisor", Role.supervisor, clock)
    memberships[(world["trip_id"], world["users"]["supervisor"].id)] = TripMembership(
        is_operator_staff=True
    )

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, f"trip.{world['trip_id']}")

    assert reply["channels"] == [f"trip.{world['trip_id']}"]


def test_another_operators_channel_is_rejected(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """B13 acceptance: unauthorized subscription rejected."""
    token = token_for(world, "supervisor", Role.supervisor, clock)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, f"operator.{uuid.uuid4()}.vehicles")

    assert reply["channels"] == []
    assert refusal_reasons(reply) == [str(Refusal.wrong_operator)]


def test_a_client_admin_is_refused_the_operator_board(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """They hold `request_queue_view`, but only for their own client."""
    token = token_for(world, "client_admin", Role.client_admin, clock)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, f"operator.{world['operator_id']}.requests")

    assert refusal_reasons(reply) == [str(Refusal.client_scoped)]


# --- the employee's channels (B13 acceptance) -----------------------------------------------


def test_an_employee_receives_their_own_trip_channel(
    web: TestClient, world: dict[str, Any], clock: FakeClock, memberships: Memberships
) -> None:
    token = token_for(world, "rider", Role.employee, clock)
    memberships[(world["trip_id"], world["users"]["rider"].id)] = TripMembership(is_rider=True)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, f"trip.{world['trip_id']}")

    assert reply["channels"] == [f"trip.{world['trip_id']}"]


def test_an_employee_receives_only_their_own_trip_channel(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """B13 acceptance, stated exactly: everything else is refused."""
    token = token_for(world, "bystander", Role.employee, clock)
    operator_id = world["operator_id"]

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(
            socket,
            f"trip.{world['trip_id']}",
            f"operator.{operator_id}.vehicles",
            f"operator.{operator_id}.requests",
            f"user.{world['users']['rider'].id}",
        )

    assert reply["channels"] == []
    assert refusal_reasons(reply) == [
        str(Refusal.not_on_this_trip),
        str(Refusal.client_scoped),
        str(Refusal.client_scoped),
        str(Refusal.not_your_user_channel),
    ]


def test_an_employee_loses_the_trip_when_their_ride_ends(
    web: TestClient, world: dict[str, Any], clock: FakeClock, memberships: Memberships
) -> None:
    """roles-and-permissions.md bounds it at pickup/drop, not at trip end."""
    memberships[(world["trip_id"], world["users"]["rider"].id)] = TripMembership(
        is_rider=True, rider_finished=True
    )
    token = token_for(world, "rider", Role.employee, clock)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, f"trip.{world['trip_id']}")

    assert refusal_reasons(reply) == [str(Refusal.ride_finished)]


def test_an_employee_receives_their_own_user_channel(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    token = token_for(world, "rider", Role.employee, clock)
    user_id = world["users"]["rider"].id

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, f"user.{user_id}")

    assert reply["channels"] == [f"user.{user_id}"]


# --- the driver's channels -------------------------------------------------------------------


def test_the_assigned_driver_receives_the_trip(
    web: TestClient, world: dict[str, Any], clock: FakeClock, memberships: Memberships
) -> None:
    token = token_for(world, "driver", Role.driver, clock)
    memberships[(world["trip_id"], world["users"]["driver"].id)] = TripMembership(
        is_assigned_driver=True
    )

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, f"trip.{world['trip_id']}")

    assert reply["channels"] == [f"trip.{world['trip_id']}"]


def test_another_driver_does_not(web: TestClient, world: dict[str, Any], clock: FakeClock) -> None:
    token = token_for(world, "other_driver", Role.driver, clock)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, f"trip.{world['trip_id']}")

    assert refusal_reasons(reply) == [str(Refusal.not_on_this_trip)]


def test_a_driver_cannot_watch_the_whole_fleet(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    token = token_for(world, "driver", Role.driver, clock)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, f"operator.{world['operator_id']}.vehicles")

    assert refusal_reasons(reply) == [str(Refusal.missing_permission)]


# --- the conversation ---------------------------------------------------------------------


def test_a_nonexistent_trip_is_refused_like_one_you_are_not_on(
    web: TestClient, world: dict[str, Any], clock: FakeClock, memberships: Memberships
) -> None:
    """A channel name must not be a way to discover whether a trip exists."""
    token = token_for(world, "rider", Role.employee, clock)
    memberships[(world["trip_id"], world["users"]["rider"].id)] = TripMembership(is_rider=True)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        unknown = subscribe(socket, f"trip.{uuid.uuid4()}")
        not_mine = subscribe(socket, f"trip.{world['trip_id']}")

    assert refusal_reasons(unknown) == [str(Refusal.not_on_this_trip)]
    assert not_mine["channels"] != []


def test_a_nonsense_channel_name_is_refused_without_closing(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    token = token_for(world, "supervisor", Role.supervisor, clock)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(socket, "payroll.everything")
        assert refusal_reasons(reply) == [str(Refusal.unknown_channel)]

        socket.send_json({"type": "ping"})
        assert socket.receive_json() == {"type": "pong"}


def test_one_refused_channel_does_not_lose_the_others(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """A client asking for six channels on login must keep the five it may read."""
    token = token_for(world, "supervisor", Role.supervisor, clock)
    operator_id = world["operator_id"]

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        reply = subscribe(
            socket,
            f"operator.{operator_id}.vehicles",
            f"operator.{uuid.uuid4()}.vehicles",
            f"operator.{operator_id}.requests",
        )

    assert reply["channels"] == [
        f"operator.{operator_id}.vehicles",
        f"operator.{operator_id}.requests",
    ]
    assert len(reply["refused"]) == 1


def test_unsubscribing_is_acknowledged(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    token = token_for(world, "supervisor", Role.supervisor, clock)
    channel = f"operator.{world['operator_id']}.vehicles"

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        subscribe(socket, channel)
        socket.send_json({"type": "unsubscribe", "channels": [channel]})
        assert socket.receive_json() == {"type": "unsubscribed", "channels": [channel]}


def test_an_unknown_frame_type_is_ignored(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """A newer client must be able to talk to an older server."""
    token = token_for(world, "supervisor", Role.supervisor, clock)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        socket.send_json({"type": "telepathy", "channels": ["whatever"]})
        socket.send_json({"type": "ping"})
        assert socket.receive_json() == {"type": "pong"}


def test_a_frame_that_is_not_an_object_closes_the_socket(
    web: TestClient, world: dict[str, Any], clock: FakeClock
) -> None:
    token = token_for(world, "supervisor", Role.supervisor, clock)

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        socket.send_json(["subscribe"])
        assert socket.receive_json()["code"] == 4408


# --- delivery ------------------------------------------------------------------------------


def test_an_event_reaches_a_subscribed_socket(
    web: TestClient, world: dict[str, Any], clock: FakeClock, app: FastAPI
) -> None:
    """The end the user feels: something happened, and the screen knows."""
    token = token_for(world, "supervisor", Role.supervisor, clock)
    channel = f"operator.{world['operator_id']}.vehicles"

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        subscribe(socket, channel)

        frame = {"type": "event", "event": "vehicle.location", "data": {"lat": 28.5}}
        _in_app_loop(web, app.state.hub.deliver, channel, frame)

        assert socket.receive_json() == frame


def test_an_event_on_a_channel_you_did_not_ask_for_does_not_arrive(
    web: TestClient, world: dict[str, Any], clock: FakeClock, app: FastAPI
) -> None:
    token = token_for(world, "supervisor", Role.supervisor, clock)
    operator_id = world["operator_id"]

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        subscribe(socket, f"operator.{operator_id}.vehicles")

        delivered = _in_app_loop(
            web,
            app.state.hub.deliver,
            f"operator.{operator_id}.alerts",
            {"type": "event", "event": "alert.raised"},
        )

        assert delivered == 0
        socket.send_json({"type": "ping"})
        assert socket.receive_json() == {"type": "pong"}


def test_disconnecting_releases_the_channel(
    web: TestClient, world: dict[str, Any], clock: FakeClock, app: FastAPI
) -> None:
    """A hub that leaks connections leaks memory for as long as the process lives."""
    token = token_for(world, "supervisor", Role.supervisor, clock)
    channel = f"operator.{world['operator_id']}.vehicles"

    with web.websocket_connect(WS_URL, headers=auth_header(token)) as socket:
        subscribe(socket, channel)
        assert app.state.hub.listeners(channel) == 1

    assert app.state.hub.listeners(channel) == 0
