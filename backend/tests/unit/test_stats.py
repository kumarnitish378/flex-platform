"""Percentiles for the operational reports (B18, OPA-05).

Worth pinning precisely: a pilot report that disagrees with the operator's own
spreadsheet by three minutes is a credibility problem, not a rounding one.
"""

from __future__ import annotations

import pytest

from app.domain.stats import median, p90, percentile


def test_the_median_of_an_odd_count_is_the_middle_value() -> None:
    assert median([5, 1, 3]) == 3


def test_the_median_of_an_even_count_is_the_average_of_the_two_middles() -> None:
    """What anyone reading "median wait" expects."""
    assert median([1, 2, 3, 4]) == 2.5


def test_one_value_is_its_own_median_and_p90() -> None:
    assert median([7]) == 7.0
    assert p90([7]) == 7.0


def test_no_data_has_no_median() -> None:
    """A day with no trips must not report a 0-minute wait, which reads as instant."""
    assert median([]) is None
    assert p90([]) is None


def test_p90_interpolates_between_ranks() -> None:
    # Ten values, position = 0.9 * 9 = 8.1, so a tenth of the way from 9 to 10.
    assert p90([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == pytest.approx(9.1)


def test_p90_of_identical_values_is_that_value() -> None:
    assert p90([4, 4, 4, 4]) == 4.0


def test_the_zeroth_percentile_is_the_minimum() -> None:
    assert percentile([9, 2, 5], 0.0) == 2.0


def test_the_hundredth_percentile_is_the_maximum() -> None:
    assert percentile([9, 2, 5], 1.0) == 9.0


def test_the_input_order_does_not_matter() -> None:
    assert percentile([10, 1, 5, 3], 0.5) == percentile([1, 3, 5, 10], 0.5)


def test_the_input_is_not_mutated() -> None:
    """The caller's list of waits is still theirs afterwards."""
    waits = [5.0, 1.0, 3.0]
    percentile(waits, 0.5)
    assert waits == [5.0, 1.0, 3.0]


def test_p90_is_never_below_the_median() -> None:
    waits = [2.0, 40.0, 7.0, 5.0, 61.0, 3.0, 9.0]
    assert p90(waits) >= median(waits)  # type: ignore[operator]


@pytest.mark.parametrize("fraction", [-0.1, 1.1])
def test_a_fraction_outside_zero_to_one_is_refused(fraction: float) -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        percentile([1, 2, 3], fraction)


def test_a_worked_example_a_person_can_check() -> None:
    """Waits of 4, 6, 9, 12 and 45 minutes: median 9, p90 32.4."""
    waits = [4.0, 6.0, 9.0, 12.0, 45.0]
    assert median(waits) == 9.0
    # position = 0.9 * 4 = 3.6, so 0.6 of the way from 12 to 45.
    assert p90(waits) == pytest.approx(12 + 0.6 * (45 - 12))
