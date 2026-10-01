# ADR-0017: A run drains rides in progress before it measures anything

- Status: accepted
- Date: 2026-10-02
- Settles: OQ-28.

## Context
`all_requests_terminal` is the assertion that nothing was left hanging, and it is the
stated acceptance for S01 `smoke_tiny` and S03 `evening_surge`. In the first trustworthy
full-suite run both failed it — S01 with one request open, S03 with two — while every
other assertion held.

The cause was not the platform. A rider sitting in a moving cab is `picked_up`, which is
not terminal, and the run simply stopped on the hour with the cab still driving. Because
live timing varies from run to run, the failure appeared and disappeared at random. **A
gate that fails at random gets ignored**, so `sim-quick` could not be trusted as a PR gate
until this was settled.

There was a second, quieter version of the same problem. A rider's SimPy process is
suspended inside a minute-by-minute poll when the environment stops, so whether their
outcome was ever written depended on whether one of those polls happened to land past the
end. That is the definition of a flaky measurement.

## Decision

**`duration_hours` is the demand window, not the length of the run.** After it closes, the
clock keeps going for up to `drain_minutes_max` (default 60) while any rider is still in a
cab, and stops the moment the last one gets out. Nothing new happens during the drain:
riders ask for nothing after the window, the supervisor has stopped assigning, and the only
processes still doing work are drivers finishing trips they had already started. A healthy
run therefore pays nothing for it.

**The run records who was still aboard, not the rider.** `_ride_home` has no deadline of
its own any more; the engine writes `unresolved` ("still riding when the run stopped") for
every rider still on board when the clock stops. The result no longer depends on poll
timing, which was the flakiness underneath the flakiness.

**The cap keeps it a fix rather than a cover-up.** If the drain runs out with someone still
in a cab, that ride is genuinely stuck — a real failure — and the run still fails.
`metrics.json` carries `drain_minutes` and `drain_capped` so the difference is visible
rather than inferred.

## Consequences
- `sim-quick` can be used as a PR gate: `all_requests_terminal` now fails only when
  something is actually wrong.
- Scenario durations keep meaning what they say. A scenario author writes the demand day
  they want to model and does not have to pad it so no ride can still be running at the
  end — the alternative that gets harder with every scenario added.
- A run can take up to an hour of simulated time longer than its `duration_hours`. At the
  speed factors the suites use this is seconds of wall time, and only when something was
  still being carried.
- `drain_minutes_max: 0` reproduces the old behaviour for a scenario that deliberately
  wants to measure exactly its own window.
- The fix exposed a related hole it does **not** close: a rider still *waiting* when the
  window closes is left with no outcome at all and counted as if they had stayed home, so
  `all_requests_terminal` can pass while riders were abandoned. It is now measured as
  `still_waiting` and raised as **OQ-29** rather than changed here, because making those
  riders `unresolved` would newly fail scenarios on a judgement nobody has made yet.

## Alternatives considered
- **Count `picked_up`-at-end as its own outcome, excluded from `unresolved`.** The cheapest
  change, and rejected: it weakens the assertion permanently. A rider genuinely stuck in a
  cab — the exact bug S05 was written to catch — would stop failing the gate.
- **Tune each scenario so no ride can still be running at the end.** Rejected: fragile, and
  it gets harder as scenarios grow. It also distorts the scenarios, which exist to describe
  a day's demand and not to be convenient to measure.
- **Leave the deadline with the rider agent and extend it to the drain end.** Rejected: it
  keeps the outcome dependent on whether a poll lands in the right minute, which is half of
  the original flakiness.
