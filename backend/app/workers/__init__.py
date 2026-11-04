"""Celery worker and beat schedule: the platform's due work in production (B20).

Three sweeps decide whether the product behaves at all, and until this existed none of
them ran outside the simulator - their only caller was `PUT /simctl/clock`, which is
mounted only when `APP_ENV=sim` (ADR-0008). Deployed, the platform silently did not
expire requests, did not warn anybody about a request about to expire, did not escalate
a request nobody had served, did not alert on a cab that had gone quiet, and did not
refresh a single stop ETA.

Nothing failed, which is why it survived: every one of those is work that is supposed to
happen *on its own*, so its absence looks exactly like a quiet morning.
"""
