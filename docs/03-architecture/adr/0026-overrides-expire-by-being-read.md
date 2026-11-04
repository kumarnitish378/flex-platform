# ADR-0026 — An override expires by being read, not by being swept

**Status:** accepted · **Date:** 2026-10-17 · **Task:** B26 · **Supersedes:** nothing

## Context

`control-model.md` §3 rule 5 gives every override an `expires_at`, defaulting to the end
of the current shift. Rule 1 says the optimizer and the failsafe must never revert an
override while it stands. Put together, the platform has to know at every moment whether
a lock, a pooling block, a forced priority or a hold is still in force.

The obvious implementation is a job: a sweep that runs every minute, finds overrides
whose time has passed, and clears the columns they set. Phase 1 already has four such
sweeps and a Celery beat to run them, so it would have cost almost nothing to add a
fifth.

## Decision

**There is no sweep. The applied state carries its own end date and every read asks
whether it still applies.**

- `ride_request.override_until` gates `lock_vehicle_id` and `forced_priority`.
- `ride_request.hold_until` is the hold's own time, as `data-model.md` already had it.
- `trip.override_until` gates `pooling_blocked` (new column, B26).
- `app/domain/overrides.py::still_applies(expires_at, now)` is the whole mechanism, and
  the dispatch service calls it where it builds the facts the hard rules judge.

Two consequences worth stating plainly:

**One expiry column per request, shared between `lock` and `force_priority`.** When both
stand on one request the **later** end date wins, because ending early would silently
drop an override whose own time had not come. The per-action truth stays exact in
`override_log`, which is what the audit and Phase 3's training data read. Both default
to the same 23:59, so the two differ only when a supervisor types a date by hand.

**`vehicle_out_of_service` is the exception: its `expires_at` is recorded and shown, and
nothing acts on it.** A lock that lapses frees a decision. A cab that comes back on the
road by itself because a timestamp passed is a cab in a workshop being sent to a rider.
Somebody says when it is back.

## Why

**A sweep would be a second source of truth.** The column would be right only because
something ran; the platform would be correct only while the beat was healthy. Every
restart, every missed tick and every deploy window would be a period in which an expired
lock still pinned a rider to a cab — and the failure is silent, because a stale lock
looks exactly like a current one.

**Expiry is cheap to ask and expensive to maintain.** `still_applies` is a comparison on
a column already loaded. The sweep would be a query, a task, a schedule entry, a metric,
and a B20 guard proving the simulator's clock drives it too.

**The simulator would have had to drive it.** Hard rule 2 means a sweep must run off the
injected `Clock`, so a scenario that jumps an hour has to be given an hour's worth of
expiry sweeping. `still_applies` gets that for free: the simulated clock is the one the
read already uses, so an override expires correctly at a simulated 23:59 with nothing
added to `/simctl/clock`.

**The columns stay honest.** Nothing rewrites `lock_vehicle_id` behind a supervisor's
back, so the board can still show "locked to DL-1234, until 23:59" after the lock has
lapsed, and the audit can still answer what was set and when.

## Also decided here: `locked_to_other_vehicle` is waivable by `reassign`, and only by it

B21 put `locked_to_other_vehicle` in `NEVER_WAIVABLE` because waiving it would
**silently** undo another supervisor's override. A `reassign` is the opposite of silent:
a human naming this request, this cab and a reason, which §3 lists as an action available
in every mode, and which the state machine has required an explicit `is_override` for
since Phase 1.

So the lock is waivable by `reassign` and by nothing else. It still needs rule 4's
narrowed reasons and a note, it is still flagged in the report, and **the lock moves with
the rider** — left behind it would point at a cab they are no longer on, and every read
afterwards would report a violation against the vehicle actually carrying them.

## Consequences

- A new table or code path that reads `lock_vehicle_id`, `forced_priority` or
  `pooling_blocked` **must** gate it on `still_applies`, or it will honour expired
  overrides. There are three such reads today, all in `DispatchService`.
- `override_log` is operational, not only an audit: `unlock` closes the open `lock` row
  by setting its `expires_at` to the moment of release.
- A report of "overrides in force at 15:00 yesterday" is answerable from `override_log`
  alone, which the sweep design would have destroyed by erasing the columns.
