"""Reading and writing one client's policy (`allocation-rules.md` §1, B28).

`client_policy` has had a table since B06 and an API never. The columns the dispatch
service read were two of nine; the rest - pooling, opt-out, the night window, the
pickup window, the no-show wait - were settable only by hand in `psql`, which means
they were not settable.

This service is the one place the row is read, written, and combined with operator
config, so "what applies to this client" has a single answer wherever it is asked:
the dispatch service for the hard rules, the driver service for the no-show wait, the
request service for whether a rider may opt out, and the admin screen for showing an
operator what their numbers resolved to.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.errors import NotFound
from app.domain.policy import ClientPolicyValues, EffectivePolicy
from app.domain.policy import resolve as resolve_policy
from app.modules.config.service import ConfigService
from app.modules.tenancy.models import Client, ClientPolicy

logger = get_logger(__name__)


class ClientPolicyService:
    def __init__(
        self, session: AsyncSession, clock: Clock, config: ConfigService | None = None
    ) -> None:
        self.session = session
        self.clock = clock
        self.config = config or ConfigService(session, clock)

    # --- resolution ---------------------------------------------------------------

    async def effective(
        self,
        operator_id: uuid.UUID,
        client_ids: set[uuid.UUID],
        settings: dict[str, Any] | None = None,
    ) -> dict[uuid.UUID, EffectivePolicy]:
        """Operator config resolved against each client's own policy.

        A client with no policy row gets the operator's numbers unchanged - every
        client today, and every client throughout Phase 1.
        """
        values = settings if settings is not None else await self.config.all_values(operator_id)
        rows = {
            policy.client_id: policy
            for policy in (
                await self.session.execute(
                    select(ClientPolicy).where(ClientPolicy.client_id.in_(client_ids))
                )
            )
            .scalars()
            .all()
        }
        return {
            client_id: resolve_policy(values, policy_values(rows.get(client_id)))
            for client_id in client_ids
        }

    async def for_client(self, operator_id: uuid.UUID, client_id: uuid.UUID) -> EffectivePolicy:
        return (await self.effective(operator_id, {client_id}))[client_id]

    # --- the row itself -------------------------------------------------------------

    async def row(self, operator_id: uuid.UUID, client_id: uuid.UUID) -> ClientPolicy | None:
        await self._client_or_404(operator_id, client_id)
        found: ClientPolicy | None = await self.session.scalar(
            select(ClientPolicy)
            .where(ClientPolicy.operator_id == operator_id)
            .where(ClientPolicy.client_id == client_id)
        )
        return found

    async def put(
        self, operator_id: uuid.UUID, client_id: uuid.UUID, changes: dict[str, Any]
    ) -> ClientPolicy:
        """Create or update the policy. Only the fields supplied are touched.

        A `null` is a real value here and clears the override, so the test is whether
        the caller **sent** the field - the same distinction B26 needed for an
        override's expiry, and for the same reason: "leave it alone" and "remove it"
        are different requests.
        """
        policy = await self.row(operator_id, client_id)
        if policy is None:
            policy = ClientPolicy(id=uuid.uuid4(), operator_id=operator_id, client_id=client_id)
            self.session.add(policy)

        for field, value in changes.items():
            setattr(policy, field, value)
        await self.session.flush()

        logger.info(
            "client_policy_updated",
            operator_id=str(operator_id),
            client_id=str(client_id),
            fields=sorted(changes),
        )
        return policy

    async def _client_or_404(self, operator_id: uuid.UUID, client_id: uuid.UUID) -> Client:
        client = await self.session.scalar(
            select(Client).where(Client.id == client_id).where(Client.operator_id == operator_id)
        )
        if client is None:
            raise NotFound("Client not found", {"id": str(client_id)})
        return client


def policy_values(policy: ClientPolicy | None) -> ClientPolicyValues | None:
    """The ORM row as the pure dataclass `domain/policy.py` resolves."""
    if policy is None:
        return None
    return ClientPolicyValues(
        pooling_allowed=policy.pooling_allowed,
        employee_opt_out_allowed=policy.employee_opt_out_allowed,
        night_safety_enabled=policy.night_safety_enabled,
        night_start=policy.night_start,
        night_end=policy.night_end,
        max_detour_factor=(
            float(policy.max_detour_factor) if policy.max_detour_factor is not None else None
        ),
        max_detour_minutes=policy.max_detour_minutes,
        pickup_window_minutes=policy.pickup_window_minutes,
        no_show_wait_minutes=policy.no_show_wait_minutes,
    )
