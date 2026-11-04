"""The load-test world's fixed numbers and rider spread (`make loadtest-seed`)."""

from __future__ import annotations

import math
import re

from app import loadtest_seed as world
from app.domain.gps import distance_m

PHONE = re.compile(r"^\+[1-9][0-9]{7,14}$")


def test_every_login_is_a_valid_distinct_phone() -> None:
    phones = [
        world.OPERATOR_ADMIN,
        *world.SUPERVISORS,
        *(world.driver_phone(n) for n in range(1, world.CABS + 1)),
        *(world.rider_phone(n) for n in range(1, world.RIDERS + 1)),
    ]
    assert all(PHONE.match(phone) for phone in phones)
    assert len(set(phones)) == len(phones) == 1 + 2 + world.CABS + world.RIDERS


def test_phones_do_not_collide_with_the_demo_world() -> None:
    from app import demo_seed

    demo = {demo_seed.OPERATOR_ADMIN, demo_seed.SUPERVISOR, demo_seed.CLIENT_ADMIN}
    demo |= {demo_seed.driver_phone(n) for n in range(1, 6)}
    demo |= {demo_seed.employee_phone(n) for n in range(1, demo_seed.EMPLOYEES + 1)}
    mine = {world.OPERATOR_ADMIN, *world.SUPERVISORS}
    mine |= {world.driver_phone(n) for n in range(1, world.CABS + 1)}
    mine |= {world.rider_phone(n) for n in range(1, world.RIDERS + 1)}
    assert not demo & mine


def test_riders_live_between_the_inner_and_outer_radius_and_are_spread_out() -> None:
    office = (world.OFFICE[1], world.OFFICE[2])
    distances = [distance_m(*office, *world.rider_home(n)) for n in range(1, world.RIDERS + 1)]
    assert min(distances) >= world.MIN_RIDER_DISTANCE_M * 0.98
    assert max(distances) <= world.RIDER_RADIUS_M * 1.02
    homes = {world.rider_home(n) for n in range(1, world.RIDERS + 1)}
    assert len(homes) == world.RIDERS, "two riders on the same pin"
    nearest = min(distance_m(*a, *b) for a in list(homes)[:20] for b in homes if a != b)
    assert nearest > 20, "pins piled on each other"
    assert math.isclose(sum(distances) / len(distances), 4000, rel_tol=0.25), (
        "equal-area spread puts the average well out from the office"
    )


def test_the_spread_is_the_same_every_run() -> None:
    assert world.rider_home(7) == world.rider_home(7)
    assert world.rider_home(7) != world.rider_home(8)
