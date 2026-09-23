# Coding standards

## 1. General
- English identifiers and comments. Terms exactly as in `glossary.md`.
- Small, focused pull requests: one task from `phase-1-tasks.md` per PR.
- Conventional Commits: `feat(dispatch): manual assign endpoint`, `fix(trips): ...`, `docs: ...`, `test: ...`, `chore: ...`.
- Branches: `feat/<task-id>-short-name`, e.g. `feat/B07-ride-request-create`.
- No commented-out code. No secrets. No magic numbers in business logic (use config keys).

## 2. Backend (Python)

### Layout
```
backend/
  pyproject.toml
  alembic/                    # migrations
  app/
    main.py                   # FastAPI app factory
    core/                     # settings, db session, clock, logging, errors, security
    domain/                   # PURE logic: enums, state_machines, rules, cost, geo utils (no I/O)
    modules/<module>/
      router.py               # HTTP only: parse, call service, return schema
      schemas.py              # Pydantic request/response models (match api-spec.yaml)
      service.py              # use-case logic, transactions, calls domain + repositories
      repository.py           # DB access only (SQLAlchemy)
      models.py               # SQLAlchemy models
    workers/                  # Celery tasks (thin; call services)
    ingestor/                 # MQTT consumer process
    realtime/                 # WebSocket hub
  tests/
    unit/                     # domain + services with fakes
    integration/              # API + DB (testcontainers)
    contract/                 # responses vs api-spec.yaml
```

### Rules
1. **Routers contain no business logic.** Services contain use cases. Domain functions are pure.
2. **Clock:** never call `datetime.now()`, `time.time()` or `date.today()` outside `app/core/clock.py`. Inject `Clock` via FastAPI dependency / service constructor.
   ```python
   class Clock(Protocol):
       def now(self) -> datetime: ...   # timezone-aware UTC
   ```
3. **Tenancy:** repository methods take `operator_id` explicitly; a base repository helper adds the filter. Tests check cross-tenant access is impossible.
4. **Permissions:** every route declares `Depends(require(Permission.X))`. No inline role checks.
5. **State changes** only via `domain/state_machines.py` transition functions, which return events; services persist status + event in one transaction.
6. **Config:** read business parameters via `ConfigService.get(operator_id, key)` with defaults from `allocation-rules.md`.
7. **Errors:** raise domain exceptions (`NotFound`, `Forbidden`, `InvalidTransition`, `Conflict`, `ValidationFailed`); a single handler maps them to the `Error` schema and HTTP codes.
8. **Async:** API and repositories are async. CPU-heavy work (OR-Tools) runs in Celery workers, never in the request path.
9. **Typing:** full type hints; `mypy --strict` for `app/domain` and `app/core`; normal mypy elsewhere.
10. **Formatting/lint:** `ruff format` and `ruff check` (rules: E, F, I, B, UP, SIM, ASYNC, N). Line length 100.
11. **Logging:** structured JSON via `structlog` or stdlib JSON formatter; include `request_id`, `operator_id`, `user_id`. Never log OTPs, tokens or full phone numbers (mask to last 4).
12. **Migrations:** one Alembic migration per schema change; never edit applied migrations; migrations must be reversible where possible.
13. **Time zones:** store UTC; convert to IST only at presentation (app) or in reports.
14. **IDs:** UUIDs; never expose sequential integers.

## 3. App (Flutter / Dart)

### Layout (feature-first)
```
app/lib/
  main.dart
  core/            # config, env, theme, router, api client wiring, auth/session, clock, errors
  data/api/        # generated OpenAPI client (do not edit by hand)
  data/local/      # drift DB (offline queue), secure storage
  services/        # location_service, mqtt_service, push_service, ws_service
  features/
    auth/          # login, otp, role switcher
    employee/      # screens E-xx
    driver/        # screens D-xx
    supervisor/    # screens S-xx
    admin/         # screens A-xx, L-xx
    common/        # shared widgets, map widget
  l10n/            # ARB files
```

### Rules
1. **State:** Riverpod providers; no business logic in widgets.
2. **Navigation:** go_router; routes generated from the active role's permissions. Unauthorized routes redirect to home.
3. **API:** only through the generated client, wrapped in repositories per feature. Never hand-write request models.
4. **Strings:** all user-visible text in ARB files from day one.
5. **Offline queue (driver):** every driver action gets a `client_event_id` (UUID) and `occurred_at`; stored in drift; sent in order; idempotent on server.
6. **Location:** foreground service only while on duty; stop it on off-duty and on logout.
7. **Maps:** one shared `AppMap` widget (MapLibre, **raster** style) — every map in the app goes through it.
   Rules (ADR-0010 §A2, enforced by its widget tests):
   - Tile URL from `TILES_URL` (`--dart-define`), never a literal in code.
   - `User-Agent` on tile requests: `flex-platform/<version> (contact: <OSM_CONTACT_EMAIL>)`. Never the
     MapLibre or HTTP client default.
   - Honour HTTP cache headers; tile cache of at least 7 days.
   - **No offline map download, no tile prefetching** — including the driver app. Fetch only what is on screen.
   - "© OpenStreetMap contributors" bottom-right, always visible; no bottom sheet, card or control may cover it.
   - **No geocoding or address autocomplete** in the app (Phase 1 has none at all): locations come from pin
     drag + landmark text or saved places.
8. **Lint:** strict analysis options; `flutter analyze` must be clean.
9. **Screen IDs** from `screens-by-role.md` appear in widget file names or keys (e.g. `Key('E-04')`) for tests.

## 4. Simulator (Python)
Same Python rules. Agents never import backend internals; they use only public API, WebSocket and MQTT (black-box testing).

## 5. Documentation
- Any behaviour change updates the relevant doc in the same PR.
- New significant decision → ADR + decision-log line.
- Unknowns → `open-questions.md`, never silent assumptions.

## 6. Pull request checklist
- [ ] Task ID in title; acceptance criteria met
- [ ] Tests added/updated; all checks green
- [ ] `api-spec.yaml` updated first if API changed; client regenerated
- [ ] Migration added if schema changed
- [ ] Docs updated
- [ ] No secrets, no hard-coded business numbers, no direct clock calls
