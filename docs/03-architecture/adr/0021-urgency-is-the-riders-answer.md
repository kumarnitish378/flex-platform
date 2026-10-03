# ADR-0021: `urgency` is the rider's answer, and the platform never rewrites it

- Status: accepted
- Date: 2026-10-03
- Decided without the product owner present, on their instruction; overrulable.

## Context
`glossary.md` defines urgency as a rider/client input: High, Medium, Low. It is one of the
few things a rider actually tells us.

Two changes made the same day both wrote to it. ADR-0016 set `urgency = high` on a rider
stranded by a breakdown. ADR-0019 set `urgency = high` on any request nobody had served in
time. Both had the same intent — make the board show this rider needs attention — and both
achieved it by overwriting what the rider had said.

Running it exposed the cost. A live `evening_surge` escalated **142 of 150 requests**. Had
that run carried the urgency rewrite, 142 of 150 requests would have read "high": the
field would have said the riders declared an urgency they never declared, and it would have
stopped distinguishing anything, because almost everything was it. The operator report and
any future cost function would both have been reading the platform's own anxiety back as
customer demand.

## Decision

**`urgency` is written on creation from what the rider or client asked for, and never
again by the platform.** The platform's own judgement about a request lives in its own
fields:

| What the platform thinks | Where it lives |
|---|---|
| "Nobody has served this in time" | `escalated_at` (and `forced_priority`) |
| "This rider is on a roadside" | `pickup_location`, plus the `request_unassigned` / stranded alert |
| "This rider should go first" | `forced_priority` |

`escalated_at` is exposed on the `RideRequest` API so a board can render a late request as
late. That is the honest version of what the urgency rewrite was reaching for: the same
visibility, without claiming the rider said something they did not.

## Consequences
- The supervisor board must show lateness from `escalated_at` rather than from urgency.
  That is an app change (A11) and the field is in the contract ahead of it.
- Reports keep meaning what they say: "how many high-urgency requests did this client
  make" stays answerable.
- `forced_priority` is still a flag nothing reads in Phase 1 — the pooling hold window is
  not implemented and the Phase 2 cost function is what will weigh it. This decision makes
  sure that when something *does* read it, it is reading the platform's judgement rather
  than a corrupted copy of the rider's.
- A supervisor can still change urgency by hand. That is a human decision with an actor on
  it, which is the difference that matters.

## Alternatives considered
- **Keep the rewrite and accept the noise.** Rejected on the 142-of-150 evidence: a field
  that nearly every row shares carries no information, and this one would also have been
  false.
- **Keep the rewrite only for stranded riders**, whose situation genuinely changed.
  Tempting, and rejected for consistency: the rider on the roadside still did not say
  "high", and one machine-written exception is how a field stops being trustworthy. The
  stranding is already recorded in `pickup_location`, `forced_priority` and an alert of its
  own — richer than a one-word urgency ever was.
- **A separate `effective_urgency`.** Rejected: two urgency fields guarantee that
  something, somewhere, reads the wrong one.
