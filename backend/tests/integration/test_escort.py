"""The night escort gate (owner decision 3; OQ-10).

After 20:00, a woman who would be the only rider in the cab needs a supervisor to say who is with
her before the trip can start. A man sharing the cab clears the flag by itself. Nothing is arranged
automatically.
"""
# ruff: noqa: F811, F401  (imported fixtures are used by name as arguments)

from __future__ import annotations

from datetime import time, timedelta
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import create_access_token
from app.domain.enums import AlertType, Role
from app.domain.night_escort import escort_required
from app.domain.state_machines import RequestStatus
from app.modules.alerts.models import Alert
from app.modules.config.service import ConfigService
from app.modules.dispatch.escort import EscortService
from app.modules.dispatch.models import Trip, TripEvent
from app.modules.people.models import Employee
from tests.builders import make_user, make_user_role, unique_phone
from tests.integration.test_driver_trips import (  # noqa: F401  (fixtures)
    JWT_SECRET,
    NOW,
    app,
    client,
    clock,
    driver,
    events,
    start,
    world,
)

pytestmark = pytest.mark.requires_db

#: 09:00 UTC on `NOW`'s day is 14:30 in Kolkata; this is 22:00 there, inside the 20:00-06:00 window.
NIGHT = NOW + timedelta(hours=7, minutes=30)


async def _night_with_one_woman(
    world: dict[str, Any], session: AsyncSession, clock: FakeClock, *, enabled: bool = True
) -> None:
    """The fixture's two-rider trip, cut down to one rider who is a woman, at 22:30."""
    clock.set(NIGHT)
    await ConfigService(session, clock).update(
        world["operator_id"], {"night_safety_enabled": enabled}
    )
    world["requests"]["second"].status = RequestStatus.cancelled
    rider = await session.get(Employee, world["requests"]["first"].employee_id)
    assert rider is not None
    rider.gender = "female"
    await session.flush()


@pytest_asyncio.fixture
async def supervisor(world: dict[str, Any], db_session: AsyncSession, clock: FakeClock) -> Any:
    user = make_user(name="Supervisor", phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.supervisor, operator_id=world["operator_id"]))
    await db_session.flush()
    token, _ = create_access_token(
        user_id=user.id,
        role=str(Role.supervisor),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=12 * 3600,
        operator_id=world["operator_id"],
    )
    return user, {"Authorization": f"Bearer {token}"}


# --- the rule, as arithmetic -------------------------------------------------------------


def _rule(genders: list[str | None], at: time = time(22, 30), enabled: bool = True) -> bool:
    return escort_required(
        enabled=enabled,
        local_time=at,
        night_start=time(20, 0),
        night_end=time(6, 0),
        genders=genders,
    )


def test_a_woman_alone_at_night_needs_an_escort() -> None:
    assert _rule(["female"]) is True


def test_a_man_sharing_the_cab_means_she_is_not_alone() -> None:
    assert _rule(["female", "male"]) is False


def test_two_women_together_are_not_alone() -> None:
    assert _rule(["female", "female"]) is False


def test_a_man_alone_or_an_unknown_gender_never_triggers_it() -> None:
    assert _rule(["male"]) is False
    assert _rule([None]) is False
    assert _rule(["other"]) is False


def test_daytime_and_a_switched_off_policy_never_trigger_it() -> None:
    assert _rule(["female"], at=time(14, 30)) is False
    assert _rule(["female"], enabled=False) is False


def test_the_window_opens_at_eight_and_crosses_midnight() -> None:
    assert _rule(["female"], at=time(20, 0)) is True
    assert _rule(["female"], at=time(2, 0)) is True
    assert _rule(["female"], at=time(19, 59)) is False


# --- the gate, against a real database -------------------------------------------------------


async def test_the_dispatch_board_flags_the_trip(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    supervisor: Any,
) -> None:
    await _night_with_one_woman(world, db_session, clock)

    items = (await client.get("/dispatch/trips", headers=supervisor[1])).json()["items"]

    escort = items[0]["escort"]
    assert escort["required"] is True and escort["confirmed"] is False


async def test_the_driver_cannot_start_a_flagged_trip(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    driver: dict[str, str],
) -> None:
    await _night_with_one_woman(world, db_session, clock)

    response = await start(client, driver, world["trip_id"], occurred_at=NIGHT)

    assert response.status_code == 409
    assert response.json()["details"]["reason"] == "escort_confirmation_required"


async def test_an_alert_is_raised_for_the_supervisor(
    world: dict[str, Any], db_session: AsyncSession, clock: FakeClock
) -> None:
    await _night_with_one_woman(world, db_session, clock)

    raised, _ = await EscortService(db_session, clock).sweep()
    again, _ = await EscortService(db_session, clock).sweep()

    alerts = (
        (
            await db_session.execute(
                select(Alert).where(Alert.type == str(AlertType.escort_required))
            )
        )
        .scalars()
        .all()
    )
    assert (raised, again) == (1, 0)  # one alert, not one per sweep
    assert [a.trip_id for a in alerts] == [world["trip_id"]]


async def test_confirming_lets_the_trip_start_and_records_who(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    driver: dict[str, str],
    supervisor: Any,
) -> None:
    await _night_with_one_woman(world, db_session, clock)
    await EscortService(db_session, clock).sweep()

    confirmed = await client.post(
        f"/dispatch/trips/{world['trip_id']}/escort-confirmation",
        json={"basis": "escort_arranged", "note": "Escort Meena"},
        headers=supervisor[1],
    )
    started = await start(client, driver, world["trip_id"], occurred_at=NIGHT)

    assert confirmed.status_code == 200, confirmed.text
    body = confirmed.json()["escort"]
    assert body["confirmed"] is True and body["basis"] == "escort_arranged"
    assert body["confirmed_by"] == str(supervisor[0].id)
    assert started.status_code == 200, started.text
    event = (
        await db_session.execute(
            select(TripEvent).where(TripEvent.reason == "escort_confirmed:escort_arranged")
        )
    ).scalar_one()
    assert event.actor_user_id == supervisor[0].id
    open_alerts = (
        (
            await db_session.execute(
                select(Alert)
                .where(Alert.type == str(AlertType.escort_required))
                .where(Alert.status != "resolved")
            )
        )
        .scalars()
        .all()
    )
    assert open_alerts == []


async def test_a_male_co_rider_present_is_also_accepted(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    supervisor: Any,
) -> None:
    await _night_with_one_woman(world, db_session, clock)

    response = await client.post(
        f"/dispatch/trips/{world['trip_id']}/escort-confirmation",
        json={"basis": "male_co_rider_present"},
        headers=supervisor[1],
    )

    assert response.status_code == 200
    assert response.json()["escort"]["basis"] == "male_co_rider_present"


async def test_an_unknown_basis_is_refused(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    supervisor: Any,
) -> None:
    await _night_with_one_woman(world, db_session, clock)

    response = await client.post(
        f"/dispatch/trips/{world['trip_id']}/escort-confirmation",
        json={"basis": "trust_me"},
        headers=supervisor[1],
    )

    assert response.status_code == 422


async def test_a_trip_that_is_not_flagged_cannot_be_confirmed(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    supervisor: Any,
) -> None:
    # Two riders at night: nobody is alone.
    clock.set(NIGHT)
    await ConfigService(db_session, clock).update(
        world["operator_id"], {"night_safety_enabled": True}
    )

    response = await client.post(
        f"/dispatch/trips/{world['trip_id']}/escort-confirmation",
        json={"basis": "escort_arranged"},
        headers=supervisor[1],
    )

    assert response.status_code == 409
    assert response.json()["details"]["reason"] == "escort_not_required"


async def test_a_trip_that_does_not_need_it_starts_normally(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    driver: dict[str, str],
) -> None:
    # Night, switched on, two riders: unaffected.
    clock.set(NIGHT)
    await ConfigService(db_session, clock).update(
        world["operator_id"], {"night_safety_enabled": True}
    )

    assert (await start(client, driver, world["trip_id"], occurred_at=NIGHT)).status_code == 200


async def test_the_policy_switch_and_the_daytime_leave_the_trip_alone(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    driver: dict[str, str],
) -> None:
    await _night_with_one_woman(world, db_session, clock, enabled=False)

    assert (await start(client, driver, world["trip_id"], occurred_at=NIGHT)).status_code == 200


async def test_a_confirmation_cannot_be_given_by_a_driver(
    client: AsyncClient, world: dict[str, Any], driver: dict[str, str]
) -> None:
    response = await client.post(
        f"/dispatch/trips/{world['trip_id']}/escort-confirmation",
        json={"basis": "escort_arranged"},
        headers=driver,
    )

    assert response.status_code == 403
