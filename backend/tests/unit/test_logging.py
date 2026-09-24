"""Logging must never leak phone numbers, and must carry request context."""

from __future__ import annotations

import json

import pytest

from app.core.logging import (
    configure_logging,
    get_logger,
    mask_phone,
    operator_id_var,
    request_id_var,
)


def test_mask_phone_keeps_only_country_prefix_and_last_four() -> None:
    assert mask_phone("+919812345678") == "+91******5678"
    assert mask_phone("9812345678") == "******5678"


def test_mask_phone_handles_short_input() -> None:
    assert mask_phone("1234") == "****"
    assert mask_phone("") == ""


def test_log_line_is_json_with_request_context(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", json_output=True)
    request_token = request_id_var.set("req-123")
    operator_token = operator_id_var.set("op-456")
    try:
        get_logger("test").info("something_happened", extra_field=7)
    finally:
        request_id_var.reset(request_token)
        operator_id_var.reset(operator_token)

    line = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(line)

    assert payload["event"] == "something_happened"
    assert payload["request_id"] == "req-123"
    assert payload["operator_id"] == "op-456"
    assert payload["extra_field"] == 7
    assert payload["level"] == "info"
    assert payload["timestamp"].endswith("Z")


def test_absent_context_is_simply_omitted(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="INFO", json_output=True)
    get_logger("test").info("no_context")
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert "request_id" not in payload
    assert "user_id" not in payload
