# Testing strategy

## 1. Layers
| Layer | What | Tools | Where |
|---|---|---|---|
| Unit (domain) | State machines, hard rules, cost function, rider weight, detour checks, mode precedence, ETA math | pytest | `backend/tests/unit/` |
| Unit (services) | Use cases with fake repositories and fake clock | pytest, pytest-asyncio | `backend/tests/unit/` |
| Integration | API endpoints with real PostgreSQL/PostGIS, Redis, Mosquitto | pytest + testcontainers (or docker compose test profile) | `backend/tests/integration/` |
| Contract | Responses validate against `api-spec.yaml`; generated FastAPI OpenAPI matches spec | schemathesis or openapi-core | `backend/tests/contract/` |
| Permission | Every endpoint × every role: allowed/denied as per matrix | parametrized pytest | `backend/tests/integration/test_permissions.py` |
| App unit/widget | Providers, repositories (mocked API), screens render per role | flutter_test, mocktail | `app/test/` |
| App integration | Login → request → track flow against sim backend | integration_test | `app/integration_test/` |
| Simulator scenarios | End-to-end system behaviour | `make sim-quick`, `make sim-full` | `simulator/` |
| Load | GPS ingestion and API under load (Phase 3+) | locust or sim S14 | `simulator/` |

## 2. Coverage targets
- `app/domain/`: ≥ 95% line and branch coverage.
- Backend overall: ≥ 80%.
- Flutter: ≥ 60% for features; 100% of role-routing logic.

## 3. Must-have tests
- Every state transition allowed and every disallowed transition rejected (table-driven).
- Every hard rule with a passing and failing case.
- Cost function worked example from `allocation-rules.md` §8 as a test.
- Locked/overridden requests never changed by optimizer or failsafe.
- Tenancy: user of operator A can never read or write operator B data (for every repository).
- Driver offline events: out-of-order arrival handled; duplicate `client_event_id` ignored.
- Clock: failsafe and expiry fire correctly when the fake clock advances.
- GPS ingestor: invalid pings dropped; out-of-order pings don't move latest position back.

## 4. Test data
- Factories (`factory_boy` or plain builders) for all entities.
- A small fixed NCR fixture: 2 offices, 3 zones, 20 employees, 6 vehicles.
- OSRM in integration tests: a tiny OSM extract (a few km² around the fixture) to keep containers light; or a stubbed routing client for unit tests.

## 5. CI pipeline (GitHub Actions)
1. Lint + type check (ruff, mypy; flutter analyze).
2. Backend unit tests.
3. Backend integration + contract + permission tests (services via containers).
4. Flutter tests.
5. `make sim-quick` (on PRs touching backend/simulator).
6. Nightly: `make sim-full`, publish metrics artifact and trend.
A PR merges only if 1–5 pass.

## 6. Manual test checklist per release
- Install on a low-end Android phone (2 GB RAM, Android 8+).
- Driver on duty for 2 hours: battery drain, GPS continuity, app killed by OS recovery.
- Airplane mode during trip: queued events sent in order after reconnect.
- Notifications received with app in background and killed.
