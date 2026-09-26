"""Scenario reset: wipe and reseed the sim database (B19).

The fixture is the one `testing-strategy.md` §4 specifies — 2 offices, 3 zones,
20 employees, 6 vehicles — plus one login per role, so the simulator's agents have
someone to authenticate as.

Everything is derived from a fixed seed, so two resets produce identical ids and the
same run really is reproducible (`simulator-spec.md` §13).
"""

from __future__ import annotations

import uuid

from geoalchemy2.shape import from_shape
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon as ShapelyPolygon
from sqlalchemy import delete, select

from app.core.clock import Clock
from app.core.logging import get_logger
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import Role, TrackerType, VehicleType
from app.modules.alerts.models import Alert
from app.modules.auth.models import AppUser, Device, OtpChallenge, RefreshToken, UserRole
from app.modules.config.models import OperatorConfig, OperatorConfigHistory
from app.modules.fleet.models import Driver, Vehicle
from app.modules.people.models import Employee, SavedPlace
from app.modules.requests.models import RideRequest, RideRequestEvent
from app.modules.simctl.schemas import ResetResult, SeededUser
from app.modules.tenancy.models import Client, ClientPolicy, Office, Operator, Zone

logger = get_logger(__name__)

#: Deterministic namespace so every reset produces the same ids.
SEED_NAMESPACE = uuid.UUID("5ca8cab5-0000-4000-8000-000000000000")

OPERATOR_NAME = "Sim Cabs"
CLIENT_NAME = "Sim Client"

# Delhi NCR fixture points (the pair used throughout the docs).
OFFICES = (("B200", 28.5703, 77.3218), ("Tower C", 28.5450, 77.3300))
ZONES = (("sector_62", 28.62, 77.36), ("sector_135", 28.50, 77.38), ("sector_168", 28.46, 77.40))
EMPLOYEE_COUNT = 20
VEHICLES = (
    ("SIM0001", VehicleType.sedan_4, 4),
    ("SIM0002", VehicleType.sedan_4, 4),
    ("SIM0003", VehicleType.sedan_4, 4),
    ("SIM0004", VehicleType.suv_6, 6),
    ("SIM0005", VehicleType.suv_6, 6),
    ("SIM0006", VehicleType.vip, 4),
)
#: One login per role, matching dev-environment.md §6's numbering style.
#: Seeded tokens must outlive a whole simulated run. A scenario covers hours of simulated
#: time in seconds of real time, so a 15-minute production TTL expires mid-run and every
#: agent starts getting 401s. Safe only because `/simctl/*` cannot exist outside
#: APP_ENV=sim (ADR-0008).
SIM_TOKEN_TTL_SECONDS = 12 * 3600

#: Distinct phone blocks per role, so seeded accounts cannot collide on the unique index.
_PHONE_BLOCK = {Role.driver: "1", Role.employee: "2"}

SEED_USERS = (
    (Role.operator_admin, "+910000000001"),
    (Role.supervisor, "+910000000002"),
    (Role.client_admin, "+910000000003"),
    (Role.driver, "+910000000004"),
    (Role.employee, "+910000000005"),
)

#: Deleted in dependency order — children before parents.
TRUNCATION_ORDER = (
    Alert,
    RideRequestEvent,
    RideRequest,
    SavedPlace,
    Employee,
    Driver,
    Vehicle,
    Office,
    ClientPolicy,
    Client,
    Zone,
    OperatorConfigHistory,
    OperatorConfig,
    UserRole,
    Device,
    RefreshToken,
    OtpChallenge,
    AppUser,
    Operator,
)


def _id(*parts: object) -> uuid.UUID:
    """A stable id for a fixture entity."""
    return uuid.uuid5(SEED_NAMESPACE, ":".join(str(part) for part in parts))


def _point(lat: float, lng: float) -> object:
    return from_shape(ShapelyPoint(lng, lat), srid=4326)


def _square(lat: float, lng: float, size: float = 0.02) -> object:
    return from_shape(
        ShapelyPolygon(
            [
                (lng, lat),
                (lng + size, lat),
                (lng + size, lat + size),
                (lng, lat + size),
                (lng, lat),
            ]
        ),
        srid=4326,
    )


class SimControlService:
    def __init__(self, session, clock: Clock, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        self.session = session
        self.clock = clock
        self.settings = settings

    async def reset(self) -> ResetResult:
        await self._truncate()
        result = await self._seed()
        await self.session.flush()
        logger.info("simctl_reset", operator_id=str(result.operator_id), at=result.now.isoformat())
        return result

    async def _truncate(self) -> None:
        """Wipe every table this fixture touches.

        Whole-table deletes rather than per-operator: a sim database has exactly one
        tenant, and leaving rows behind between scenarios is how a run stops being
        reproducible.
        """
        for model in TRUNCATION_ORDER:
            await self.session.execute(delete(model))
        await self.session.flush()

    async def _seed(self) -> ResetResult:
        operator = Operator(id=_id("operator"), name=OPERATOR_NAME)
        self.session.add(operator)
        await self.session.flush()

        corporate = Client(id=_id("client"), operator_id=operator.id, name=CLIENT_NAME)
        self.session.add(corporate)
        self.session.add(
            ClientPolicy(id=_id("policy"), operator_id=operator.id, client_id=corporate.id)
        )
        await self.session.flush()

        office_ids = []
        for name, lat, lng in OFFICES:
            office = Office(
                id=_id("office", name),
                operator_id=operator.id,
                client_id=corporate.id,
                name=name,
                location=_point(lat, lng),
            )
            self.session.add(office)
            office_ids.append(office.id)

        zone_ids = []
        for name, lat, lng in ZONES:
            zone = Zone(
                id=_id("zone", name), operator_id=operator.id, name=name, area=_square(lat, lng)
            )
            self.session.add(zone)
            zone_ids.append(zone.id)
        await self.session.flush()

        users = await self._seed_users(operator.id, corporate.id)

        employee_ids = []
        for index in range(EMPLOYEE_COUNT):
            # Spread homes across the zones so pooling has something to work with.
            base_lat, base_lng = ZONES[index % len(ZONES)][1:]
            employee = Employee(
                id=_id("employee", index),
                operator_id=operator.id,
                client_id=corporate.id,
                name=f"Sim Employee {index + 1:02d}",
                phone=f"+9190000{index:05d}",
                office_id=office_ids[index % len(office_ids)],
                home_location=_point(base_lat + index * 0.001, base_lng + index * 0.001),
                priority=5,
                is_vip=(index == 0),
            )
            # Every employee gets a login, not just the first: the simulator's employee
            # agents each create their own requests, and `/ride-requests` scopes a
            # rider to their own employee record (M05).
            if index == 0:
                rider = next(u for u in users if u.role == str(Role.employee))
                employee.user_id = rider.user_id
            else:
                extra = await self._seed_login(
                    operator.id, Role.employee, index, client_id=corporate.id
                )
                employee.user_id = extra.user_id
                users.append(extra)
            self.session.add(employee)
            employee_ids.append(employee.id)

        driver_ids = []
        vehicle_ids = []
        for index, (rego, vehicle_type, seats) in enumerate(VEHICLES):
            vehicle = Vehicle(
                id=_id("vehicle", rego),
                operator_id=operator.id,
                registration_no=rego,
                vehicle_type=vehicle_type,
                seat_capacity=seats,
                tracker_type=TrackerType.app,
            )
            self.session.add(vehicle)
            vehicle_ids.append(vehicle.id)

            driver = Driver(
                id=_id("driver", index),
                operator_id=operator.id,
                name=f"Sim Driver {index + 1}",
                phone=f"+9191000{index:05d}",
                default_vehicle_id=vehicle.id,
            )
            # Every driver gets a login, not just the first: M04 signs one driver into
            # each cab, and a fleet sharing one account cannot - a driver may hold only
            # one open duty session (B11).
            if index == 0:
                seeded_driver = next(u for u in users if u.role == str(Role.driver))
                driver.user_id = seeded_driver.user_id
            else:
                extra = await self._seed_login(operator.id, Role.driver, index)
                driver.user_id = extra.user_id
                users.append(extra)
            self.session.add(driver)
            driver_ids.append(driver.id)

        await self.session.flush()

        return ResetResult(
            operator_id=operator.id,
            client_id=corporate.id,
            office_ids=office_ids,
            zone_ids=zone_ids,
            employee_ids=employee_ids,
            vehicle_ids=vehicle_ids,
            driver_ids=driver_ids,
            users=users,
            now=self.clock.now(),
        )

    async def _seed_login(
        self,
        operator_id: uuid.UUID,
        role: Role,
        index: int,
        client_id: uuid.UUID | None = None,
    ) -> SeededUser:
        """One more account for a person the simulator needs to act as.

        The per-role logins in `SEED_USERS` are one each; agents need one *per* driver and
        per employee, because a driver may hold only one open duty session (B11) and a
        rider may only create requests for themselves (B09). Returned in `users` alongside
        the role logins.
        """
        key = f"{role}-{index}"
        phone = f"+9100{_PHONE_BLOCK[role]}{index:05d}"
        user = AppUser(id=_id("user", key), phone=phone, name=f"Sim {role} {index}")
        self.session.add(user)
        await self.session.flush()
        self.session.add(
            UserRole(
                id=_id("role", key),
                user_id=user.id,
                role=role,
                operator_id=operator_id,
                client_id=client_id,
            )
        )
        token, _ = create_access_token(
            user_id=user.id,
            role=str(role),
            secret=self.settings.jwt_secret.get_secret_value(),
            clock=self.clock,
            ttl_seconds=SIM_TOKEN_TTL_SECONDS,
            operator_id=operator_id,
            client_id=client_id,
        )
        return SeededUser(role=str(role), phone=phone, user_id=user.id, access_token=token)

    async def _seed_users(self, operator_id: uuid.UUID, client_id: uuid.UUID) -> list[SeededUser]:
        """One login per role, with a ready-to-use access token.

        Handing back tokens skips the OTP round trip for every agent at start-up. It is
        safe only because this endpoint cannot exist outside APP_ENV=sim.
        """
        seeded: list[SeededUser] = []
        for role, phone in SEED_USERS:
            user = AppUser(id=_id("user", role), phone=phone, name=f"Sim {role}")
            self.session.add(user)
            await self.session.flush()

            scoped_client = client_id if role in (Role.client_admin, Role.employee) else None
            self.session.add(
                UserRole(
                    id=_id("role", role),
                    user_id=user.id,
                    role=role,
                    operator_id=operator_id,
                    client_id=scoped_client,
                )
            )

            token, _ = create_access_token(
                user_id=user.id,
                role=str(role),
                secret=self.settings.jwt_secret.get_secret_value(),
                clock=self.clock,
                ttl_seconds=SIM_TOKEN_TTL_SECONDS,
                operator_id=operator_id,
                client_id=scoped_client,
            )
            seeded.append(
                SeededUser(role=str(role), phone=phone, user_id=user.id, access_token=token)
            )

        await self.session.flush()
        return seeded

    async def count_rows(self, model: type) -> int:
        """Small helper used by the tests to prove truncation happened."""
        result = await self.session.execute(select(model))
        return len(list(result.scalars().all()))
