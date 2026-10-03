# ADR-0023: `alert_wait_minutes` is the "too long" threshold, and the audit that found it

- Status: accepted
- Date: 2026-10-03
- Decided without the product owner present, on their instruction; overrulable.

## Context
ADR-0019 noted that `enroute_reuse_max_eta_minutes` had been a declared config key that
**nothing read** for three milestones, and recommended a sweep for others like it. The
sweep (26 declared keys, cross-referenced against every read in `backend/app` and
`simulator/sim`) found **14 keys nothing reads**.

Twelve are honestly Phase 2 and named as such in their own descriptions: the cost-function
weights (`weight_wait`, `weight_empty_km`, `cost_new_vehicle`, the three
`urgency_factor_*`), the failsafe pair, the micro-batch window, the pooling hold window,
and the night-safety window. They are declared ahead of the optimizer that will read them,
which is deliberate.

One was not. **`alert_wait_minutes`** — "Pending request turns red", default 20 — is a
Phase 1 concept, and **every one of the seven scenarios sets it to 20**, several with
comments explaining why that value matters to their assertion. `evening_surge` calls it
"S03's own bar". Seven scenario authors configured a threshold the platform ignored
entirely.

That is the inverse of ADR-0015's rule. ADR-0015 says a scenario feature the simulator
cannot model faithfully is refused with the reason, never approximated, because a run that
measures the wrong thing produces confident wrong answers. Silently accepting config that
does nothing is the same failure from the other end: the scenario believes it configured
the platform, and the run's numbers are quoted as though it had.

Meanwhile ADR-0019 had just invented `retry_after_minutes` (default 10) for "how long is
too long before we escalate" — a second name for the same idea, five days later.

## Decision

**`alert_wait_minutes` is the single answer to "how long is too long".** It is the moment
the board turns a request red, the moment escalation starts, and the moment the search
begins to widen. One number, in the operator's own vocabulary, that they already set.

**`retry_after_minutes` keeps only the cadence**: how often an *already* escalated request
widens its search another step. Its description now says so.

So the ladder, with shipped defaults, is:

| Waited | What happens |
|---|---|
| < 20 min | Ordinary candidate rules; nothing special |
| 20 min | Escalated: `escalated_at` stamped, rolling alert raised, search widened to 30 min |
| 30 min | Widened to 40 |
| 40 min+ | Widened to 45 and held there (`retry_eta_max_minutes`) |

## Consequences
- Escalation now starts at 20 minutes rather than 10, so it is **more conservative** than
  what ADR-0019 shipped this morning — and it is the number the operator chose.
- Every scenario's `alert_wait_minutes: 20` now does something. S03's comment about its
  own bar becomes true rather than aspirational.
- One fewer knob that can disagree with another. Two thresholds for the same judgement is
  a configuration trap: set them inconsistently and the board turns red at a time that has
  nothing to do with when the platform starts trying harder.
- The remaining twelve unread keys are documented as Phase 2 in their declarations, so the
  next person auditing does not have to re-derive which absences are deliberate.
- The audit script lives in the scratchpad, not the repo. If this keeps happening it should
  become a test — "every declared key is read, or says which phase reads it" — and that is
  worth doing the next time a key is added rather than now.

## Alternatives considered
- **Keep both thresholds.** Rejected: "warn me at 20" and "escalate at 10" are the same
  decision wearing two hats, and nothing good happens when they disagree.
- **Delete `alert_wait_minutes` and keep `retry_after_minutes`.** Rejected: the key every
  scenario already sets, and whose name matches the operator's mental model, is the one to
  keep. Deleting it would also silently change seven scenarios.
- **Leave it unread and document it as Phase 2.** Rejected: it is not Phase 2. The board
  exists, the alert exists, and the scenarios are already asking for it.
