"""Domain exceptions and the single handler that turns them into the `Error` schema.

Codes and shape come from `api-spec.yaml` (`components.schemas.Error`):
`{code, message, details?}`. Services raise these; routers never build error responses
by hand (`coding-standards.md` §2 rule 7).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class DomainError(Exception):
    """Base class. `code` matches the Error schema's documented examples."""

    code: str = "internal_error"
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR

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
    http_status = status.HTTP_404_NOT_FOUND


class Forbidden(DomainError):
    code = "forbidden"
    http_status = status.HTTP_403_FORBIDDEN


class InvalidTransition(DomainError):
    """A state change that `trip-lifecycle.md` does not allow."""

    code = "invalid_transition"
    http_status = status.HTTP_409_CONFLICT


class Conflict(DomainError):
    code = "conflict"
    http_status = status.HTTP_409_CONFLICT


class ValidationFailed(DomainError):
    code = "validation_error"
    http_status = status.HTTP_422_UNPROCESSABLE_CONTENT


class RateLimited(DomainError):
    code = "rate_limited"
    http_status = status.HTTP_429_TOO_MANY_REQUESTS


def _error_response(status_code: int, payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=payload)


def register_error_handlers(app: FastAPI) -> None:
    """Install the handlers that map every failure onto the Error schema."""

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        # Expected, business-level outcomes: info, not error.
        logger.info("domain_error", code=exc.code, message=exc.message, details=exc.details)
        return _error_response(exc.http_status, exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def _request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            {
                "code": ValidationFailed.code,
                "message": "Request validation failed",
                "details": {"errors": _safe_validation_details(exc)},
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(
            exc.status_code,
            {"code": _code_for_status(exc.status_code), "message": str(exc.detail)},
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Never leak internals to the client; the log carries the traceback.
        logger.exception("unhandled_error", error=type(exc).__name__)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {"code": "internal_error", "message": "Internal server error"},
        )


def _safe_validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Field locations and messages only — never echo submitted values back.

    Request bodies carry phone numbers and OTPs (`coding-standards.md` §2 rule 11).
    """
    return [
        {"loc": [str(part) for part in error.get("loc", ())], "msg": error.get("msg", "")}
        for error in exc.errors()
    ]


def _code_for_status(status_code: int) -> str:
    return {
        status.HTTP_401_UNAUTHORIZED: "unauthorized",
        status.HTTP_403_FORBIDDEN: Forbidden.code,
        status.HTTP_404_NOT_FOUND: NotFound.code,
        status.HTTP_409_CONFLICT: Conflict.code,
        status.HTTP_422_UNPROCESSABLE_CONTENT: ValidationFailed.code,
        status.HTTP_429_TOO_MANY_REQUESTS: RateLimited.code,
    }.get(status_code, "error")
