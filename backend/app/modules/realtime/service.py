"""Loading the facts a channel decision needs (B13).

`channels.py` decides; this finds out. Split that way because "may this employee watch
this trip" is a rule worth testing on its own, and because the rule must not quietly grow
a database query inside it.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import Role
from app.domain.state_machines import RequestStatus
from app.modules.dispatch.models import Trip
from app.modules.fleet.models import Driver
from app.modules.people.models import Employee
from app.modules.realtime.channels import Subscriber, TripMembership
from app.modules.requests.models import RideRequest

#: Roles that watch the whole operator's board rather than one trip.
OPERATOR_STAFF_ROLES = frozenset({Role.supervisor, Role.operator_admin, Role.platform_admin})

#: A rider's own journey is over once their request reaches one of these.
FINISHED_RIDER_STATUSES = frozenset(
    {
        RequestStatus.dropped,
        RequestStatus.cancelled,
        RequestStatus.no_show,
        RequestStatus.expired,
    }
)


class MembershipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def trip_membership(
        self, trip_id: uuid.UUID, subscriber: Subscriber
    ) -> TripMembership | None:
        """How this subscriber relates to a trip, or `None` if the trip is not theirs.

        A trip belonging to another operator returns `None` rather than an empty
        membership: "no such trip for you" and "not on this trip" must be indistinguishable
        from outside, or the channel name becomes a way to probe for trips.
        """
        trip = await self.session.scalar(select(Trip).where(Trip.id == trip_id))
        if trip is None or trip.operator_id != subscriber.operator_id:
            return None

        if Role(subscriber.role) in OPERATOR_STAFF_ROLES:
            return TripMembership(is_operator_staff=True)

        if Role(subscriber.role) is Role.driver:
            driver_id = await self.session.scalar(
                select(Driver.id).where(Driver.user_id == subscriber.user_id)
            )
            return TripMembership(is_assigned_driver=driver_id == trip.driver_id)

        employee_id = await self.session.scalar(
            select(Employee.id).where(Employee.user_id == subscriber.user_id)
        )
        if employee_id is None:
            return TripMembership()

        status = await self.session.scalar(
            select(RideRequest.status)
            .where(RideRequest.trip_id == trip_id)
            .where(RideRequest.employee_id == employee_id)
        )
        if status is None:
            return TripMembership()
        return TripMembership(
            is_rider=True,
            rider_finished=status in {str(value) for value in FINISHED_RIDER_STATUSES},
        )
