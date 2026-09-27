# ADR-0014: One simulation run at a time per backend, enforced by the backend

- Status: accepted
- Date: 2026-09-27

## Context
Every scenario begins with `POST /simctl/reset`, which truncates every tenant table and
seeds a fresh world. That is the right behaviour for a reproducible run and a disaster
when two runs share a backend: the second reset destroys the first run's world, and the
first run then fails somewhere much later with an error that names nothing relevant — a
409 on an assignment, a rider whose token stopped working, a fleet that went motionless.

This is not hypothetical. It cost **three long runs** during M06–M08, including the
16-simulated-hour `normal_weekday` twice. Each time the diagnosis took longer than the
run.

Being careful is not a control. The failure is silent, the victim is the *other* process,
and the person who causes it is usually doing something reasonable — kicking off a suite
while a scenario finishes, or re-running a probe.

## Decision
The backend refuses it.

`POST /simctl/reset` accepts a `run_id`. The first reset claims the backend by writing
that id to Redis (`sim:run`) with a two-hour TTL; a reset from a different `run_id` while
the claim stands returns **409** naming the owner. `force: true` takes it over, for a
claim left behind by a run that crashed.

Three details matter more than they look:

- **The claim is atomic** (`SET NX`), not read-then-write. The first implementation read
  the owner and then wrote — so two suites started in the same instant both read "no
  owner" and both claimed, which is exactly the collision the claim exists to stop.
- **Each clock push renews the TTL**, so a long run keeps its claim for as long as it is
  actually running, and only a stopped run lets it lapse.
- **A finished run releases it** (`POST /simctl/release`). The TTL is the fallback for a
  crash, not how a claim normally ends; without the release the next run — often the same
  person seconds later — is refused by a run that no longer exists.

A reset with no `run_id` is unaffected, so the backend's own test suite and any existing
caller keep working.

## Consequences
- The failure is now immediate, local, and says what is wrong: a 409 naming the run that
  holds the backend, instead of an inexplicable error an hour into someone else's run.
- CI can run the suite without arranging exclusivity by convention.
- A crashed run blocks the backend for up to two hours unless `force` is used. That is the
  deliberate trade: a claim that expired quickly would not survive a 16-hour scenario,
  and `force` is one flag away.
- `/simctl/*` exists only under `APP_ENV=sim` (ADR-0008), so none of this reaches
  production.

## Alternatives considered
- **A lock file on the developer's machine.** Rejected: it does not see CI, does not see
  another machine pointed at the same database, and the thing being protected is the
  backend, not the client.
- **Refuse resets outright and require an explicit teardown.** Rejected: a suite legitimately
  resets once per scenario, and a crashed run would need manual clearing every time.
- **Namespace each run's data instead of truncating.** Rejected as a much larger change:
  every query would need the run as a tenant dimension, and reproducibility currently
  comes from starting genuinely empty.
