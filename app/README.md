# app

Flutter universal app. One codebase, screens rendered by role (employee, driver,
supervisor, operator admin, client admin). Android first.

Screens: `docs/01-requirements/screens-by-role.md`. Layout and rules:
`docs/05-engineering/coding-standards.md` §3.

Maps use a MapLibre **raster** style with the tile URL from `TILES_URL`; attribution is
always visible bottom-right; no tile prefetching or offline download; no address search in
Phase 1 (ADR-0010).

Requires the Flutter SDK (`flutter analyze`, `flutter test`).

## Building this app

- **`AGENTS.md`** - the working agreement: the traps, what exists, the conventions, the
  commands, and the task order. Read it before writing Dart.
- **`HANDOFF_PROMPT.md`** - a prompt to paste into a model that is building a task here.

The Flutter SDK on this machine is at `C:\Users\nitis\flutter`; put its `bin` on PATH.
`flutter analyze` must be clean and `flutter test` green before a task counts as done.

