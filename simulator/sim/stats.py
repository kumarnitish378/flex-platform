"""Small statistics shared by the metrics modules."""

from __future__ import annotations


def percentile(values: list[float], fraction: float) -> float | None:
    """Linear-interpolated percentile. `None` for an empty sample."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight
