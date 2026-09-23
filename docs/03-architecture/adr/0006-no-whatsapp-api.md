# ADR-0006: No WhatsApp API; app + push notifications

- Status: accepted
- Date: 2026-09-24

## Context
Current operations use WhatsApp. Using the WhatsApp Business API would keep habits but adds cost, template approval and dependency.

## Decision
Employees, drivers and supervisors use the universal app. Notifications via push (FCM or ntfy). WhatsApp is not integrated.

## Consequences
- Employees must install the app; onboarding support is needed at pilot launch.
- Supervisors can create requests on behalf of employees during transition (SUP-04).
- Optional SMS fallback for critical messages remains an open question.
