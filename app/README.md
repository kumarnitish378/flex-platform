# app

Flutter universal app. One codebase, screens rendered by role (employee, driver,
supervisor, operator admin, client admin). Android first.

Screens: `docs/01-requirements/screens-by-role.md`. Layout and rules:
`docs/05-engineering/coding-standards.md` §3.

Maps use a MapLibre **raster** style with the tile URL from `TILES_URL`; attribution is
always visible bottom-right; no tile prefetching or offline download; no address search in
Phase 1 (ADR-0010).

Requires the Flutter SDK (`flutter analyze`, `flutter test`).
