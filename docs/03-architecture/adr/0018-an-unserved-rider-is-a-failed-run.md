# ADR-0018: A rider nobody came for is a failed run

- Status: accepted
- Date: 2026-10-02
- Settles: OQ-29. Completes ADR-0017.

## Context
Every scenario asserts `all_requests_terminal` — nothing left hanging. Settling OQ-28
showed the assertion was blind to the one outcome it most needs to catch.

A rider's agent sits in a minute-by-minute poll. When the run stopped, that process was
suspended and never wrote an outcome, so the record kept its default: `not_travelling`,
the value meaning "stayed at home today". A rider the platform had abandoned at their
pickup point was therefore indistinguishable from a rider who never asked for a cab — and
`all_requests_terminal` passed straight over them.

So the assertion could be green on a run that left people on the street. That is worse
than the OQ-28 flakiness it was found next to: a gate that fails at random gets ignored,
but a gate that passes when it should fail gets *trusted*.

## Decision

**A rider who asked for a cab and never got one is `unresolved`**, recorded with the
detail "still waiting when the demand window closed". `unresolved` already fails
`all_requests_terminal`, so no assertion changes — the assertion simply becomes true to
its name.

**The run records them, at the moment the window closes**, before the drain. The drain
exists to let rides already under way finish (ADR-0017); it is not extra time in which
anyone can be served, so measuring waiting riders at the window close is measuring the day
the scenario actually described.

**A rider left waiting takes no further action.** Their patience often expires during the
drain, and a give-up there would report a cancellation the day never contained — turning
an abandonment into a tidy `gave_up` and hiding it again.

**`unresolved` is reported in its two halves**, because they are different failures:

| Metric | Meaning |
|---|---|
| `still_waiting` | Asked for a cab, nobody ever came. The platform losing a rider. |
| `still_riding` | Being carried when the clock stopped, after the drain. A ride that never ended. |

## Consequences
- **Scenarios that pass today will fail**, truthfully: they do leave riders unserved. S02
  `normal_weekday` is the extreme already on record — 240 riders asked, 240 gave up — and
  any scenario whose fleet cannot cover its demand now says so in the verdict rather than
  only in the wait percentiles.
- A red run names its own cause: `still_waiting` is a service failure to fix in dispatch,
  `still_riding` is a ride that never completed.
- No scenario tolerance was introduced. An `still_waiting_max` per scenario was the other
  candidate and is rejected below; if it turns out a scenario genuinely wants to describe a
  day it cannot fully serve, that is a number to add then, deliberately, not a default to
  ship now.

## Alternatives considered
- **A per-scenario tolerance (`still_waiting_max`).** Rejected for now: it asks every
  scenario author to pick a number of abandoned riders they find acceptable, before anyone
  has seen what the platform actually does. The assertion already means zero; start there
  and relax deliberately if a scenario earns it.
- **Report the count and never fail on it.** Rejected: that is the state this ADR exists to
  end. A number nobody is obliged to look at is a number nobody looks at.
- **Let the rider give up during the drain and count it as `gave_up`.** Rejected: it
  reports an action the demand window never contained, and it launders the platform's worst
  outcome into its second-worst.
