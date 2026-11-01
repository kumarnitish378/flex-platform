"""The per-client monthly billing export (B38).

The treatments (no-show, late cancel, distance basis) are provisional config keys because
OQ-01 and OQ-03 are open, so the tests state each treatment and what it must do to the
numbers - and the central property: the export reconciles with the `trip` and
`ride_request` rows it came from, however the treatments are set.
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
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import ActorType, Role
from app.domain.modes import Mode
from app.domain.state_machines import RequestStatus
from app.main import create_app
from app.modules.dispatch.models import Trip
from app.modules.reports.billing import BillingService
from app.modules.tenancy.models import Operator
from tests.builders import make_user, make_user_role, unique_phone
from tests.integration.ledger import cab, employee_at, make_ride, make_trip
from tests.integration.worlds import (
    OFFICE,
    World,
    add_client,
    add_employee,
    build_world,
    near,
    set_config,
)

pytestmark = pytest.mark.requires_db

OCT = datetime(2026, 10, 14, 4, 0, tzinfo=UTC)
JWT_SECRET = "billing-tests-secret-0123456789abcdef"


class Month:
    """A month of finished work across two clients, with every distance stated.

    Trip 1 (3 Oct): one A rider and one B rider share 20 km  -> 10 km each
    Trip 2 (4 Oct): one A rider alone, 12 km
    Trip 3 (5 Oct): a cab drove 5 km to an A rider who was not there (no-show)
    plus: an A request cancelled while queued, an A request cancelled after a cab was
    assigned, an A ride in September and one in November (both outside the month).
    """

    def __init__(self) -> None:
        self.world: World
        self.client_a: Any
        self.client_b: Any
        self.trips: list[Trip] = []


async def build_month(session: AsyncSession) -> Month:
    month = Month()
    world = await build_world(session, FakeClock(OCT), Mode.manual)
    month.world = world
    other_client, other_office = await add_client(session, world, "Client B", Mode.manual)
    month.client_a = world.client
    month.client_b = other_client

    a1 = await employee_at(session, world, "A One")
    a2 = await employee_at(session, world, "A Two")
    a3 = await employee_at(session, world, "A Three")
    b1 = await add_employee(
        session,
        world,
        near(*OFFICE, north_km=-4.0),
        "B One",
        client=other_client,
        office=other_office,
    )
    vehicle = await cab(session, world)

    t1 = await make_trip(
        session, world, vehicle, when=OCT - timedelta(days=11) + timedelta(hours=2), km=20.0
    )
    t2 = await make_trip(
        session, world, vehicle, when=OCT - timedelta(days=10) + timedelta(hours=2), km=12.0
    )
    t3 = await make_trip(
        session, world, vehicle, when=OCT - timedelta(days=9) + timedelta(hours=2), km=5.0
    )
    month.trips = [t1, t2, t3]

    day3, day4, day5 = (OCT - timedelta(days=days) for days in (11, 10, 9))
    await make_ride(
        session,
        world,
        a1,
        asked_at=day3,
        status=RequestStatus.dropped,
        trip=t1,
        wait_minutes=6,
        sequence=1,
    )
    await make_ride(
        session,
        world,
        b1,
        asked_at=day3,
        status=RequestStatus.dropped,
        trip=t1,
        wait_minutes=9,
        sequence=2,
    )
    await make_ride(
        session, world, a2, asked_at=day4, status=RequestStatus.dropped, trip=t2, wait_minutes=5
    )
    await make_ride(session, world, a3, asked_at=day5, status=RequestStatus.no_show, trip=t3)
    await make_ride(session, world, a1, asked_at=OCT, status=RequestStatus.cancelled)
    await make_ride(
        session,
        world,
        a2,
        asked_at=OCT + timedelta(days=1),
        status=RequestStatus.cancelled,
        assigned_by=ActorType.supervisor,
    )
    await make_ride(
        session,
        world,
        a1,
        asked_at=datetime(2026, 9, 30, 6, 0, tzinfo=UTC),
        status=RequestStatus.cancelled,
    )
    await make_ride(
        session,
        world,
        a1,
        asked_at=datetime(2026, 11, 2, 6, 0, tzinfo=UTC),
        status=RequestStatus.cancelled,
    )
    return month


async def export(session: AsyncSession, month: Month, client: Any, **config: Any) -> dict[str, Any]:
    if config:
        await set_config(session, month.world, **config)
    built = await BillingService(session, month.world.clock).export(
        month.world.operator_id, client.id, "2026-10"
    )
    return built.as_dict()


async def test_the_default_treatment_and_what_it_adds_up_to(db_session: AsyncSession) -> None:
    month = await build_month(db_session)

    result = await export(db_session, month, month.client_a)

    assert result["treatment"] == {
        "no_show_billable": True,
        "late_cancel_billable": False,
        "distance_basis": "trip_share",
        "basis": "per_km",
        "rate_per_km": None,
    }
    summary = result["summary"]
    assert summary["rides"] == 5, "September and November are outside October"
    assert summary["completed"] == 2 and summary["no_shows"] == 1 and summary["cancellations"] == 2
    assert summary["billable_rides"] == 3  # two completed rides and the billed no-show
    assert summary["billable_trips"] == 3
    assert summary["riders"] == 3
    assert summary["billable_km"] == 27.0  # 10 (half of trip 1) + 12 + 5 (the no-show's trip)


async def test_a_pooled_trips_kilometres_are_shared_so_the_clients_add_up_to_the_trip(
    db_session: AsyncSession,
) -> None:
    """Reconciliation: across clients, billed km equals the km the cab drove."""
    month = await build_month(db_session)

    a = (await export(db_session, month, month.client_a))["summary"]["billable_km"]
    b = (await export(db_session, month, month.client_b))["summary"]["billable_km"]

    driven = await db_session.scalar(
        select(func.sum(Trip.actual_distance_m) / 1000.0).where(
            Trip.id.in_([t.id for t in month.trips])
        )
    )
    assert b == 10.0
    assert a + b == pytest.approx(driven)


async def test_every_row_traces_to_a_ride_and_says_why_it_is_or_is_not_billed(
    db_session: AsyncSession,
) -> None:
    month = await build_month(db_session)

    rows = (await export(db_session, month, month.client_a))["rows"]

    reasons = sorted(row["billable_reason"] for row in rows)
    assert reasons == [
        "cancelled_before_assignment",
        "completed",
        "completed",
        "late_cancel_not_billed",
        "no_show_billed",
    ]
    pooled = next(r for r in rows if r["riders_on_trip"] == 2)
    assert pooled["trip_share_km"] == 10.0 and pooled["billable_km"] == 10.0
    assert all(r["employee"] for r in rows)


async def test_no_show_treatment_changes_the_invoice_and_nothing_else(
    db_session: AsyncSession,
) -> None:
    month = await build_month(db_session)

    billed = (await export(db_session, month, month.client_a))["summary"]
    not_billed = (await export(db_session, month, month.client_a, billing_no_show_billable=False))[
        "summary"
    ]

    assert billed["rides"] == not_billed["rides"], "the rides are the same; only billing differs"
    assert not_billed["billable_rides"] == billed["billable_rides"] - 1
    assert not_billed["billable_km"] == billed["billable_km"] - 5.0


async def test_a_late_cancellation_is_billed_only_if_the_operator_says_so(
    db_session: AsyncSession,
) -> None:
    month = await build_month(db_session)

    default = (await export(db_session, month, month.client_a))["summary"]
    late = await export(db_session, month, month.client_a, billing_late_cancel_billable=True)
    reasons = {row["billable_reason"] for row in late["rows"]}

    assert late["summary"]["billable_rides"] == default["billable_rides"] + 1
    assert "late_cancel_billed" in reasons
    assert "cancelled_before_assignment" in reasons, "never assigned: never billable"
    assert late["summary"]["billable_km"] == default["billable_km"], "no cab drove for it"


async def test_the_direct_basis_bills_the_riders_own_journey_whatever_the_pooling(
    db_session: AsyncSession,
) -> None:
    month = await build_month(db_session)

    direct = await export(db_session, month, month.client_a, billing_distance_basis="direct")

    completed = [r for r in direct["rows"] if r["billable_reason"] == "completed"]
    assert all(r["billable_km"] == r["direct_km"] and r["direct_km"] > 0 for r in completed)
    assert direct["summary"]["billable_km"] != 27.0


async def test_a_month_is_the_operators_calendar_month(db_session: AsyncSession) -> None:
    """A ride asked at 00:30 IST on 1 October is October's, though it is 30 September in UTC."""
    month = await build_month(db_session)
    await db_session.execute(
        update(Operator)
        .where(Operator.id == month.world.operator_id)
        .values(timezone="Asia/Kolkata")
    )
    rider = await employee_at(db_session, month.world, "Midnight")
    await make_ride(
        db_session,
        month.world,
        rider,
        asked_at=datetime(2026, 9, 30, 19, 0, tzinfo=UTC),
        status=RequestStatus.cancelled,
    )

    rows = (await export(db_session, month, month.client_a))["rows"]

    assert any(row["employee"] == "Midnight" and row["date"] == "2026-10-01" for row in rows)


async def test_a_trip_with_no_measured_distance_bills_zero_km_not_a_guess(
    db_session: AsyncSession,
) -> None:
    month = await build_month(db_session)
    await db_session.execute(
        update(Trip).where(Trip.id == month.trips[1].id).values(actual_distance_m=None)
    )

    result = await export(db_session, month, month.client_a)

    assert result["summary"]["billable_km"] == 15.0  # 10 + 0 + 5


async def test_a_bad_month_is_refused(db_session: AsyncSession) -> None:
    from app.domain.errors import ValidationFailed

    month = await build_month(db_session)

    for bad in ("2026-13", "October", "2026-1", ""):
        with pytest.raises(ValidationFailed):
            await BillingService(db_session, month.world.clock).export(
                month.world.operator_id, month.client_a.id, bad
            )


async def test_another_operators_client_is_not_found(db_session: AsyncSession) -> None:
    from app.domain.errors import NotFound

    month = await build_month(db_session)

    with pytest.raises(NotFound):
        await BillingService(db_session, month.world.clock).export(
            uuid.uuid4(), month.client_a.id, "2026-10"
        )


# --- the endpoint ----------------------------------------------------------------


@pytest_asyncio.fixture
async def api(
    db_session: AsyncSession,
) -> AsyncIterator[tuple[AsyncClient, Month, dict[str, dict[str, str]]]]:
    month = await build_month(db_session)
    clock = month.world.clock
    admin = make_user(name="Admin", phone=unique_phone())
    client_user = make_user(name="Client admin", phone=unique_phone())
    supervisor = make_user(name="Sunil", phone=unique_phone())
    db_session.add_all([admin, client_user, supervisor])
    await db_session.flush()
    operator_id = month.world.operator_id
    db_session.add(make_user_role(admin.id, Role.operator_admin, operator_id=operator_id))
    db_session.add(
        make_user_role(
            client_user.id, Role.client_admin, operator_id=operator_id, client_id=month.client_a.id
        )
    )
    db_session.add(make_user_role(supervisor.id, Role.supervisor, operator_id=operator_id))
    await db_session.flush()
    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
        routing_provider="approx",
    )
    application: FastAPI = create_app(settings=settings, clock=clock)

    class _Factory:
        def __call__(self) -> object:
            return _NoClose(db_session)

    application.state.session_factory = _Factory()

    def token(user: Any, role: Role, client_id: uuid.UUID | None = None) -> dict[str, str]:
        value, _ = create_access_token(
            user_id=user.id,
            role=str(role),
            secret=JWT_SECRET,
            clock=clock,
            ttl_seconds=900,
            operator_id=operator_id,
            client_id=client_id,
        )
        return {"Authorization": f"Bearer {value}"}

    headers = {
        "admin": token(admin, Role.operator_admin),
        "client": token(client_user, Role.client_admin, month.client_a.id),
        "supervisor": token(supervisor, Role.supervisor),
    }
    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://test/api/v1"
    ) as http:
        yield http, month, headers


class _NoClose:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


async def test_the_endpoint_serves_json_and_a_csv_with_the_same_rows(
    api: tuple[AsyncClient, Month, dict[str, dict[str, str]]],
) -> None:
    http, month, headers = api
    url = f"/reports/billing?month=2026-10&client_id={month.client_a.id}"

    as_json = await http.get(url, headers=headers["admin"])
    as_csv = await http.get(url + "&format=csv", headers=headers["admin"])

    assert as_json.status_code == 200 and as_csv.status_code == 200
    lines = as_csv.text.splitlines()
    assert lines[0].startswith("date,request_id,employee,direction,status,billable")
    assert len(lines) - 1 == len(as_json.json()["rows"]) == 5
    assert "attachment" in as_csv.headers["content-disposition"]


async def test_a_client_admin_is_invoiced_for_their_own_people_whatever_they_ask(
    api: tuple[AsyncClient, Month, dict[str, dict[str, str]]],
) -> None:
    http, month, headers = api

    asking_for_b = await http.get(
        f"/reports/billing?month=2026-10&client_id={month.client_b.id}", headers=headers["client"]
    )

    assert asking_for_b.status_code == 200
    assert asking_for_b.json()["client_id"] == str(month.client_a.id)


async def test_a_supervisor_has_no_billing_and_an_admin_must_name_a_client(
    api: tuple[AsyncClient, Month, dict[str, dict[str, str]]],
) -> None:
    http, month, headers = api

    assert (
        await http.get(
            f"/reports/billing?month=2026-10&client_id={month.client_a.id}",
            headers=headers["supervisor"],
        )
    ).status_code == 403
    assert (
        await http.get("/reports/billing?month=2026-10", headers=headers["admin"])
    ).status_code == 422
    assert (
        await http.get(
            f"/reports/billing?month=2026-1&client_id={month.client_a.id}", headers=headers["admin"]
        )
    ).status_code == 422


# --- per kilometre (owner decision, OQ-03) ---------------------------------------------


async def test_the_client_is_billed_per_kilometre_at_the_operators_rate(
    db_session: AsyncSession,
) -> None:
    month = await build_month(db_session)

    result = await export(db_session, month, month.client_a, billing_rate_per_km=12.5)

    assert result["treatment"]["basis"] == "per_km"
    assert result["treatment"]["rate_per_km"] == 12.5
    assert result["summary"]["billable_km"] == 27.0
    assert result["summary"]["amount"] == 337.5  # 27 km x 12.5


async def test_without_a_rate_there_is_a_distance_and_never_a_guessed_price(
    db_session: AsyncSession,
) -> None:
    month = await build_month(db_session)

    result = await export(db_session, month, month.client_a)

    assert result["summary"]["billable_km"] == 27.0
    assert result["summary"]["amount"] is None


async def test_a_trip_count_is_information_not_the_basis(db_session: AsyncSession) -> None:
    """Three billable trips of different lengths: the amount follows the km, not the count."""
    month = await build_month(db_session)

    result = await export(db_session, month, month.client_a, billing_rate_per_km=1)

    assert result["summary"]["billable_trips"] == 3
    assert result["summary"]["amount"] == result["summary"]["billable_km"]


async def test_riders_never_see_a_charge(
    api: tuple[AsyncClient, Month, dict[str, dict[str, str]]],
) -> None:
    """Riders do not pay: no billing for the employee role, and no money in their ride payloads."""
    from app.domain.enums import Role as _Role
    from app.modules.auth.permissions import Permission, permissions_for
    from app.modules.requests.schemas import RideRequestOut

    assert Permission.billing_view not in permissions_for(_Role.employee)
    money = ("amount", "price", "charge", "fare", "cost", "rate", "km_billed", "billable")
    leaked = [name for name in RideRequestOut.model_fields if any(word in name for word in money)]
    assert leaked == []
