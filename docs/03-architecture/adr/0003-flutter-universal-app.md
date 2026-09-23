# ADR-0003: One universal Flutter app for all roles

- Status: accepted
- Date: 2026-09-24

## Context
Five roles need mobile access. Maintaining separate apps costs time.

## Decision
A single Flutter app (Android first). After login, the server returns roles and permissions; the app renders screens accordingly. Supervisor/admin screens are responsive and will ship as a Flutter web build later.

## Alternatives considered
- Separate driver/employee/admin apps: more stores listings and code duplication.
- React Native: comparable, but Flutter gives Android, iOS and web from one codebase with consistent rendering.
- Web-only (PWA) for employees: rejected in favour of one installable app with push.

## Consequences
- Server-side authorization on every endpoint is mandatory.
- Background location is requested only for the driver role, when going on duty (Google Play policy).
- iOS (employees with iPhones) is a later build step, not a rewrite.
