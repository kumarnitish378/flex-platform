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
from app.domain.enums import AlertType, Direction, Role
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


# --- the last-out rule (owner decision 2026-11-02) ---------------------------------------------
#
# On a shared trip home, a woman who is the last rider left in the cab needs an escort, however many
# people shared the earlier part. The fixture's two riders are dropped "first" then "second".


async def _going_home(
    world: dict[str, Any],
    session: AsyncSession,
    clock: FakeClock,
    *,
    first: str,
    second: str,
    direction: Direction = Direction.from_office,
) -> None:
    """The fixture trip made a night trip home: `first` is dropped first, `second` is last out."""
    from app.modules.dispatch.models import Trip

    clock.set(NIGHT)
    await ConfigService(session, clock).update(world["operator_id"], {"night_safety_enabled": True})
    trip = await session.get(Trip, world["trip_id"])
    assert trip is not None
    trip.direction = direction
    for label, gender in (("first", first), ("second", second)):
        rider = await session.get(Employee, world["requests"][label].employee_id)
        assert rider is not None
        rider.gender = gender
    await session.flush()


async def _escort_of_the_trip(client: AsyncClient, headers: dict[str, str]) -> dict[str, Any]:
    items = (await client.get("/dispatch/trips", headers=headers)).json()["items"]
    escort: dict[str, Any] = items[0]["escort"]
    return escort


async def test_a_woman_last_out_of_a_shared_trip_home_is_flagged(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    supervisor: Any,
) -> None:
    await _going_home(world, db_session, clock, first="male", second="female")

    escort = await _escort_of_the_trip(client, supervisor[1])

    assert escort["required"] is True and escort["reason"] == "last_out"
    assert escort["confirmed"] is False


async def test_a_man_last_out_is_not_flagged_even_with_a_woman_before_him(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    supervisor: Any,
) -> None:
    await _going_home(world, db_session, clock, first="female", second="male")

    assert (await _escort_of_the_trip(client, supervisor[1]))["required"] is False


async def test_two_women_going_home_still_leave_the_last_one_alone(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    supervisor: Any,
) -> None:
    await _going_home(world, db_session, clock, first="female", second="female")

    assert (await _escort_of_the_trip(client, supervisor[1]))["reason"] == "last_out"


async def test_going_to_the_office_is_not_a_last_out_trip(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    supervisor: Any,
) -> None:
    """Everyone is dropped at the office together; the lone stretch there is the first pickup."""
    await _going_home(
        world, db_session, clock, first="male", second="female", direction=Direction.to_office
    )

    assert (await _escort_of_the_trip(client, supervisor[1]))["required"] is False


async def test_the_driver_cannot_start_a_last_out_trip_until_an_escort_is_confirmed(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    driver: dict[str, str],
) -> None:
    await _going_home(world, db_session, clock, first="male", second="female")

    refused = await start(client, driver, world["trip_id"], occurred_at=NIGHT)

    assert refused.status_code == 409
    assert refused.json()["details"]["reason"] == "escort_confirmation_required"
    assert refused.json()["details"]["escort_reason"] == "last_out"


async def test_a_male_co_rider_cannot_clear_a_last_out_trip(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    supervisor: Any,
) -> None:
    """He is dropped before her; he is not there when she is alone."""
    await _going_home(world, db_session, clock, first="male", second="female")

    response = await client.post(
        f"/dispatch/trips/{world['trip_id']}/escort-confirmation",
        json={"basis": "male_co_rider_present"},
        headers=supervisor[1],
    )

    assert response.status_code == 422
    assert response.json()["details"]["escort_reason"] == "last_out"


async def test_an_arranged_escort_clears_it_and_the_trip_starts(
    client: AsyncClient,
    world: dict[str, Any],
    db_session: AsyncSession,
    clock: FakeClock,
    driver: dict[str, str],
    supervisor: Any,
) -> None:
    await _going_home(world, db_session, clock, first="male", second="female")

    confirmed = await client.post(
        f"/dispatch/trips/{world['trip_id']}/escort-confirmation",
        json={"basis": "escort_arranged", "note": "Escort Meena meets the cab"},
        headers=supervisor[1],
    )
    started = await start(client, driver, world["trip_id"], occurred_at=NIGHT)

    assert confirmed.status_code == 200 and confirmed.json()["escort"]["confirmed"] is True
    assert confirmed.json()["escort"]["reason"] == "last_out"
    assert started.status_code == 200, started.text


async def test_a_confirmation_given_for_one_reason_does_not_cover_another(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock
) -> None:
    """A man vouched for a lone woman; then the trip changed so she is last out. Ask again."""
    from app.modules.dispatch.models import Trip

    await _going_home(world, db_session, clock, first="male", second="female")
    trip = await db_session.get(Trip, world["trip_id"])
    assert trip is not None
    trip.escort_basis = "male_co_rider_present"
    await db_session.flush()

    status = (await EscortService(db_session, clock).assess([trip]))[trip.id]

    assert status.reason is not None and status.confirmed is False


async def test_the_flag_exists_the_moment_the_trip_is_planned(db_session: AsyncSession) -> None:
    """Assigning the second rider home at night raises the alert at once, not at the next sweep."""
    from app.domain.enums import ActorType
    from app.domain.state_machines import Actor
    from app.modules.dispatch.service import DispatchService
    from tests.integration.worlds import (
        OFFICE,
        add_cab,
        add_employee,
        add_request,
        build_world,
        eta_service,
        near,
        ping,
        set_config,
    )

    clock = FakeClock(NIGHT)
    world = await build_world(db_session, clock, None)
    await set_config(db_session, world, night_safety_enabled=True)
    cab = await add_cab(db_session, world, OFFICE)
    man = await add_employee(db_session, world, near(*OFFICE, north_km=-3), "Raj", gender="male")
    woman = await add_employee(
        db_session, world, near(*OFFICE, north_km=-4), "Asha", gender="female"
    )
    dispatch = DispatchService(db_session, clock, eta_service(clock))
    supervisor_actor = Actor(str(ActorType.supervisor))
    # The man lives nearer the office, so he is dropped first and she is last out.
    first = await add_request(db_session, world, man, direction=Direction.from_office)
    second = await add_request(db_session, world, woman, direction=Direction.from_office)
    await ping(db_session, world, cab, OFFICE)

    trip = await dispatch.assign(world.operator_id, first.id, cab.id, supervisor_actor, None)
    await dispatch.assign(
        world.operator_id, second.id, cab.id, supervisor_actor, None, trip_id=trip.id
    )

    alerts = (
        (
            await db_session.execute(
                select(Alert).where(Alert.type == str(AlertType.escort_required))
            )
        )
        .scalars()
        .all()
    )
    assert [a.trip_id for a in alerts] == [trip.id]
    assert alerts[0].data == {"reason": "woman_last_out_at_night"}
