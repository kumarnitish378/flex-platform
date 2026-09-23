# Pending workflows — ACTION REQUIRED (one-time, ~30 seconds)

`ci.yml` in this folder is the finished **F02** CI pipeline. It is parked here instead of
`.github/workflows/` for one reason only:

> `! [remote rejected] dev/overnight-1 -> dev/overnight-1 (refusing to allow an OAuth App to
> create or update workflow .github/workflows/ci.yml without `workflow` scope)`

Both credentials on this machine (the git credential helper and `gh`, scopes `gist`, `read:org`,
`repo`) lack the **`workflow`** scope, so *no* push containing a file under `.github/workflows/`
can succeed. Parking it here keeps the rest of the branch pushable.

## To activate it

```powershell
gh auth refresh -s workflow          # interactive: opens a browser, grants the workflow scope
git mv .github/workflows-pending/ci.yml .github/workflows/ci.yml
git rm .github/workflows-pending/README.md
git commit -m "ci: F02 activate CI workflow"
git push
```

Then open a pull request from `dev/overnight-1` to `main` and confirm the run is green — that is
the remaining acceptance criterion for F02, which could not be verified overnight.

## What the workflow does

| Job | Behaviour |
|---|---|
| `detect` | Decides which parts of the monorepo exist yet |
| `backend-lint` | ruff check, ruff format --check, mypy — no-op with a message while `backend/` has no `pyproject.toml` |
| `backend-test` | pytest — same no-op behaviour |
| `app-analyze` / `app-test` | `flutter analyze` / `flutter test` — no-op until `app/pubspec.yaml` exists (task A01) |
| `sim-quick` | simulator tests + `python -m sim suite quick` — no-op until task M01 |
| `policy-guards` | Fails the build on hard-coded public OSM URLs in code, or a committed `.env` |

CI sets `ROUTING_PROVIDER=approx` globally, so no job can call the public OSM servers (ADR-0010).
