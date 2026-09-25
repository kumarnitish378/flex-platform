# Decision log

Newest first. Significant technical decisions also have an ADR.

| Date | Decision | Why | Ref |
|---|---|---|---|
| 2026-09-25 | `Alert.severity` in api-spec.yaml amended from `critical/high/normal` to `critical/warning/info` | The original ladder has no informational level, and B17 needs one: "VIP-no-vehicle (manual phase: informational)". The backend had already diverged in B09; the spec was changed first and the code left alone rather than the reverse | B17, api-spec.yaml |
| 2026-09-25 | The WebSocket contract lives in `websocket-protocol.md`, referenced from `api-spec.yaml` under `x-websocket`, and the same change-the-contract-first rule applies to it | OpenAPI 3.1 cannot describe a WebSocket, and a fake `GET /ws` path would generate a useless Dart client method. A pointer plus a real document keeps one place to change first without corrupting codegen | B13, CLAUDE.md hard rule 1 |
| 2026-09-25 | `/ws` accepts the access token in the `Authorization` header or in a first `auth` frame - **never** in the query string | A URL ends up in proxy logs, browser history and `Referer` headers; an access token there is an access token leaked. The `auth` frame covers browsers, which cannot set headers on a WebSocket upgrade | B13, websocket-protocol.md section 1 |
| 2026-09-25 | Operator WebSocket channels additionally require the caller **not** to be client-scoped, beyond holding the permission | `client_admin` holds `request_queue_view` for their own client; the permission alone would have handed them every other client's requests on `operator.{id}.requests` | B13, OQ-25 |
| 2026-09-25 | Manual assignment **reports** hard-rule violations instead of refusing them; only seat capacity (plus tenancy and the state machine) blocks | A supervisor overriding the rules is the purpose of manual mode - the rules encode averages, and the supervisor knows the road is flooded. Capacity is different in kind: five people do not fit in a four-seat car. Violations are stored on the trip event so an override stays visible | ADR-0011, B14 |
| 2026-09-24 | `/auth/otp/request` always answers 202, never 404, and OTP verification returns one indistinguishable error for wrong/expired/missing/locked-out | A 404 makes the endpoint a directory of an operator's staff and riders; distinguishable verify errors tell an attacker which half is right. Both conflict with the data-minimisation rules in `non-functional.md` (Privacy). api-spec.yaml amended to match | B03, OQ-24 |
| 2026-09-24 | Aligned with the OSMF usage policies: **no public Nominatim** (forbidden for vehicle-tracking apps) — Phase 1 ships **no geocoding**, map pins + landmark text, `GeocodingProvider=none`, self-hosted Nominatim optional later (I02c); public raster tiles with a distinct User-Agent, ≥ 7-day cache, no prefetch or offline download, attribution bottom-right; public services have no SLA, so self-hosted OSRM + tiles are required before the paid pilot | Comply with `operations.osmfoundation.org/policies/{nominatim,tiles}`; avoid building on infrastructure that can be withdrawn for commercial use | ADR-0010 §A1–A3 |
| 2026-09-24 | Use the **public OSM servers** (OSRM demo, Nominatim, OSM tiles) for development and early phases; self-hosting stays the upgrade path, switchable by config only. Routing provider interface (`osrm` / `approx` / `cached`), shared 1 req/s limiter with `approx` fallback, identifying User-Agent, backend-only cached geocoding, simulator and optimizer on `approx`, attribution on every map | Start building without a 16 GB map-server setup, while staying inside the OSM usage policy | ADR-0010 (amends ADR-0004) |
| 2026-09-24 | Contract-first API; Dart client generated from `api-spec.yaml` | Keep app and backend in sync with AI agents working on both | ADR-0009 |
| 2026-09-24 | Backend: Python + FastAPI modular monolith, PostgreSQL + PostGIS, Redis, Celery, Mosquitto MQTT, Docker Compose, Caddy, Prometheus/Grafana, GitHub Actions | Same language as optimizer/ML/simulator; simple ops for a small team | ADR-0001, 0002, 0005, 0007 |
| 2026-09-24 | Flutter for all clients; web build for supervisor/admin dashboards later | One codebase for Android, iOS, web | ADR-0003 |
| 2026-09-24 | One universal app; screens rendered by role after login | One install, one codebase | ADR-0003 |
| 2026-09-24 | Closed-loop simulator (SITL-style) with simulated cabs, drivers, employees, supervisors; release gate for every phase | Test without live operations | ADR-0008 |
| 2026-09-24 | Free, open-source maps only: OSM, OSRM, Nominatim, MapLibre, self-hosted tiles | Cost and independence | ADR-0004 |
| 2026-09-24 | No WhatsApp API | Avoid cost and dependency | ADR-0006 |
| 2026-09-24 | Full-flex product built in phases (not MVP-only) | Long-term product; each phase usable alone | roadmap.md |
| 2026-09-23 | Supervisor override available in every mode (not a separate mode) | Step in on one trip without changing global mode | control-model.md |
| 2026-09-23 | Three modes: Manual, Semi-auto, Full auto, set per scope | Human-in-the-loop for dynamic situations; trust building | control-model.md |
| 2026-09-23 | Visibility first (tracking, ETA, status) before AI | Main pain is uncertainty and >1 h waits; manual dispatch via WhatsApp | roadmap.md |
| 2026-09-23 | Business model Option B: sell to cab operators | Less competition, faster sales, operators bring clients | vision-and-scope.md |
| 2026-09-23 | Hybrid allocation: rules → ML → optimizer, not a pure neural network | Deterministic business rules must be enforceable | allocation-rules.md |
| 2026-09-23 | Cost function in minutes-equivalent with detour cost; no separate traffic term | Mixed units and double-counted traffic in original idea | allocation-rules.md |
| 2026-09-23 | "Nearby" defined by ETA, not distance | 5 km can mean 8 or 40 min in NCR | allocation-rules.md |
| 2026-09-23 | Use existing solver (OR-Tools) for pooling (DARP) | Solved problem; don't reinvent | allocation-rules.md |
| (from earlier brainstorm) | VIP → VIP car immediately, no waiting, no sharing | User requirement | allocation-rules.md |
| (from earlier brainstorm) | Priority 1 (highest)–10; urgency High/Medium/Low | User requirement | glossary.md |
| (from earlier brainstorm) | Pickup ±10 min; evening hold 10–30 min; high priority no wait; return-trip reuse; zone pooling; history-based prediction | User requirements | allocation-rules.md |
