"""`make create-operator`: the first rows of a real pilot - the operator and its first admin.

Everything else (clients, offices, cabs, drivers, riders, policies) is entered by that admin in the
app or loaded from an onboarding pack, but somebody has to create the tenant and the person who
can log in to do it. There is no API for that on purpose (`create operator` is platform-admin
only, and the platform admin is us), so this is the command a platform admin runs on the server.

Safe to run again with the same arguments: it finds the operator by name and the admin by phone and
changes nothing. It refuses a phone that already belongs to a user of a different operator.

    python -m app.create_operator --name "Sharma Cabs" --admin-name "R. Sharma" \\
        --admin-phone +919812345678 [--timezone Asia/Kolkata] [--rate-per-km 8]
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
import uuid
from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock, SystemClock
from app.core.db import create_engine, create_session_factory
from app.core.settings import Settings
from app.domain.enums import Role
from app.modules.auth.models import AppUser, UserRole
from app.modules.config.service import ConfigService
from app.modules.tenancy.models import Operator

PHONE = re.compile(r"^\+[1-9][0-9]{7,14}$")


class CreateOperatorError(Exception):
    """Bad arguments, or a clash with existing data. The message is for the person typing."""


@dataclass(frozen=True, slots=True)
class Created:
    operator_id: uuid.UUID
    admin_user_id: uuid.UUID
    operator_created: bool
    admin_created: bool


async def create_operator(
    session: AsyncSession,
    clock: Clock,
    *,
    name: str,
    admin_name: str,
    admin_phone: str,
    timezone: str = "Asia/Kolkata",
    rate_per_km: float | None = None,
) -> Created:
    name, admin_name = name.strip(), admin_name.strip()
    if not name or not admin_name:
        raise CreateOperatorError("--name and --admin-name must not be empty")
    if not PHONE.match(admin_phone):
        raise CreateOperatorError("--admin-phone must be international, e.g. +919812345678")
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise CreateOperatorError(f"Unknown timezone {timezone!r}") from exc
    if rate_per_km is not None and rate_per_km < 0:
        raise CreateOperatorError("--rate-per-km cannot be negative")

    operator = await session.scalar(
        select(Operator).where(func.lower(Operator.name) == name.lower())
    )
    operator_created = operator is None
    if operator is None:
        operator = Operator(id=uuid.uuid4(), name=name, timezone=timezone)
        session.add(operator)
        await session.flush()
    elif operator.timezone != timezone:
        raise CreateOperatorError(
            f"Operator {name!r} already exists with timezone {operator.timezone}; "
            "change it deliberately, not by re-running this command"
        )

    user = await session.scalar(select(AppUser).where(AppUser.phone == admin_phone))
    admin_created = user is None
    if user is None:
        user = AppUser(id=uuid.uuid4(), phone=admin_phone, name=admin_name)
        session.add(user)
        await session.flush()

    held = (
        (await session.execute(select(UserRole).where(UserRole.user_id == user.id))).scalars().all()
    )
    elsewhere = [r for r in held if r.operator_id not in (None, operator.id)]
    if elsewhere:
        raise CreateOperatorError(f"{admin_phone} already belongs to a user of another operator")
    if not any(r.role == Role.operator_admin and r.operator_id == operator.id for r in held):
        session.add(
            UserRole(
                id=uuid.uuid4(),
                user_id=user.id,
                role=Role.operator_admin,
                operator_id=operator.id,
            )
        )
        await session.flush()

    if rate_per_km is not None:
        await ConfigService(session, clock).update(
            operator.id, {"billing_rate_per_km": rate_per_km}
        )

    return Created(operator.id, user.id, operator_created, admin_created)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m app.create_operator", description=__doc__)
    parser.add_argument("--name", required=True, help="The cab company's name")
    parser.add_argument("--admin-name", required=True, help="The first operator admin's name")
    parser.add_argument("--admin-phone", required=True, help="Their phone, e.g. +919812345678")
    parser.add_argument("--timezone", default="Asia/Kolkata")
    parser.add_argument("--rate-per-km", type=float, default=None, help="Billing rate, e.g. 8")
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    settings = Settings()
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    try:
        async with factory() as session:
            try:
                result = await create_operator(
                    session,
                    SystemClock(),
                    name=args.name,
                    admin_name=args.admin_name,
                    admin_phone=args.admin_phone,
                    timezone=args.timezone,
                    rate_per_km=args.rate_per_km,
                )
            except CreateOperatorError as exc:
                print(f"Not done: {exc}", file=sys.stderr)
                return 1
            await session.commit()
    finally:
        await engine.dispose()

    print(f"Operator {args.name!r}: {'created' if result.operator_created else 'already existed'}")
    print(f"  id {result.operator_id}")
    print(
        f"Operator admin {args.admin_phone}: "
        f"{'created' if result.admin_created else 'already existed'}"
    )
    print("They can now log in with that phone and set up the rest in the app.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args(sys.argv[1:]))))
