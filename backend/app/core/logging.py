"""Structured JSON logging with request context.

Every log line carries `request_id`, and `operator_id` / `user_id` once auth is in place
(`coding-standards.md` §2 rule 11). OTPs, tokens and full phone numbers must never be
logged — use `mask_phone` for anything phone-shaped.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

import structlog

# Request-scoped context, set by the middleware and merged into every log line.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
operator_id_var: ContextVar[str | None] = ContextVar("operator_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)

_configured = False


def mask_phone(phone: str) -> str:
    """`+919812345678` -> `+91*****5678`. Never log an unmasked number."""
    if len(phone) <= 4:
        return "*" * len(phone)
    prefix = phone[:3] if phone.startswith("+") else ""
    return f"{prefix}{'*' * (len(phone) - len(prefix) - 4)}{phone[-4:]}"


def _add_request_context(
    _logger: Any, _method: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    for key, var in (
        ("request_id", request_id_var),
        ("operator_id", operator_id_var),
        ("user_id", user_id_var),
    ):
        value = var.get()
        if value is not None:
            event_dict[key] = value
    return event_dict


def configure_logging(
    level: str = "INFO", json_output: bool = True, cache_loggers: bool = True
) -> None:
    """Configure structlog + stdlib logging. Safe to call more than once.

    `cache_loggers=False` makes every call resolve `sys.stdout` afresh. Tests need that:
    a cached logger keeps writing to the stream that was current when it was first used,
    which after a captured test is a closed file.
    """
    global _configured

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if json_output
        else structlog.dev.ConsoleRenderer(colors=False)
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_request_context,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=cache_loggers,
    )

    # Route uvicorn/sqlalchemy stdlib logs through the same stream.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelNamesMapping().get(level.upper(), logging.INFO),
        force=True,
    )
    _configured = True


def get_logger(name: str | None = None) -> Any:
    """Return a bound structlog logger, configuring defaults on first use."""
    if not _configured:
        configure_logging()
    return structlog.get_logger(name)
