# AGENTS.md — building the Smart Cab app

Read this fully before writing any Dart. It is the working agreement for this directory.
The root `CLAUDE.md` applies too; this file is the app-specific part of it.

The backend and simulator are finished and heavily tested (1277 backend tests, 286
simulator tests). **The app is the only unbuilt part of Phase 1.** Everything you need
already exists on the server side — your job is screens and plumbing, not inventing
behaviour.

---

## 1. The ten things that will bite you

Read these even if you read nothing else. Each one has cost real time on this project.

1. **The API contract is `docs/03-architecture/api-spec.yaml`.** Change the spec first,
   run `make api-client`, then write code. Never hand-write a request or response model.
   Never edit `app/packages/smart_cab_api/` — it is generated and wiped on every run.

2. **`POST /auth/otp/request` answers 202 for any well-formed phone number**, registered
   or not. That is deliberate (OQ-24): a 404 would turn the endpoint into a directory of
   an operator's staff. **Never** show "no such user" — you cannot know, and the server
   will not tell you.

3. **`POST /auth/otp/verify` gives one indistinguishable error** for wrong code, expired
   code, unknown number and locked-out account. Show one message. Distinguishing them
   tells an attacker which half of their guess was right.

4. **Every call needs `Authorization` *and* `X-Active-Role`.** A person can hold several
   roles; the server authorises the one they are *using*. `AuthInterceptor` already does
   this — use the shared `dioProvider`, never a bare `Dio()`.

5. **No address search anywhere, in any screen** (ADR-0010 §A1, hard rule 7). Phase 1
   ships no geocoding at all. Locations come from a draggable map pin plus free-text
   landmark, or a saved place. This applies to E-02, S-08, A-04 and L-02.

6. **Map rules are enforced by tests, not taste** (ADR-0010 §A2):
   - Tile URL from `TILES_URL` via `--dart-define`. **A URL literal in source fails a
     repo guard** — including one in a comment. There is a test that greps for it.
   - A distinct `User-Agent` on tile requests, never the MapLibre default.
   - Honour HTTP cache headers, cache ≥ 7 days.
   - **No offline map download and no tile prefetching, anywhere, including the driver
     app.** Fetch only what is on screen.
   - "© OpenStreetMap contributors" visible bottom-right on every map, never covered by
     a sheet, card or control.

7. **All user-visible text goes in `lib/l10n/app_en.arb` from the first line you write.**
   Not "later". A string literal in a widget is a bug.

8. **Driver actions are offline-first.** Every driver action carries a `client_event_id`
   (UUID) and `occurred_at`, is queued in drift, and is sent in order. The server is
   idempotent on `client_event_id` — it already handles replays, so never dedupe by
   guessing.

9. **Hiding a screen is not security.** The server authorises every call. Role-based
   routing exists so a driver is not offered a screen whose every button 403s — not as a
   permission system. Never skip a server check because the UI hides something.

10. **Do not fake a login, a trip, or a position to make a screen look finished.** This
    project's rule is that a missing thing stays visibly missing. If you need something
    that does not exist, add an entry to `docs/07-decisions/open-questions.md` and say so.

---

## 2. What already exists

| Piece | Where | State |
|---|---|---|
| Project, theme, strict lints, ARB | `lib/core/`, `lib/l10n/` | done (A01) |
| Role-based routing | `lib/core/router.dart` | done — `homeForRole`, `roleMayOpen` |
| Session state | `lib/core/session.dart` | done — plain state, no I/O |
| Generated API client | `packages/smart_cab_api/` | done (A02), 137 models |
| Auth interceptor | `lib/data/api/auth_interceptor.dart` | done, 9 tests |
| Token store (secure storage) | `lib/core/token_store.dart` | done |
| Auth repository | `lib/data/api/auth_repository.dart` | done |
| Session controller | `lib/core/session_controller.dart` | done — restore/signIn/refresh/switch/signOut |
| **Login and role switcher UI** | `lib/features/auth/`, `lib/features/common/` | **placeholders — your first task** |

So A03's logic is written and A03's *screens* are not. Start there.

### Layout (feature-first — `coding-standards.md` §3)

```
lib/
  core/        config, theme, router, session, token store
  data/api/    hand-written wrapper over the generated client
  data/local/  drift (offline queue), secure storage
  services/    location, mqtt, push, websocket
  features/
    auth/      C-01..C-03
    employee/  E-xx
    driver/    D-xx
    supervisor/S-xx
    admin/     A-xx, L-xx
    common/    shared widgets, the one AppMap
  l10n/        ARB files
packages/smart_cab_api/   generated — never edit
```

### Conventions

- **State:** Riverpod. No business logic in widgets.
- **Navigation:** go_router. Add routes to `rolesForRoute` so the role check covers them.
- **Screen keys:** the id from `screens-by-role.md` as a widget `Key` — `Key('E-04')`,
  `Key('home-driver')`. Tests find screens by key.
- **Tests:** `flutter_test` + `mocktail`. A widget test per screen; a unit test per piece
  of logic. Test the *behaviour that would be wrong*, not that the widget renders.

---

## 3. Commands

The Flutter SDK is at `C:\Users\nitis\flutter`. Put `C:\Users\nitis\flutter\bin` on PATH.

```
cd app
flutter pub get
flutter analyze          # must be clean - this is part of done
flutter test             # must be green
flutter build apk --debug
flutter run              # with an emulator or device attached
```

Regenerating the client after a spec change, from the repo root:

```
make api-client          # or: python scripts/api_client.py
```

Running against a real backend:

```
make up                                  # postgres, redis
bash scripts/live_stack.sh up            # broker, migrations, API, GPS ingestor
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

`10.0.2.2` is the host machine as seen from the Android emulator. `localhost` is the
emulator itself, which is the single most common waste of an afternoon here.

### Two machine quirks on this PC

- **`build_runner` must run with `--force-jit`.** Windows Application Control blocks
  `gen_snapshot.exe`, so the default AOT path fails. `scripts/api_client.py` already
  passes it.
- The openapi generator needs its `-i` path in POSIX form; a `D:\...` path is rejected as
  an illegal URI. Already handled in the script.

---

## 4. The work, in order

Each task's full acceptance criteria are in `docs/06-phases/phase-1-tasks.md`. Do **one**
task at a time, finish it, run analyze and tests, then move on.

| Task | What | Screens |
|---|---|---|
| **A03** | Login + session + role switcher — *start here* | C-01, C-02, C-03 |
| A04 | Role-based navigation shell | — |
| A05 | Shared `AppMap` widget (MapLibre raster) | C-06 |
| A06 | Employee: request + confirmation + home | E-01..E-03 |
| A07 | Realtime (`/ws`) + push services | — |
| A08 | Employee: live tracking, completion, history, SOS | E-04.. |
| A09 | Driver: duty + location service + MQTT | D-01.. |
| A10 | Driver: trips + stop actions + offline queue | D-02.. |
| A11 | Supervisor: live map, queue, assign panel | S-01.. |
| A12 | Admin + client admin screens | A-xx, L-xx |

### A03 precisely

Logic is done; build the screens on top of `sessionControllerProvider`.

- **C-02 Login.** Phone input defaulting to `+91`, then a 6-digit code field with a
  resend that unlocks after 30 seconds. On a refused code show one message. The
  controller already exposes `stage`, `busy`, `rejected` and `unavailable` — render
  those, do not re-derive them.
- **C-01 Splash.** Call `restore()`, then route by role. It already exists in skeleton
  form; wire it to the controller.
- **C-03 Role switcher.** Only when `session.canSwitchRole`. Calls
  `sessionController.switchTo(role)`, which also remembers the choice for next launch.

Done when: OTP login works against the dev backend, tokens are in secure storage, an
expired access token refreshes transparently, and a multi-role user can switch.

---

## 5. Definition of done (every task)

- The task's own acceptance criteria are met and shown by a test.
- `flutter analyze` clean; `flutter test` green.
- Every user-visible string is in an ARB file.
- `api-spec.yaml` updated **first** if anything about the contract changed, and the
  client regenerated.
- No TODO without a matching entry in `docs/07-decisions/open-questions.md`.
- The task ticked in `docs/06-phases/phase-1-tasks.md` with a short note on what changed.

## 6. Where to look things up

| Question | File |
|---|---|
| What goes on this screen? | `docs/01-requirements/screens-by-role.md` |
| Which role may do this? | `docs/00-product/roles-and-permissions.md` |
| What are the request/trip states? | `docs/02-domain/trip-lifecycle.md` |
| What does this endpoint return? | `docs/03-architecture/api-spec.yaml` |
| Why is it built this way? | `docs/03-architecture/adr/` |
| What is still undecided? | `docs/07-decisions/open-questions.md` |
| Code style and layout | `docs/05-engineering/coding-standards.md` §3 |
