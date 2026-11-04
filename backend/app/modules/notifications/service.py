"""Turning "notify the employee" into a message on a phone (B16).

`state_machines.py` says *who* in role terms, `app/domain/notifications.py` says *what*,
and this finds the actual people, writes the record, and pushes to their devices.

Recorded first, sent second, and deliberately never fatal: a rider who was told nothing
because the push provider was down is a support problem, but a trip that failed to be
assigned because the push provider was down is an operational one. The `notification` row
is written either way, with `delivered` saying which happened.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.enums import Role, UserStatus
from app.domain.notifications import Notification as Message
from app.domain.notifications import NotificationType, build
from app.domain.state_machines import Recipient
from app.modules.auth.models import AppUser, Device, UserRole
from app.modules.notifications.models import Notification
from app.modules.notifications.push import STALE_DEVICE_DAYS, LogPushSender, PushMessage, PushSender

logger = get_logger(__name__)

#: Which roles stand behind each broadcast recipient.
BROADCAST_ROLES: dict[Recipient, tuple[Role, ...]] = {
    Recipient.supervisor: (Role.supervisor,),
    Recipient.operator_admin: (Role.operator_admin,),
}


@dataclass(slots=True)
class Audience:
    """Who the caller has resolved for each role in this particular event.

    Supplied by the caller because only it knows which employee, which driver and which
    cab: a notification service that went looking would need to understand trips.
    """

    employee: uuid.UUID | None = None
    driver: uuid.UUID | None = None
    previous_driver: uuid.UUID | None = None
    #: Broadcast roles are resolved from `user_role` for this operator.
    operator_id: uuid.UUID | None = None
    extra: dict[Recipient, list[uuid.UUID]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SendResult:
    recorded: int = 0
    pushed: int = 0


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        sender: PushSender | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.sender = sender or LogPushSender()

    async def notify(
        self,
        event: NotificationType,
        audience: Audience,
        context: dict[str, Any] | None = None,
    ) -> SendResult:
        """Send everything `trip-lifecycle.md` section 6 says this event should send."""
        messages = build(event, context)
        if not messages:
            return SendResult()

        recorded = 0
        pushed = 0
        for message in messages:
            for user_id in await self._users_for(message.recipient, audience):
                delivered = await self._deliver(user_id, message)
                recorded += 1
                pushed += 1 if delivered else 0

        if recorded:
            # Not `event=`: structlog already uses that name for the log message itself.
            logger.info(
                "notifications_sent",
                notification=str(event),
                recorded=recorded,
                pushed=pushed,
            )
        return SendResult(recorded=recorded, pushed=pushed)

    async def _deliver(self, user_id: uuid.UUID, message: Message) -> bool:
        now = self.clock.now()
        record = Notification(
            user_id=user_id,
            type=str(message.type),
            title=message.title,
            body=message.body,
            data=message.data or None,
            sent_at=now,
            delivered=False,
        )
        self.session.add(record)
        await self.session.flush()

        tokens = await self._tokens_for(user_id)
        delivered = False
        for token in tokens:
            sent = await self.sender.send(
                PushMessage(
                    token=token,
                    title=message.title,
                    body=message.body,
                    data={**(message.data or {}), "type": str(message.type)},
                    high_priority=message.high_priority,
                    notification_id=record.id,
                )
            )
            delivered = delivered or sent

        record.delivered = delivered
        return delivered

    async def _users_for(self, recipient: Recipient, audience: Audience) -> list[uuid.UUID]:
        """The actual people behind a role for this event."""
        if recipient in audience.extra:
            return audience.extra[recipient]

        direct = {
            Recipient.employee: audience.employee,
            Recipient.driver: audience.driver,
            Recipient.previous_driver: audience.previous_driver,
        }
        if recipient in direct:
            user_id = direct[recipient]
            return [user_id] if user_id is not None else []

        roles = BROADCAST_ROLES.get(recipient)
        if roles is None or audience.operator_id is None:
            return []
        return await self._users_with_role(audience.operator_id, roles)

    async def _users_with_role(
        self, operator_id: uuid.UUID, roles: tuple[Role, ...]
    ) -> list[uuid.UUID]:
        """Everyone holding one of these roles for this operator.

        Scoped to the operator, always: a supervisor at one cab company must never be
        paged about another's trip.
        """
        result = await self.session.execute(
            select(UserRole.user_id)
            .join(AppUser, AppUser.id == UserRole.user_id)
            .where(UserRole.operator_id == operator_id)
            .where(UserRole.role.in_([str(role) for role in roles]))
            .where(AppUser.status == str(UserStatus.active))
            .distinct()
        )
        return list(result.scalars().all())

    async def _tokens_for(self, user_id: uuid.UUID) -> list[str]:
        """Push tokens for a user's live devices.

        Devices unseen for `STALE_DEVICE_DAYS` are skipped: that token is usually a
        reinstalled or lost phone, and pushing to it wastes a request per notification
        forever.
        """
        cutoff = self.clock.now() - timedelta(days=STALE_DEVICE_DAYS)
        result = await self.session.execute(
            select(Device.push_token)
            .where(Device.user_id == user_id)
            # A device that has never checked in is newly registered, not stale.
            .where((Device.last_seen_at.is_(None)) | (Device.last_seen_at >= cutoff))
        )
        return [token for token in result.scalars().all() if token]

    async def unread(self, user_id: uuid.UUID) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.read_at.is_(None))
            .order_by(Notification.sent_at.desc())
        )
        return list(result.scalars().all())
