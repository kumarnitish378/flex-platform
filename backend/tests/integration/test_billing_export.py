"""Per-cab-per-day billing against a real database (B38; owner decision 2026-11-02, OQ-03).

The employer company pays per cab per day on the km between duty start and duty end, dead km
included, at the operator's rate per km. Riders never pay. Each test states the distances it
needs, so every number below can be checked by hand.
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
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.geo import to_point
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import Role
from app.domain.errors import Conflict, NotFound, ValidationFailed
from app.domain.modes import Mode
from app.domain.state_machines import RequestStatus
from app.main import create_app
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Vehicle
from app.modules.reports.billing import BillingService
from app.modules.tracking.models import LocationPing
from tests.builders import make_user, make_user_role, unique_phone
from tests.integration.ledger import make_ride, make_trip
from tests.integration.worlds import (
    NOW,
    OFFICE,
    World,
    add_cab,
    add_client,
    add_employee,
    build_world,
    near,
    set_config,
)

pytestmark = pytest.mark.requires_db

JWT_SECRET = "billing-tests-secret-0123456789abcdef"
MONTH = "2026-10"
# 09:00 IST on the 5th. The operator's timezone is Asia/Kolkata, so this is the 5th locally.
NINE_IST = datetime(2026, 10, 5, 3, 30, tzinfo=UTC)


class Fleet:
    """One operator, two clients, one cab, and helpers to give the cab duty sessions."""

    def __init__(self) -> None:
        self.world: World
        self.cab: Vehicle
        self.client_b: Any
        self.office_b: Any
        self.driver_id: uuid.UUID

    async def duty(
        self,
        session: AsyncSession,
        *,
        start: datetime = NINE_IST,
        hours: float | None = 9,
        gps_km: float | None = None,
        odometer: tuple[float, float] | None = None,
        cab: Vehicle | None = None,
    ) -> DutySession:
        vehicle = cab or self.cab
        row = DutySession(
            id=uuid.uuid4(),
            operator_id=self.world.operator_id,
            driver_id=self.driver_id,
            vehicle_id=vehicle.id,
            started_at=start,
            ended_at=None if hours is None else start + timedelta(hours=hours),
            gps_distance_m=None if gps_km is None else gps_km * 1000.0,
            odometer_start_km=odometer[0] if odometer else None,
            odometer_end_km=odometer[1] if odometer else None,
        )
        session.add(row)
        await session.flush()
        return row

    async def carry(
        self, session: AsyncSession, *, client: Any, when: datetime, name: str = "Rider"
    ) -> None:
        """A finished trip on the cab carrying one rider of `client`."""
        trip = await make_trip(session, self.world, self.cab, when=when, km=10.0)
        office = self.world.office if client is self.world.client else self.office_b
        rider = await add_employee(
            session, self.world, near(*OFFICE, north_km=-4), name, client=client, office=office
        )
        await make_ride(
            session,
            self.world,
            rider,
            asked_at=when - timedelta(hours=1),
            status=RequestStatus.dropped,
            trip=trip,
            wait_minutes=5,
        )


async def build_fleet(session: AsyncSession, *, rate: float = 8.0) -> Fleet:
    fleet = Fleet()
    fleet.world = await build_world(session, FakeClock(NOW), Mode.manual)
    fleet.cab = await add_cab(session, fleet.world, OFFICE)
    # `add_cab` opens a duty session of its own; the tests build theirs.
    existing = (await session.execute(select(DutySession))).scalars().one()
    fleet.driver_id = existing.driver_id
    await session.execute(delete(DutySession).where(DutySession.id == existing.id))
    await session.execute(delete(LocationPing).where(LocationPing.vehicle_id == fleet.cab.id))
    fleet.client_b, fleet.office_b = await add_client(session, fleet.world, "Client B", Mode.manual)
    # Both clients were created in one transaction, so `created_at` ties; name the default.
    await set_config(session, fleet.world, billing_default_client_id=str(fleet.world.client.id))
    if rate:
        await set_config(session, fleet.world, billing_rate_per_km=rate)
    return fleet


async def export(session: AsyncSession, fleet: Fleet, client: Any = None) -> dict[str, Any]:
    result = await BillingService(session, fleet.world.clock).export(
        fleet.world.operator_id, (client or fleet.world.client).id, MONTH
    )
    return result.as_dict()


# --- the basis: one row per cab per day -------------------------------------------------


async def test_a_cab_day_is_billed_on_its_running_km_at_the_rate(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, gps_km=112.5)

    result = await export(db_session, fleet)

    assert result["treatment"]["basis"] == "per_cab_per_day_km"
    assert result["treatment"]["rate_per_km"] == 8.0
    [row] = result["rows"]
    assert row["date"] == "2026-10-05" and row["gps_km"] == 112.5 and row["billed_km"] == 112.5
    assert row["amount"] == 900.0
    assert result["summary"]["amount"] == 900.0 and result["summary"]["cab_days"] == 1


async def test_dead_km_between_trips_are_in_the_day_with_no_trip_at_all(
    db_session: AsyncSession,
) -> None:
    """The cab drove 60 km and carried nobody: the day is still billed."""
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, gps_km=60.0)

    result = await export(db_session, fleet)

    assert result["summary"]["billed_km"] == 60.0
    assert result["rows"][0]["flags"] == ["no_client_trips"]  # one client: the default, but say so


async def test_two_sessions_on_one_cab_one_day_make_one_row(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, hours=4, gps_km=40.0)
    await fleet.duty(db_session, start=NINE_IST + timedelta(hours=5), hours=4, gps_km=25.0)

    result = await export(db_session, fleet)

    [row] = result["rows"]
    assert row["billed_km"] == 65.0 and len(row["sessions"]) == 2
    assert row["duty_out"] > row["duty_in"]


async def test_the_day_is_the_operators_local_day(db_session: AsyncSession) -> None:
    """23:30 IST on the 5th is 18:00 UTC: it belongs to the 5th, not the 6th."""
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, start=datetime(2026, 10, 5, 18, 0, tzinfo=UTC), hours=3, gps_km=30)
    await fleet.duty(db_session, start=datetime(2026, 10, 5, 19, 0, tzinfo=UTC), hours=3, gps_km=5)

    result = await export(db_session, fleet)

    assert [row["date"] for row in result["rows"]] == ["2026-10-05", "2026-10-06"]


async def test_other_months_are_not_on_the_invoice(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, start=datetime(2026, 9, 30, 3, 0, tzinfo=UTC), gps_km=50)
    await fleet.duty(db_session, start=datetime(2026, 11, 1, 3, 0, tzinfo=UTC), gps_km=70)
    await fleet.duty(db_session, gps_km=10)

    assert (await export(db_session, fleet))["summary"]["billed_km"] == 10.0


async def test_without_a_rate_there_are_kilometres_and_no_price(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session, rate=0)
    await fleet.duty(db_session, gps_km=50.0)

    result = await export(db_session, fleet)

    assert result["summary"]["billed_km"] == 50.0 and result["summary"]["amount"] is None
    assert result["rows"][0]["amount"] is None


# --- GPS, from the pings --------------------------------------------------------------------


async def _pings(
    session: AsyncSession, fleet: Fleet, points: list[tuple[float, tuple[float, float]]]
) -> None:
    for minutes, place in points:
        session.add(
            LocationPing(
                vehicle_id=fleet.cab.id,
                operator_id=fleet.world.operator_id,
                recorded_at=NINE_IST + timedelta(minutes=minutes),
                received_at=NINE_IST + timedelta(minutes=minutes),
                location=to_point(*place),
                source="sim",
            )
        )
    await session.flush()


async def test_a_session_still_open_is_measured_from_its_pings_so_far(
    db_session: AsyncSession,
) -> None:
    fleet = await build_fleet(db_session)
    fleet.world.clock.set(NINE_IST + timedelta(hours=2))
    await fleet.duty(db_session, hours=None)
    start = near(*OFFICE, north_km=0)
    await _pings(
        db_session,
        fleet,
        [(0, start), (10, near(*start, north_km=2)), (20, near(*start, north_km=5))],
    )

    [row] = (await export(db_session, fleet))["rows"]

    assert 4.9 < row["gps_km"] < 5.1
    assert "still_on_duty" in row["flags"] and row["duty_out"] is None


async def test_a_gps_jump_is_ignored_not_billed(db_session: AsyncSession) -> None:
    """A bad fix 80 km away for one minute would otherwise add 160 km to the day."""
    fleet = await build_fleet(db_session)
    fleet.world.clock.set(NINE_IST + timedelta(hours=2))
    await fleet.duty(db_session, hours=None)
    start = near(*OFFICE, north_km=0)
    await _pings(
        db_session,
        fleet,
        [
            (0, start),
            (10, near(*start, north_km=2)),
            (11, near(*start, north_km=80)),  # the bad fix
            (20, near(*start, north_km=5)),
        ],
    )

    [row] = (await export(db_session, fleet))["rows"]

    assert 4.9 < row["gps_km"] < 5.1


async def test_a_session_with_no_pings_has_no_gps_figure_and_says_so(
    db_session: AsyncSession,
) -> None:
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, gps_km=None)

    [row] = (await export(db_session, fleet))["rows"]

    assert row["gps_km"] is None and row["billed_km"] == 0.0 and "no_gps" in row["flags"]


# --- the odometer -----------------------------------------------------------------------------


async def test_an_odometer_within_ten_percent_is_quiet(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, gps_km=100.0, odometer=(12_000, 12_105))

    [row] = (await export(db_session, fleet))["rows"]

    assert row["odometer_km"] == 105.0 and row["billed_km"] == 100.0
    assert "odometer_gap" not in row["flags"]


async def test_a_gap_over_the_threshold_flags_the_row_and_still_bills_gps(
    db_session: AsyncSession,
) -> None:
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, gps_km=100.0, odometer=(12_000, 12_130))

    [row] = (await export(db_session, fleet))["rows"]

    assert "odometer_gap" in row["flags"] and row["gap_percent"] == 23.1
    assert row["billed_km"] == 100.0


async def test_the_threshold_is_the_operators_to_set(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session)
    await set_config(db_session, fleet.world, billing_odometer_gap_percent=2)
    await fleet.duty(db_session, gps_km=100.0, odometer=(12_000, 12_105))

    assert "odometer_gap" in (await export(db_session, fleet))["rows"][0]["flags"]


async def test_an_operator_can_bill_a_session_on_its_odometer(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session)
    duty = await fleet.duty(db_session, gps_km=100.0, odometer=(12_000, 12_130))
    admin = make_user(name="Admin", phone=unique_phone())
    db_session.add(admin)
    await db_session.flush()
    billing = BillingService(db_session, fleet.world.clock)

    await billing.set_basis(fleet.world.operator_id, admin.id, duty.id, "odometer", "GPS dropped")
    [row] = (await export(db_session, fleet))["rows"]

    assert row["billed_km"] == 130.0 and row["amount"] == 1040.0
    assert "odometer_billed" in row["flags"]
    await db_session.refresh(duty)
    assert duty.billing_basis_set_by == admin.id and duty.billing_basis_note == "GPS dropped"


async def test_the_odometer_cannot_be_billed_without_both_readings(
    db_session: AsyncSession,
) -> None:
    fleet = await build_fleet(db_session)
    duty = await fleet.duty(db_session, gps_km=100.0, odometer=None)
    billing = BillingService(db_session, fleet.world.clock)

    with pytest.raises(Conflict):
        await billing.set_basis(fleet.world.operator_id, uuid.uuid4(), duty.id, "odometer", None)
    with pytest.raises(ValidationFailed):
        await billing.set_basis(fleet.world.operator_id, uuid.uuid4(), duty.id, "vibes", None)
    with pytest.raises(NotFound):
        await billing.set_basis(fleet.world.operator_id, uuid.uuid4(), uuid.uuid4(), "gps", None)


# --- which client pays --------------------------------------------------------------------------


async def test_a_cab_day_goes_to_the_client_whose_riders_it_carried(
    db_session: AsyncSession,
) -> None:
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, gps_km=80.0)
    await fleet.carry(db_session, client=fleet.client_b, when=NINE_IST + timedelta(hours=2))

    a = await export(db_session, fleet)
    b = await export(db_session, fleet, fleet.client_b)

    assert a["rows"] == [] and a["summary"]["billed_km"] == 0.0
    assert b["summary"]["billed_km"] == 80.0 and b["rows"][0]["flags"] == []


async def test_a_cab_serving_two_clients_is_billed_to_the_default_and_flagged(
    db_session: AsyncSession,
) -> None:
    fleet = await build_fleet(db_session)
    await set_config(db_session, fleet.world, billing_default_client_id=str(fleet.world.client.id))
    await fleet.duty(db_session, gps_km=90.0)
    await fleet.carry(db_session, client=fleet.world.client, when=NINE_IST + timedelta(hours=1))
    await fleet.carry(
        db_session, client=fleet.client_b, when=NINE_IST + timedelta(hours=3), name="Other"
    )

    a = await export(db_session, fleet)
    b = await export(db_session, fleet, fleet.client_b)

    assert a["rows"][0]["flags"] == ["multiple_clients"]
    assert a["summary"]["billed_km"] == 90.0
    assert b["rows"] == [], "billed once, to one client"


async def test_with_several_clients_and_no_default_the_oldest_is_used_and_it_says_so(
    db_session: AsyncSession,
) -> None:
    fleet = await build_fleet(db_session)
    await set_config(db_session, fleet.world, billing_default_client_id="")
    await fleet.duty(db_session, gps_km=40.0)

    rows = (await export(db_session, fleet))["rows"] + (
        await export(db_session, fleet, fleet.client_b)
    )["rows"]

    assert len(rows) == 1, "billed once, to whichever client is oldest"
    assert "default_client_unset" in rows[0]["flags"]


# --- the CSV and the endpoint ------------------------------------------------------------


async def test_the_csv_is_one_line_per_cab_day_and_a_total(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session)
    await fleet.duty(db_session, gps_km=100.0)
    await fleet.duty(db_session, start=NINE_IST + timedelta(days=1), gps_km=50.0)

    csv_text = (
        await BillingService(db_session, fleet.world.clock).export(
            fleet.world.operator_id, fleet.world.client.id, MONTH
        )
    ).as_csv()

    lines = csv_text.splitlines()
    assert lines[0].startswith("date,cab,drivers,duty_in,duty_out,gps_km,odometer_km")
    assert len(lines) == 1 + 2 + 1
    assert lines[-1].startswith("TOTAL,2 cab-days") and ",150.0,8.0,1200.0," in lines[-1]


async def test_a_bad_month_is_refused(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session)

    for bad in ("2026-13", "October", "2026-1", ""):
        with pytest.raises(ValidationFailed):
            await BillingService(db_session, fleet.world.clock).export(
                fleet.world.operator_id, fleet.world.client.id, bad
            )


async def test_another_operators_client_is_not_found(db_session: AsyncSession) -> None:
    fleet = await build_fleet(db_session)

    with pytest.raises(NotFound):
        await BillingService(db_session, fleet.world.clock).export(
            uuid.uuid4(), fleet.world.client.id, MONTH
        )


class _NoClose:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


@pytest_asyncio.fixture
async def api(
    db_session: AsyncSession,
) -> AsyncIterator[tuple[AsyncClient, Fleet, dict[str, dict[str, str]], DutySession]]:
    fleet = await build_fleet(db_session)
    duty = await fleet.duty(db_session, gps_km=100.0, odometer=(12_000, 12_130))
    clock = fleet.world.clock
    people = {}
    for label, role, client in (
        ("admin", Role.operator_admin, None),
        ("client", Role.client_admin, fleet.world.client),
        ("other_client", Role.client_admin, fleet.client_b),
        ("supervisor", Role.supervisor, None),
        ("employee", Role.employee, fleet.world.client),
    ):
        user = make_user(name=label, phone=unique_phone())
        db_session.add(user)
        await db_session.flush()
        db_session.add(
            make_user_role(
                user.id,
                role,
                operator_id=fleet.world.operator_id,
                client_id=client.id if client else None,
            )
        )
        people[label] = (user, role, client)
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
    headers = {}
    for label, (user, role, client) in people.items():
        token, _ = create_access_token(
            user_id=user.id,
            role=str(role),
            secret=JWT_SECRET,
            clock=clock,
            ttl_seconds=900,
            operator_id=fleet.world.operator_id,
            client_id=client.id if client else None,
        )
        headers[label] = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://test/api/v1"
    ) as http:
        yield http, fleet, headers, duty


async def test_the_endpoint_serves_json_and_the_same_rows_as_csv(
    api: tuple[AsyncClient, Fleet, dict[str, dict[str, str]], DutySession],
) -> None:
    http, fleet, headers, _ = api
    url = f"/reports/billing?month={MONTH}&client_id={fleet.world.client.id}"

    as_json = await http.get(url, headers=headers["admin"])
    as_csv = await http.get(url + "&format=csv", headers=headers["admin"])

    assert as_json.status_code == 200 and as_csv.status_code == 200, as_json.text
    assert len(as_csv.text.splitlines()) - 2 == len(as_json.json()["rows"]) == 1
    assert "attachment" in as_csv.headers["content-disposition"]


async def test_a_client_admin_is_invoiced_for_their_own_company_whatever_they_ask(
    api: tuple[AsyncClient, Fleet, dict[str, dict[str, str]], DutySession],
) -> None:
    http, fleet, headers, _ = api

    response = await http.get(
        f"/reports/billing?month={MONTH}&client_id={fleet.client_b.id}", headers=headers["client"]
    )

    assert response.status_code == 200
    assert response.json()["client_id"] == str(fleet.world.client.id)


async def test_riders_and_supervisors_have_no_billing_and_an_admin_must_name_a_client(
    api: tuple[AsyncClient, Fleet, dict[str, dict[str, str]], DutySession],
) -> None:
    http, fleet, headers, _ = api

    assert (
        await http.get(f"/reports/billing?month={MONTH}", headers=headers["supervisor"])
    ).status_code == 403
    assert (
        await http.get(f"/reports/billing?month={MONTH}", headers=headers["employee"])
    ).status_code == 403
    assert (
        await http.get(f"/reports/billing?month={MONTH}", headers=headers["admin"])
    ).status_code == 422


async def test_marking_the_odometer_over_http_is_an_operator_admins_call(
    api: tuple[AsyncClient, Fleet, dict[str, dict[str, str]], DutySession],
) -> None:
    http, fleet, headers, duty = api
    path = f"/admin/duty-sessions/{duty.id}/billing-basis"

    refused = await http.put(path, json={"basis": "odometer"}, headers=headers["client"])
    done = await http.put(path, json={"basis": "odometer", "note": "ok"}, headers=headers["admin"])
    report = await http.get(
        f"/reports/billing?month={MONTH}&client_id={fleet.world.client.id}",
        headers=headers["admin"],
    )

    assert refused.status_code == 403
    assert done.status_code == 200 and done.json()["basis"] == "odometer"
    assert report.json()["rows"][0]["billed_km"] == 130.0
