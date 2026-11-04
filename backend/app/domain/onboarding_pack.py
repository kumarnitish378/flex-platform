"""Validation of a pilot onboarding pack (R03), without a database.

A pack is a folder (or zip) of CSV files an operator fills in before the pilot starts:

====================  =====================================================  ==========
file                  columns                                                required
====================  =====================================================  ==========
clients.csv           name, contact_name, contact_phone                      yes
offices.csv           client_name, name, lat, lng, address_text              yes
zones.csv             name, boundary ("lat lng; lat lng; lat lng; ...")      no
client_policies.csv   client_name + the `ClientPolicyInput` fields           no
vehicles.csv          registration_no, model, vehicle_type, seat_capacity,   yes
                      tracker_type
drivers.csv           name, phone, licence_last4, vehicle_registration       yes
employees.csv         client_name + the employee import columns (B07)        yes
====================  =====================================================  ==========

`validate_pack` takes the file texts and returns **every** problem, not the first: an
operator with 35 cabs and 300 riders needs the whole list in one pass. Errors would make
the load fail or load something wrong; warnings are things worth a second look (an
example row left in, a woman rider with no escort flag on a night client, ...).

The row rules for employees are the ones the real import uses (`employee_import`), so a
pack that passes here passes there. The other files follow the admin API's own limits
(`fleet.schemas`, `ClientPolicyInput`).
"""

from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass, field
from datetime import time
from typing import Final

from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.validation import explain_validity

from app.domain.employee_import import (
    FALSE_VALUES,
    MAX_ROWS,
    TRUE_VALUES,
    ImportFormatError,
    parse_csv,
    validate_coordinate,
    validate_phone,
)
from app.domain.enums import TrackerType, VehicleType

CLIENTS: Final = "clients.csv"
OFFICES: Final = "offices.csv"
ZONES: Final = "zones.csv"
POLICIES: Final = "client_policies.csv"
VEHICLES: Final = "vehicles.csv"
DRIVERS: Final = "drivers.csv"
EMPLOYEES: Final = "employees.csv"

REQUIRED_FILES: Final = (CLIENTS, OFFICES, VEHICLES, DRIVERS, EMPLOYEES)
OPTIONAL_FILES: Final = (ZONES, POLICIES)

COLUMNS: Final[dict[str, tuple[str, ...]]] = {
    CLIENTS: ("name", "contact_name", "contact_phone"),
    OFFICES: ("client_name", "name", "lat", "lng", "address_text"),
    ZONES: ("name", "boundary"),
    POLICIES: (
        "client_name",
        "pooling_allowed",
        "employee_opt_out_allowed",
        "night_safety_enabled",
        "night_start",
        "night_end",
        "max_detour_factor",
        "max_detour_minutes",
        "pickup_window_minutes",
        "no_show_wait_minutes",
    ),
    VEHICLES: ("registration_no", "model", "vehicle_type", "seat_capacity", "tracker_type"),
    DRIVERS: ("name", "phone", "licence_last4", "vehicle_registration"),
    EMPLOYEES: (
        "client_name",
        "name",
        "phone",
        "office_name",
        "home_lat",
        "home_lng",
        "landmark",
        "priority",
        "is_vip",
        "night_escort_required",
        "gender",
    ),
}
#: Columns a file may not do without. Everything else in `COLUMNS` can be left empty.
MUST_HAVE: Final[dict[str, tuple[str, ...]]] = {
    CLIENTS: ("name",),
    OFFICES: ("client_name", "name", "lat", "lng"),
    ZONES: ("name", "boundary"),
    POLICIES: ("client_name",),
    VEHICLES: ("registration_no", "vehicle_type", "seat_capacity"),
    DRIVERS: ("name", "phone"),
    EMPLOYEES: ("client_name", "name", "phone", "office_name", "home_lat", "home_lng"),
}

#: A row whose name starts like this is a template example the operator forgot to delete.
EXAMPLE_PREFIX: Final = "example"

MAX_VEHICLES: Final = 500
MAX_SEATS: Final = 12
#: Mirrors the `client_policy` CHECK constraints (data-model.md).
POLICY_RANGES: Final[dict[str, tuple[float, float]]] = {
    "max_detour_factor": (1.0, 3.0),
    "max_detour_minutes": (0, 60),
    "pickup_window_minutes": (0, 30),
    "no_show_wait_minutes": (1, 15),
}
POLICY_BOOLEANS: Final = ("pooling_allowed", "employee_opt_out_allowed", "night_safety_enabled")


@dataclass(frozen=True, slots=True)
class Issue:
    file: str
    row: int | None
    field: str
    message: str
    severity: str = "error"

    def line(self) -> str:
        where = self.file if self.row is None else f"{self.file}:{self.row}"
        subject = f" [{self.field}]" if self.field else ""
        return f"{self.severity.upper():7} {where}{subject} {self.message}"


@dataclass
class PackReport:
    issues: list[Issue] = field(default_factory=list)
    #: Valid rows found per file, for the summary line.
    rows: dict[str, int] = field(default_factory=dict)
    #: Files present, in the order they were checked.
    files: list[str] = field(default_factory=list)
    #: Rows per file that look like a template example, reported as one warning per file.
    example_rows: dict[str, list[int]] = field(default_factory=dict)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, file: str, row: int | None, column: str, message: str) -> None:
        self.issues.append(Issue(file, row, column, message, "error"))

    def warn(self, file: str, row: int | None, column: str, message: str) -> None:
        self.issues.append(Issue(file, row, column, message, "warning"))


@dataclass(frozen=True, slots=True)
class Row:
    number: int
    values: dict[str, str]

    def get(self, column: str) -> str:
        return self.values.get(column, "")


def validate_pack(files: dict[str, str]) -> PackReport:
    """Check a whole pack. `files` maps a file name (`vehicles.csv`) to its text."""
    report = PackReport()

    for name in files:
        if name not in COLUMNS:
            report.warn(name, None, "", "Not one of the pack files; it is ignored")
    for name in REQUIRED_FILES:
        if name not in files:
            report.error(name, None, "", "This file is required and is missing")

    tables: dict[str, list[Row]] = {}
    for name in (*REQUIRED_FILES, *OPTIONAL_FILES):
        if name in files:
            rows = _read(name, files[name], report)
            if rows is not None:
                tables[name] = rows
                report.files.append(name)

    # A file that could not be read stands in as None, so rows that point at it are not all
    # reported as "unknown client" on top of the real problem.
    clients = _clients(tables[CLIENTS], report) if CLIENTS in tables else None
    offices = _offices(tables[OFFICES], clients, report) if OFFICES in tables else None
    zones = _zones(tables.get(ZONES, []), report)
    night_clients = _policies(tables.get(POLICIES, []), clients, report)
    vehicles = _vehicles(tables[VEHICLES], report) if VEHICLES in tables else None
    _drivers(tables.get(DRIVERS, []), vehicles, report)
    _employees(
        files.get(EMPLOYEES),
        tables.get(EMPLOYEES, []),
        clients,
        offices,
        zones,
        night_clients,
        report,
    )
    _across_files(tables, report)
    for name, numbers in report.example_rows.items():
        listed = ", ".join(str(n) for n in sorted(set(numbers)))
        report.warn(
            name,
            None,
            "",
            f"Row(s) {listed} look like template examples (the name starts with 'Example') - "
            "delete them unless they are real",
        )
    return report


# --- reading --------------------------------------------------------------------------


def _read(name: str, text: str, report: PackReport) -> list[Row] | None:
    """Rows as header-keyed dicts; None when the file itself is unusable."""
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    if reader.fieldnames is None:
        report.error(name, None, "", "The file is empty")
        return None

    headers = [(h or "").strip().lower() for h in reader.fieldnames]
    expected = COLUMNS[name]
    missing = [c for c in MUST_HAVE[name] if c not in headers]
    if missing:
        report.error(
            name,
            1,
            "",
            f"Missing column(s): {', '.join(missing)}. Expected header: {', '.join(expected)}",
        )
        return None
    for unknown in (h for h in headers if h and h not in expected):
        report.warn(name, 1, unknown, "Unknown column; it is ignored")

    rows: list[Row] = []
    for number, raw in enumerate(reader, start=2):
        values = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        if not any(values.values()):
            continue
        if len(rows) >= MAX_ROWS:
            report.error(name, number, "", f"Too many rows; the limit is {MAX_ROWS}")
            break
        rows.append(Row(number, values))
    if not rows:
        report.error(name, None, "", "The file has a header but no rows")
    report.rows[name] = len(rows)
    return rows


def _required(name: str, row: Row, report: PackReport) -> bool:
    ok = True
    for column in MUST_HAVE[name]:
        if not row.get(column):
            report.error(name, row.number, column, f"{column} is required")
            ok = False
    return ok


def _flag_example(name: str, row: Row, column: str, report: PackReport) -> None:
    if row.get(column).lower().startswith(EXAMPLE_PREFIX):
        report.example_rows.setdefault(name, []).append(row.number)


def _duplicates(
    name: str, rows: list[tuple[Row, str]], column: str, what: str, report: PackReport
) -> None:
    seen: dict[str, int] = {}
    for row, key in rows:
        if not key:
            continue
        if key in seen:
            report.error(name, row.number, column, f"{what} repeats row {seen[key]}")
        else:
            seen[key] = row.number


def _phone(name: str, row: Row, column: str, report: PackReport) -> None:
    for problem in validate_phone(row.number, row.get(column)):
        report.error(name, row.number, column, problem.message)


# --- one function per file --------------------------------------------------------------


def _clients(rows: list[Row], report: PackReport) -> set[str]:
    known: set[str] = set()
    for row in rows:
        if not _required(CLIENTS, row, report):
            continue
        if len(row.get("name")) > 200:
            report.error(CLIENTS, row.number, "name", "name is longer than 200 characters")
        if row.get("contact_phone"):
            _phone(CLIENTS, row, "contact_phone", report)
        _flag_example(CLIENTS, row, "name", report)
        known.add(row.get("name").lower())
    _duplicates(CLIENTS, [(r, r.get("name").lower()) for r in rows], "name", "Client name", report)
    return known


def _offices(rows: list[Row], clients: set[str] | None, report: PackReport) -> dict[str, set[str]]:
    """Office names per client (lower-cased), for the employee check."""
    by_client: dict[str, set[str]] = {}
    for row in rows:
        if not _required(OFFICES, row, report):
            continue
        client = row.get("client_name").lower()
        if clients is not None and client not in clients:
            report.error(
                OFFICES,
                row.number,
                "client_name",
                f"No client {row.get('client_name')!r} in clients.csv",
            )
        for problem in validate_coordinate(row.number, "lat", row.get("lat"), 90.0):
            report.error(OFFICES, row.number, "lat", problem.message)
        for problem in validate_coordinate(row.number, "lng", row.get("lng"), 180.0):
            report.error(OFFICES, row.number, "lng", problem.message)
        if len(row.get("address_text")) > 500:
            report.error(OFFICES, row.number, "address_text", "address_text is over 500 characters")
        _flag_example(OFFICES, row, "name", report)
        by_client.setdefault(client, set()).add(row.get("name").lower())
    _duplicates(
        OFFICES,
        [(r, f"{r.get('client_name').lower()}/{r.get('name').lower()}") for r in rows],
        "name",
        "Office (for that client)",
        report,
    )
    if clients is not None and rows:
        for client in sorted(clients - by_client.keys()):
            report.error(OFFICES, None, "client_name", f"Client {client!r} has no office")
    return by_client


def parse_boundary(text: str) -> list[tuple[float, float]]:
    """`"28.1 77.1; 28.2 77.1; 28.2 77.2"` -> `[(28.1, 77.1), ...]`; ValueError when malformed."""
    points: list[tuple[float, float]] = []
    for part in (p.strip() for p in text.replace("\n", ";").split(";")):
        if not part:
            continue
        pieces = part.replace(",", " ").split()
        if len(pieces) != 2:
            raise ValueError(f"{part!r} is not 'lat lng'")
        lat, lng = float(pieces[0]), float(pieces[1])
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError(f"{part!r} is outside the world (lat -90..90, lng -180..180)")
        points.append((lat, lng))
    return points


def _zones(rows: list[Row], report: PackReport) -> list[tuple[str, ShapelyPolygon]]:
    polygons: list[tuple[str, ShapelyPolygon]] = []
    for row in rows:
        if not _required(ZONES, row, report):
            continue
        if len(row.get("name")) > 200:
            report.error(ZONES, row.number, "name", "name is longer than 200 characters")
        _flag_example(ZONES, row, "name", report)
        try:
            points = parse_boundary(row.get("boundary"))
        except ValueError as exc:
            report.error(ZONES, row.number, "boundary", str(exc))
            continue
        lng_lat = [(lng, lat) for lat, lng in points]
        if lng_lat and lng_lat[0] == lng_lat[-1]:
            lng_lat = lng_lat[:-1]
        if len(set(lng_lat)) < 3:
            report.error(
                ZONES, row.number, "boundary", "A zone needs at least three distinct corners"
            )
            continue
        polygon = ShapelyPolygon([*lng_lat, lng_lat[0]])
        if not polygon.is_valid:
            report.error(
                ZONES,
                row.number,
                "boundary",
                f"That outline crosses itself ({explain_validity(polygon)})",
            )
            continue
        polygons.append((row.get("name"), polygon))
    _duplicates(ZONES, [(r, r.get("name").lower()) for r in rows], "name", "Zone name", report)
    return polygons


def _time_of(text: str) -> time | None:
    try:
        return time.fromisoformat(text)
    except ValueError:
        return None


def _policies(rows: list[Row], clients: set[str] | None, report: PackReport) -> set[str]:
    """Returns the clients (lower-cased) whose policy turns night safety on."""
    night: set[str] = set()
    for row in rows:
        if not _required(POLICIES, row, report):
            continue
        client = row.get("client_name").lower()
        if clients is not None and client not in clients:
            report.error(
                POLICIES,
                row.number,
                "client_name",
                f"No client {row.get('client_name')!r} in clients.csv",
            )
        for column in POLICY_BOOLEANS:
            value = row.get(column).lower()
            if value and value not in TRUE_VALUES | FALSE_VALUES:
                report.error(
                    POLICIES, row.number, column, f"Expected yes/no, got {row.get(column)!r}"
                )
        for column in ("night_start", "night_end"):
            if row.get(column) and _time_of(row.get(column)) is None:
                report.error(
                    POLICIES,
                    row.number,
                    column,
                    f"Expected a time like 20:00, got {row.get(column)!r}",
                )
        for column, (low, high) in POLICY_RANGES.items():
            value = row.get(column)
            if not value:
                continue
            try:
                number = float(value)
                if column != "max_detour_factor" and number != int(number):
                    raise ValueError
            except ValueError:
                kind = "a number" if column == "max_detour_factor" else "a whole number"
                report.error(
                    POLICIES, row.number, column, f"{column} must be {kind}, got {value!r}"
                )
                continue
            if not low <= number <= high:
                report.error(
                    POLICIES, row.number, column, f"{column} must be between {low} and {high}"
                )
        on = row.get("night_safety_enabled").lower() in TRUE_VALUES
        if on:
            night.add(client)
            if not (row.get("night_start") and row.get("night_end")):
                report.warn(
                    POLICIES,
                    row.number,
                    "night_start",
                    "Night safety is on without its own window; the operator's window applies",
                )
        elif row.get("night_start") or row.get("night_end"):
            report.warn(
                POLICIES,
                row.number,
                "night_safety_enabled",
                "A night window is set but night safety is off",
            )
    _duplicates(
        POLICIES,
        [(r, r.get("client_name").lower()) for r in rows],
        "client_name",
        "Policy for that client",
        report,
    )
    return night


def _vehicles(rows: list[Row], report: PackReport) -> set[str]:
    known: set[str] = set()
    for row in rows:
        if not _required(VEHICLES, row, report):
            continue
        registration = _normal_registration(row.get("registration_no"))
        if len(row.get("registration_no")) > 20:
            report.error(
                VEHICLES, row.number, "registration_no", "registration_no is over 20 characters"
            )
        if row.get("vehicle_type") not in {t.value for t in VehicleType}:
            report.error(
                VEHICLES,
                row.number,
                "vehicle_type",
                f"Expected one of {', '.join(t.value for t in VehicleType)}, "
                f"got {row.get('vehicle_type')!r}",
            )
        seats = row.get("seat_capacity")
        if not seats.isdigit() or not 1 <= int(seats) <= MAX_SEATS:
            report.error(
                VEHICLES,
                row.number,
                "seat_capacity",
                f"seat_capacity must be a whole number from 1 to {MAX_SEATS}, got {seats!r}",
            )
        if row.get("tracker_type") and row.get("tracker_type") not in {
            t.value for t in TrackerType
        }:
            report.error(
                VEHICLES,
                row.number,
                "tracker_type",
                f"Expected app or esp32, got {row.get('tracker_type')!r}",
            )
        if len(row.get("model")) > 100:
            report.error(VEHICLES, row.number, "model", "model is over 100 characters")
        _flag_example(VEHICLES, row, "registration_no", report)
        known.add(registration)
    _duplicates(
        VEHICLES,
        [(r, _normal_registration(r.get("registration_no"))) for r in rows],
        "registration_no",
        "Registration number",
        report,
    )
    if len(rows) > MAX_VEHICLES:
        report.error(VEHICLES, None, "", f"More than {MAX_VEHICLES} vehicles; split the pack")
    return known


def _normal_registration(text: str) -> str:
    """`dl 1c ab 1234` and `DL1CAB1234` are one cab."""
    return "".join(text.split()).replace("-", "").upper()


def _drivers(rows: list[Row], vehicles: set[str] | None, report: PackReport) -> set[str]:
    """Registrations (normalised) that have a driver, for the "cab with no driver" warning."""
    with_driver: set[str] = set()
    for row in rows:
        if not _required(DRIVERS, row, report):
            continue
        if len(row.get("name")) > 200:
            report.error(DRIVERS, row.number, "name", "name is longer than 200 characters")
        _phone(DRIVERS, row, "phone", report)
        licence = row.get("licence_last4")
        if licence and not (len(licence) == 4 and licence.isalnum()):
            report.error(
                DRIVERS,
                row.number,
                "licence_last4",
                "licence_last4 is the last four letters/digits only",
            )
        registration = _normal_registration(row.get("vehicle_registration"))
        if registration:
            if vehicles is None or registration in vehicles:
                with_driver.add(registration)
            else:
                report.error(
                    DRIVERS,
                    row.number,
                    "vehicle_registration",
                    f"No vehicle {row.get('vehicle_registration')!r} in vehicles.csv",
                )
        _flag_example(DRIVERS, row, "name", report)
    _duplicates(DRIVERS, [(r, r.get("phone")) for r in rows], "phone", "Driver phone", report)
    if vehicles is not None and DRIVERS in report.rows:
        for registration in sorted(vehicles - with_driver):
            report.warn(
                VEHICLES,
                None,
                "registration_no",
                f"Vehicle {registration} has no driver in drivers.csv",
            )
    return with_driver


def _employees(
    text: str | None,
    rows: list[Row],
    clients: set[str] | None,
    offices: dict[str, set[str]] | None,
    zones: list[tuple[str, ShapelyPolygon]],
    night_clients: set[str],
    report: PackReport,
) -> None:
    if text is None or EMPLOYEES not in report.rows:
        return
    # The real import's own rules, so a pack that passes here passes there.
    try:
        parsed = parse_csv(text)
    except ImportFormatError as exc:
        report.error(EMPLOYEES, 1, "", str(exc))
        return
    for problem in parsed.errors:
        report.error(EMPLOYEES, problem.row, problem.field, problem.message)

    missing_gender: Counter[str] = Counter()
    for row in rows:
        client = row.get("client_name").lower()
        if clients is not None and row.get("client_name") and client not in clients:
            report.error(
                EMPLOYEES,
                row.number,
                "client_name",
                f"No client {row.get('client_name')!r} in clients.csv",
            )
        elif (
            offices is not None
            and row.get("office_name")
            and row.get("office_name").lower() not in offices.get(client, set())
        ):
            report.error(
                EMPLOYEES,
                row.number,
                "office_name",
                f"Client {row.get('client_name')!r} has no office "
                f"{row.get('office_name')!r} in offices.csv",
            )
        _flag_example(EMPLOYEES, row, "name", report)
        if not row.get("gender") and client in night_clients:
            missing_gender[row.get("client_name")] += 1

    for employee in parsed.employees:
        if zones and not any(
            polygon.covers(ShapelyPoint(employee.home_lng, employee.home_lat))
            for _, polygon in zones
        ):
            report.warn(
                EMPLOYEES,
                employee.row,
                "home_lat",
                "Home is outside every zone in zones.csv (it will not be pooled by zone)",
            )
    for client, count in missing_gender.items():
        report.warn(
            EMPLOYEES,
            None,
            "gender",
            f"{count} employee(s) of {client!r} have no gender; the night escort rule cannot "
            "protect them (unknown gender never triggers it)",
        )


def _across_files(tables: dict[str, list[Row]], report: PackReport) -> None:
    driver_phones = {r.get("phone"): r.number for r in tables.get(DRIVERS, []) if r.get("phone")}
    for row in tables.get(EMPLOYEES, []):
        phone = row.get("phone")
        if phone in driver_phones:
            report.warn(
                EMPLOYEES,
                row.number,
                "phone",
                f"Same phone as drivers.csv row {driver_phones[phone]}; one person, two roles?",
            )
