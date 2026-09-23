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
