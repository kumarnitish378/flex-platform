"""Per-cab-per-day billing arithmetic (owner decision 2026-11-02; OQ-03), without a database."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.cab_day_billing import (
    Basis,
    Flag,
    SessionFacts,
    build_cab_day,
    check_odometer_reading,
    gap_percent,
    odometer_km,
)
from app.domain.errors import ValidationFailed

NINE = datetime(2026, 10, 5, 3, 30, tzinfo=UTC)


def session(
    gps: float | None,
    start: float | None = None,
    end: float | None = None,
    *,
    hours: tuple[int, int] = (0, 9),
    basis: Basis = Basis.gps,
    closed: bool = True,
    driver: str = "Asha",
    sid: str = "s1",
) -> SessionFacts:
    return SessionFacts(
        session_id=sid,
        driver=driver,
        started_at=NINE + timedelta(hours=hours[0]),
        ended_at=NINE + timedelta(hours=hours[1]) if closed else None,
        gps_km=gps,
        odometer_start_km=start,
        odometer_end_km=end,
        basis=basis,
    )


def day(*sessions: SessionFacts, threshold: float = 10.0, rate: float | None = 8.0):  # type: ignore[no-untyped-def]
    return build_cab_day(
        vehicle="DL01DEMO01",
        day="2026-10-05",
        sessions=sessions,
        threshold_percent=threshold,
        rate_per_km=rate,
    )


def test_a_day_is_billed_on_gps_kilometres_at_the_rate() -> None:
    row = day(session(gps=112.5))

    assert row.billed_km == 112.5
    assert row.amount == 900.0  # 112.5 km x Rs 8
    assert row.flags == ()


def test_dead_kilometres_are_part_of_the_day() -> None:
    """The distance is the whole duty, not the trips: nothing here knows about trips."""
    row = day(session(gps=40.0), session(gps=25.0, hours=(10, 12), sid="s2"))

    assert row.billed_km == 65.0
    assert row.duty_in == NINE and row.duty_out == NINE + timedelta(hours=12)


def test_without_a_rate_there_is_no_amount() -> None:
    assert day(session(gps=50.0), rate=None).amount is None


def test_the_odometer_is_closing_minus_opening() -> None:
    assert odometer_km(12_000.0, 12_118.5) == 118.5
    assert odometer_km(None, 12_118.5) is None
    assert odometer_km(12_000.0, None) is None


def test_a_closing_reading_below_the_opening_one_is_not_a_distance() -> None:
    assert odometer_km(12_100.0, 12_000.0) is None
    with pytest.raises(ValidationFailed):
        check_odometer_reading(12_100.0, 12_000.0)
    check_odometer_reading(12_000.0, 12_000.0)
    check_odometer_reading(None, 5.0)


def test_a_gap_over_the_threshold_is_flagged_and_never_resolved() -> None:
    row = day(session(gps=100.0, start=1000.0, end=1130.0))  # odometer 130 vs GPS 100

    assert round(row.gap_percent or 0, 1) == 23.1
    assert Flag.odometer_gap in row.flags
    assert row.billed_km == 100.0, "billed on GPS: the platform does not pick the odometer"


def test_a_gap_inside_the_threshold_is_quiet() -> None:
    row = day(session(gps=100.0, start=1000.0, end=1105.0))

    assert Flag.odometer_gap not in row.flags


def test_the_threshold_is_configurable() -> None:
    sessions = (session(gps=100.0, start=1000.0, end=1105.0),)

    assert (
        Flag.odometer_gap
        in build_cab_day(
            vehicle="X", day="d", sessions=sessions, threshold_percent=2.0, rate_per_km=8.0
        ).flags
    )


def test_the_odometer_is_billed_only_when_an_operator_marked_it() -> None:
    marked = day(session(gps=100.0, start=1000.0, end=1130.0, basis=Basis.odometer))

    assert marked.billed_km == 130.0
    assert Flag.odometer_billed in marked.flags


def test_marking_the_odometer_without_readings_falls_back_to_gps() -> None:
    assert day(session(gps=100.0, basis=Basis.odometer)).billed_km == 100.0


def test_no_pings_means_no_gps_figure_not_zero() -> None:
    row = day(session(gps=None))

    assert row.gps_km is None
    assert Flag.no_gps in row.flags
    assert row.billed_km == 0.0


def test_a_session_still_open_is_flagged() -> None:
    row = day(session(gps=12.0, closed=False))

    assert Flag.still_on_duty in row.flags and row.duty_out is None


def test_two_drivers_on_one_cab_one_day_share_a_row() -> None:
    row = day(
        session(gps=10.0, driver="Asha"), session(gps=20.0, driver="Ravi", hours=(10, 12), sid="b")
    )

    assert row.drivers == ("Asha", "Ravi")


def test_gap_percent_needs_both_figures() -> None:
    assert gap_percent(None, 100.0) is None
    assert gap_percent(100.0, 0.0) is None
