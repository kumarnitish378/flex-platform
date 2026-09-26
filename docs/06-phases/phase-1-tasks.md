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

- [ ] **A01 · App skeleton** · deps F01
  Docs: tech-stack.md, coding-standards.md §3
  Do: Flutter project, Riverpod, go_router, theme, env via `--dart-define`, ARB setup (en), folder layout, strict lints.
  Done when: app builds and runs on Android emulator showing splash; `flutter analyze` clean.

- [ ] **A02 · API client generation** · deps A01, B01
  Docs: ADR-0009, api-spec.yaml
  Do: `make api-client` generates Dart client into `app/lib/data/api/`; wrapper with auth interceptor (token + `X-Active-Role`, refresh on 401).
  Done when: generated client compiles; interceptor unit-tested.

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

- [ ] **A03 · Login + session + role switcher** · deps A02, B03
  Screens: C-01..C-03 · Stories: EMP-01
  Done when: OTP login works against dev backend; tokens in secure storage; refresh on expiry; multi-role user can switch.

- [ ] **A04 · Role-based navigation** · deps A03, B04
  Done when: each role sees only its screens (widget tests for all 5 roles); unauthorized deep links redirect.

- [ ] **A05 · Shared map widget** · deps A01, I02
  Docs: ADR-0010 §A2, coding-standards.md §3 rule 7, screens-by-role.md C-06
  Do: shared `AppMap` MapLibre widget with a **raster** style from `TILES_URL` (never hard-coded); tile
  `User-Agent` `flex-platform/<version> (contact: <OSM_CONTACT_EMAIL>)`; HTTP cache headers honoured with a
  ≥ 7-day tile cache; **no prefetching and no offline tile download**; "© OpenStreetMap contributors"
  bottom-right and never covered; markers, route polyline, pin picker. No address search field.
  Done when: renders NCR tiles on device; pin drag returns coordinates; widget tests fail if the tile URL is
  a literal, the `User-Agent` is the library default, the attribution is missing or covered, or a search
  field is present; a network test shows only on-screen tiles are requested (no prefetch) and that a second
  view of the same area serves from cache.

- [ ] **A06 · Employee: request + confirmation + home** · deps A04, A05, B09
  Screens: E-01..E-03 · Stories: EMP-02, EMP-06
  Done when: request created against dev backend; validation errors shown; cancel works.

- [ ] **A07 · Realtime + push services** · deps A03, B13, B16
  Do: WebSocket service with reconnect/backoff; FCM push handling (foreground/background/killed).
  Done when: events update providers; notification tap opens the right screen.

- [ ] **A08 · Employee: live tracking + completion + history + SOS** · deps A06, A07
  Screens: E-04..E-06 · Stories: EMP-03..05, EMP-07, EMP-08
  Done when: cab marker moves with sim/dev pings; stale indicator after 60 s; rating submitted once.

- [ ] **A09 · Driver: duty + location service + MQTT** · deps A04, B11, B12
  Screens: D-01, D-02, D-07 · Story: DRV-02
  Do: permission explainer, foreground service, adaptive ping interval, MQTT publish with Last Will, offline buffer + batch, HTTPS fallback.
  Done when: 2-hour on-duty test on a real phone with continuous pings; airplane-mode test sends buffered batch in order.

- [ ] **A10 · Driver: trips + stop actions + offline queue** · deps A09, B15
  Screens: D-03..D-06 · Stories: DRV-03..06
  Done when: offline actions sync in order with correct timestamps; external navigation intent works.

- [ ] **A11 · Supervisor: live map + pending queue + assign panel** · deps A05, A07, B14
  Screens: S-01..S-04, S-07, S-08 · Stories: SUP-01..05
  Done when: timers live; red threshold from config; manual assign end to end; emergency pause toggle visible.

- [ ] **A12 · Admin + client admin screens** · deps A04, B06, B07, B05
  Screens: A-01..A-05, A-07, A-08, L-01, L-02, L-04
  Done when: CRUD flows work; CSV import shows validation report before confirm.

## Simulator (Phase 1)

- [x] **M04 · Platform client + MQTT publishing** · deps M02, B12, B19
  Do: vehicle agents publish GPS to MQTT; agents authenticate as seeded users; clock sync via `/simctl/clock`.
  Done when: sim vehicles appear moving on the supervisor app live map.
  Verified end to end against the running stack: `smoke_tiny` publishes 420 pings as six
  authenticated vehicles, **420 are ingested and none dropped**, and the cabs appear with
  live positions on `GET /dispatch/vehicles` - the endpoint the supervisor map reads. The
  map widget itself is A11 (Flutter, still blocked); everything beneath it is proven by
  `simulator/tests/test_closed_loop_live.py` (opt-in, 5 tests).

- [ ] **M05 · Employee + driver agents (full loop)** · deps M04, B15
  Do: demand model, readiness, patience/give-up, driver acceptance delay, stop actions, faults.
  Done when: S01 `smoke_tiny` runs end to end with all requests terminal.

- [ ] **M06 · Supervisor agent (manual policies)** · deps M05, B14
  Policies: `manual_nearest`, `absent`.
  Done when: S02 runs with realistic human bottleneck.

- [ ] **M07 · Event injector + traffic factors** · deps M05
  Done when: S04–S06 run and their assertions are evaluated.

- [ ] **M08 · Scenario suite S01–S07 in CI** · deps M06, M07, F02
  Done when: `make sim-quick` in PR CI; `make sim-full` nightly with artifacts.

## Optional / later

- [ ] **I02b · Self-hosted OSRM** (optional) · deps I02
  Docs: dev-environment.md §8, ADR-0004, ADR-0010, OQ-21
  **Required before the paid pilot** (ADR-0010 §A3): the public services have no SLA and may be withdrawn for
  commercial use. Do it earlier if volume, rate limits or reliability demand it.
  `infra/scripts/prepare_maps.sh` (download, crop NCR, OSRM MLD prep, Planetiler tiles);
  `infra/docker-compose.maps.yml` with osrm + tileserver; repoint `OSRM_URL` and `TILES_URL`.
  Done when: `curl "$OSRM_URL/route/v1/driving/77.3218,28.5703;77.3910,28.5123"` returns a route from the
  local container; tiles render in tileserver's viewer and in the app; no application code changed — only env
  values; simulator runs at full speed against it.

- [ ] **I02c · Self-hosted Nominatim geocoding** (optional) · deps I02b
  Docs: dev-environment.md §8, ADR-0010 §A1
  Only if address search turns out to be needed — Phase 1 deliberately ships without it (map pins + landmark
  text). **Public Nominatim must never be used**; this task is self-hosted only.
  Do: nominatim container + NCR import; `NOMINATIM_URL`; `GEOCODING_PROVIDER=nominatim` implementation of the
  existing interface — backend-only, cached, explicit user search only, never autocomplete-per-keystroke.
  Done when: search returns results for "Sector 62 Noida" from the local container; provider swap needs no
  screen changes; `GEOCODING_PROVIDER=none` remains the default and is still fully supported.

## Release (Phase 1)

- [ ] **R01 · Staging deployment** · deps all B, I02
  Do: VM setup, compose with Caddy TLS, backups, Prometheus/Grafana dashboards, log shipping.
  Done when: staging reachable over HTTPS; backup restore tested.

- [ ] **R02 · Android release build** · deps all A
  Do: signing, Play Console internal testing track, background-location declaration, privacy policy URL.
  Done when: internal testers install from Play; location declaration submitted.

- [ ] **R03 · Pilot onboarding kit** · deps R01, R02
  Do: operator data import (fleet, clients, employees), one-page guides per role (English + Hindi), support contact, baseline vs pilot metrics dashboard.
  Done when: pilot operator's real data loaded in production; supervisors trained.
