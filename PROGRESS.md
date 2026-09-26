# Smart Cab - PROGRESS

## Summary (2026-09-26)

**Branch `dev/overnight-1`, 51 commits, all pushed. Working tree clean. Nothing merged to
`main`, no history rewritten, no force pushes, no secrets committed.**

**Every backend task is done (B01-B19), plus all foundation and infra tasks, plus the
simulator through M04.** 27 of 48 tasks complete; the 21 that remain are the Flutter app
(blocked), the rest of the simulator, optional self-hosting, and release.

The headline: **the closed loop works.** A simulated fleet drives the real API, publishes
GPS to the real broker as authenticated vehicles, and appears on the endpoint the
supervisor's map reads - 420 pings out, 420 ingested, none dropped.

### Done this run
| Task | What you have now |
|---|---|
| **B11** | Driver duty, `duty_session`, per-vehicle MQTT credentials, generated Mosquitto password/ACL files |
| **B12** | GPS ingestor: pure drop rules, partitioned `location_ping`, Redis latest position, aiomqtt consumer, HTTPS fallback |
| **B13** | `/ws` realtime hub: token auth, per-channel permission checks, Redis pub/sub fan-out |
| **B14** | Dispatch board, candidate vehicles with ETA and added minutes, manual assignment, automation pause |
| **B15** | Driver trips and stop actions, offline idempotency, the 30-second stop-ETA refresh job |
| **B16** | Notifications: provider interface (log / ntfy / fcm), records, every row of `trip-lifecycle.md` section 6 |
| **B17** | Alerts: SOS, driver issues, list/acknowledge/resolve, stale-vehicle sweep, VIP-no-vehicle |
| **B18** | Trip ratings and the operator report (JSON + CSV), median/p90 wait |
| **B19** | `/simctl/clock` and `/simctl/reset`, sim-only |
| **M04** | The closed loop: platform client, MQTT publishing, shared clock, fleet spawning |

**1177 backend tests, 143 simulator tests, all passing.** ruff, ruff format and mypy clean
on both packages. 100% branch coverage of the state machines, enforced.

### Real defects this run found (not test bugs)

The ones worth knowing about, because each was invisible until something exercised it:

1. **Tokens were validated against the real system clock.** PyJWT checks `iat` and `nbf`
   itself even with `verify_exp` off, so any clock ahead of wall time - exactly what the
   simulator does - had every token rejected as "not yet valid".
2. **One shared `Geography` instance leaked NOT NULL between columns.** GeoAlchemy2 stamps
   a column's `nullable` onto the type object, so `employee.home_location` was NOT NULL in
   the database while the model said optional. There is now a test comparing every
   geography column against `information_schema`.
3. **The GPS ingestor could not start on Windows at all** (aiomqtt needs `add_writer`), and
   **died on its first flush** because it imported only the tracking model, so
   `location_ping`'s foreign key to `vehicle` could not resolve.
4. **The dev Mosquitto ACL silently dropped every authenticated publish.** Rules before the
   first `user`/`pattern` line apply to anonymous clients only - the trap the ACL file's own
   comment warns about.
5. **A no-show left the rider's drop stop pending forever**, so the driver could never
   complete the trip.
6. **`client_admin` could have subscribed to the whole operator's request feed** over the
   WebSocket: they hold `request_queue_view` for their own client, so the permission alone
   was not enough.

### You must install or decide

| # | Action | Unblocks | Why |
|---|---|---|---|
| 1 | **Install the Flutter SDK** | A01-A12, and R02 | Twelve app tasks, the only large blocked group. The Android SDK is already on this machine |
| 2 | Decide **OQ-20**: FCM or self-hosted ntfy | Real push | `PUSH_PROVIDER=log` today. `ntfy` is fully implemented and works now; `fcm` raises with the reason, because silently dropping every push is the failure nobody notices until a rider is standing outside at 7am |
| 3 | Confirm **OQ-25**: which permission guards alerts | Nothing | `/alerts` and the alerts channel ride on `request_queue_view`. Fine unless SOS should reach only a safety lead |
| 4 | Confirm **OQ-24** (202-always on OTP) and **OQ-22/OQ-23** (approx speed, ETA factors) | Tuning only | All three have provisional, documented defaults |
| 5 | Decide **OQ-21**: when to self-host OSRM and tiles | Before the paid pilot | The public OSM services have no SLA and may be withdrawn for commercial use (ADR-0010 A3) |
| 6 | Review **`AGENTS.md`** | Nothing | It appeared in the tree as a byte-identical copy of `CLAUDE.md` and got picked up by a commit. I did not write it. Two copies of the agent rules will drift - keep one, or make one a pointer |

### Decisions I made that you can overrule

Each is recorded in `docs/07-decisions/decision-log.md` with its reasoning:

- **ADR-0011:** manual assignment *reports* hard-rule violations and applies anyway; only
  seat capacity refuses. Overriding the optimizer is the point of manual mode.
- The **WebSocket contract** lives in `docs/03-architecture/websocket-protocol.md`, pointed
  at from `api-spec.yaml` under `x-websocket`. OpenAPI cannot describe a socket.
- **No access token in a WebSocket query string** - header, or a first `auth` frame.
- `Alert.severity` in the spec changed from `critical/high/normal` to
  `critical/warning/info`: the original had no informational level and B17 needs one.

### How to run it

```powershell
make up                      # postgres + postgis, redis, mosquitto
make check-infra             # verifies all three
make backend-dev             # the API on :8000
make test                    # 1177 backend tests
make lint                    # ruff + format + mypy, both packages
make sim-quick               # simulator smoke scenario
```

To watch the closed loop for yourself:

```powershell
# terminal 1
$env:APP_ENV="sim"; $env:SIMCTL_ENABLED="true"; make backend-dev
# terminal 2  (from backend/)
$env:APP_ENV="sim"; python -m app.ingestor
# terminal 3  (from simulator/)
python -m sim run scenarios/smoke_tiny.yaml --platform http://localhost:8000/api/v1
```

It prints `mqtt published=420 unpublished=0`, and `GET /api/v1/dispatch/vehicles` then
shows the cabs with live positions. The five opt-in tests that assert this:

```powershell
$env:SIM_PLATFORM_URL="http://localhost:8000/api/v1"
python -m pytest tests/test_closed_loop_live.py
```

### Suggested next tasks, in order

1. **M05** (employee + driver agents, full loop) - unblocked now, and the natural next step:
   it turns idling cabs into real trips and exercises B14/B15 end to end.
2. **M06, M07, M08** follow from M05 and get the scenario suite into CI.
3. **A01 onwards** the moment Flutter is installed. A11 (supervisor live map) is the one
   that finally shows the simulated cabs moving on a real screen.
4. **I02b** (self-hosted OSRM) before any paid pilot.

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
| 06:55 | B16 | done | Notifications: push provider interface, `notification` records, and every row of `trip-lifecycle.md` section 6 wired to the transition that causes it. 50 tests. The section 6 table is **data, not scattered `if`s** - `app/domain/notifications.py` maps event to (recipient role, title, body), so a test can walk every row and a message sent to the wrong role fails the build. `log` is the default provider and what the tests run against; `ntfy` is fully implemented (plain HTTP, no credentials); **`fcm` raises with the reason** rather than pretending, because silently dropping every push is the failure nobody notices until a rider is standing outside at 7am. The "cab 5 minutes away" trigger fires once per stop from the ETA job - an ETA wobbling either side of five minutes would otherwise buzz a phone every thirty seconds, which is how people turn notifications off | **Decide OQ-20** (FCM vs self-hosted ntfy) before the pilot. `PUSH_PROVIDER=log` until then; `ntfy` works today if you stand up a server |
| 08:10 | B17 | done | Alerts: `/sos`, `/driver/issues`, `/alerts` list, acknowledge and resolve, plus the stale-vehicle sweep and the VIP-no-vehicle prompt. 31 tests. **SOS is the most forgiving path in the codebase on purpose** - a wrong trip id does not refuse it, because someone pressing that button is not in a position to have got the payload right; acceptance measured at well under the 2-second budget, and a second test has a supervisor on a real socket receive the frame. A breakdown or accident takes the vehicle `out_of_service` immediately (DRV-06) - waiting for supervisor confirmation would keep assigning riders to a cab on the hard shoulder - and the vehicle comes from the driver's duty session, never the request body. Stale-vehicle alerts deduplicate on the open alert, so ten minutes of silence is one alert, not twenty, but a resolved one can be raised again. **api-spec.yaml amended first** (hard rule 1): `Alert.severity` was `critical/high/normal`, which has no informational level, and B17 needs one for VIP-no-vehicle; it is now `critical/warning/info`, matching the code | Confirm OQ-25 - alerts still ride on `request_queue_view` |
| 09:20 | B18 | done | Trip ratings and the operator report. 43 tests. **Wait is defined once** - from the rider asking to the rider getting in - because that is the number this product exists to reduce, and a request that never got a cab has `null` rather than zero, since counting cancellations as instant service would flatter every average the pilot is judged on. Median and p90 use linear interpolation between closest ranks (numpy/R type 7), stated explicitly in `app/domain/stats.py`: percentile definitions differ by minutes on small samples, and a report that disagrees with the operator's own spreadsheet is a credibility problem. The CSV is generated from the same rows as the JSON, and a test asserts the two agree. A client admin sees their own client whatever `client_id` they ask for. Added `require_any()` to the B04 framework for the one endpoint two roles reach through different permissions | Nothing |
| 09:35 | M04 | done | **The loop closes.** A `smoke_tiny` run now seeds the real backend, shares its clock, signs a driver into each cab, publishes 420 GPS pings to the real Mosquitto as six authenticated vehicles, and all 420 land in `location_ping` with none dropped - then the cabs show up with live positions on `GET /dispatch/vehicles`, the endpoint the supervisor map reads. 28 unit tests plus 5 opt-in live ones. Verified by hand against the running stack, not just asserted. The last bug was the interesting one: a compressed run publishes an hour of pings in under a second while the backend's clock walks that hour through 60 HTTP calls, so the pings outran the clock and the ingestor correctly rejected them all as `too_far_future`. The sink now **paces** publication to the shared clock - a real cab cannot outrun time, and now neither can a simulated one | Nothing. To see it: `make up`, `APP_ENV=sim make backend-dev`, `python -m app.ingestor`, then `python -m sim run scenarios/smoke_tiny.yaml --platform http://localhost:8000/api/v1` |
| 09:35 | bug | fixed | **The GPS ingestor could not start on Windows at all.** aiomqtt needs `add_writer`, which the default proactor event loop does not implement, so `python -m app.ingestor` died on connect with a traceback that never mentions MQTT. The dev machine is Windows; production is Linux, where the fix is a no-op | Nothing |
| 09:35 | bug | fixed | **The ingestor died on its first flush**, unable to resolve `location_ping`'s foreign key to `vehicle`: it imported only the tracking model, so `Base.metadata` was incomplete. It imports `app.models` now, as Alembic does - the same class of bug the `backend-packaging` CI job exists to catch, in the one process that job does not cover | Nothing |
| 09:35 | bug | fixed | **The dev Mosquitto ACL silently dropped every authenticated publish.** Rules before the first `user`/`pattern` line apply to anonymous clients only, so a client that sends a username - the driver app and the simulator both do - was denied at QoS 0 with no error anywhere. The ACL file's own comment warns about exactly this. Added the authenticated dev rule; production still uses the generated per-vehicle file | Nothing |
| 09:35 | bug | fixed | **The ingestor judged simulated pings against wall-clock time.** `/simctl/clock` now publishes simulated time to Redis and the ingestor reads it (`SharedSimClock`), so the two processes agree on what time it is (CLAUDE.md hard rule 2, across a process boundary) | Nothing |
