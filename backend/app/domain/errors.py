"""Domain exceptions.

Pure: no framework imports, so `app/domain` stays importable by the simulator's analysis
tools and by tests with no web stack. `app/core/errors.py` maps these onto HTTP responses.

Codes match `api-spec.yaml` (`components.schemas.Error`).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any


class DomainError(Exception):
    """Base class. `code` is the value that reaches the client."""

    code: str = "internal_error"
    http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return payload


class NotFound(DomainError):
    code = "not_found"
    http_status = HTTPStatus.NOT_FOUND


class Forbidden(DomainError):
    code = "forbidden"
    http_status = HTTPStatus.FORBIDDEN


class InvalidTransition(DomainError):
    """A state change `trip-lifecycle.md` does not allow."""

    code = "invalid_transition"
    http_status = HTTPStatus.CONFLICT


class Conflict(DomainError):
    code = "conflict"
    http_status = HTTPStatus.CONFLICT


class ValidationFailed(DomainError):
    code = "validation_error"
    http_status = HTTPStatus.UNPROCESSABLE_ENTITY


class RateLimited(DomainError):
    code = "rate_limited"
    http_status = HTTPStatus.TOO_MANY_REQUESTS
