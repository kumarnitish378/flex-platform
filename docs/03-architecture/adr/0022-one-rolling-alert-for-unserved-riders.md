# ADR-0022: One rolling alert for unserved riders, and it clears itself

- Status: accepted
- Date: 2026-10-03
- Settles: OQ-31. Decided without the product owner present, on their instruction; overrulable.

## Context
ADR-0019 raises a `request_unassigned` alert when nobody has served a request in time, one
per request, deduped so each fires once. That is right for a quiet morning.

A live `evening_surge` run escalated **142 of 150 requests**, which under that design is
142 open alerts on one board. The count was honest — 142 riders really were unserved — and
the board was useless. Worse than useless: the next alert that genuinely needs a human, an
SOS or a breakdown, arrives into a list of 142 rows and is indistinguishable from them.

An alert is the product admitting something needs a human (the module docstring says so).
142 admissions of the same thing is not 142 things needing a human; it is one.

## Decision

**One rolling `request_unassigned` alert per operator**, carrying `riders` (how many are
unserved) and `longest_wait_minutes` (the worst of them). While an open or acknowledged one
exists, later escalations **update it in place** rather than adding rows.

Per-request detail is not duplicated into the alert. It is on the request — `escalated_at`,
the wait, the rider — which is where a supervisor who clicks through is already looking.
The alert's job is to make them look.

**The alert resolves itself when the condition clears.** Once no `queued` request for that
operator carries an `escalated_at`, the sweep sets it `resolved`. A condition alert that
outlives its condition is worse than no alert: it says riders are stranded when they are
not, and it trains people to ignore the row — so when it is true again, nobody looks. The
row survives with `resolved_at`, so the history is intact.

## Consequences
- The board shows one row that reads "12 riders unserved, longest waiting 48 min" and
  changes as the morning does, instead of a wall of identical rows.
- `riders` accumulates across sweeps rather than being recounted, so it reads as "how many
  have been failed since this started", not "how many right now". That is the number a
  supervisor is accountable for; the live count is the board's own job.
- Auto-resolution means an alert can open and close without a human ever seeing it — on a
  day where the queue cleared itself. The `notification` and `alert` rows remain, so the
  report can still say it happened.
- A supervisor acknowledging the alert does not stop it updating: the condition is still
  true and the count still matters. It stops only when it is no longer true.

## Alternatives considered
- **Per-request alerts, collapsed by type in the app.** Rejected: it moves a data problem
  into every client that ever renders alerts, and the WebSocket feed would still carry 142
  events. The server should not emit 142 statements of one fact.
- **Keep one alert per request and rely on the board's sort order.** Rejected: that is the
  behaviour this settles, and the sort order does not help the SOS buried among them.
- **Leave the alert open until a human resolves it.** Rejected: see above — a stale "riders
  stranded" row is actively misleading, and the first thing a supervisor learns is to
  ignore it.
- **Re-count `riders` from the queue each sweep.** Tempting, and it would make the number
  live. Rejected because it then silently falls as riders give up, so the alert would get
  *quieter* as the morning got worse.
