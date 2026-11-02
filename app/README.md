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

## Phone Testing Build (Debug APK with APP_TESTING=true)

To build a debug APK for phone testing with single-step test login (`APP_TESTING=true`) against a laptop on a local Wi-Fi network (replace `192.168.1.34` with your laptop's LAN IP):

```bash
flutter build apk --debug \
  --dart-define=API_BASE_URL=http://192.168.1.34:8000/api/v1 \
  --dart-define=MQTT_HOST=192.168.1.34 \
  --dart-define=MQTT_PORT=1883 \
  --dart-define=TILES_URL=http://192.168.1.34:8081/styles/basic/{z}/{x}/{y}.png \
  --dart-define=OSM_CONTACT_EMAIL=you@example.com \
  --dart-define=APP_TESTING=true
```

### Installing on Device via ADB

```bash
adb install -r build/app/outputs/flutter-apk/app-debug.apk
```
