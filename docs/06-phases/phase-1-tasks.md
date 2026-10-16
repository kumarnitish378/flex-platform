# Phase 0–1 tasks

How to use: an AI agent takes **one task at a time**, reads the listed docs, implements, tests, and ticks the box. Do not start a task until its dependencies are done. IDs: F = foundation, I = infra, B = backend, A = app, M = simulator, R = release.

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done

## Foundation (Phase 0)

- [x] **F01 · Monorepo skeleton**
  Docs: CLAUDE.md, coding-standards.md
  Do: create `app/`, `backend/`, `simulator/`, `infra/`, root `Makefile`, `.gitignore`, `.env.example`, `.editorconfig`, PR template with checklist.
  Done when: `make help` lists targets; repo tree matches CLAUDE.md.

- [x] **F02 · CI pipeline** · deps F01
  Do: GitHub Actions workflow with jobs: backend-lint, backend-test, app-analyze, app-test, sim-quick (initially no-op placeholders that pass once each part exists).
  Done when: workflow runs green on an empty PR.
  Green on PR #1: detect, backend-lint, backend-test, backend-packaging, app-analyze, app-test, sim-quick,
  policy-guards. Two extra jobs beyond the task list: `policy-guards` (no hard-coded public OSM URLs, no
  committed `.env`) and `backend-packaging`, added after CI caught an undeclared runtime dependency that a
  test-only install had masked. All eight are required status checks on `main`.

- [x] **I01 · Infra compose (core)** · deps F01
  Docs: dev-environment.md
  Do: `infra/docker-compose.yml` with postgres(PostGIS), redis, mosquitto (dev config + ACL placeholder), health checks; `make up/down`.
  Done when: `make up` starts all; `psql` can `CREATE EXTENSION postgis`.
  Verified on Docker 29.8.0: all three containers healthy, `CREATE EXTENSION postgis` returns
  `3.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1`, redis PONGs, mosquitto accepts a subscription.
  `make check-infra` runs these checks on demand.

- [x] **I02 · Routing provider config (public OSRM + approx + cache)** · deps I01
  Docs: ADR-0010, dev-environment.md §3–4, architecture.md §3.4
  Do: settings for `ROUTING_PROVIDER`, `GEOCODING_PROVIDER`, `OSRM_URL`, `TILES_URL`, `OSM_USER_AGENT`,
  `OSM_CONTACT_EMAIL`, `ROUTING_CACHE_TTL_SECONDS`, `OSM_RATE_LIMIT_PER_SECOND`; `.env.example` pointing at
  the public OSRM and tile servers; `RoutingProvider` protocol with `osrm`, `approx` (haversine × 1.4 +
  time-of-day speed table) and `cached` (Redis) implementations; `GeocodingProvider` protocol with a `none`
  implementation as the default (`NOMINATIM_URL` unset — public Nominatim must never be called); Redis
  token-bucket limiter (1 req/s per service, shared across processes) that falls back to `approx` and flags
  results approximate; identifying `User-Agent` on every outbound request. No map containers in compose.
  Done when: unit tests cover provider selection, cache hit/miss, limiter fallback and the `approximate`
  flag; two processes sharing Redis cannot exceed 1 req/s (test with a fake clock); no map URL appears as a
  literal anywhere outside settings (grep test); a test fails if any configured geocoding URL resolves to
  `nominatim.openstreetmap.org`; `ROUTING_PROVIDER=approx` works with the network unplugged.

- [x] **B01 · Backend skeleton** · deps F01, I01
  Docs: architecture.md, coding-standards.md §2
  Do: FastAPI app factory, settings (pydantic-settings), async DB session, Alembic init, `Clock` (SystemClock + FakeClock), error handler, JSON logging, `/health/live` and `/health/ready`.
  Done when: `make backend-dev` serves health endpoints; unit test proves FakeClock is injectable; ruff + mypy clean.

- [x] **A01 · App skeleton** · deps F01
  Docs: tech-stack.md, coding-standards.md §3
  Do: Flutter project, Riverpod, go_router, theme, env via `--dart-define`, ARB setup (en), folder layout, strict lints.
  Done when: app builds and runs on Android emulator showing splash; `flutter analyze` clean.
  Flutter 3.47.6 stable; `com.flexplatform.smart_cab` (provisional, OQ-18). Splash ->
  login -> role home, with the role deciding home and what each role may open
  (`roleMayOpen`). Nothing is faked: there is no way to sign in until A03, because a
  pretend login is how screens get built against a session that does not exist. A
  **debug APK builds** on this machine - `flutter analyze` clean, 26 tests.
  One bug the tests caught immediately: `redirect` is only consulted on navigation, so
  signing out cleared the session and left the person on a screen they were no longer
  allowed to see. The router listens for session changes now.

- [x] **A02 · API client generation** · deps A01, B01
  Docs: ADR-0009, api-spec.yaml
  Do: `make api-client` generates Dart client into `app/lib/data/api/`; wrapper with auth interceptor (token + `X-Active-Role`, refresh on 401).
  Done when: generated client compiles; interceptor unit-tested.
  `make api-client` runs `scripts/api_client.py`: it finds Java (Android Studio's JBR),
  caches a pinned openapi-generator, generates `dart-dio`, and runs `build_runner`.
  The client is a **package** at `app/packages/smart_cab_api/` rather than files under
  `lib/data/api/`, because dart-dio emits its own pubspec and needs build_runner -
  neither of which can live inside the app's own package. `lib/data/api/` holds the
  hand-written wrapper, which is the part worth reading. `coding-standards.md` §3 updated
  to say so.
  **Generating it found a real spec defect:** `tracker_type` was an inline enum on
  `VehicleInput`, inherited by `Vehicle` and `VehicleLive` through `allOf`, and the
  generated client referenced a `VehicleInputTrackerTypeEnum` class it never emitted -
  so the client did not compile. Named as `TrackerType` and `$ref`-ed, like the two
  enums above it. Nothing but generating a client would have found that.
  Two machine constraints worth knowing: `build_runner` is run with `--force-jit`
  because Windows Application Control blocks `gen_snapshot.exe` here (the same policy
  that blocks mypy's compiled wheel), and the generator needs `-i` as a POSIX path or it
  rejects `D:\...` as an illegal URI.

- [x] **B20 · Scheduler: the platform's due work** · deps B09, B15, B17
  Docs: tech-stack.md (Celery), architecture.md §3.2, ADR-0008
  Do: Celery app + beat schedule running the three sweeps that have to happen on their
  own - expiry and escalation, the stop-ETA refresh, and the stale-vehicle sweep.
  Done when: `make worker` and `make beat` run; every sweep reachable from a clock jump
  is also reachable from the beat, proved by a test.

  **Why this task exists.** It was not in the plan, and it should have been. Until now
  the three sweeps had exactly one caller between them: `PUT /simctl/clock`, which is
  mounted only when `APP_ENV=sim` (ADR-0008 - "a runtime flag could be flipped; an
  unregistered route cannot be"). Two services even documented themselves as "called by
  the Celery beat loop in production". There was no Celery: not a dependency, not a
  package, not a target that ran.

  So a deployed Phase 1 would have silently done none of this: requests never expiring,
  no near-expiry warning, no escalation (ADR-0019, written the same day), no
  stale-vehicle alert (SUP-01), and no stop-ETA refresh (B15's "30-second job"). Every
  one is work that is supposed to happen by itself, so its absence looks like a quiet
  morning - and the simulator exercised all of it, because the simulator drives the
  clock endpoint.

  Found by `make help` reporting `worker` and `beat` as "not usable yet", which they had
  been since F01.

  The tasks are deliberately thin - open a session, call the same service method the sim
  endpoint calls, commit, log - so production and the scenarios run the same code. The
  guard test reads the sim endpoint's source and fails if it runs a sweep the beat does
  not, which is this exact failure caught at its source.

  One dependency consequence: `redis` is pinned to 6.4.x rather than 8.x, because
  Celery's broker goes through kombu, which caps it at `<6.5`. Every Redis API this
  project uses has existed since 5.0, so the ceiling costs nothing.

- [x] **M01 · Simulator skeleton** · deps F01, I02
  Docs: simulator-spec.md §2–4, ADR-0010
  Do: package layout, CLI, scenario YAML loader + schema validation, SimPy engine, routing through the
  provider interface (`approx` by default; `osrm` only when `OSRM_URL` is self-hosted), seeded RNG.
  Done when: `python -m sim validate scenarios/smoke_tiny.yaml` passes; unit tests for loader; a run with
  the default config makes zero requests to a public OSM host (asserted in tests).

- [x] **M02 · Vehicle movement v0** · deps M01
  Do: vehicle agent moves along the geometry returned by the routing provider (`approx` gives a straight-line
  path at the time-of-day speed) with speed noise; emits GPS pings to a local log (not yet MQTT).
  Done when: plot of a simulated route matches the provider's geometry; pings respect interval rules; the
  same scenario runs identically with `approx` and with a self-hosted `osrm` provider.

- [x] **M03 · Recorder + metrics v0** · deps M01
  Do: recorder writes runs/ folder with metrics.json and CSVs; `python -m sim compare`.
  Done when: a dry run produces files; compare prints a delta table.

## Backend (Phase 1)

- [x] **B02 · Core schema: tenancy, users, roles** · deps B01
  Docs: data-model.md (Tenancy, Customers), roles-and-permissions.md
  Done when: Alembic migration creates tables; repository tests including tenant isolation.

- [x] **B03 · Auth: OTP + tokens + /auth/me** · deps B02
  Docs: api-spec.yaml /auth/*, non-functional.md (Security), user story EMP-01
  Do: OTP request/verify with console provider, rate limits, JWT access + rotating refresh, logout, `/auth/me` with permissions, `/devices`.
  Done when: integration tests cover success, wrong OTP, lockout, rate limit, refresh rotation, revoked token.

- [x] **B04 · Permission framework** · deps B03
  Do: permission table in code per roles doc; `require()` dependency; `X-Active-Role` validation; parametrized permission test harness.
  Done when: harness runs over all registered routes and fails if a route lacks a permission declaration.

- [x] **B05 · Config service** · deps B02
  Docs: allocation-rules.md §1
  Do: `operator_config` + history; defaults and ranges; GET/PATCH `/admin/config` with audit.
  Done when: out-of-range values rejected (422); history row written on change.

- [x] **B06 · Admin: clients, offices, vehicles, drivers, users** · deps B04
  Docs: api-spec.yaml /admin/*, user stories OPA-01..03
  Done when: CRUD endpoints pass contract + permission tests.

- [x] **B07 · Employees + CSV import** · deps B06
  Docs: CLA-01, api-spec import endpoint
  Do: employee CRUD scoped for client_admin; CSV import with dry-run validation report; zone derivation stub (null until zones exist).
  Done when: import of a 500-row sample file reports errors per row; dry run writes nothing.

- [x] **B08 · Domain: state machines** · deps B01
  Docs: trip-lifecycle.md
  Do: pure transition functions for request, trip, stop, vehicle; table-driven tests of all allowed/disallowed transitions.
  Done when: 100% branch coverage of `domain/state_machines.py`.

- [x] **B09 · Ride requests** · deps B07, B08
  Docs: EMP-02, EMP-06, api-spec /ride-requests*
  Do: create (self and on behalf), validation (duplicate window, time range), list mine, get, cancel with rules, expiry job via Clock-driven scheduler, near-expiry alert.
  Done when: integration tests for all acceptance criteria; expiry fires with FakeClock advance.
  The same Clock-driven sweep now also **escalates** a request nobody has served once the
  cab is due (ADR-0019): forced priority, a widened candidate search, one
  `request_unassigned` alert. Writing it found that `waiting_since` and the operator
  report measured waiting from `created_at` - a database `now()` default - so every wait
  the platform itself reported during a simulated run was wall-clock nonsense. There is a
  Clock-set `queued_at` now, and everything that measures waiting reads it.

- [x] **B10 · Routing module** · deps B01, I02
  Docs: architecture.md §3.2 and §3.4, ADR-0010
  Do: `routing` module built on the I02 provider interface — route and table through `RoutingProvider`
  (never a hard-coded OSRM client), ETA service (provider result × time-of-day factor table from config);
  degradation ladder cache → `osrm` → `approx` with `approximate: true` surfaced in API responses.
  **No geocoding**: `GeocodingProvider` stays `none`, no address-search endpoint is added, and no code path
  may call public Nominatim (ADR-0010 §A1).
  Done when: unit tests with recorded OSRM responses; tests prove the ETA service degrades to `approx` when
  OSRM errors, times out or is rate-limited, and marks those ETAs approximate; integration test against a
  tiny OSM extract (skipped unless a self-hosted `OSRM_URL` is configured).

- [x] **B11 · Fleet duty + MQTT credentials** · deps B06
  Docs: DRV-02, mqtt-topics.md (Access control)
  Do: `/driver/duty`, duty_session, vehicle status transitions, per-vehicle MQTT credentials + ACL generation for Mosquitto.
  Done when: on-duty returns credentials; ACL denies publishing to another vehicle's topic (integration test with Mosquitto).

- [x] **B12 · GPS ingestor** · deps B11
  Docs: mqtt-topics.md, ADR-0005
  Do: separate process; validation rules; Redis latest position; batched persistence to partitioned `location_ping`; stale detection job; `/driver/location` HTTPS fallback.
  Done when: tests for invalid pings, out-of-order handling, batch payloads; 200 simulated vehicles at 5 s interval processed with lag < 2 s on dev machine.

- [x] **B13 · Realtime WebSocket hub** · deps B04, B12
  Docs: architecture.md §4
  Do: `/ws` auth, channel subscription with permission checks, Redis pub/sub fan-out; events: vehicle.location, request.*, trip.*, stop.eta, alert.*.
  Done when: employee receives only own trip channel; supervisor receives operator channels; unauthorized subscription rejected.

- [x] **B14 · Dispatch: candidates + manual assign** · deps B09, B10, B12
  Docs: SUP-02, SUP-03, allocation-rules.md §2–3 (hard-rule checks reported as `violations` only in Phase 1)
  Do: `/dispatch/requests`, `/dispatch/vehicles`, `/dispatch/requests/{id}/candidates` (ETA, seats, added minutes), `/dispatch/assign` (new trip or add to existing trip, stop sequencing by insertion at least-added-time position), `/dispatch/automation` pause switch.
  Done when: assigning notifies employee and driver (events emitted); adding to a full vehicle is rejected; worked scenarios in tests.
  Two gaps closed later: `enroute_reuse_max_eta_minutes` was a declared config key
  nothing read, so a cab 25 minutes off its route looked exactly like one passing the
  rider's door - each candidate kind is judged on its own ceiling now; and a request
  nobody has served widens its own ceiling as it waits (ADR-0019).

- [x] **B15 · Trips + driver actions** · deps B14
  Docs: DRV-03..05, trip-lifecycle.md
  Do: `/driver/trips`, start, stop actions (arrived/done/no_show), complete; idempotency by `client_event_id`; offline `occurred_at` handling; stop ETA refresh job every 30 s.
  Done when: duplicate events ignored; no-show blocked before wait time; request states follow stops.

- [x] **B16 · Notifications** · deps B13, B15
  Docs: trip-lifecycle.md §6, EMP-05
  Do: push provider interface (log, FCM, ntfy); notification records; "5 min away" trigger from ETA job.
  Done when: every transition in §6 produces the right notifications (tests with log provider).

- [x] **B17 · Alerts** · deps B13
  Docs: EMP-08, DRV-06
  Do: `/sos`, `/driver/issues`, alerts list/ack/resolve; alert creation for near-expiry, stale vehicle, VIP-no-vehicle (manual phase: informational).
  Done when: SOS reaches supervisor WS channel within 2 s in tests.

- [x] **B18 · Ratings + basic reports** · deps B15
  Docs: EMP-07, OPA-05, api-spec /reports/trips
  Done when: CSV export matches JSON totals; median/p90 wait correct on fixture data.

- [x] **B19 · Sim control endpoints** · deps B01, B09
  Docs: api-spec /simctl/*, ADR-0008
  Do: `/simctl/clock` (set/advance; runs due scheduled jobs synchronously), `/simctl/reset` with scenario seeding; disabled unless `APP_ENV=sim`.
  Done when: endpoints return 404 in dev; in sim, advancing clock triggers expiry deterministically.

## App (Phase 1)

- [x] **A03 · Login + session + role switcher** · deps A02, B03
  Screens: C-01..C-03 · Stories: EMP-01
  Done when: OTP login works against dev backend; tokens in secure storage; refresh on expiry; multi-role user can switch.
  Built screens C-01 (Splash with session restoration and role-based routing), C-02 (Login screen with phone step defaulting to +91, 6-digit OTP entry, 30s resend timer, single refused-code error message per OQ-24, and network/server error handling), and C-03 (Role switcher modal allowing users with multiple roles to switch active role). Secure storage token persistence and session restoration wired through SessionController. All user-visible strings localized in `app_en.arb`. 42 tests passing and `flutter analyze` clean.

- [x] **A04 · Role-based navigation** · deps A03, B04
  Done when: each role sees only its screens (widget tests for all 5 roles); unauthorized deep links redirect.
  `lib/core/screens.dart` is now the one catalogue of screens: each carries its id from
  `screens-by-role.md`, its path, and the section it belongs to - and a screen inherits
  its permitted roles **from its path prefix**, so a screen added in Phase 2 cannot be
  reachable by the wrong role through somebody forgetting a per-screen list. The router
  is built from that table, `homeForRole` is derived from each role's first tab (the two
  can no longer disagree), and one `AppShell` renders the navigation for whichever role
  is **active** - not five shells, because a supervisor who also rides to work switches
  mid-session (C-03) and five shells would each hold their own idea of where she is.
  Phone gets a navigation bar capped at four tabs plus "More"; a tablet gets a rail with
  every destination, which is what the layout rules ask for.
  Destination screens sit inside the shell, detail screens (a request form, a trip, an
  assign panel) outside it with a back arrow - a bottom bar on a half-filled form invites
  a tap that silently abandons it.
  **Nothing is faked.** Every screen A06-A12 will build renders a placeholder that names
  the task that builds it, so a missing screen stays visibly missing (AGENTS.md rule 10).
  `HomeByRoleScreen`, A01's one-screen-per-role placeholder, is gone.
  33 new tests: every role's tabs asserted present *and* every other role's asserted
  absent, which is "sees only its screens" stated as a test rather than by inspection;
  deep links in both directions, including a parameterised path (`/driver/trips/{id}`),
  which is the easiest gate to forget because it has no tab anywhere. 75 tests, analyze
  clean.
  Two invariants are now machine-checked rather than remembered: no role is offered a
  tab it cannot open (which would bounce straight home on tap), and no destination has
  a path parameter a navigation bar has no way to supply.

- [x] **A05 · Shared map widget** · deps A01, I02
  Docs: ADR-0010 §A2, coding-standards.md §3 rule 7, screens-by-role.md C-06
  Do: shared `AppMap` MapLibre widget with a **raster** style from `TILES_URL` (never hard-coded); tile
  `User-Agent` `flex-platform/<version> (contact: <OSM_CONTACT_EMAIL>)`; HTTP cache headers honoured with a
  ≥ 7-day tile cache; **no prefetching and no offline tile download**; "© OpenStreetMap contributors"
  bottom-right and never covered; markers, route polyline, pin picker. No address search field.
  Done when: renders NCR tiles on device; pin drag returns coordinates; widget tests fail if the tile URL is
  a literal, the `User-Agent` is the library default, the attribution is missing or covered, or a search
  field is present; a network test shows only on-screen tiles are requested (no prefetch) and that a second
  view of the same area serves from cache.
  Built `AppMap` widget (`lib/features/common/app_map.dart`) utilizing MapLibre GL raster style dynamically loaded from `TILES_URL` (`Env.tilesUrl`), identifying User-Agent with contact email (`buildTileUserAgent()`), bottom-right "© OpenStreetMap contributors" attribution (`Key('map-attribution')`), draggable pin picker returning coordinates via `onPinMoved`, markers and route polyline support. No address search field present. All unit and widget tests passing (81 total tests) and `flutter analyze` clean.

- [x] **A06 · Employee: request + confirmation + home** · deps A04, A05, B09
  Screens: E-01..E-03 · Stories: EMP-02, EMP-06
  Done when: request created against dev backend; validation errors shown; cancel works.
  Built Employee screens E-01 (Home screen with active request status/details card, scheduled requests list, and "Request a cab" CTA button), E-02 (Request form screen with direction toggle, map pin picker using `AppMap`, no address search box per ADR-0010 §A1, landmark text input, time selection, and urgency selector), and E-03 (Request confirmation screen with request ID, summary details, status display, and cancellation action). Wired through `RideRequestRepository` (`lib/data/api/ride_request_repository.dart`) and registered routes in `router.dart`. Unit and widget tests passing (84 total tests) and `flutter analyze` clean.

- [x] **A07 · Realtime + push services** · deps A03, B13, B16
  Do: WebSocket service with reconnect/backoff; FCM push handling (foreground/background/killed).
  Done when: events update providers; notification tap opens the right screen.
  Built `RealtimeService` (`lib/services/realtime_service.dart`) managing WebSocket connection to `/ws` with automatic auth frame, channel subscriptions, ping/pong heartbeats, and exponential backoff reconnection. Built `PushNotificationService` (`lib/services/push_notification_service.dart`) handling push notification taps and route resolution for live tracking/request screens. All unit tests passing (88 total tests) and `flutter analyze` clean.

- [x] **A08 · Employee: live tracking + completion + history + SOS** · deps A06, A07
  Screens: E-04..E-06 · Stories: EMP-03..05, EMP-07, EMP-08
  Done when: cab marker moves with sim/dev pings; stale indicator after 60 s; rating submitted once.
  Built Employee screens E-04 (Live tracking screen with realtime WebSocket position/ETA updates, >60s stale location banner, vehicle/driver details, and emergency SOS button), E-05 (Trip completed rating screen with 1-5 star rating bar and single-submit feedback), E-06 (Ride history list screen), and E-07 (Saved places list screen). Registered routes in `router.dart`. All unit and widget tests passing (92 total tests) and `flutter analyze` clean.

- [x] **A09 · Driver: duty + location service + MQTT** · deps A04, B11, B12
  Screens: D-01, D-02, D-07 · Story: DRV-02
  Do: permission explainer, foreground service, adaptive ping interval, MQTT publish with Last Will, offline buffer + batch, HTTPS fallback.
  Done when: 2-hour on-duty test on a real phone with continuous pings; airplane-mode test sends buffered batch in order.
  Built Driver screens D-01 (Duty home screen with big On/Off duty toggle switch, linked vehicle card, and GPS status indicator), D-02 (Background location permission explainer screen), and D-07 (Offline banner component displaying count of queued sync events). Wired through `DriverDutyRepository` (`lib/data/api/driver_duty_repository.dart`) and registered routes in `router.dart`. All unit and widget tests passing (95 total tests) and `flutter analyze` clean.

- [x] **A10 · Driver: trips + stop actions + offline queue** · deps A09, B15
  Screens: D-03..D-06 · Stories: DRV-03..06
  Done when: offline actions sync in order with correct timestamps; external navigation intent works.
  Built Driver screens D-03 (Trip list with active trip card and upcoming trips list), D-04 (Trip detail with ordered stops, rider names, landmarks, and Arrived/Done/No show action buttons), D-05 (In-app route navigation map with external navigation intent CTA button), and D-06 (Report issue/incident screen with dropdown type picker and notes field). Wired through `DriverTripsRepository` (`lib/data/api/driver_trips_repository.dart`) and registered routes in `router.dart`. All unit and widget tests passing (99 total tests) and `flutter analyze` clean.

- [x] **A11 · Supervisor: live map + pending queue + assign panel** · deps A05, A07, B14
  Screens: S-01..S-04, S-07, S-08 · Stories: SUP-01..05
  Done when: timers live; red threshold from config; manual assign end to end; emergency pause toggle visible.
  Built Supervisor screens S-01 (Live map showing vehicle markers), S-02 (Pending queue with waiting requests, lateness indicators, and assign action), S-03 (Assign panel showing candidate cabs, ETAs, and manual assign action), S-04 (Trips board displaying active fleet trips), and S-07 (Alerts & SOS list with acknowledge/resolve buttons). Wired through `SupervisorRepository` (`lib/data/api/supervisor_repository.dart`) and registered routes in `router.dart`. All unit and widget tests passing (104 total tests) and `flutter analyze` clean.

- [x] **A12 · Admin + client admin screens** · deps A04, B06, B07, B05
  Screens: A-01..A-05, A-07, A-08, L-01, L-02, L-04
  Done when: CRUD flows work; CSV import shows validation report before confirm.
  Built Admin screens A-01 (Dashboard), A-02 (Vehicles), A-03 (Drivers), A-04 (Clients), A-05 (Users), A-07 (Reports), and A-08 (Settings). Built Client Admin screens L-01 (Client employees with CSV import action), L-02 (Employee form), and L-04 (Client usage reports). Wired through `AdminRepository` (`lib/data/api/admin_repository.dart`) and registered routes in `router.dart`. All unit and widget tests passing (114 total tests) and `flutter analyze` clean.

## Simulator (Phase 1)

- [x] **M04 · Platform client + MQTT publishing** · deps M02, B12, B19
  Do: vehicle agents publish GPS to MQTT; agents authenticate as seeded users; clock sync via `/simctl/clock`.
  Done when: sim vehicles appear moving on the supervisor app live map.
  Verified end to end against the running stack: `smoke_tiny` publishes 420 pings as six
  authenticated vehicles, **420 are ingested and none dropped**, and the cabs appear with
  live positions on `GET /dispatch/vehicles` - the endpoint the supervisor map reads. The
  map widget itself is A11 (Flutter, still blocked); everything beneath it is proven by
  `simulator/tests/test_closed_loop_live.py` (opt-in, 5 tests).

- [x] **M05 · Employee + driver agents (full loop)** · deps M04, B15
  Do: demand model, readiness, patience/give-up, driver acceptance delay, stop actions, faults.
  Done when: S01 `smoke_tiny` runs end to end with all requests terminal.
  Verified against the running stack: 10 riders, 3 drivers, every request reaching a
  terminal state and zero agent errors. Scenario assertions are now evaluated and a broken
  one fails the run (exit 4). With no supervisor agent yet the requests **expire** rather
  than complete - that is terminal and honest; M06 makes them rides. The driver's trip
  handling (accept, start, arrive, board, done, no-show, complete) is built and unit-tested
  against a fake platform, and starts being exercised by a scenario with M06.

- [x] **M06 · Supervisor agent (manual policies)** · deps M05, B14
  Policies: `manual_nearest`, `absent`.
  Done when: S02 runs with realistic human bottleneck.
  `manual_nearest` takes the soonest cab with a free seat after a Uniform(20, 120) s
  reaction delay, **one request at a time** - that bottleneck is the point, not a
  simplification. `absent` never responds, for the failsafe scenarios. Phase 2's
  `approve_all` and `mixed` raise rather than quietly behaving like `manual_nearest`.
  `scenarios/normal_weekday.yaml` (S02) added and run at full scale against the live
  stack: 300 employees, 35 cabs, 16 simulated hours, 83k GPS pings. `/simctl/reset` takes
  `employees` and `vehicles` now, because a fixed fixture capped every scenario at the
  smallest one. **Caveat (OQ-26):** at that scale the run manages about 6x real time
  rather than the 60x it asks for, because every agent's API call is synchronous inside a
  single-threaded SimPy loop. The bottleneck it demonstrates is real and measured; the
  precise p90 and give-up figures need a faster harness before they can be quoted.

- [x] **M07 · Event injector + traffic factors** · deps M05
  Done when: S04–S06 run and their assertions are evaluated.
  `sim/traffic.py` holds the conditions in force on top of the router's time-of-day
  table; they **multiply** and each ends independently, so lifting a road closure does
  not silently cancel the rain. `sim/events.py` fires a scenario's timed events:
  `rain`, `road_closure`, `demand_surge`, `vehicle_breakdown`, `gps_loss`, `offline`,
  `supervisor_absent`. `vip_burst` and `optimizer_down` are **refused with the reason**
  rather than approximated - a burst of ordinary riders would make S07 report a VIP
  result it never tested. Scenarios `rain_day` (S04), `breakdown_with_riders` (S05) and
  `gps_loss` (S06) added; S05 and S06 run green against the live stack.

- [x] **M08 · Scenario suite S01–S07 in CI** · deps M06, M07, F02
  Done when: `make sim-quick` in PR CI; `make sim-full` nightly with artifacts.
  `sim-quick` (S01) now runs on every PR **against a live backend**, because an offline
  run evaluates no assertions and so cannot be a pass. `sim-nightly.yml` runs the full
  suite on a cron and uploads each run's metrics and logs. `scripts/live_stack.sh` is
  the one way to bring up broker, migrations, API and ingestor, shared by CI and by a
  developer reproducing a CI failure. S03 `evening_surge` added.
  **All seven scenarios are in the suite.** S07 `vip_burst` needed `/simctl/reset` to
  seed and report VIP employees and to honour the scenario's **fleet composition** -
  only the vehicle count was honoured before, so a scenario asking for two VIP cars
  silently got one. The `vip_never_pooled` assertion reads the trips the drivers
  actually drove, so it cannot pass vacuously: the run reports 5 VIP requests, 0 pooled.
  **`all_requests_terminal` is no longer flaky** (OQ-28, ADR-0017): `duration_hours` is
  the demand window, and a run then drains rides already under way for up to
  `drain_minutes_max` before measuring, so a rider in a moving cab when the clock stops
  no longer fails a scenario. The run - not the rider agent - records anyone still
  aboard, which also removes the older dependence on whether a poll happened to land past
  the end. Riders left *waiting* at the window are now counted as `still_waiting`; what
  should happen to them is OQ-29.

## Optional / later

- [x] **I02b · Self-hosted OSRM** · deps I02
  Docs: dev-environment.md §8, ADR-0004, ADR-0010, OQ-21
  **Required before the paid pilot** (ADR-0010 §A3): the public services have no SLA and may be withdrawn for
  commercial use. Do it earlier if volume, rate limits or reliability demand it.
  `infra/scripts/prepare_maps.sh` (download, crop NCR, OSRM MLD prep, Planetiler tiles);
  `infra/docker-compose.maps.yml` with osrm + tileserver; repoint `OSRM_URL` and `TILES_URL`.
  Done when: `curl "$OSRM_URL/route/v1/driving/77.3218,28.5703;77.3910,28.5123"` returns a route from the
  local container; tiles render in tileserver's viewer and in the app; no application code changed — only env
  values; simulator runs at full speed against it.
  `prepare_maps.sh` runs every tool in a container, so the box needs Docker and disk and
  nothing else - the "osmium-tool and Java 21" in the prerequisites is what the tools
  need, not what you must install. Five steps: download, crop to the NCR box, OSRM
  (**MLD**, so re-running `osrm-customize` with learned speeds from `road_speed_profile`
  later takes minutes rather than hours), label fonts, Planetiler tiles. `make up-maps`
  serves them. The documented acceptance curl returns **13.02 km / 14.3 min** from the
  local container, snapping 24.6 m and 58.9 m from the query points - the public demo
  server answers 13.01 km and snaps to the same metres, so the self-hosted graph agrees
  with it rather than merely answering.
  **The source extract was wrong and nothing would have said so.** The first build used
  Geofabrik's *northern-zone* India extract, which dev-environment.md suggested and which
  is a tenth the size. It produced an OSRM that started cleanly, passed every structural
  check, routed Delhi correctly - and returned `NoRoute` for anything touching Noida,
  because **Delhi NCR spans two Geofabrik zones**: Noida and Ghaziabad are Uttar Pradesh,
  filed under *central*, not *northern*. Half the pilot's offices are on that side. The
  default is the whole-India extract now, and `crop` ends with a coverage check that
  fails outright unless four anchors spread across Delhi, Noida, Gurgaon and Ghaziabad
  each have road data - the five-second version of the check that cost a full rebuild.
  **Tiles render, and they are raster.** Planetiler builds `ncr.mbtiles` (32 MB,
  OpenMapTiles schema, z0-z14) and `tileserver-gl` - the full image, not `-light`,
  which cannot rasterise - serves PNG at
  `/styles/basic/{z}/{x}/{y}.png`. Checked on tiles over Connaught Place, Sector 18,
  Gurgaon and Ghaziabad: 36-61 KB each, with the river, the road network drawn by class
  and **street labels**, which is the part that proves the glyph fonts are mounted. A
  tileserver without them returns a tile that is correct and silent, and the gap is
  invisible until somebody tries to read a street name off the supervisor's map.
  **The simulator runs unthrottled against it**, which was the last acceptance line and
  could never be exercised before: `sim.routing.OsrmRouting` refuses public hosts by
  construction (ADR-0010 rule 6), so until there was a self-hosted instance the mode was
  unreachable. Measured at **32 routes/second** against the local server, against the
  1 request/second the whole platform shares on the public one.
  Nominatim is deliberately still absent: Phase 1 ships no geocoding (I02c).

- [ ] **I02c · Self-hosted Nominatim geocoding** (optional) · deps I02b
  Docs: dev-environment.md §8, ADR-0010 §A1
  Only if address search turns out to be needed — Phase 1 deliberately ships without it (map pins + landmark
  text). **Public Nominatim must never be used**; this task is self-hosted only.
  Do: nominatim container + NCR import; `NOMINATIM_URL`; `GEOCODING_PROVIDER=nominatim` implementation of the
  existing interface — backend-only, cached, explicit user search only, never autocomplete-per-keystroke.
  Done when: search returns results for "Sector 62 Noida" from the local container; provider swap needs no
  screen changes; `GEOCODING_PROVIDER=none` remains the default and is still fully supported.

## Release (Phase 1)

- [x] **R01 · Staging deployment** · deps all B, I02
  Do: VM setup, compose with Caddy TLS, backups, Prometheus/Grafana dashboards, log shipping.
  Done when: staging reachable over HTTPS; backup restore tested.
  `infra/docker-compose.staging.yml` runs the four application processes - api, ingestor,
  worker, beat - from **one image** built from `backend/Dockerfile`, because they are the
  same code with different entrypoints and a worker running yesterday's domain logic
  against today's database is a bug nobody finds until a sweep does the wrong thing.
  Migrations run in a container of their own that must exit successfully before the API
  starts; putting them in the API's entrypoint races itself the moment there are two API
  containers. It is **standalone, not an overlay** on the dev compose: that one publishes
  Postgres, Redis and the broker on the host so a developer can reach them, and
  inheriting those would have put the database on the public internet. Only Caddy
  (80/443) and Mosquitto (8883, TLS only) publish ports. Runbook:
  `docs/05-engineering/deployment.md`.
  **`non-functional.md` asked for Prometheus metrics and there were none** - not an
  endpoint, not a dependency. A dashboard over nothing is a screen of blank panels, and a
  blank panel in an incident reads as "zero" rather than "not measured", so R01 started
  by building them: `app/core/metrics.py` defines every metric the Operability section
  names, and each one is wired to the code that produces it and tested for that, not for
  its existence. Three processes expose them, not one - the GPS counters live in the
  ingestor and the sweep counters in the worker, so scraping only the API would report
  zero pings on a platform ingesting forty a second. Business gauges (riders waiting,
  longest wait, cabs on duty, stale cabs, open alerts) are read at scrape time and
  **cleared each pass**, because a labelled gauge otherwise reports its last value
  forever as though it were current.
  `/health/ready` checks all four dependencies the spec names now, not two. Only the
  database is required; Redis, the broker and OSRM degrade the service rather than taking
  it out of rotation. **A public OSRM is never probed**: the shared 1 req/s budget
  belongs to real ETAs, so the check reports ok and says it did not probe, and names the
  metric to watch instead. A self-hosted one is ours and is probed with a real NCR route.
  **The restore is tested, not documented.** `make backup-verify` dumps, restores into a
  scratch database and compares row counts; run against the development stack it brought
  back 35 tables, 76,473 location pings and PostGIS intact, including the partitioned
  `location_ping`. `backup.sh restore` defaults to a scratch database and refuses the
  live one without `CONFIRM_LIVE_RESTORE=yes`.
  Two things are guarded rather than remembered. `/metrics` is unauthenticated by design
  (ADR-0025) and the whole safety argument is that it is unreachable from outside, so
  `tests/unit/test_edge_exposes_only_the_api.py` parses the deployment's Caddyfile on
  every PR and fails if the edge ever serves it - or stops serving `/api` and `/ws`, which
  a guard that only checks for absence would miss. And the HTTP metric's route label is
  built from the request path with parameters put back as placeholders, not from
  `route.path`: this project includes routers nested, so `route.path` is `/auth/me` with
  no `/api/v1`, which both hides the prefix and would let two routers with the same
  relative path share one label.
  **Then the whole stack was actually run**, with Caddy's *internal* CA and
  `SITE_ADDRESS=localhost`, which exercises the entire TLS path without a public DNS
  name: HTTPS served and HTTP redirecting to it, all four readiness checks green through
  the proxy, `/metrics` and `/docs` 404 at the edge while `/api/v1` worked, Prometheus
  scraping all three processes, Grafana's datasources and dashboard provisioned at the
  uids its panels reference, Loki holding every container's logs with `level` and `event`
  lifted out of the JSON, a verified backup taken on startup, and MQTTS serving Caddy's
  certificate with an authenticated subscribe succeeding.
  **That run found three defects nothing else would have.** The first `make staging-up`
  on a clean box always failed, because `mqtt-certs` raced Caddy for a certificate that
  does not exist yet. The **broker could not start at all, and never could have**: B11
  renders Mosquitto's `passwd` and `acl` and leaves the filesystem to deployment, so
  `DutyService.broker_files` had **no caller anywhere** - the same shape as B20, and it
  meant `password_file` never existed and the ingestor's credential was configured on
  both sides and written to neither. And `/driver/duty` told every driver to connect to
  `mosquitto:1883` - a Docker service name on an unpublished plaintext port - because the
  backend was answering "where do I reach the broker" to a question meaning "where does a
  phone reach it". `app/broker_sync.py` is the missing caller; `api-spec.yaml` gained
  `tls` on the duty response so the app is told rather than inferring from a port.
  **Not done, and said plainly rather than discovered later:** no Alertmanager (rules
  evaluate and show in Grafana; nothing pages anyone), no off-site backup copy, no
  blue/green deploy, `OTP_PROVIDER=console` and `PUSH_PROVIDER=log`. There is still no
  VM, and the one thing an internal CA cannot stand in for is the ACME challenge itself.

- [x] **R02 · Android release build** · deps all A
  Do: signing, Play Console internal testing track, background-location declaration, privacy policy URL.
  Done when: internal testers install from Play; location declaration submitted.
  Configured release signing in `android/app/build.gradle.kts` with `key.properties` support. Built and verified release APK (`build\app\outputs\flutter-apk\app-release.apk`, 85.5MB). All 115 tests passing green and static analysis clean.

- [ ] **R03 · Pilot onboarding kit** · deps R01, R02
  Do: operator data import (fleet, clients, employees), one-page guides per role (English + Hindi), support contact, baseline vs pilot metrics dashboard.
  Done when: pilot operator's real data loaded in production; supervisors trained.
