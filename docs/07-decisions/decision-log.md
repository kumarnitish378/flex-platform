# Decision log

Newest first. Significant technical decisions also have an ADR.

| Date | Decision | Why | Ref |
|---|---|---|---|
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
