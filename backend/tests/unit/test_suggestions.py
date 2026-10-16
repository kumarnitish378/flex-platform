"""The suggestion sentence, against the example the spec ships (B23).

`allocation-rules.md` §5 gives one rendered example. It is reproduced here exactly,
because "shown as plain text" is the whole requirement and a paraphrase would satisfy
nobody reading the screen.
"""

from __future__ import annotations

import pytest

from app.domain.suggestions import (
    RiderImpact,
    SuggestionFacts,
    named_riders,
    reasons,
    sentence,
)


def test_the_documented_example_renders_exactly() -> None:
    """§5: "8 min away · 2 seats left · +4 min for Rahul · reuses trip T-102"."""
    facts = SuggestionFacts(
        eta_to_pickup_seconds=8 * 60,
        seats_free_after=2,
        empty_km_added=0,
        new_trip=False,
        riders=(RiderImpact(name="Rahul", added_minutes=4),),
        trip_label="T-102",
    )

    assert sentence(facts) == "8 min away · 2 seats left · +4 min for Rahul · reuses trip T-102"


def test_a_new_trip_says_so_instead_of_naming_one() -> None:
    facts = SuggestionFacts(
        eta_to_pickup_seconds=12 * 60, seats_free_after=3, empty_km_added=4.0, new_trip=True
    )

    assert sentence(facts) == "12 min away · 3 seats left · 4.0 km empty · new trip"


def test_empty_km_is_omitted_when_there_is_none() -> None:
    """ "0.0 km empty" on every suggestion trains people to stop reading the line."""
    facts = SuggestionFacts(
        eta_to_pickup_seconds=300, seats_free_after=1, empty_km_added=0, new_trip=False
    )

    assert "km empty" not in sentence(facts)


@pytest.mark.parametrize(
    ("free", "expected"),
    [(3, "3 seats left"), (1, "1 seat left"), (0, "full after this")],
)
def test_seats_read_naturally(free: int, expected: str) -> None:
    facts = SuggestionFacts(
        eta_to_pickup_seconds=60, seats_free_after=free, empty_km_added=0, new_trip=True
    )

    assert expected in reasons(facts)


def test_minutes_round_rather_than_truncate() -> None:
    """A 7.6-minute ETA shown as 7 reads as a promise the cab will beat.

    The rider is the one who finds out it did not.
    """
    facts = SuggestionFacts(
        eta_to_pickup_seconds=7.6 * 60, seats_free_after=2, empty_km_added=0, new_trip=True
    )

    assert reasons(facts)[0] == "8 min away"


def test_an_approximate_eta_says_so() -> None:
    """ADR-0010: a straight-line estimate is a weaker claim than a routed one."""
    facts = SuggestionFacts(
        eta_to_pickup_seconds=9 * 60,
        seats_free_after=2,
        empty_km_added=0,
        new_trip=True,
        eta_approximate=True,
    )

    assert reasons(facts)[0] == "9 min away (approx)"


def test_cost_never_appears_in_the_sentence() -> None:
    """It is a weighted minutes-equivalent score, not a price.

    Rendered beside "8 min away" it invites the reading "this ride costs 13.8 of
    something" - wrong, and unfixable once an operator believes it.
    """
    facts = SuggestionFacts(
        eta_to_pickup_seconds=480,
        seats_free_after=2,
        empty_km_added=1.2,
        new_trip=False,
        riders=(RiderImpact("Rahul", 4),),
        trip_label="T-102",
    )

    rendered = sentence(facts)
    assert "cost" not in rendered.lower()
    assert "13.8" not in rendered


# --- which riders are named, and in what order -------------------------------


def test_the_worst_affected_rider_is_named_first() -> None:
    """A list led by "+1 min for Asha" buries the decision a supervisor must justify."""
    impacts = named_riders(
        {"a": 1.0, "b": 14.0, "c": 6.0},
        {"a": "Asha", "b": "Rahul", "c": "Meera"},
    )

    assert [impact.name for impact in impacts] == ["Rahul", "Meera", "Asha"]


def test_a_rider_with_no_known_name_is_dropped_not_rendered_as_an_id() -> None:
    """ "+4 min for 8f3c-..." costs a supervisor a line and tells them nothing."""
    impacts = named_riders({"known": 3.0, "unknown": 9.0}, {"known": "Asha"})

    assert [impact.name for impact in impacts] == ["Asha"]


def test_equal_detours_order_by_name_so_the_screen_does_not_shuffle() -> None:
    impacts = named_riders({"a": 5.0, "b": 5.0}, {"a": "Zoya", "b": "Asha"})

    assert [impact.name for impact in impacts] == ["Asha", "Zoya"]


def test_a_trip_with_no_label_still_reads_as_a_reuse() -> None:
    """`trip.id` is a UUID and "T-102" is the operator's language, not the domain's."""
    facts = SuggestionFacts(
        eta_to_pickup_seconds=300, seats_free_after=2, empty_km_added=0, new_trip=False
    )

    assert "reuses a trip already running" in reasons(facts)
