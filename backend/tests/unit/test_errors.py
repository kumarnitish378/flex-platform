"""Every failure must come back in the api-spec `Error` shape: {code, message, details?}."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from app.core.errors import (
    Conflict,
    DomainError,
    Forbidden,
    InvalidTransition,
    NotFound,
    RateLimited,
    ValidationFailed,
    register_error_handlers,
)


class Body(BaseModel):
    count: int
    phone: str


def build_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)
    router = APIRouter()

    @router.get("/raise/{kind}")
    async def raise_error(kind: str) -> dict[str, str]:
        errors: dict[str, DomainError] = {
            "not_found": NotFound("Trip not found", {"trip_id": "abc"}),
            "forbidden": Forbidden("Not your trip"),
            "invalid_transition": InvalidTransition("cannot go completed -> assigned"),
            "conflict": Conflict("Vehicle already full"),
            "validation": ValidationFailed("Pickup time in the past"),
            "rate_limited": RateLimited("Too many OTP requests"),
        }
        raise errors[kind]

    @router.post("/body")
    async def take_body(body: Body) -> dict[str, int]:
        return {"count": body.count}

    @router.get("/boom")
    async def boom() -> dict[str, str]:
        raise RuntimeError("database on fire")

    app.include_router(router)
    return app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=build_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.parametrize(
    ("kind", "status_code", "code"),
    [
        ("not_found", 404, "not_found"),
        ("forbidden", 403, "forbidden"),
        ("invalid_transition", 409, "invalid_transition"),
        ("conflict", 409, "conflict"),
        ("validation", 422, "validation_error"),
        ("rate_limited", 429, "rate_limited"),
    ],
)
async def test_domain_errors_map_to_status_and_code(
    client: AsyncClient, kind: str, status_code: int, code: str
) -> None:
    response = await client.get(f"/raise/{kind}")
    assert response.status_code == status_code
    payload = response.json()
    assert payload["code"] == code
    assert isinstance(payload["message"], str) and payload["message"]
    assert set(payload) <= {"code", "message", "details"}


async def test_details_are_passed_through(client: AsyncClient) -> None:
    payload = (await client.get("/raise/not_found")).json()
    assert payload["details"] == {"trip_id": "abc"}


async def test_request_validation_uses_the_error_schema(client: AsyncClient) -> None:
    response = await client.post("/body", json={"count": "not-a-number", "phone": "+919812345678"})
    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["details"]["errors"][0]["loc"] == ["body", "count"]


async def test_validation_errors_never_echo_submitted_values(client: AsyncClient) -> None:
    """A 422 must not leak the phone number (or an OTP) back into logs and clients."""
    response = await client.post("/body", json={"count": "nope", "phone": "+919812345678"})
    assert "+919812345678" not in response.text
    assert "nope" not in response.text


async def test_unhandled_exception_becomes_a_clean_500(client: AsyncClient) -> None:
    response = await client.get("/boom")
    assert response.status_code == 500
    payload = response.json()
    assert payload == {"code": "internal_error", "message": "Internal server error"}
    assert "database on fire" not in response.text


async def test_unknown_route_uses_the_error_schema(client: AsyncClient) -> None:
    response = await client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
