"""CSV row parsing and validation for the employee import (B07).

Pure: takes text, returns parsed rows and errors. No database, no HTTP. That is what
lets the row rules be tested exhaustively and cheaply, and it keeps the service free to
decide what to do with a valid row.

Columns, from the api-spec summary:
`name, phone, office_name, home_lat, home_lng, landmark, priority, is_vip`
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

REQUIRED_COLUMNS = ("name", "phone", "office_name", "home_lat", "home_lng")
OPTIONAL_COLUMNS = ("landmark", "priority", "is_vip", "night_escort_required")
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

DEFAULT_PRIORITY = 5
MIN_PRIORITY, MAX_PRIORITY = 1, 10

# Matches the api-spec `Phone` pattern.
PHONE_PREFIX = "+"
MIN_PHONE_DIGITS, MAX_PHONE_DIGITS = 8, 15

TRUE_VALUES = frozenset({"true", "yes", "y", "1"})
FALSE_VALUES = frozenset({"false", "no", "n", "0", ""})

#: A row limit, so a mis-uploaded file cannot become a denial of service.
MAX_ROWS = 5000


@dataclass(frozen=True, slots=True)
class RowError:
    row: int
    field: str
    message: str

    def as_dict(self) -> dict[str, object]:
        return {"row": self.row, "field": self.field, "message": self.message}


@dataclass(frozen=True, slots=True)
class ParsedEmployee:
    """One valid CSV row. `office_name` still has to be resolved to an office id."""

    row: int
    name: str
    phone: str
    office_name: str
    home_lat: float
    home_lng: float
    landmark: str | None
    priority: int
    is_vip: bool
    night_escort_required: bool


@dataclass
class ParseResult:
    total_rows: int = 0
    employees: list[ParsedEmployee] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)

    @property
    def valid_rows(self) -> int:
        return len(self.employees)


class ImportFormatError(Exception):
    """The file itself is unusable — not a row problem."""


def parse_csv(content: str) -> ParseResult:
    """Parse and validate every row.

    Every problem row is reported rather than stopping at the first: a client admin
    uploading 500 employees needs the whole list of what to fix, not one line at a time.
    """
    text = content.lstrip("﻿")  # Excel writes a BOM
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise ImportFormatError("The file is empty")

    headers = [(name or "").strip().lower() for name in reader.fieldnames]
    missing = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing:
        raise ImportFormatError(
            "Missing required column(s): "
            + ", ".join(missing)
            + ". Expected header: "
            + ", ".join(ALL_COLUMNS)
        )

    result = ParseResult()
    seen_phones: dict[str, int] = {}

    for index, raw in enumerate(reader, start=2):  # row 1 is the header
        if index - 1 > MAX_ROWS:
            raise ImportFormatError(f"Too many rows; the limit is {MAX_ROWS}")

        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        if not any(row.values()):
            continue  # a blank line is not an error

        result.total_rows += 1
        errors = _validate_row(index, row)

        phone = row.get("phone", "")
        if phone and phone in seen_phones:
            errors.append(
                RowError(index, "phone", f"Duplicate of row {seen_phones[phone]} in this file")
            )
        elif phone:
            seen_phones[phone] = index

        if errors:
            result.errors.extend(errors)
            continue

        result.employees.append(
            ParsedEmployee(
                row=index,
                name=row["name"],
                phone=phone,
                office_name=row["office_name"],
                home_lat=float(row["home_lat"]),
                home_lng=float(row["home_lng"]),
                landmark=row.get("landmark") or None,
                priority=int(row["priority"]) if row.get("priority") else DEFAULT_PRIORITY,
                is_vip=_as_bool(row.get("is_vip", "")),
                night_escort_required=_as_bool(row.get("night_escort_required", "")),
            )
        )

    return result


def _validate_row(index: int, row: dict[str, str]) -> list[RowError]:
    errors: list[RowError] = []

    if not row.get("name"):
        errors.append(RowError(index, "name", "Name is required"))
    elif len(row["name"]) > 200:
        errors.append(RowError(index, "name", "Name is longer than 200 characters"))

    errors.extend(_validate_phone(index, row.get("phone", "")))
    if not row.get("office_name"):
        errors.append(RowError(index, "office_name", "Office name is required"))

    errors.extend(_validate_coordinate(index, "home_lat", row.get("home_lat", ""), 90.0))
    errors.extend(_validate_coordinate(index, "home_lng", row.get("home_lng", ""), 180.0))
    errors.extend(_validate_priority(index, row.get("priority", "")))

    for column in ("is_vip", "night_escort_required"):
        value = row.get(column, "").lower()
        if value and value not in TRUE_VALUES and value not in FALSE_VALUES:
            errors.append(RowError(index, column, f"Expected yes/no, got {row.get(column, '')!r}"))

    return errors


def _validate_phone(index: int, phone: str) -> list[RowError]:
    if not phone:
        return [RowError(index, "phone", "Phone is required")]
    if not phone.startswith(PHONE_PREFIX):
        return [
            RowError(index, "phone", "Phone must be in international format, e.g. +919812345678")
        ]
    digits = phone[1:]
    if not digits.isdigit():
        return [RowError(index, "phone", "Phone must contain digits only after '+'")]
    if digits.startswith("0"):
        return [RowError(index, "phone", "Country code cannot start with 0")]
    if not MIN_PHONE_DIGITS <= len(digits) <= MAX_PHONE_DIGITS:
        return [
            RowError(
                index,
                "phone",
                f"Phone must have {MIN_PHONE_DIGITS}-{MAX_PHONE_DIGITS} digits after '+'",
            )
        ]
    return []


def _validate_coordinate(index: int, column: str, value: str, limit: float) -> list[RowError]:
    if not value:
        return [RowError(index, column, f"{column} is required")]
    try:
        number = float(value)
    except ValueError:
        return [RowError(index, column, f"{column} must be a number, got {value!r}")]
    if not -limit <= number <= limit:
        return [RowError(index, column, f"{column} must be between -{limit} and {limit}")]
    return []


def _validate_priority(index: int, value: str) -> list[RowError]:
    if not value:
        return []
    try:
        priority = int(value)
    except ValueError:
        return [RowError(index, "priority", f"Priority must be a whole number, got {value!r}")]
    if not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        return [
            RowError(
                index,
                "priority",
                f"Priority must be between {MIN_PRIORITY} and {MAX_PRIORITY} (1 is highest)",
            )
        ]
    return []


def _as_bool(value: str) -> bool:
    return value.strip().lower() in TRUE_VALUES
