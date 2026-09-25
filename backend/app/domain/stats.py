"""Percentiles for the operational reports (B18, OPA-05).

Pure, and separate from the report query, because "what is the p90 wait" is a question
about a list of numbers and should be checkable against a list of numbers.

**Method:** linear interpolation between closest ranks (the same definition as numpy's
default and R's type 7). Stated explicitly because percentile definitions differ by
several minutes on small samples, and a pilot report that disagrees with the operator's
own spreadsheet is a credibility problem rather than a rounding one. It also makes the
median the ordinary average of the two middle values for an even count, which is what
anyone reading "median wait" expects.
"""

from __future__ import annotations

from collections.abc import Sequence


def percentile(values: Sequence[float], fraction: float) -> float | None:
    """The value at `fraction` (0.0-1.0) through the sorted data.

    `None` for no data: a report of an empty day must say "no trips", not "0 minutes",
    which reads like instant service.
    """
    if not values:
        return None
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"fraction must be between 0 and 1, got {fraction}")

    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])

    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def median(values: Sequence[float]) -> float | None:
    return percentile(values, 0.5)


def p90(values: Sequence[float]) -> float | None:
    return percentile(values, 0.9)
