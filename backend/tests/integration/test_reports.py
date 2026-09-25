"""Ratings and the trip report (B18, EMP-07, OPA-05).

Acceptance: CSV export matches the JSON totals, and median/p90 wait are correct on
fixture data.

The fixture builds five requests with **known** waits - 4, 6, 9, 12 and 45 minutes - plus
a no-show and a cancellation, so the expected numbers can be worked out by hand rather
than read back off the implementation.
"""

from __future__ import annotations

import csv
import io
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.geo import to_point
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import Direction, Role, Urgency, VehicleType
from app.domain.state_machines import RequestStatus, StopKind, StopStatus, TripStatus, VehicleStatus
from app.main import create_app
from app.modules.dispatch.models import Trip, TripStop
from app.modules.fleet.models import Driver, Vehicle
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

NOW = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)
JWT_SECRET = "report-tests-secret-0123456789abc"

OFFICE = (28.5000, 77.4000)
HOME = (28.5300, 77.4000)

#: Waits, in minutes, the fixture builds. Median 9; p90 = 12 + 0.6 * (45 - 12) = 31.8.
WAITS = [4, 6, 9, 12, 45]
EXPECTED_MEDIAN = 9.0
EXPECTED_P90 = 31.8


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()

    first_client = make_client(operator.id, "Acme Corp")
    second_client = make_client(operator.id, "Globex")
    db_session.add_all([first_client, second_client])
    await db_session.flush()

    office = make_office(operator.id, first_client.id)
    office.location = to_point(*OFFICE)
    other_office = make_office(operator.id, second_client.id, name="G1")
    other_office.location = to_point(*OFFICE)
    db_session.add_all([office, other_office])
    await db_session.flush()

    users: dict[str, Any] = {}
    for label, role, client_scope in (
        ("rider", Role.employee, first_client),
        ("other_rider", Role.employee, first_client),
        ("admin", Role.operator_admin, None),
        ("supervisor", Role.supervisor, None),
        ("client_admin", Role.client_admin, second_client),
        ("driver", Role.driver, None),
    ):
        user = make_user(name=label, phone=unique_phone())
        db_session.add(user)
        await db_session.flush()
        db_session.add(
            make_user_role(
                user.id,
                role,
                operator_id=operator.id,
                client_id=client_scope.id if client_scope is not None else None,
            )
        )
        users[label] = user
    await db_session.flush()

    employee = make_employee(operator.id, first_client.id, office.id, name="rider")
    employee.home_location = to_point(*HOME)
    employee.user_id = users["rider"].id
    other_employee = make_employee(operator.id, second_client.id, other_office.id, name="other")
    other_employee.home_location = to_point(*HOME)
    db_session.add_all([employee, other_employee])
    await db_session.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        registration_no="UP16RP0001",
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

    trip = Trip(
        operator_id=operator.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        direction=Direction.to_office,
        office_id=office.id,
        status=TripStatus.completed,
        planned_start=NOW - timedelta(hours=2),
        mode_used="manual",
    )
    db_session.add(trip)
    await db_session.flush()

    completed: list[RideRequest] = []
    for index, wait in enumerate(WAITS):
        asked_at = NOW - timedelta(hours=3) + timedelta(minutes=index)
        request = RideRequest(
            operator_id=operator.id,
            client_id=first_client.id,
            employee_id=employee.id,
            direction=Direction.to_office,
            office_id=office.id,
            location=employee.home_location,
            requested_time=asked_at + timedelta(minutes=20),
            urgency=Urgency.medium,
            status=RequestStatus.dropped,
            trip_id=trip.id,
            expires_at=asked_at + timedelta(hours=2),
            created_at=asked_at,
        )
        db_session.add(request)
        await db_session.flush()
        db_session.add_all(
            [
                TripStop(
                    operator_id=operator.id,
                    trip_id=trip.id,
                    sequence=index * 2 + 1,
                    stop_type=StopKind.pickup,
                    request_id=request.id,
                    location=employee.home_location,
                    status=StopStatus.done,
                    done_at=asked_at + timedelta(minutes=wait),
                ),
                TripStop(
                    operator_id=operator.id,
                    trip_id=trip.id,
                    sequence=index * 2 + 2,
                    stop_type=StopKind.drop,
                    request_id=request.id,
                    location=office.location,
                    status=StopStatus.done,
                    done_at=asked_at + timedelta(minutes=wait + 25),
                ),
            ]
        )
        completed.append(request)
    await db_session.flush()

    # One no-show and one cancellation: neither ever got in, so neither has a wait.
    for status in (RequestStatus.no_show, RequestStatus.cancelled):
        db_session.add(
            RideRequest(
                operator_id=operator.id,
                client_id=first_client.id,
                employee_id=employee.id,
                direction=Direction.to_office,
                office_id=office.id,
                location=employee.home_location,
                requested_time=NOW,
                urgency=Urgency.medium,
                status=status,
                cancel_reason="Cancelled by employee"
                if status == RequestStatus.cancelled
                else None,
                expires_at=NOW + timedelta(hours=2),
                created_at=NOW - timedelta(hours=1),
            )
        )

    # A different client's request, for the client filter.
    db_session.add(
        RideRequest(
            operator_id=operator.id,
            client_id=second_client.id,
            employee_id=other_employee.id,
            direction=Direction.to_office,
            office_id=other_office.id,
            location=other_employee.home_location,
            requested_time=NOW,
            urgency=Urgency.medium,
            status=RequestStatus.queued,
            expires_at=NOW + timedelta(hours=2),
            created_at=NOW - timedelta(hours=1),
        )
    )
    await db_session.flush()

    return {
        "operator_id": operator.id,
        "client_id": first_client.id,
        "other_client_id": second_client.id,
        "employee": employee,
        "users": users,
        "completed": completed,
        "driver": driver,
        "vehicle": vehicle,
    }


@pytest_asyncio.fixture
async def app(
    database_ready: bool, db_session: AsyncSession, clock: FakeClock
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
    scope = {
        Role.employee: world["client_id"],
        Role.client_admin: world["other_client_id"],
    }.get(role)
    token, _ = create_access_token(
        user_id=world["users"][label].id,
        role=str(role),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=3600,
        operator_id=world["operator_id"],
        client_id=scope,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin(world: dict[str, Any], clock: FakeClock) -> dict[str, str]:
    return headers_for(world, "admin", Role.operator_admin, clock)


@pytest.fixture
def rider(world: dict[str, Any], clock: FakeClock) -> dict[str, str]:
    return headers_for(world, "rider", Role.employee, clock)


WINDOW = "from=2026-09-25&to=2026-09-25"


# --- the report (OPA-05) ------------------------------------------------------------


async def test_the_report_counts_what_happened(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    body = (await client.get(f"/reports/trips?{WINDOW}", headers=admin)).json()

    assert body["requests"] == 8  # five completed, a no-show, a cancellation, one other client
    assert body["trips"] == 5
    assert body["no_shows"] == 1
    assert body["cancellations"] == 1


async def test_median_and_p90_wait_are_correct_on_the_fixture(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    """B18 acceptance. Waits of 4, 6, 9, 12 and 45 minutes."""
    body = (await client.get(f"/reports/trips?{WINDOW}", headers=admin)).json()

    assert body["median_wait_minutes"] == EXPECTED_MEDIAN
    assert body["p90_wait_minutes"] == pytest.approx(EXPECTED_P90, abs=0.05)


async def test_a_request_that_never_got_a_cab_has_no_wait(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    """Counting a cancellation as a zero-minute wait would flatter every average."""
    rows = (await client.get(f"/reports/trips?{WINDOW}", headers=admin)).json()["rows"]

    cancelled = next(row for row in rows if row["status"] == str(RequestStatus.cancelled))
    assert cancelled["wait_minutes"] is None


async def test_each_row_names_the_driver_and_vehicle(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    """OPA-05 asks for per-driver reporting."""
    rows = (await client.get(f"/reports/trips?{WINDOW}", headers=admin)).json()["rows"]

    completed = [row for row in rows if row["status"] == str(RequestStatus.dropped)]
    assert all(row["driver_id"] == str(world["driver"].id) for row in completed)
    assert all(row["vehicle_id"] == str(world["vehicle"].id) for row in completed)


async def test_the_client_filter_narrows_the_report(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    body = (
        await client.get(
            f"/reports/trips?{WINDOW}&client_id={world['other_client_id']}", headers=admin
        )
    ).json()

    assert body["requests"] == 1
    assert body["trips"] == 0


async def test_an_empty_window_reports_no_wait_rather_than_zero(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    body = (await client.get("/reports/trips?from=2020-01-01&to=2020-01-02", headers=admin)).json()

    assert body["requests"] == 0
    assert body["median_wait_minutes"] is None
    assert body["p90_wait_minutes"] is None


async def test_a_backwards_window_is_rejected(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    response = await client.get("/reports/trips?from=2026-09-25&to=2026-09-01", headers=admin)
    assert response.status_code == 422


async def test_the_window_includes_both_end_dates(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    """1st to 7th means seven days, not six and a bit."""
    one_day = (await client.get(f"/reports/trips?{WINDOW}", headers=admin)).json()
    assert one_day["requests"] == 8


# --- CSV (B18 acceptance) ----------------------------------------------------------------


async def test_the_csv_carries_every_row(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    response = await client.get(f"/reports/trips?{WINDOW}&format=csv", headers=admin)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert len(rows) == 8


async def test_the_csv_matches_the_json_totals(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    """B18 acceptance, stated exactly. A CSV that disagrees is worse than no CSV."""
    body = (await client.get(f"/reports/trips?{WINDOW}", headers=admin)).json()
    csv_rows = list(
        csv.DictReader(
            io.StringIO(
                (await client.get(f"/reports/trips?{WINDOW}&format=csv", headers=admin)).text
            )
        )
    )

    assert len(csv_rows) == body["requests"]
    assert (
        sum(1 for row in csv_rows if row["status"] == str(RequestStatus.no_show))
        == body["no_shows"]
    )
    assert (
        sum(1 for row in csv_rows if row["status"] == str(RequestStatus.cancelled))
        == body["cancellations"]
    )

    waits = sorted(float(row["wait_minutes"]) for row in csv_rows if row["wait_minutes"])
    assert waits == sorted(float(w) for w in WAITS)


async def test_the_csv_is_offered_as_a_download(
    client: AsyncClient, world: dict[str, Any], admin: dict[str, str]
) -> None:
    response = await client.get(f"/reports/trips?{WINDOW}&format=csv", headers=admin)
    assert "attachment" in response.headers["content-disposition"]


# --- who may read it ------------------------------------------------------------------------


async def test_a_supervisor_may_read_the_operational_report(
    client: AsyncClient, world: dict[str, Any], clock: FakeClock
) -> None:
    headers = headers_for(world, "supervisor", Role.supervisor, clock)
    assert (await client.get(f"/reports/trips?{WINDOW}", headers=headers)).status_code == 200


async def test_a_client_admin_sees_only_their_own_client(
    client: AsyncClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """Asking for another client's id must not widen what they get back."""
    headers = headers_for(world, "client_admin", Role.client_admin, clock)

    body = (
        await client.get(f"/reports/trips?{WINDOW}&client_id={world['client_id']}", headers=headers)
    ).json()

    assert body["requests"] == 1
    assert all(row["client_id"] == str(world["other_client_id"]) for row in body["rows"])


async def test_a_driver_may_not_read_the_report(
    client: AsyncClient, world: dict[str, Any], clock: FakeClock
) -> None:
    headers = headers_for(world, "driver", Role.driver, clock)
    assert (await client.get(f"/reports/trips?{WINDOW}", headers=headers)).status_code == 403


async def test_an_employee_may_not_read_the_report(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str]
) -> None:
    assert (await client.get(f"/reports/trips?{WINDOW}", headers=rider)).status_code == 403


# --- ratings (EMP-07) --------------------------------------------------------------------------


async def test_a_rider_can_rate_a_finished_ride(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str]
) -> None:
    request = world["completed"][0]

    response = await client.post(
        f"/ride-requests/{request.id}/rating",
        json={"rating": 4, "comment": "Driver was early"},
        headers=rider,
    )

    assert response.status_code == 201
    assert response.json()["rating"] == 4


async def test_a_ride_can_be_rated_only_once(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str]
) -> None:
    """EMP-07: "once per trip"."""
    request = world["completed"][1]
    await client.post(f"/ride-requests/{request.id}/rating", json={"rating": 5}, headers=rider)

    second = await client.post(
        f"/ride-requests/{request.id}/rating", json={"rating": 1}, headers=rider
    )
    assert second.status_code == 409


async def test_an_unfinished_ride_cannot_be_rated(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str], db_session: AsyncSession
) -> None:
    pending = RideRequest(
        operator_id=world["operator_id"],
        client_id=world["client_id"],
        employee_id=world["employee"].id,
        direction=Direction.to_office,
        office_id=world["completed"][0].office_id,
        location=world["employee"].home_location,
        requested_time=NOW,
        urgency=Urgency.medium,
        status=RequestStatus.assigned,
        expires_at=NOW + timedelta(hours=2),
    )
    db_session.add(pending)
    await db_session.flush()

    response = await client.post(
        f"/ride-requests/{pending.id}/rating", json={"rating": 5}, headers=rider
    )
    assert response.status_code == 409


async def test_nobody_can_rate_someone_elses_ride(
    client: AsyncClient, world: dict[str, Any], clock: FakeClock
) -> None:
    """Rating a ride you were not on puts words in the rider's mouth."""
    other = headers_for(world, "other_rider", Role.employee, clock)

    response = await client.post(
        f"/ride-requests/{world['completed'][2].id}/rating", json={"rating": 1}, headers=other
    )
    assert response.status_code in {403, 404}


@pytest.mark.parametrize("rating", [0, 6, -1])
async def test_a_rating_outside_one_to_five_is_rejected(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str], rating: int
) -> None:
    response = await client.post(
        f"/ride-requests/{world['completed'][3].id}/rating",
        json={"rating": rating},
        headers=rider,
    )
    assert response.status_code == 422


async def test_an_unknown_ride_is_a_404(
    client: AsyncClient, world: dict[str, Any], rider: dict[str, str]
) -> None:
    response = await client.post(
        f"/ride-requests/{uuid.uuid4()}/rating", json={"rating": 5}, headers=rider
    )
    assert response.status_code == 404


async def test_rating_needs_a_token(client: AsyncClient, world: dict[str, Any]) -> None:
    response = await client.post(
        f"/ride-requests/{world['completed'][0].id}/rating", json={"rating": 5}
    )
    assert response.status_code == 401


# --- the rider's own history (EMP-07) ------------------------------------------------------------


async def test_the_history_reports_the_wait_the_rider_had(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock
) -> None:
    from app.modules.reports.service import ReportService

    rows = await ReportService(db_session, clock).history(
        world["operator_id"], world["employee"].id
    )

    waits = sorted(row.wait_minutes for row in rows if row.wait_minutes is not None)
    assert waits == pytest.approx([float(w) for w in sorted(WAITS)])


async def test_the_history_is_only_the_riders_own(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock
) -> None:
    from app.modules.reports.service import ReportService

    rows = await ReportService(db_session, clock).history(
        world["operator_id"], world["employee"].id
    )
    assert all(row.employee_id == world["employee"].id for row in rows)


async def test_the_history_stops_at_ninety_days(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock
) -> None:
    """EMP-07: "my last 90 days of trips"."""
    from app.modules.reports.service import ReportService

    db_session.add(
        RideRequest(
            operator_id=world["operator_id"],
            client_id=world["client_id"],
            employee_id=world["employee"].id,
            direction=Direction.to_office,
            office_id=world["completed"][0].office_id,
            location=world["employee"].home_location,
            requested_time=NOW - timedelta(days=200),
            urgency=Urgency.medium,
            status=RequestStatus.dropped,
            expires_at=NOW - timedelta(days=200),
            created_at=NOW - timedelta(days=200),
        )
    )
    await db_session.flush()

    rows = await ReportService(db_session, clock).history(
        world["operator_id"], world["employee"].id
    )
    assert len(rows) == 7  # five completed plus the no-show and the cancellation


def test_the_fixture_waits_are_what_the_docstring_claims() -> None:
    """Guards the guard: if WAITS changes, the expected median and p90 must change too."""
    from app.domain.stats import median, p90

    assert median([float(w) for w in WAITS]) == EXPECTED_MEDIAN
    assert p90([float(w) for w in WAITS]) == pytest.approx(EXPECTED_P90, abs=0.05)


def test_the_report_window_constant_matches_the_fixture_dates() -> None:
    assert date(2026, 9, 25) == NOW.date()
