<!-- Title format: "<type>(<scope>): <TASK-ID> short description", e.g. "feat(dispatch): B14 manual assign" -->

## Task
Task ID from `docs/06-phases/phase-1-tasks.md`:

## What changed

## How it was verified

## Checklist (docs/05-engineering/coding-standards.md §6)
- [ ] Task ID in title; acceptance criteria met
- [ ] Tests added/updated; all checks green (`make lint`, `make test`)
- [ ] `api-spec.yaml` updated **first** if the API changed; Dart client regenerated
- [ ] Migration added if the schema changed
- [ ] Docs updated (behaviour change → doc change in this PR)
- [ ] New significant decision → ADR + `decision-log.md` line
- [ ] Unknowns recorded in `open-questions.md`, not guessed
- [ ] No secrets, no hard-coded business numbers, no direct clock calls
- [ ] No hard-coded map service URLs; no calls to public OSM servers in tests or loops (ADR-0010)
