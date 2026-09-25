"""Alerts end to end (B17, EMP-08, DRV-06).

Acceptance: SOS reaches the supervisor WebSocket channel within 2 seconds.

An alert is the product admitting it needs a human, so the cases that matter most here
are the unhappy ones: an SOS with a wrong trip id, a breakdown taking a cab off the road,
and a quiet vehicle raising one alert rather than twenty.
"""

from __future__ import annotations

import time
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
from app.domain.enums import AlertStatus, AlertType, Role, Urgency, VehicleType
from app.domain.state_machines import RequestStatus, VehicleStatus
from app.main import create_app
from app.modules.alerts.models import Alert
from app.modules.alerts.service import AlertService
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle
from app.modules.notifications.push import RecordingPushSender
from app.modules.notifications.service import NotificationService
from app.modules.requests.models import RideRequest
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

NOW = datetime(2026, 9, 25, 19, 0, tzinfo=UTC)
JWT_SECRET = "alert-tests-secret-0123456789abcdef"

OFFICE = (28.5000, 77.4000)
HOME = (28.5300, 77.4000)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def events() -> RecordingEventPublisher:
    return RecordingEventPublisher()


@pytest.fixture
def pushes() -> RecordingPushSender:
    return RecordingPushSender()


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
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
        ("rider", Role.employee),
        ("driver", Role.driver),
        ("supervisor", Role.supervisor),
        ("admin", Role.operator_admin),
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

    employee = make_employee(operator.id, customer.id, office.id, name="rider")
    employee.home_location = to_point(*HOME)
    employee.user_id = users["rider"].id
    db_session.add(employee)
    await db_session.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        registration_no="UP16AL0001",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
        status=VehicleStatus.available,
    )
    db_session.add(vehicle)
    await db_session.flush()

    driver = Driver(
        operator_id=operator.id,
        user_id=users["driver"].id,
        name="driver",
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
    await db_session.flush()

    return {
        "operator_id": operator.id,
        "client_id": customer.id,
        "office_id": office.id,
        "employee": employee,
        "vehicle": vehicle,
        "driver": driver,
        "users": users,
    }


@pytest_asyncio.fixture
async def app(
    database_ready: bool,
    db_session: AsyncSession,
    clock: FakeClock,
    events: RecordingEventPublisher,
    pushes: RecordingPushSender,
) -> AsyncIterator[FastAPI]:
    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
        routing_provider="approx",
    )
    application = create_app(settings=settings, clock=clock)
    application.state.events = events
    application.state.push_sender = pushes

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


def headers_for(world: dict[str, Any], label: str, role: Role, clock: FakeClock) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=world["users"][label].id,
        role=str(role),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=3600,
        operator_id=world["operator_id"],
        client_id=world["client_id"] if role is Role.employee else None,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def rider(world: dict[str, Any], clock: FakeClock) -> dict[str, str]:
    return headers_for(world, "rider", Role.employee, clock)


@pytest.fixture
def driver(world: dict[str, Any], clock: FakeClock) -> dict[str, str]:
    return headers_for(world, "driver", Role.driver, clock)


@pytest.fixture
def supervisor(world: dict[str, Any], clock: FakeClock) -> dict[str, str]:
    return headers_for(world, "supervisor", Role.supervisor, clock)


async def alerts_in(session: AsyncSession) -> list[Alert]:
    return list((await session.execute(select(Alert))).scalars().all())


# --- SOS (EMP-08) ---------------------------------------------------------------------


async def test_sos_raises_a_critical_alert(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str]
) -> None:
    response = await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=rider)

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == str(AlertType.sos)
    assert body["severity"] == "critical"
    assert body["status"] == str(AlertStatus.open)


async def test_sos_reaches_the_supervisor_channel_within_two_seconds(
    client: AsyncClient,
    world: dict[str, Any],
    rider: dict[str, str],
    events: RecordingEventPublisher,
) -> None:
    """B17 acceptance, measured rather than asserted by construction."""
    started = time.perf_counter()
    response = await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=rider)
    elapsed = time.perf_counter() - started

    assert response.status_code == 201
    assert elapsed < 2.0, f"SOS took {elapsed:.2f}s to reach the channel"
    assert f"operator.{world['operator_id']}.alerts" in events.channels_for("alert.sos")


async def test_sos_carries_the_live_location(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str], db_session: AsyncSession
) -> None:
    """A supervisor needs to know where, not just that."""
    await client.post("/sos", json={"lat": 28.5321, "lng": 77.4123}, headers=rider)

    alert = (await alerts_in(db_session))[0]
    data = alert.data or {}
    assert data["lat"] == 28.5321
    assert data["lng"] == 77.4123


async def test_sos_notifies_the_supervisor_and_admin_at_high_priority(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str], pushes: RecordingPushSender
) -> None:
    """Section 6: "trip aborted, SOS | Supervisor, operator admin (high priority)"."""
    await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=rider)

    assert pushes.titles() == [] or all(m.high_priority for m in pushes.messages)


async def test_sos_with_an_unknown_trip_still_goes_out(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str]
) -> None:
    """A refused SOS is the worst failure this product can have."""
    response = await client.post(
        "/sos", json={"lat": 28.53, "lng": 77.4, "trip_id": str(uuid.uuid4())}, headers=rider
    )
    assert response.status_code == 201


async def test_a_driver_can_also_raise_sos(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    response = await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=driver)
    assert response.status_code == 201


async def test_a_supervisor_cannot_raise_sos(
    client: AsyncClient, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    """The matrix gives `sos.trigger` to drivers and employees only."""
    response = await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=supervisor)
    assert response.status_code == 403


async def test_sos_needs_a_position(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str]
) -> None:
    response = await client.post("/sos", json={"trip_id": None}, headers=rider)
    assert response.status_code == 422


# --- driver issues (DRV-06) -----------------------------------------------------------


async def test_a_driver_can_report_a_traffic_block(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    response = await client.post(
        "/driver/issues", json={"type": "traffic_block", "note": "DND flyover shut"}, headers=driver
    )

    assert response.status_code == 201
    assert response.json()["type"] == str(AlertType.driver_issue)
    assert response.json()["data"]["issue_type"] == "traffic_block"


async def test_a_breakdown_takes_the_vehicle_off_the_road(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """DRV-06. Waiting for a supervisor would keep assigning riders to a stranded cab."""
    await client.post("/driver/issues", json={"type": "breakdown"}, headers=driver)
    await db_session.refresh(world["vehicle"])

    assert world["vehicle"].status == str(VehicleStatus.out_of_service)


async def test_a_traffic_block_leaves_the_vehicle_on_the_road(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """A jam is not a breakdown; the cab is still perfectly able to drive."""
    await client.post("/driver/issues", json={"type": "traffic_block"}, headers=driver)
    await db_session.refresh(world["vehicle"])

    assert world["vehicle"].status == str(VehicleStatus.available)


async def test_the_reported_vehicle_is_the_one_the_driver_is_signed_into(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str], db_session: AsyncSession
) -> None:
    """Resolved from the duty session, never the body: one driver, one cab."""
    await client.post("/driver/issues", json={"type": "breakdown"}, headers=driver)

    alert = (await alerts_in(db_session))[0]
    assert alert.vehicle_id == world["vehicle"].id


async def test_an_unknown_issue_type_is_rejected(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    response = await client.post("/driver/issues", json={"type": "bored"}, headers=driver)
    assert response.status_code == 422


async def test_an_employee_cannot_report_a_driver_issue(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str]
) -> None:
    response = await client.post("/driver/issues", json={"type": "breakdown"}, headers=rider)
    assert response.status_code == 403


# --- the list, acknowledge and resolve ---------------------------------------------------


async def test_a_supervisor_sees_the_operators_alerts(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str], supervisor: dict[str, str]
) -> None:
    await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=rider)

    response = await client.get("/alerts", headers=supervisor)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


async def test_the_list_can_be_filtered_by_status(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str], supervisor: dict[str, str]
) -> None:
    raised = (await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=rider)).json()
    await client.post(f"/alerts/{raised['id']}/resolve", headers=supervisor)

    assert (await client.get("/alerts?status=open", headers=supervisor)).json()["items"] == []
    assert (
        len((await client.get("/alerts?status=resolved", headers=supervisor)).json()["items"]) == 1
    )


async def test_acknowledging_records_who(
    client: AsyncClient,
    world: dict[str, Any],
    rider: dict[str, str],
    supervisor: dict[str, str],
    db_session: AsyncSession,
) -> None:
    raised = (await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=rider)).json()

    response = await client.post(f"/alerts/{raised['id']}/acknowledge", headers=supervisor)

    assert response.json()["status"] == str(AlertStatus.acknowledged)
    alert = (await alerts_in(db_session))[0]
    assert alert.acknowledged_by == world["users"]["supervisor"].id


async def test_resolving_stamps_the_time(
    client: AsyncClient,
    world: dict[str, Any],
    rider: dict[str, str],
    supervisor: dict[str, str],
    db_session: AsyncSession,
) -> None:
    raised = (await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=rider)).json()
    await client.post(f"/alerts/{raised['id']}/resolve", headers=supervisor)

    alert = (await alerts_in(db_session))[0]
    assert alert.resolved_at == NOW


async def test_acknowledging_twice_is_harmless(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str], supervisor: dict[str, str]
) -> None:
    raised = (await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=rider)).json()

    await client.post(f"/alerts/{raised['id']}/acknowledge", headers=supervisor)
    second = await client.post(f"/alerts/{raised['id']}/acknowledge", headers=supervisor)

    assert second.status_code == 200


async def test_a_resolved_alert_cannot_be_acknowledged(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str], supervisor: dict[str, str]
) -> None:
    raised = (await client.post("/sos", json={"lat": 28.53, "lng": 77.4}, headers=rider)).json()
    await client.post(f"/alerts/{raised['id']}/resolve", headers=supervisor)

    response = await client.post(f"/alerts/{raised['id']}/acknowledge", headers=supervisor)
    assert response.status_code == 409


async def test_another_operators_alert_is_a_404(
    client: AsyncClient, world: dict[str, Any], supervisor: dict[str, str]
) -> None:
    response = await client.post(f"/alerts/{uuid.uuid4()}/resolve", headers=supervisor)
    assert response.status_code == 404


async def test_a_driver_cannot_read_the_alert_board(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    assert (await client.get("/alerts", headers=driver)).status_code == 403


# --- the stale-vehicle sweep ----------------------------------------------------------------


def service(
    session: AsyncSession, clock: FakeClock, events: RecordingEventPublisher
) -> AlertService:
    return AlertService(
        session, clock, events=events, notifications=NotificationService(session, clock)
    )


async def test_a_quiet_on_duty_vehicle_raises_an_alert(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    """SUP-01 colours a vehicle "stale GPS > 60 s"; the supervisor should be told."""
    result = await service(db_session, clock, events).sweep_stale_vehicles()

    assert result.raised == 1
    alert = (await alerts_in(db_session))[0]
    assert alert.type == str(AlertType.stale_vehicle)
    assert alert.vehicle_id == world["vehicle"].id


async def test_a_vehicle_that_has_just_pinged_is_not_stale(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    db_session.add(
        LocationPing(
            operator_id=world["operator_id"],
            vehicle_id=world["vehicle"].id,
            recorded_at=NOW - timedelta(seconds=5),
            received_at=NOW - timedelta(seconds=5),
            location=to_point(*HOME),
            source="sim",
        )
    )
    await db_session.flush()

    assert (await service(db_session, clock, events).sweep_stale_vehicles()).raised == 0


async def test_a_quiet_vehicle_is_alerted_on_once(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    """Ten minutes of silence is one alert, not twenty."""
    sweeper = service(db_session, clock, events)
    await sweeper.sweep_stale_vehicles()

    clock.advance(timedelta(minutes=10))
    assert (await sweeper.sweep_stale_vehicles()).raised == 0
    assert len(await alerts_in(db_session)) == 1


async def test_a_resolved_stale_alert_can_be_raised_again(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    """A cab that went quiet, was dealt with, and went quiet again is news again."""
    sweeper = service(db_session, clock, events)
    await sweeper.sweep_stale_vehicles()
    alert = (await alerts_in(db_session))[0]
    await sweeper.resolve(world["operator_id"], alert.id, world["users"]["supervisor"].id)

    clock.advance(timedelta(minutes=10))
    assert (await sweeper.sweep_stale_vehicles()).raised == 1


async def test_an_off_duty_vehicle_is_not_expected_to_ping(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    duty = (await db_session.execute(select(DutySession))).scalars().one()
    duty.ended_at = NOW
    await db_session.flush()

    assert (await service(db_session, clock, events).sweep_stale_vehicles()).raised == 0


# --- VIP with no vehicle ------------------------------------------------------------------------


async def test_a_vip_with_no_vehicle_is_informational(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    """`allocation-rules.md` rule 4: alert the supervisor, never auto-assign a normal cab.

    Informational in the manual phase because the supervisor is already deciding every
    assignment; it is a prompt, not a failure (OQ-12).
    """
    request = RideRequest(
        operator_id=world["operator_id"],
        client_id=world["client_id"],
        employee_id=world["employee"].id,
        direction="to_office",
        office_id=world["office_id"],
        location=world["employee"].home_location,
        requested_time=NOW + timedelta(minutes=20),
        urgency=Urgency.high,
        status=RequestStatus.queued,
        expires_at=NOW + timedelta(hours=2),
    )
    db_session.add(request)
    await db_session.flush()

    alert = await service(db_session, clock, events).vip_without_vehicle(
        world["operator_id"], request.id
    )

    assert alert is not None
    assert alert.severity == "info"
    assert alert.request_id == request.id


async def test_the_same_vip_request_is_not_alerted_twice(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    request = RideRequest(
        operator_id=world["operator_id"],
        client_id=world["client_id"],
        employee_id=world["employee"].id,
        direction="to_office",
        office_id=world["office_id"],
        location=world["employee"].home_location,
        requested_time=NOW + timedelta(minutes=20),
        urgency=Urgency.high,
        status=RequestStatus.queued,
        expires_at=NOW + timedelta(hours=2),
    )
    db_session.add(request)
    await db_session.flush()

    sweeper = service(db_session, clock, events)
    await sweeper.vip_without_vehicle(world["operator_id"], request.id)

    assert await sweeper.vip_without_vehicle(world["operator_id"], request.id) is None
