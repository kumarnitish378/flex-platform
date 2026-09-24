# Overnight run — PROGRESS

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
