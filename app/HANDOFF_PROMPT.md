# Paste this into the model building the app

Everything below the line is the prompt. It is written to be pasted as-is at the start of
a session with the working directory set to `D:\flex-platform`.

Two notes for you, not for the model:

- Give it **one task at a time**. The prompt tells it to do A03 and stop. When A03 is
  done and you are happy, change the task name in the last section and paste again.
- It will try to tick the task off in `docs/06-phases/phase-1-tasks.md`. Check that the
  claim matches what you can actually see on the emulator before you believe it.

---

You are building the Android app for **Smart Cab**, a cab operations platform for
corporate transport. The working directory is `D:\flex-platform`.

## Read these first, in this order

1. `app/AGENTS.md` — the working agreement for the app. Read it **fully**. It lists ten
   specific traps, each of which has already cost this project real time.
2. `CLAUDE.md` in the repo root — the project's hard rules.
3. `docs/06-phases/phase-1-tasks.md` — find task **A03** and read its acceptance criteria.
4. `docs/01-requirements/screens-by-role.md` — the "Common" section, screens C-01 to C-03.

Do not skim these. The project has strict conventions that are enforced by tests, and
code that ignores them will fail `flutter analyze` or a repo guard.

## What is already built

The backend and the simulator are complete and heavily tested. **Do not change them.**
Your work is confined to `app/`.

Within the app, A01 (skeleton, routing, theme, localisation) and A02 (generated API
client, auth interceptor) are done. A03's *logic* is done too — token storage, the auth
repository and the session controller all exist and compile. What is missing is A03's
**screens**.

`flutter analyze` is currently clean and 26 tests pass. Keep it that way: if your change
makes either fail, fix it before moving on.

## The five things most likely to go wrong

These are from `app/AGENTS.md`, repeated because they matter most:

1. `POST /auth/otp/request` returns **202 for any well-formed phone number**, whether or
   not it belongs to a user. This is deliberate. **Never** display "no such user" or
   "number not registered" — the server will not tell you, by design.
2. `POST /auth/otp/verify` returns **one indistinguishable error** for a wrong code, an
   expired code, an unknown number and a locked-out account. Show **one** message for all
   of them.
3. **Every user-visible string must go in `app/lib/l10n/app_en.arb`.** Not afterwards. A
   literal string in a widget is a defect in this project.
4. **Never edit anything under `app/packages/smart_cab_api/`.** It is generated from
   `docs/03-architecture/api-spec.yaml` and is wiped whenever it is regenerated. If you
   need a field that is not there, the spec is wrong — say so, do not patch the client.
5. **Do not fake anything to make a screen look complete.** No stub login that pretends
   to work, no hardcoded trip, no invented position. If something you need does not
   exist, stop and say so plainly.

## How to work

- Use the existing `sessionControllerProvider` for all sign-in behaviour. It already
  exposes `stage`, `busy`, `rejected` and `unavailable`. Render that state; do not
  re-implement it in the widget.
- Use the shared `dioProvider`, never a bare `Dio()` — the auth interceptor is attached
  to it and adds the two headers every call needs.
- Give each screen a `Key` matching its id from the screens document: `Key('C-02')`.
- Write a widget test per screen. Test the behaviour that would be *wrong* if broken — a
  resend button that is enabled before 30 seconds, a wrong code that shows a specific
  error — not that the widget renders.

Commands (the Flutter SDK is at `C:\Users\nitis\flutter`):

```
cd app
flutter analyze     # must be clean
flutter test        # must be green
flutter run         # with an emulator attached
```

To run against a real backend, from the repo root: `make up`, then
`bash scripts/live_stack.sh up`, then
`flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1`. Use `10.0.2.2`, not
`localhost` — on an Android emulator `localhost` is the emulator itself.

## Your task

**A03 — Login, session and role switcher.** Build these three screens:

- **C-02 Login.** Phone input defaulting to `+91`, then a 6-digit code field. A resend
  option that becomes available after 30 seconds. One error message for a refused code; a
  different one for "could not reach the server", because telling somebody to re-check a
  code that was correct is maddening.
- **C-01 Splash.** Call `restore()` on the session controller, then route by role. A
  skeleton exists — wire it up.
- **C-03 Role switcher.** Shown only when the person holds more than one role. Calls
  `switchTo(role)`, which also remembers the choice for the next launch.

Done when: OTP login works against the dev backend, tokens are in secure storage, an
expired access token refreshes without the person noticing, and a multi-role user can
switch roles.

When A03 is finished: run `flutter analyze` and `flutter test`, tick A03 in
`docs/06-phases/phase-1-tasks.md` with a one-paragraph note on what you built, and
**stop**. Do not start A04. Report what you did, what you could not do, and anything you
found that looked wrong.
