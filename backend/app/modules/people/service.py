"""Employee management and CSV import (B07).

Scope matters here more than anywhere so far: a `client_admin` may only ever touch their
own client's employees. The router supplies the caller's `client_id`; this service
refuses any request whose target client differs.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from geoalchemy2.shape import from_shape
from shapely.geometry import Point as ShapelyPoint
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.employee_import import ParsedEmployee, RowError, parse_csv
from app.domain.errors import Conflict, Forbidden, NotFound
from app.modules.people.models import Employee
from app.modules.tenancy.models import Client, Office

logger = get_logger(__name__)


@dataclass
class ImportReport:
    total_rows: int = 0
    valid_rows: int = 0
    created: int = 0
    updated: int = 0
    errors: list[dict[str, object]] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "created": self.created,
            "updated": self.updated,
            "errors": self.errors,
        }


class EmployeeService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self.session = session
        self.clock = clock

    # --- CRUD ---------------------------------------------------------------

    async def list_employees(
        self, operator_id: uuid.UUID, client_id: uuid.UUID, caller_client_id: uuid.UUID | None
    ) -> list[Employee]:
        self._check_client_scope(client_id, caller_client_id)
        await self._client_or_404(operator_id, client_id)
        result = await self.session.execute(
            select(Employee)
            .where(Employee.operator_id == operator_id)
            .where(Employee.client_id == client_id)
            .order_by(Employee.name)
        )
        return list(result.scalars().all())

    async def create_employee(
        self,
        operator_id: uuid.UUID,
        client_id: uuid.UUID,
        data: dict[str, Any],
        caller_client_id: uuid.UUID | None,
    ) -> Employee:
        self._check_client_scope(client_id, caller_client_id)
        await self._client_or_404(operator_id, client_id)
        await self._office_or_404(operator_id, client_id, data["office_id"])

        if await self._by_phone(operator_id, client_id, data["phone"]) is not None:
            raise Conflict("An employee with that phone already exists for this client")

        employee = Employee(operator_id=operator_id, client_id=client_id, **data)
        self.session.add(employee)
        await self.session.flush()
        return employee

    async def update_employee(
        self,
        operator_id: uuid.UUID,
        employee_id: uuid.UUID,
        changes: dict[str, Any],
        caller_client_id: uuid.UUID | None,
    ) -> Employee:
        employee = (
            (
                await self.session.execute(
                    select(Employee)
                    .where(Employee.operator_id == operator_id)
                    .where(Employee.id == employee_id)
                )
            )
            .scalars()
            .one_or_none()
        )
        if employee is None:
            raise NotFound("Employee not found", {"id": str(employee_id)})

        self._check_client_scope(employee.client_id, caller_client_id)

        if "office_id" in changes:
            await self._office_or_404(operator_id, employee.client_id, changes["office_id"])
        if "phone" in changes and changes["phone"] != employee.phone:
            clash = await self._by_phone(operator_id, employee.client_id, changes["phone"])
            if clash is not None:
                raise Conflict("An employee with that phone already exists for this client")

        for field_name, value in changes.items():
            setattr(employee, field_name, value)
        await self.session.flush()
        return employee

    # --- CSV import ---------------------------------------------------------

    async def import_csv(
        self,
        operator_id: uuid.UUID,
        client_id: uuid.UUID,
        content: str,
        caller_client_id: uuid.UUID | None,
        dry_run: bool = True,
    ) -> ImportReport:
        """Validate a CSV and, unless this is a dry run, apply it.

        A dry run writes nothing at all — not even for the rows that are valid. The
        point is to let a client admin see the whole report before committing, so a
        partial apply would defeat it.
        """
        self._check_client_scope(client_id, caller_client_id)
        await self._client_or_404(operator_id, client_id)

        parsed = parse_csv(content)
        report = ImportReport(
            total_rows=parsed.total_rows,
            valid_rows=parsed.valid_rows,
            errors=[error.as_dict() for error in parsed.errors],
        )

        offices = await self._offices_by_name(operator_id, client_id)
        resolvable: list[tuple[ParsedEmployee, uuid.UUID]] = []

        for employee in parsed.employees:
            office_id = offices.get(employee.office_name.strip().lower())
            if office_id is None:
                report.errors.append(
                    RowError(
                        employee.row,
                        "office_name",
                        f"No office named {employee.office_name!r} for this client",
                    ).as_dict()
                )
                report.valid_rows -= 1
                continue
            resolvable.append((employee, office_id))

        if dry_run:
            logger.info(
                "employee_import_dry_run",
                client_id=str(client_id),
                total=report.total_rows,
                valid=report.valid_rows,
                errors=len(report.errors),
            )
            return report

        existing = {
            employee.phone: employee
            for employee in await self.list_employees(operator_id, client_id, caller_client_id)
        }

        for parsed_employee, office_id in resolvable:
            current = existing.get(parsed_employee.phone)
            location = _point(parsed_employee.home_lat, parsed_employee.home_lng)

            if current is None:
                self.session.add(
                    Employee(
                        operator_id=operator_id,
                        client_id=client_id,
                        name=parsed_employee.name,
                        phone=parsed_employee.phone,
                        office_id=office_id,
                        home_location=location,
                        home_landmark=parsed_employee.landmark,
                        priority=parsed_employee.priority,
                        is_vip=parsed_employee.is_vip,
                        night_escort_required=parsed_employee.night_escort_required,
                        # zone_id stays null: zone derivation needs zones to exist, and
                        # assigning one lands with the zone work, not here.
                    )
                )
                report.created += 1
            else:
                current.name = parsed_employee.name
                current.office_id = office_id
                current.home_location = location
                current.home_landmark = parsed_employee.landmark
                current.priority = parsed_employee.priority
                current.is_vip = parsed_employee.is_vip
                current.night_escort_required = parsed_employee.night_escort_required
                report.updated += 1

        await self.session.flush()
        logger.info(
            "employee_import_applied",
            client_id=str(client_id),
            created=report.created,
            updated=report.updated,
            errors=len(report.errors),
        )
        return report

    # --- helpers ------------------------------------------------------------

    @staticmethod
    def _check_client_scope(
        target_client_id: uuid.UUID, caller_client_id: uuid.UUID | None
    ) -> None:
        """A client_admin carries a client_id and may not reach past it.

        Operator-level roles carry none, and are allowed across all of their clients.
        """
        if caller_client_id is not None and caller_client_id != target_client_id:
            raise Forbidden("This role may only manage its own client's employees")

    async def _client_or_404(self, operator_id: uuid.UUID, client_id: uuid.UUID) -> Client:
        client = (
            (
                await self.session.execute(
                    select(Client)
                    .where(Client.operator_id == operator_id)
                    .where(Client.id == client_id)
                )
            )
            .scalars()
            .one_or_none()
        )
        if client is None:
            raise NotFound("Client not found", {"id": str(client_id)})
        return client

    async def _office_or_404(
        self, operator_id: uuid.UUID, client_id: uuid.UUID, office_id: uuid.UUID
    ) -> Office:
        office = (
            (
                await self.session.execute(
                    select(Office)
                    .where(Office.operator_id == operator_id)
                    .where(Office.client_id == client_id)
                    .where(Office.id == office_id)
                )
            )
            .scalars()
            .one_or_none()
        )
        if office is None:
            raise NotFound("Office not found for this client", {"id": str(office_id)})
        return office

    async def _offices_by_name(
        self, operator_id: uuid.UUID, client_id: uuid.UUID
    ) -> dict[str, uuid.UUID]:
        result = await self.session.execute(
            select(Office)
            .where(Office.operator_id == operator_id)
            .where(Office.client_id == client_id)
        )
        return {office.name.strip().lower(): office.id for office in result.scalars().all()}

    async def _by_phone(
        self, operator_id: uuid.UUID, client_id: uuid.UUID, phone: str
    ) -> Employee | None:
        result = await self.session.execute(
            select(Employee)
            .where(Employee.operator_id == operator_id)
            .where(Employee.client_id == client_id)
            .where(Employee.phone == phone)
        )
        return result.scalars().one_or_none()


def _point(lat: float, lng: float) -> Any:
    return from_shape(ShapelyPoint(lng, lat), srid=4326)
