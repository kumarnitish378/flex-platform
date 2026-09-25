"""Notifications reaching real people (B16, `trip-lifecycle.md` section 6).

Acceptance: every transition in section 6 produces the right notifications, tested with
the log (here, recording) provider.

The templates are checked exhaustively in `tests/unit/test_notification_templates.py`;
this is about the half that needs a database - finding who the "supervisor" is, writing
the record, and pushing to that person's devices and nobody else's.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.domain.enums import DevicePlatform, Role, UserStatus
from app.domain.notifications import NotificationType
from app.domain.state_machines import Recipient
from app.modules.auth.models import Device
from app.modules.notifications.models import Notification
from app.modules.notifications.push import STALE_DEVICE_DAYS, RecordingPushSender
from app.modules.notifications.service import Audience, NotificationService
from tests.builders import (
    make_client,
    make_operator,
    make_user,
    make_user_role,
    unique_phone,
)

NOW = datetime(2026, 9, 25, 7, 0, tzinfo=UTC)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def sender() -> RecordingPushSender:
    return RecordingPushSender()


def service(
    session: AsyncSession, clock: FakeClock, sender: RecordingPushSender
) -> NotificationService:
    return NotificationService(session, clock, sender)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
    """One operator with a rider, a driver, two supervisors and an admin."""
    operator = make_operator()
    other = make_operator("Rival Cabs")
    db_session.add_all([operator, other])
    await db_session.flush()

    customer = make_client(operator.id)
    db_session.add(customer)
    await db_session.flush()

    users: dict[str, Any] = {}
    for label, role, owner in (
        ("rider", Role.employee, operator),
        ("driver", Role.driver, operator),
        ("supervisor_a", Role.supervisor, operator),
        ("supervisor_b", Role.supervisor, operator),
        ("admin", Role.operator_admin, operator),
        ("rival_supervisor", Role.supervisor, other),
    ):
        user = make_user(name=label, phone=unique_phone())
        db_session.add(user)
        await db_session.flush()
        # The `employee` role is scoped to a client; a CHECK constraint enforces it.
        db_session.add(
            make_user_role(
                user.id,
                role,
                operator_id=owner.id,
                client_id=customer.id if role is Role.employee else None,
            )
        )
        users[label] = user
    await db_session.flush()

    for label in ("rider", "driver", "supervisor_a"):
        db_session.add(
            Device(
                user_id=users[label].id,
                platform=DevicePlatform.android,
                push_token=f"token-{label}",
                last_seen_at=NOW - timedelta(hours=1),
            )
        )
    await db_session.flush()

    return {"operator_id": operator.id, "other_operator_id": other.id, "users": users}


async def records(session: AsyncSession) -> list[Notification]:
    result = await session.execute(select(Notification).order_by(Notification.type))
    return list(result.scalars().all())


# --- reaching the right people ------------------------------------------------------


async def test_an_assignment_reaches_the_rider_and_the_driver(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    result = await service(db_session, clock, sender).notify(
        NotificationType.request_assigned,
        Audience(
            employee=world["users"]["rider"].id,
            driver=world["users"]["driver"].id,
            operator_id=world["operator_id"],
        ),
        {"registration_no": "UP16AB1234"},
    )

    assert result.recorded == 2
    assert set(sender.tokens()) == {"token-rider", "token-driver"}


async def test_a_supervisor_notification_reaches_every_supervisor(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    """ "Supervisor" is a role, not a person: whoever is on shift must hear it."""
    result = await service(db_session, clock, sender).notify(
        NotificationType.request_near_expiry,
        Audience(operator_id=world["operator_id"]),
        {"request_id": str(uuid.uuid4())},
    )

    assert result.recorded == 2
    written = await records(db_session)
    assert {row.user_id for row in written} == {
        world["users"]["supervisor_a"].id,
        world["users"]["supervisor_b"].id,
    }


async def test_another_operators_supervisor_is_never_paged(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    await service(db_session, clock, sender).notify(
        NotificationType.request_near_expiry, Audience(operator_id=world["operator_id"])
    )

    written = await records(db_session)
    assert world["users"]["rival_supervisor"].id not in {row.user_id for row in written}


async def test_an_emergency_reaches_the_supervisor_and_the_admin(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    result = await service(db_session, clock, sender).notify(
        NotificationType.sos, Audience(operator_id=world["operator_id"])
    )

    # Two supervisors plus one operator admin.
    assert result.recorded == 3
    assert all(message.high_priority for message in sender.messages)


async def test_a_suspended_user_is_not_notified(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    world["users"]["supervisor_b"].status = UserStatus.suspended
    await db_session.flush()

    result = await service(db_session, clock, sender).notify(
        NotificationType.request_near_expiry, Audience(operator_id=world["operator_id"])
    )
    assert result.recorded == 1


async def test_a_recipient_nobody_filled_in_is_skipped(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    """A request with no driver yet must not crash the cancellation notice."""
    result = await service(db_session, clock, sender).notify(
        NotificationType.request_cancelled,
        Audience(operator_id=world["operator_id"], employee=None),
        {"cancelled_by_employee": True},
    )

    # The driver is unknown, so only the supervisors hear.
    assert result.recorded == 2


async def test_an_explicit_recipient_list_wins(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    """A caller that already knows exactly who should hear must not be second-guessed."""
    only = world["users"]["supervisor_a"].id
    result = await service(db_session, clock, sender).notify(
        NotificationType.request_near_expiry,
        Audience(operator_id=world["operator_id"], extra={Recipient.supervisor: [only]}),
    )

    assert result.recorded == 1
    assert (await records(db_session))[0].user_id == only


# --- the record ----------------------------------------------------------------------


async def test_the_notification_is_written_down(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    """ "I was never told my cab changed" needs an answer six months later."""
    await service(db_session, clock, sender).notify(
        NotificationType.cab_arrived,
        Audience(employee=world["users"]["rider"].id, operator_id=world["operator_id"]),
        {"trip_id": "t1"},
    )

    row = (await records(db_session))[0]
    assert row.type == str(NotificationType.cab_arrived)
    assert row.sent_at == NOW
    assert row.read_at is None
    assert row.data == {"trip_id": "t1"}


async def test_a_delivered_notification_says_so(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    await service(db_session, clock, sender).notify(
        NotificationType.cab_arrived,
        Audience(employee=world["users"]["rider"].id, operator_id=world["operator_id"]),
    )
    assert (await records(db_session))[0].delivered is True


async def test_a_user_with_no_device_is_recorded_but_not_delivered(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    """The in-app list must still show it when they next open the app."""
    await service(db_session, clock, sender).notify(
        NotificationType.cab_arrived,
        Audience(employee=world["users"]["supervisor_b"].id, operator_id=world["operator_id"]),
    )

    row = (await records(db_session))[0]
    assert row.delivered is False
    assert sender.messages == []


async def test_the_unread_list_is_what_the_badge_counts(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    notifier = service(db_session, clock, sender)
    rider = world["users"]["rider"].id
    await notifier.notify(
        NotificationType.cab_arrived, Audience(employee=rider, operator_id=world["operator_id"])
    )
    await notifier.notify(
        NotificationType.trip_completed, Audience(employee=rider, operator_id=world["operator_id"])
    )

    assert len(await notifier.unread(rider)) == 2

    first = (await records(db_session))[0]
    first.read_at = NOW
    await db_session.flush()
    assert len(await notifier.unread(rider)) == 1


# --- devices ---------------------------------------------------------------------------


async def test_every_device_of_a_user_gets_it(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    """Phone and tablet, both signed in; the rider should not have to guess which buzzes."""
    db_session.add(
        Device(
            user_id=world["users"]["rider"].id,
            platform=DevicePlatform.ios,
            push_token="token-rider-tablet",
            last_seen_at=NOW,
        )
    )
    await db_session.flush()

    await service(db_session, clock, sender).notify(
        NotificationType.cab_arrived,
        Audience(employee=world["users"]["rider"].id, operator_id=world["operator_id"]),
    )

    assert set(sender.tokens()) == {"token-rider", "token-rider-tablet"}


async def test_a_long_dead_device_is_skipped(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    """A reinstalled phone's token would otherwise cost a request per notification forever."""
    db_session.add(
        Device(
            user_id=world["users"]["rider"].id,
            platform=DevicePlatform.android,
            push_token="token-rider-old",
            last_seen_at=NOW - timedelta(days=STALE_DEVICE_DAYS + 1),
        )
    )
    await db_session.flush()

    await service(db_session, clock, sender).notify(
        NotificationType.cab_arrived,
        Audience(employee=world["users"]["rider"].id, operator_id=world["operator_id"]),
    )

    assert sender.tokens() == ["token-rider"]


async def test_a_brand_new_device_is_not_treated_as_stale(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, sender: RecordingPushSender
) -> None:
    """Registered a second ago and never seen since is new, not abandoned."""
    db_session.add(
        Device(
            user_id=world["users"]["supervisor_b"].id,
            platform=DevicePlatform.android,
            push_token="token-fresh",
            last_seen_at=None,
        )
    )
    await db_session.flush()

    await service(db_session, clock, sender).notify(
        NotificationType.cab_arrived,
        Audience(employee=world["users"]["supervisor_b"].id, operator_id=world["operator_id"]),
    )

    assert sender.tokens() == ["token-fresh"]
