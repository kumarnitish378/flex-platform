"""Owner decision 1: the phone publishes after ~5 m or a 60 s heartbeat; stale must allow for it."""

from __future__ import annotations

import pytest

from app.domain import config_keys
from app.domain.errors import ValidationFailed


def test_defaults_are_a_five_metre_filter_and_a_sixty_second_heartbeat() -> None:
    defaults = config_keys.defaults()

    assert defaults["gps_distance_filter_m"] == 5
    assert defaults["gps_heartbeat_seconds"] == 60


def test_the_default_stale_threshold_outlasts_a_missed_heartbeat() -> None:
    defaults = config_keys.defaults()

    config_keys.check_consistency(defaults)
    assert defaults["stale_gps_seconds"] >= 1.5 * defaults["gps_heartbeat_seconds"]


def test_a_stale_threshold_that_a_heartbeat_can_trip_is_refused() -> None:
    values = {**config_keys.defaults(), "stale_gps_seconds": 60}

    with pytest.raises(ValidationFailed, match="1.5"):
        config_keys.check_consistency(values)


def test_a_slower_heartbeat_needs_a_longer_threshold() -> None:
    values = {**config_keys.defaults(), "gps_heartbeat_seconds": 120}

    with pytest.raises(ValidationFailed):
        config_keys.check_consistency(values)
    config_keys.check_consistency({**values, "stale_gps_seconds": 180})
