"""The full operator report, each number reproduced from a fixture worked out by hand (B39)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.domain.enums import ActorType
from app.domain.failsafe import SuggestionStatus
from app.domain.modes import Mode
from app.domain.overrides import OverrideAction, ReasonCode
from app.domain.state_machines import RequestStatus
from app.modules.dispatch.optimizer_models import OptimizerRun
from app.modules.dispatch.override_models import OverrideLog
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.reports.operations import OperationsReportService
from tests.integration.ledger import cab, employee_at, make_ride, make_trip
from tests.integration.worlds import World, build_world

pytestmark = pytest.mark.requires_db

DAY = datetime(2026, 10, 14, 4, 0, tzinfo=UTC)  # 09:30 IST on a Wednesday
PERIOD = (date(2026, 10, 14), date(2026, 10, 14))


async def fixture_world(session: AsyncSession) -> World:
    return await build_world(session, FakeClock(DAY + timedelta(hours=12)), Mode.manual)


async def run(session: AsyncSession, world: World, client_id: uuid.UUID | None = None):  # type: ignore[no-untyped-def]
    return await OperationsReportService(session, world.clock).report(
        world.operator_id, *PERIOD, client_id=client_id
    )


async def test_requests_and_the_wait_distribution(db_session: AsyncSession) -> None:
    world = await fixture_world(db_session)
    waits = [3, 4, 6, 12, 25, 70]  # one per bucket edge case
    trips = [
        await make_trip(
            db_session, world, await cab(db_session, world), when=DAY + timedelta(hours=2), km=10
        )
        for _ in waits
    ]
    for index, (minutes, trip) in enumerate(zip(waits, trips, strict=True)):
        rider = await employee_at(db_session, world, f"R{index}")
        await make_ride(
            db_session,
            world,
            rider,
            asked_at=DAY,
            status=RequestStatus.dropped,
            trip=trip,
            wait_minutes=minutes,
        )
    rider = await employee_at(db_session, world, "NS")
    await make_ride(db_session, world, rider, asked_at=DAY, status=RequestStatus.no_show)
    for name in ("C1", "C2"):
        await make_ride(
            db_session,
            world,
            await employee_at(db_session, world, name),
            asked_at=DAY,
            status=RequestStatus.cancelled,
        )
    await make_ride(
        db_session,
        world,
        await employee_at(db_session, world, "EX"),
        asked_at=DAY,
        status=RequestStatus.expired,
    )
    await make_ride(
        db_session,
        world,
        await employee_at(db_session, world, "Q"),
        asked_at=DAY,
        status=RequestStatus.queued,
    )

    report = (await run(db_session, world)).as_dict()

    assert report["requests"] == {
        "total": 11,
        "completed": 6,
        "no_shows": 1,
        "cancelled": 2,
        "expired": 1,
        "still_open": 1,
    }
    wait = report["wait"]
    assert wait["measured"] == 6
    # Linear interpolation between closest ranks (R type 7), as the Phase 1 report defines it.
    assert wait["median_minutes"] == 9.0
    assert wait["p90_minutes"] == 47.5
    assert wait["distribution"] == {
        "0-5": 2,
        "5-10": 1,
        "10-15": 1,
        "15-20": 0,
        "20-30": 1,
        "30-45": 0,
        "45-60": 0,
        "60+": 1,
    }


async def test_pooling_vehicles_and_cab_km_come_from_the_trips_the_cabs_drove(
    db_session: AsyncSession,
) -> None:
    world = await fixture_world(db_session)
    cabs = [await cab(db_session, world) for _ in range(3)]
    # Four trips carrying 1, 2, 2 and 3 riders; cab 0 drives two of them.
    plan = [(cabs[0], 10.0, 1), (cabs[1], 20.0, 2), (cabs[2], 30.0, 2), (cabs[0], 40.0, 3)]
    for number, (vehicle, km, riders) in enumerate(plan):
        trip = await make_trip(
            db_session, world, vehicle, when=DAY + timedelta(hours=1 + number), km=km
        )
        for seat in range(riders):
            await make_ride(
                db_session,
                world,
                await employee_at(db_session, world, f"T{number}R{seat}"),
                asked_at=DAY,
                status=RequestStatus.dropped,
                trip=trip,
                wait_minutes=5,
                sequence=seat + 1,
            )
    # A trip that never carried anyone, and one with no measured distance: neither counts.
    await make_trip(db_session, world, cabs[1], when=DAY + timedelta(hours=8), km=99.0)
    unmeasured = await make_trip(db_session, world, cabs[2], when=DAY + timedelta(hours=9), km=None)
    await make_ride(
        db_session,
        world,
        await employee_at(db_session, world, "UM"),
        asked_at=DAY,
        status=RequestStatus.dropped,
        trip=unmeasured,
        wait_minutes=5,
    )

    report = (await run(db_session, world)).as_dict()

    pooling, distance = report["pooling"], report["distance"]
    assert pooling["trips"] == 5
    assert pooling["riders_carried"] == 9
    assert pooling["riders_per_trip"] == 1.8
    assert pooling["pooled_trips"] == 3 and pooling["pooling_rate"] == 0.6
    assert pooling["vehicles_used"] == 3
    # 10 + 20 + 30 + 40 over the four trips whose distance was measured.
    assert distance["trips_measured"] == 4
    assert distance["cab_km_total"] == 100.0
    assert distance["cab_km_per_trip"] == 25.0
    assert distance["cab_km_per_rider"] == 12.5


async def test_overrides_by_reason_and_action(db_session: AsyncSession) -> None:
    world = await fixture_world(db_session)
    rider = await employee_at(db_session, world, "O")
    request = await make_ride(db_session, world, rider, asked_at=DAY, status=RequestStatus.queued)
    entries = [
        (OverrideAction.lock, ReasonCode.local_knowledge, []),
        (OverrideAction.reassign, ReasonCode.local_knowledge, []),
        (OverrideAction.reassign, ReasonCode.safety, ["detour_factor_exceeded"]),
    ]
    for action, reason, waived in entries:
        db_session.add(
            OverrideLog(
                operator_id=world.operator_id,
                action=action,
                request_id=request.id,
                reason_code=reason,
                at=DAY + timedelta(hours=1),
                waived_violations=waived,
                before={},
                after={},
            )
        )
    await db_session.flush()

    overrides = (await run(db_session, world)).as_dict()["overrides"]

    assert overrides["total"] == 3
    assert overrides["hard_rule_overrides"] == 1
    assert overrides["by_reason"] == {"local_knowledge": 2, "safety": 1}
    assert overrides["by_action"] == {"lock": 1, "reassign": 2}


async def test_suggestion_acceptance_counts_accepted_and_never_the_failsafe(
    db_session: AsyncSession,
) -> None:
    """OQ-39: accepted over what a person answered; failsafe and superseded are not verdicts."""
    world = await fixture_world(db_session)
    vehicle = await cab(db_session, world)
    other = await cab(db_session, world)
    decided_at = DAY + timedelta(hours=1)

    async def offer(status: SuggestionStatus, *, alternative: bool = False) -> None:
        rider = await employee_at(db_session, world, f"S{uuid.uuid4().hex[:4]}")
        trip = None
        if alternative:
            trip = await make_trip(db_session, world, other, when=decided_at, km=5)
        request = await make_ride(
            db_session,
            world,
            rider,
            asked_at=DAY,
            status=RequestStatus.assigned if trip else RequestStatus.queued,
            trip=trip,
            wait_minutes=1 if trip else None,
        )
        db_session.add(
            Suggestion(
                operator_id=world.operator_id,
                request_id=request.id,
                vehicle_id=vehicle.id,
                rank=1,
                cost=1.0,
                reasons=[],
                status=str(status),
                offered_at=DAY,
                failsafe_due_at=DAY,
                decided_at=decided_at,
            )
        )
        if alternative:
            db_session.add(
                Suggestion(
                    operator_id=world.operator_id,
                    request_id=request.id,
                    vehicle_id=other.id,
                    rank=2,
                    cost=2.0,
                    reasons=[],
                    status=str(SuggestionStatus.superseded),
                    offered_at=DAY,
                    failsafe_due_at=DAY,
                )
            )

    for _ in range(5):
        await offer(SuggestionStatus.accepted)
    await offer(SuggestionStatus.rejected)
    await offer(SuggestionStatus.rejected, alternative=True)  # chose the system's second cab
    for _ in range(3):
        await offer(SuggestionStatus.failsafe_assigned)
    await offer(SuggestionStatus.superseded)
    await db_session.flush()

    suggestions = (await run(db_session, world)).as_dict()["suggestions"]

    assert suggestions["answered_by_a_person"] == 7
    assert suggestions["accepted"] == 5 and suggestions["rejected"] == 2
    assert suggestions["failsafe_assigned"] == 3
    assert suggestions["rejected_for_an_offered_alternative"] == 1
    assert suggestions["acceptance_rate"] == pytest.approx(5 / 7, abs=1e-4)
    assert suggestions["acceptance_rate_with_alternatives"] == pytest.approx(6 / 7, abs=1e-4)


async def test_a_period_with_no_offers_has_no_acceptance_rate_not_a_zero(
    db_session: AsyncSession,
) -> None:
    world = await fixture_world(db_session)

    suggestions = (await run(db_session, world)).as_dict()["suggestions"]

    assert suggestions["acceptance_rate"] is None and suggestions["answered_by_a_person"] == 0


async def test_who_assigned_and_what_the_optimizer_did(db_session: AsyncSession) -> None:
    world = await fixture_world(db_session)
    for who in (
        ActorType.optimizer,
        ActorType.optimizer,
        ActorType.supervisor,
        ActorType.system_failsafe,
    ):
        await make_ride(
            db_session,
            world,
            await employee_at(db_session, world, f"A{uuid.uuid4().hex[:4]}"),
            asked_at=DAY,
            status=RequestStatus.assigned,
            assigned_by=who,
        )
    for status, applied in (("solved", 4), ("failed", 0), ("solved", 2)):
        db_session.add(
            OptimizerRun(
                operator_id=world.operator_id,
                started_at=DAY + timedelta(hours=1),
                status=status,
                requests=4,
                placed=applied,
                unplaced=0,
                applied=applied,
                suggested=0,
                hinted=0,
                request_ids=[],
            )
        )
    await db_session.flush()

    report = (await run(db_session, world)).as_dict()

    assert report["assignments_by_actor"] == {"optimizer": 2, "supervisor": 1, "system_failsafe": 1}
    assert report["optimizer"] == {
        "runs": 3,
        "failed": 1,
        "applied": 6,
        "suggested": 0,
        "hinted": 0,
    }


async def test_the_report_is_scoped_to_the_operators_calendar_days(
    db_session: AsyncSession,
) -> None:
    """A ride asked at 00:30 IST on the 14th belongs to the 14th, not the 13th UTC."""
    world = await fixture_world(db_session)
    just_after_midnight_ist = datetime(2026, 10, 13, 19, 0, tzinfo=UTC)  # 00:30 IST on the 14th
    just_before_midnight_ist = datetime(2026, 10, 14, 18, 0, tzinfo=UTC)  # 23:30 IST on the 14th
    after = datetime(2026, 10, 14, 19, 0, tzinfo=UTC)  # 00:30 IST on the 15th
    for index, when in enumerate((just_after_midnight_ist, just_before_midnight_ist, after)):
        await make_ride(
            db_session,
            world,
            await employee_at(db_session, world, f"D{index}"),
            asked_at=when,
            status=RequestStatus.cancelled,
        )
    from sqlalchemy import update

    from app.modules.tenancy.models import Operator

    await db_session.execute(
        update(Operator).where(Operator.id == world.operator_id).values(timezone="Asia/Kolkata")
    )

    report = (await run(db_session, world)).as_dict()

    assert report["requests"]["total"] == 2


async def test_csv_carries_exactly_the_json_numbers(db_session: AsyncSession) -> None:
    world = await fixture_world(db_session)
    trip = await make_trip(
        db_session, world, await cab(db_session, world), when=DAY + timedelta(hours=1), km=12.5
    )
    await make_ride(
        db_session,
        world,
        await employee_at(db_session, world, "CSV"),
        asked_at=DAY,
        status=RequestStatus.dropped,
        trip=trip,
        wait_minutes=7,
    )

    built = await run(db_session, world)
    lines = built.as_csv().splitlines()

    assert lines[0] == "section,metric,value"
    assert "distance,cab_km_total,12.5" in lines
    assert "wait,median_minutes,7.0" in lines
    assert "wait,distribution.5-10,1" in lines
    assert "suggestions,acceptance_rate," in lines  # None is an empty cell, not a zero


async def test_a_client_sees_only_their_own_rides(db_session: AsyncSession) -> None:
    from tests.integration.worlds import OFFICE, add_client, add_employee, near

    world = await build_world(db_session, FakeClock(DAY), Mode.manual)
    other_client, other_office = await add_client(db_session, world, "Other", Mode.manual)
    mine = await employee_at(db_session, world, "Mine")
    theirs = await add_employee(
        db_session,
        world,
        near(*OFFICE, north_km=-4),
        "Theirs",
        client=other_client,
        office=other_office,
    )
    await make_ride(db_session, world, mine, asked_at=DAY, status=RequestStatus.cancelled)
    await make_ride(db_session, world, theirs, asked_at=DAY, status=RequestStatus.cancelled)

    scoped = (await run(db_session, world, client_id=world.client.id)).as_dict()
    everyone = (await run(db_session, world)).as_dict()

    assert scoped["requests"]["total"] == 1 and everyone["requests"]["total"] == 2
