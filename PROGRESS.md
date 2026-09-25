# Overnight run - PROGRESS

## Morning summary

**Branch `dev/overnight-1`, 15 commits, all pushed. Working tree clean. No secrets committed.**
Nothing was merged to `main`, no history rewritten, no force pushes.

### Done (8 tasks)
| Task | What you have now |
|---|---|
| Section 1 docs | ADR-0010 sweep finished (`control-model.md` was the only file still missing it) |
| **F01** | Monorepo skeleton, Makefile, `.env.example`, PR template, PowerShell mirror of every make target |
| **I01** | `infra/docker-compose.yml` (postgres+PostGIS, redis, mosquitto) - written, *not* verified |
| **B01** | FastAPI skeleton: app factory, settings, Clock, JSON logging, error handler, Alembic, health endpoints |
| **I02** | Routing provider interface (`osrm` / `approx` / `cached`), Redis rate limiter, `GeocodingProvider=none` |
| **B08** | Domain state machines, 100% statement *and* branch coverage, enforced by a make target and CI |
| **B10** | ETA service, time-of-day factor, degradation ladder, `eta_approximate` added to the API contract |
| **M01-M03** | Simulator: scenario loader, engine, seeded RNG, vehicle movement, GPS pings, recorder, compare |

Backend + simulator: **345 backend tests, 114 simulator tests, all passing**; ruff, ruff format and mypy
clean on both packages.

### You must install or decide

| # | Action | Unblocks | Why |
|---|---|---|---|
| 1 | **`gh auth refresh -s workflow`**, then `git mv .github/workflows-pending/ci.yml .github/workflows/ci.yml`, commit, push | F02 | No credential here has the GitHub `workflow` scope, so *any* push touching `.github/workflows/` is rejected. The pipeline is written and validated; it just cannot be uploaded. Steps are in `.github/workflows-pending/README.md` |
| 2 | **Install Docker Desktop**, then `make up && make check-infra` | I01, and the whole B02-B19 chain | `make check-infra` runs I01's exact acceptance criteria (PostGIS extension, redis PING, mosquitto subscribe) |
| 3 | **Install Flutter + Android SDK** | A01-A12 | Nothing app-side could be started |
| 4 | Decide **OQ-22** (`approx` base speed, provisional 24 km/h) and **OQ-23** (ETA time-of-day factors) | Tuning only | Both are config values with provisional defaults and a documented source; neither blocks code |
| 5 | Review the **api-spec change** in B10 (`eta_approximate` fields) | - | Contract change, made spec-first per hard rule 1 |

### How to run what was built

```powershell
# one-time
python scripts\venv_setup.py --install     # creates .venv, installs backend + simulator

# checks (both routes work; use whichever you prefer)
make lint            # or  .\scripts\dev.ps1 lint      - ruff + format + mypy, both packages
make test            # or  .\scripts\dev.ps1 test      - 345 backend tests
make test-domain-coverage                                # B08: fails under 100% branch coverage

# the API (health endpoints work; there are no business endpoints yet)
make backend-dev
curl http://localhost:8000/health/live      # 200 {"status":"ok"}
curl http://localhost:8000/health/ready     # 503 until Postgres runs - the detail says why

# the simulator
cd simulator
python -m sim validate scenarios/smoke_tiny.yaml
python -m sim run scenarios/smoke_tiny.yaml     # writes runs/<timestamp>_smoke_tiny/
python -m sim compare runs/<run-a> runs/<run-b>
make sim-quick
```

### Suggested next tasks, in order
1. **Activate CI** (action 1 above) - two commands, and every later PR gets checked.
2. **Docker, then B02** (core schema: tenancy, users, roles). It gates B03-B07 and everything after.
3. **B05** (config service) soon after B02: the provisional constants in `EtaConfig` and `ApproxConfig`
   are waiting for a real home in `operator_config`, which is where OQ-22/OQ-23 get resolved.
4. **A01** once Flutter is installed - it has no backend dependency and can run in parallel.

### Two things worth knowing
- `runs/` is git-ignored, so simulator output never lands in a commit.
- One commit message (`b460187`, I01) has mangled text: backticks in the message were expanded by the
  shell before git saw them. The content is intact and the code is unaffected; I did not amend it because
  the commit was already pushed and rewriting pushed history was out of bounds.

---


Branch: `dev/overnight-1` (from `main` @ b135a4d). Started 2026-09-24, unattended.
Append-only log below; newest entries at the bottom of each section.

---

## Environment check (2026-09-24, start of run)

| Tool | Available | Detail |
|---|---|---|
| git | **yes** | 2.54.0.windows.1; remote `origin` → github.com/kumarnitish378/flex-platform, `git ls-remote` authenticates OK |
| python | **yes** | 3.14.4 (`C:\Users\nitis\AppData\Local\Programs\Python\Python314\python.exe`). Note: docs target 3.12; 3.14 satisfies `>=3.12` but some C-extension wheels (asyncpg) may not exist yet — see per-task notes |
| pip | **yes** | 26.2 |
| uv | **no** | not installed; using `python -m venv` + pip instead (no system-wide installs performed) |
| docker | **NO** | `docker` not on PATH in either shell; daemon status unknown/unavailable |
| flutter | **NO** | not on PATH |
| make | **yes** | GNU Make 3.81 (GnuWin32) — resolvable from both Git Bash and PowerShell |
| node | yes | v24.15.0 (not required by any Phase 1 task) |
| Shells | PowerShell 5.1 (primary) + Git Bash |

**Consequences for tonight**
- Docker missing → anything whose acceptance criteria require running Postgres/PostGIS, Redis or Mosquitto
  containers can be *written* but not *verified*. Those tasks are marked accordingly below.
- Flutter missing → all `A0x` app tasks are blocked.
- GnuWin32 make on Windows is unreliable with POSIX recipes, so equivalent PowerShell scripts are provided in
  `scripts/` and documented in `README.md` (as instructed).

---

## Task log

| Time | Task | Status | What changed | Morning action for you |
|---|---|---|---|---|
| 00:00 | Setup | done | Branch `dev/overnight-1` created from main; `PROGRESS.md` added; environment probed (table above) | Nothing |
| 00:20 | Section 1 docs | done | `control-model.md` section 6 rewritten (routing degradation ladder incl. rate-limit case, approximate flag, tile-cache degradation, no geocoding to degrade). Every other file in the ADR-0010 sweep was already correct from commits 96f0657/b135a4d on main, so skipped per instruction. Commit `docs: public OSM servers per OSMF policies (ADR-0010)` | Nothing |
| 00:45 | F01 | done | Monorepo skeleton: `app/ backend/ simulator/ infra/ scripts/` with per-directory READMEs, root `Makefile`, `.gitignore`, `.editorconfig`, `.env.example`, PR template. `make help` parses the Makefile so help cannot drift, and names the task that creates each unusable target. `scripts/dev.ps1` mirrors every target for PowerShell. Verified: `make help` and `.\scripts\dev.ps1 help` both run | Nothing |
| 01:10 | F02 | **blocked (partially done)** | Complete CI pipeline written: detect + backend-lint + backend-test + app-analyze + app-test + sim-quick + policy-guards, `ROUTING_PROVIDER=approx` so CI can never hit public OSM. YAML validated locally; both policy guards dry-run clean. **Parked at `.github/workflows-pending/ci.yml`** because no credential here has the GitHub `workflow` OAuth scope (git helper and `gh` both have only gist/read:org/repo) - any push touching `.github/workflows/` is rejected | **Run `gh auth refresh -s workflow`, then `git mv .github/workflows-pending/ci.yml .github/workflows/ci.yml`, commit, push, open the PR and confirm green.** Full instructions in `.github/workflows-pending/README.md` |
| 02:05 | I01 | **blocked (written, unverified)** | `infra/docker-compose.yml` (postgres+PostGIS, redis, mosquitto; health checks, named volumes, UTC postgres), `postgres/init/01-extensions.sql` (postgis + pgcrypto), mosquitto dev config + ACL placeholder documenting the per-vehicle rules B11 will generate. YAML validated. Added `scripts/check_infra.py` / `make check-infra` which runs this task's exact acceptance criteria | **Install Docker Desktop**, then `make up` and `make check-infra`. Task stays `[~]` until that passes |
| 03:40 | B01 | done | FastAPI app factory + `app/core/{clock,settings,errors,logging,db,health}.py`, Alembic (URL from settings, never committed), health endpoints, 41 tests. Health lives at the root, outside `/api/v1` and outside api-spec.yaml, per architecture.md section 5. Verified: ruff + ruff format + mypy clean, 41 tests pass, uvicorn really serves `/health/live` 200 and `/health/ready` 503-with-reason. `make`/`dev.ps1` now run through `scripts/venv_exec.py` so they use `.venv`, not whichever python is on PATH. Backend versions pinned and recorded in tech-stack.md | Nothing. Optional: `make install` on your side to create the same `.venv` |
| 05:30 | I02 | done | Routing provider interface with `approx` / `osrm` / `cached` implementations, Redis token-bucket limiter shared across processes, identifying User-Agent, `GeocodingProvider` with the Phase 1 `none` implementation, providers wired into the app factory. Settings now reject a public Nominatim URL at startup. Verified: ruff + mypy clean, 117 tests, including two processes over one Redis held to 1 req/s under a fake clock, and a guard test that fails on any hard-coded public OSM URL. Fixed a latent structlog bug that broke any test logging after the logging tests. Added OQ-22 (the `approx` base speed is the one number no doc specifies - implemented as a config key at a provisional 24 km/h) | Decide OQ-22 eventually; nothing blocking |
| 06:40 | B08 | done | `app/domain/state_machines.py`: pure transitions for request/trip/stop/vehicle, returning events with the notification targets from trip-lifecycle.md section 6; guards for cancel-reason, no-show wait, supervisory unassign and locked requests. Exceptions moved to `app/domain/errors.py` so the domain imports no framework. **100% statement and branch coverage**, now enforced by `make test-domain-coverage` and a CI step. 323 tests pass | Nothing |
| 07:50 | M01 | done | Simulator package: scenario loader (strict pydantic - a typo is an error, not a silent no-op), SimPy engine, SimClock, per-agent seeded RNG, routing client, CLI. `scenarios/smoke_tiny.yaml` (S01). The OSRM client refuses public hosts in its constructor. Verified: `python -m sim validate scenarios/smoke_tiny.yaml` passes, a bad file exits 1 with the reason, `make sim-quick` runs; 64 tests | Nothing |
| 08:20 | M02 | done | `VehicleAgent`: follows the routed geometry with lognormal speed noise and 5 m GPS noise, emits pings with the exact `mqtt-topics.md` payload to a pluggable sink. Ping intervals include the subtle rule (a cab at a light keeps 5 s pings; 30 s only after 2 min stationary); off duty emits nothing at all. "Plot matches the geometry" is checked numerically - every ping within a metre of the polyline - so it runs in CI. 88 tests | Nothing |
| 08:45 | M03 | done | Recorder writes `runs/<timestamp>_<scenario>/` with metrics.json, pings.csv, requests.csv, trips.csv, events.log, summary.md; `python -m sim compare A B` prints a delta table. Demand metrics are **null, not zero**, because "nobody gave up" and "not measured until M05" are different claims. 114 tests | Nothing |
| 09:30 | B10 | done | `EtaService` on the I02 provider interface: time-of-day factor (not applied to `approx`, which would double-count), `approximate` flag, single table call for matrices. **api-spec.yaml changed first** (hard rule 1): `eta_approximate` on TripStop and Candidate, `pickup_eta_approximate` on the assignment view. Degradation tested as behaviour - OSRM error, timeout and rate-limit each yield a usable flagged ETA, and recovery is immediate. Live-OSRM integration test included, skipped unless `OSRM_URL` is self-hosted. Added OQ-23 for the factor values. 345 tests, 3 skipped | Decide OQ-23 eventually; nothing blocking |
| 09:45 | B02-B19 (except B08, B10) | **blocked** | Not started. Every remaining backend task needs PostgreSQL + PostGIS to meet its acceptance criteria (migrations, repository and tenant-isolation tests, testcontainers), and Docker is not installed | **Install Docker Desktop.** Then B02 is the next task |
| 09:45 | A01-A12 | **blocked** | Not started. All app tasks need the Flutter SDK | **Install Flutter SDK + Android SDK** if you want app work next |
| 09:45 | M04-M08 | **blocked** | Depend on B12/B19 (GPS ingestor, sim control endpoints), which need the database | Unblocked by Docker, then the B-chain |
| 09:45 | R01-R03 | **blocked** | Need a staging VM, Play Console access and pilot data | Out of scope for an overnight run |
| 10:05 | OQ-02 | done | Status set to "resolved by owner (2026-09-24); details to be added by owner". No details invented | Write the actual resolution into OQ-02 when you can |
| 10:20 | I01 | done (was blocked) | Docker Desktop is installed now, so I01's acceptance criteria finally ran. Postgres and redis passed first time; **mosquitto was unhealthy** - the healthcheck subscribed to `$SYS/broker/uptime` but the dev ACL grants `sc/v1/#` only, so the subscription was silently denied and the check hung. Both the compose healthcheck and `check_infra.py` now use `mosquitto_sub -E` on `sc/v1/#`. All three containers healthy; PostGIS 3.4 confirmed | Nothing. `make up` then `make check-infra` reproduces it |
| 11:40 | B02 | done | 12 tables (operator, client, office, client_policy, zone, app_user, user_role, refresh_token, otp_challenge, device, employee, saved_place), Alembic migration, tenant-scoped repositories, 40 integration tests on real PostGIS. Found and fixed two real defects: the `user_role` unique constraint did nothing for NULL `client_id` (now NULLS NOT DISTINCT), and autogenerate wanted to drop PostGIS's `spatial_ref_sys`. CI gained a PostGIS service and a guard that fails if the integration suite skips | Review the schema against `data-model.md` when you get a chance |
| 13:10 | B03 | done | Six auth endpoints, 36 integration tests on real Postgres with a FakeClock. **Amended api-spec.yaml first** (hard rule 1): `/auth/otp/request` now always answers 202, because the specified 404 would have made it a directory of staff and riders - recorded in the decision log with OQ-24 so you can overrule. Verify failures are byte-identical whatever went wrong. OTP codes and refresh tokens stored hashed (tests assert they never appear in clear). PyJWT flagged our HMAC key as under RFC 7518's 32-byte minimum, so staging/prod now refuse a short `JWT_SECRET` | Decide OQ-24 (202-always vs 404); pick an SMS provider (OQ-16) before real logins |
| 14:05 | B04 | done | `require(Permission.X)` dependency + the harness that walks every route and fails if one declares no permission / `public_route()` / `self_service_route()`. Found that this FastAPI version nests included routers, so my first walker found **zero** routes and passed vacuously - there is now a test that fails if the harness ever sees nothing again. Denied cells of the matrix tested explicitly | Nothing |
| 15:20 | B05 | done | Config registry with every key/default/range from allocation-rules.md section 1, `operator_config` + history tables, GET/PATCH `/admin/config`. Out-of-range rejected with 422; history row per change; no history row when the value is unchanged. Patches validate in full before writing, so a bad third key cannot leave the first two applied | Nothing |
| 16:30 | B06 | done | Eight `/admin/*` endpoints (clients, offices, vehicles, drivers, invites) + vehicle/driver tables, 43 tests. Tenancy checked on **cross-references** too: creating an office under another operator's client, or pointing a driver at a foreign vehicle, is a 404 - the FK alone would have allowed both. The supervisor "status only" matrix row needed a field-level check, not just a route-level one | Nothing |
| 17:40 | B07 | done | Employee CRUD scoped for `client_admin` + CSV import with dry-run report. 66 tests. The parser is pure (no DB, no HTTP) and reports **every** bad row rather than stopping at the first - a 500-row file with 50 bad phones returns exactly 50 errors with spreadsheet-accurate row numbers. Dry run is the default and writes nothing at all, not even the valid rows. Re-importing updates by phone instead of duplicating. `zone_id` stays null, as the task specifies | Nothing |
| 19:10 | B09 | done | Ride requests: create (self and on behalf), EMP-02 validation (7-day range, 60-minute same-direction duplicate window), list mine, get, cancel, and a **Clock-driven expiry sweep** with the 15-minute near-expiry alert. 42 tests. Expiry is proven by advancing a FakeClock, never by sleeping. Every status change goes through the B08 state machine and writes a `ride_request_event`; `_apply` is the only writer of `status`. Also added the `alert` table (B17 adds its endpoints) since the near-expiry warning needs somewhere to land | Nothing |
| 20:05 | B19 | done | `/simctl/clock` (GET/PUT) and `/simctl/reset`, mounted **only** when `APP_ENV=sim` - the router is never registered elsewhere, so dev/staging/prod 404 because the paths genuinely do not exist rather than because a flag says so. PUT runs due work synchronously before returning, so the simulator can never race a worker. Reset seeds the fixture testing-strategy.md section 4 specifies (2 offices, 3 zones, 20 employees, 6 vehicles) with deterministic ids and one ready-to-use token per role. `scenario_yaml` is refused loudly rather than half-honoured. 24 tests | Nothing |
| 22:30 | B11 | done | `/driver/duty` (on/off), `duty_session`, vehicle status through the state machine, per-vehicle MQTT credentials and generated Mosquitto password/ACL files. 48 tests. The `$7$` password format was reverse-engineered from the real broker (`mosquitto_passwd` in the container) and is reproduced byte for byte - pinned by a test, because a wrong format would silently lock out every driver. **The ACL denial is verified against the live broker**: run `MQTT_ACL_TEST=1 pytest tests/integration/test_mqtt_acl_live.py` after `make up` (opt-in, since it reconfigures the shared dev broker and restores it afterwards). Found and fixed a real bug: a driver going on duty could silently clear a supervisor's out-of-service flag | Optional: run the live ACL test yourself to see it |
| 01:15 | B12 | done | GPS ingest, transport-agnostic: the same validation serves MQTT and the `/driver/location` HTTPS fallback, so a driver on a bad connection cannot get laxer rules than one on a good one. Pure drop rules in `app/domain/gps.py` (accuracy, age, future, implied speed, batch cap), an aiomqtt consumer process (`python -m app.ingestor`), Redis latest-position + pub/sub for B13, and batched inserts into a **RANGE-partitioned** `location_ping` (monthly partitions + a default, created by the migration). Out-of-order pings are stored but never move the map marker backwards. The vehicle on the HTTPS route is resolved from the open duty session, **never** from the request body, so a driver cannot post as another cab. 70 tests. Acceptance measured: 200 vehicles x 3 cycles persisted in 0.23 s total, about 0.06 s per 200-ping cycle against a budget of 2 s | Nothing |
| 03:05 | B14 | done | Dispatch board, candidates and manual assignment. Five endpoints, trip/trip_stop/trip_event tables, 80 tests. Took B14 **before** B13 on purpose: B13's acceptance is "employee receives only own trip channel", and trips did not exist yet. Sequencing and the eleven hard rules are pure (`app/domain/dispatch.py`), driven by one pre-fetched ETA matrix rather than a routing call per insertion position. **ADR-0011** records the one judgement call the task forced: manual assign *reports* hard-rule violations and applies anyway - overriding the optimizer is the point of manual mode - with capacity the single refusal, because five people do not fit in a four-seat car. Accepted violations are written to `trip_event` so an override stays visible. Found and fixed two real bugs on the way (see the next two rows) | Nothing |
| 03:05 | bug | fixed | **Tokens were validated against the real system clock.** PyJWT checks `iat`/`nbf` itself even with `verify_exp` off, so any clock running ahead of wall-clock time - exactly what the simulator does - had every token rejected as "not yet valid". All three checks now use the injected Clock (CLAUDE.md hard rule 2). Two regression tests, including one that proves expiry is still enforced | Nothing |
| 03:05 | bug | fixed | **One shared `Geography` instance was leaking NOT NULL between columns.** `Point = Geography(...)` was shared by seven columns; GeoAlchemy2 stamps a column's `nullable` onto the type object, so the first `nullable=False` silently made the rest NOT NULL - `employee.home_location` was NOT NULL in the database while the model said optional. `Point`/`Polygon` are factories now, and a test compares every geography column's nullability against `information_schema` so it cannot drift again | Nothing. `home_location` was set NOT NULL deliberately, matching data-model.md |
| 03:05 | bug | fixed | Alembic autogenerate wanted to **drop the `location_ping` partitions** (same class of bug as `spatial_ref_sys` in B02): partitions are real tables no model declares. `env.py` now filters them and their inherited indexes | Nothing |
| 04:30 | B13 | done | `/ws`: token auth, channel subscription with per-channel permission checks, Redis pub/sub fan-out. 56 tests. **`docs/03-architecture/websocket-protocol.md` is new and is the contract** - OpenAPI cannot describe a WebSocket, so `api-spec.yaml` points at it under `x-websocket` and the change-the-contract-first rule applies there too. The token is accepted in the `Authorization` header or a first `auth` frame, **never** in the query string (URLs end up in proxy logs and browser history). Found a real authorisation hole while writing it: `client_admin` holds `request_queue_view`, so permission alone would have let them subscribe to the whole operator's request feed - operator channels now also require the caller not to be client-scoped. The hub keeps one Redis subscription per channel however many sockets want it, and one dead or hanging socket cannot stall the others | Confirm OQ-25 (which permission guards the alerts channel) when B17 lands |
| 05:50 | B15 | done | Driver trips and stop actions: `/driver/trips`, start, arrived / done / no_show, complete, plus the 30-second stop-ETA refresh job. 53 tests. **Two clocks throughout**: `occurred_at` is when the driver tapped and is the business time; `Clock.now()` is when we heard and is the audit time - otherwise a trip that finished at 18:04 gets recorded as finishing at 19:30 when the phone found signal. Idempotency is the database's job: `client_event_id` is a unique index on `trip_event`, so a retried offline event cannot pick the same rider up twice. The ETA job walks the remaining stops in order so a rider three stops down sees the queue ahead of them rather than a direct time, and it refuses to invent an ETA for a cab that has not pinged; `/simctl/clock` runs it, so simulated time refreshes ETAs too. Three real bugs found while writing it: the same idempotency key was written to two rows when start had to pass through `dispatched`; only the first stop of a trip was ever `en_route`, so no later stop could legally reach `arrived`; and a no-show left the rider's drop stop pending forever, so the driver could never complete the trip | Nothing |
