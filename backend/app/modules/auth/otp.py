"""OTP delivery providers.

`dev-environment.md`: in dev, `OTP_PROVIDER=console` prints the code to the log. A real
SMS gateway arrives with OQ-16 (provider not chosen yet), so the interface exists and the
adapter does not — rather than a half-written integration with a guessed API.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.core.logging import get_logger, mask_phone
from app.core.settings import OtpProvider, Settings

logger = get_logger(__name__)


@runtime_checkable
class OtpSender(Protocol):
    name: str

    async def send(self, phone: str, code: str) -> None: ...


class ConsoleOtpSender:
    """Prints the code. Development only.

    The code is printed in full because that is the entire point in dev, but the phone
    number is still masked: logs get shared, pasted and shipped to aggregators, and a
    number is personal data under the DPDP rules in `non-functional.md`.
    """

    name = "console"

    async def send(self, phone: str, code: str) -> None:
        logger.info("otp_console_delivery", phone=mask_phone(phone), code=code)


class RecordingOtpSender:
    """Captures codes instead of sending them. Tests only."""

    name = "recording"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send(self, phone: str, code: str) -> None:
        self.sent.append((phone, code))

    def last_code_for(self, phone: str) -> str | None:
        for sent_phone, code in reversed(self.sent):
            if sent_phone == phone:
                return code
        return None


def build_otp_sender(settings: Settings) -> OtpSender:
    if settings.otp_provider is OtpProvider.console:
        return ConsoleOtpSender()
    raise NotImplementedError(
        "No SMS provider is implemented yet - the provider and its DLT registration are "
        "still open (OQ-16). Use OTP_PROVIDER=console until that is decided."
    )
