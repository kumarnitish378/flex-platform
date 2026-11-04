"""The business gauges report the database, not zero (R01).

These are the panels a supervisor's manager looks at: how many riders are waiting, how
long the oldest has waited, how many cabs have gone quiet. A gauge that stays at zero
while riders queue is the failure mode worth testing, so every assertion here is made
against rows that were actually inserted.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import metrics
from app.core.clock import FakeClock
from app.core.geo import to_point
from app.domain.enums import AlertSeverity, AlertStatus, AlertType, Urgency, VehicleType
from app.domain.state_machines import RequestStatus, VehicleStatus
from app.modules.alerts.models import Alert
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle
from app.modules.observability import BusinessGaugeCollector
from app.modules.requests.models import RideRequest
from tests.builders import (
    make_client,
    make_employee,
    make_office,
    make_operator,
    unique_phone,
)

pytestmark = pytest.mark.requires_db

NOW = datetime(2026, 9, 25, 7, 30, tzinfo=UTC)
HOME = (28.5300, 77.4000)


def gauge(metric: object, **labels: str) -> float:
    name = metric._name  # type: ignore[attr-defined]
    got = metrics.REGISTRY.get_sample_value(name, labels)
    return 0.0 if got is None else got


@dataclass(frozen=True)
class World:
    operator_id: uuid.UUID
    client_id: uuid.UUID
    office_id: uuid.UUID
    employee_id: uuid.UUID


async def _world(session: AsyncSession) -> World:
    operator = make_operator()
    client = make_client(operator.id)
    office = make_office(operator.id, client.id)
    employee = make_employee(operator.id, client.id, office.id, phone=unique_phone())
    # Flushed in dependency order: SQLAlchemy sorts an `add_all` by table, and
    # `employee` is not guaranteed to land after the `client` it points at.
    for entity in (operator, client, office, employee):
        session.add(entity)
        await session.flush()
    return World(operator.id, client.id, office.id, employee.id)


def _request(
    operator_id: uuid.UUID,
    client_id: uuid.UUID,
    employee_id: uuid.UUID,
    office_id: uuid.UUID,
    *,
    status: RequestStatus,
    queued_at: datetime,
) -> RideRequest:
    return RideRequest(
        id=uuid.uuid4(),
        operator_id=operator_id,
        client_id=client_id,
        employee_id=employee_id,
        direction="to_office",
        office_id=office_id,
        location=to_point(*HOME),
        requested_time=NOW + timedelta(minutes=30),
        urgency=Urgency.medium,
        status=status,
        queued_at=queued_at,
        expires_at=NOW + timedelta(hours=2),
    )


async def test_a_queued_rider_shows_up_as_pending_with_their_wait(
    db_session: AsyncSession,
) -> None:
    world = await _world(db_session)
    db_session.add(
        _request(
            world.operator_id,
            world.client_id,
            world.employee_id,
            world.office_id,
            status=RequestStatus.queued,
            queued_at=NOW - timedelta(minutes=18),
        )
    )
    await db_session.flush()

    await BusinessGaugeCollector(db_session, FakeClock(NOW)).collect()

    label = str(world.operator_id)
    assert gauge(metrics.pending_requests, operator_id=label) == 1
    # Measured from `queued_at`, the Clock-set origin - not `created_at`, the database
    # default that B09 found every reported wait being measured from.
    assert gauge(metrics.longest_pending_wait, operator_id=label) == pytest.approx(18 * 60, abs=1)


async def test_an_assigned_rider_is_no_longer_pending(db_session: AsyncSession) -> None:
    world = await _world(db_session)
    db_session.add(
        _request(
            world.operator_id,
            world.client_id,
            world.employee_id,
            world.office_id,
            status=RequestStatus.assigned,
            queued_at=NOW - timedelta(minutes=40),
        )
    )
    await db_session.flush()

    await BusinessGaugeCollector(db_session, FakeClock(NOW)).collect()

    assert gauge(metrics.pending_requests, operator_id=str(world.operator_id)) == 0


async def test_an_on_duty_cab_that_never_pinged_counts_as_stale(
    db_session: AsyncSession,
) -> None:
    """Never heard from is worse than heard from late, not better (SUP-01)."""
    world = await _world(db_session)

    vehicle = Vehicle(
        id=uuid.uuid4(),
        operator_id=world.operator_id,
        registration_no=f"DL{uuid.uuid4().hex[:6].upper()}",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
        status=VehicleStatus.available,
    )
    driver = Driver(
        id=uuid.uuid4(),
        operator_id=world.operator_id,
        name="Ravi",
        phone=unique_phone(),
    )
    db_session.add_all([vehicle, driver])
    await db_session.flush()
    db_session.add(
        DutySession(
            id=uuid.uuid4(),
            operator_id=world.operator_id,
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            started_at=NOW - timedelta(hours=1),
        )
    )
    await db_session.flush()

    await BusinessGaugeCollector(db_session, FakeClock(NOW)).collect()

    label = str(world.operator_id)
    assert gauge(metrics.vehicles_on_duty, operator_id=label) == 1
    assert gauge(metrics.stale_vehicles, operator_id=label) == 1


async def test_open_alerts_are_split_by_severity(db_session: AsyncSession) -> None:
    world = await _world(db_session)
    db_session.add_all(
        [
            Alert(
                id=uuid.uuid4(),
                operator_id=world.operator_id,
                type=AlertType.sos,
                severity=AlertSeverity.critical,
                status=AlertStatus.open,
            ),
            Alert(
                id=uuid.uuid4(),
                operator_id=world.operator_id,
                type=AlertType.stale_vehicle,
                severity=AlertSeverity.warning,
                status=AlertStatus.acknowledged,
            ),
            Alert(
                id=uuid.uuid4(),
                operator_id=world.operator_id,
                type=AlertType.stale_vehicle,
                severity=AlertSeverity.warning,
                status=AlertStatus.resolved,
            ),
        ]
    )
    await db_session.flush()

    await BusinessGaugeCollector(db_session, FakeClock(NOW)).collect()

    label = str(world.operator_id)
    assert gauge(metrics.open_alerts, operator_id=label, severity="critical") == 1
    # Acknowledged is still open work; resolved is not.
    assert gauge(metrics.open_alerts, operator_id=label, severity="warning") == 1


async def test_gauges_are_cleared_between_passes(db_session: AsyncSession) -> None:
    """Otherwise a label keeps its last value forever and reads as current."""
    world = await _world(db_session)
    request = _request(
        world.operator_id,
        world.client_id,
        world.employee_id,
        world.office_id,
        status=RequestStatus.queued,
        queued_at=NOW - timedelta(minutes=5),
    )
    db_session.add(request)
    await db_session.flush()
    await BusinessGaugeCollector(db_session, FakeClock(NOW)).collect()
    assert gauge(metrics.pending_requests, operator_id=str(world.operator_id)) == 1

    request.status = str(RequestStatus.assigned)
    await db_session.flush()
    await BusinessGaugeCollector(db_session, FakeClock(NOW)).collect()

    assert gauge(metrics.pending_requests, operator_id=str(world.operator_id)) == 0
