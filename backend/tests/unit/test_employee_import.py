"""CSV parsing and row validation (B07), tested without a database.

The rule that matters: **every** bad row is reported, not just the first. A client admin
importing 500 employees needs the whole list of what to fix.
"""

from __future__ import annotations

import pytest

from app.domain.employee_import import (
    MAX_ROWS,
    ImportFormatError,
    parse_csv,
)

HEADER = "name,phone,office_name,home_lat,home_lng,landmark,priority,is_vip"
GOOD_ROW = "Asha,+919812345678,B200,28.5123,77.3910,Near temple,3,no"


def csv_of(*rows: str, header: str = HEADER) -> str:
    return "\n".join([header, *rows]) + "\n"


# --- happy path ---------------------------------------------------------------


def test_a_valid_row_parses() -> None:
    result = parse_csv(csv_of(GOOD_ROW))
    assert result.total_rows == 1
    assert result.valid_rows == 1
    assert result.errors == []

    employee = result.employees[0]
    assert employee.name == "Asha"
    assert employee.phone == "+919812345678"
    assert employee.office_name == "B200"
    assert employee.home_lat == 28.5123
    assert employee.priority == 3
    assert employee.is_vip is False
    assert employee.landmark == "Near temple"


def test_optional_columns_may_be_omitted() -> None:
    result = parse_csv(
        csv_of(
            "Asha,+919812345678,B200,28.5,77.3",
            header="name,phone,office_name,home_lat,home_lng",
        )
    )
    assert result.valid_rows == 1
    assert result.employees[0].priority == 5, "the documented default"
    assert result.employees[0].is_vip is False
    assert result.employees[0].landmark is None


def test_headers_are_case_and_space_insensitive() -> None:
    result = parse_csv(
        csv_of(
            "Asha,+919812345678,B200,28.5,77.3",
            header=" Name , PHONE ,Office_Name, home_lat ,home_lng",
        )
    )
    assert result.valid_rows == 1


def test_values_are_trimmed() -> None:
    result = parse_csv(csv_of("  Asha  , +919812345678 , B200 ,28.5,77.3,, , "))
    assert result.employees[0].name == "Asha"
    assert result.employees[0].phone == "+919812345678"


def test_blank_lines_are_ignored() -> None:
    result = parse_csv(csv_of(GOOD_ROW, ",,,,,,,", GOOD_ROW.replace("+9198123456 78", "x")))
    assert result.total_rows == 2


def test_excel_byte_order_mark_is_tolerated() -> None:
    result = parse_csv("﻿" + csv_of(GOOD_ROW))
    assert result.valid_rows == 1


@pytest.mark.parametrize(
    "value,expected",
    [
        ("yes", True),
        ("Y", True),
        ("true", True),
        ("1", True),
        ("no", False),
        ("", False),
        ("FALSE", False),
        ("0", False),
    ],
)
def test_boolean_spellings(value: str, expected: bool) -> None:
    row = f"Asha,+919812345678,B200,28.5,77.3,,,{value}"
    result = parse_csv(csv_of(row))
    assert result.valid_rows == 1
    assert result.employees[0].is_vip is expected


# --- file-level problems --------------------------------------------------------


def test_empty_file_is_rejected() -> None:
    with pytest.raises(ImportFormatError, match="empty"):
        parse_csv("")


def test_missing_required_column_is_rejected() -> None:
    with pytest.raises(ImportFormatError, match="home_lng"):
        parse_csv(csv_of("Asha,+919812345678,B200,28.5", header="name,phone,office_name,home_lat"))


def test_the_error_names_the_expected_header() -> None:
    with pytest.raises(ImportFormatError, match="office_name"):
        parse_csv(csv_of("Asha", header="name"))


def test_a_file_over_the_row_limit_is_rejected() -> None:
    rows = [GOOD_ROW.replace("+919812345678", f"+9198{i:08d}") for i in range(MAX_ROWS + 5)]
    with pytest.raises(ImportFormatError, match="Too many rows"):
        parse_csv(csv_of(*rows))


# --- row-level problems ----------------------------------------------------------


def test_missing_name() -> None:
    result = parse_csv(csv_of(",+919812345678,B200,28.5,77.3"))
    assert result.valid_rows == 0
    assert result.errors[0].field == "name"
    assert result.errors[0].row == 2, "row 1 is the header"


@pytest.mark.parametrize(
    "phone",
    ["", "9812345678", "+91abc", "+0919812345678", "+9112", "+9198123456789012345"],
)
def test_bad_phones(phone: str) -> None:
    result = parse_csv(csv_of(f"Asha,{phone},B200,28.5,77.3"))
    assert result.valid_rows == 0
    assert any(error.field == "phone" for error in result.errors)


def test_phone_must_be_international() -> None:
    result = parse_csv(csv_of("Asha,9812345678,B200,28.5,77.3"))
    assert "international" in result.errors[0].message


@pytest.mark.parametrize(
    ("lat", "lng"),
    [("abc", "77.3"), ("28.5", "abc"), ("128.5", "77.3"), ("28.5", "277.3"), ("", "77.3")],
)
def test_bad_coordinates(lat: str, lng: str) -> None:
    result = parse_csv(csv_of(f"Asha,+919812345678,B200,{lat},{lng}"))
    assert result.valid_rows == 0
    assert any(error.field.startswith("home_") for error in result.errors)


@pytest.mark.parametrize("priority", ["0", "11", "-1", "high"])
def test_bad_priority(priority: str) -> None:
    result = parse_csv(csv_of(f"Asha,+919812345678,B200,28.5,77.3,,{priority},no"))
    assert result.valid_rows == 0
    assert any(error.field == "priority" for error in result.errors)


def test_priority_message_explains_the_scale() -> None:
    result = parse_csv(csv_of("Asha,+919812345678,B200,28.5,77.3,,11,no"))
    assert "1 is highest" in result.errors[0].message


def test_bad_boolean_is_reported() -> None:
    result = parse_csv(csv_of("Asha,+919812345678,B200,28.5,77.3,,3,maybe"))
    assert any(error.field == "is_vip" for error in result.errors)


def test_missing_office_name() -> None:
    result = parse_csv(csv_of("Asha,+919812345678,,28.5,77.3"))
    assert any(error.field == "office_name" for error in result.errors)


def test_duplicate_phone_within_the_file() -> None:
    result = parse_csv(csv_of(GOOD_ROW, GOOD_ROW))
    assert result.total_rows == 2
    assert result.valid_rows == 1
    assert "Duplicate of row 2" in result.errors[0].message


def test_every_problem_in_a_row_is_reported_together() -> None:
    """One pass should tell the admin everything wrong with the row."""
    result = parse_csv(csv_of(",bad-phone,,999,999,,99,maybe"))
    fields = {error.field for error in result.errors}
    assert {"name", "phone", "office_name", "home_lat", "home_lng", "priority", "is_vip"} <= fields


def test_good_and_bad_rows_are_separated() -> None:
    result = parse_csv(
        csv_of(
            GOOD_ROW,
            "Bad,not-a-phone,B200,28.5,77.3",
            "Ravi,+919812345679,B200,28.6,77.4",
        )
    )
    assert result.total_rows == 3
    assert result.valid_rows == 2
    assert len(result.errors) == 1
    assert result.errors[0].row == 3


def test_row_numbers_match_the_spreadsheet() -> None:
    """A report is useless if the row numbers do not match what the admin sees."""
    result = parse_csv(
        csv_of(GOOD_ROW, GOOD_ROW.replace("Asha", "Bad").replace("+919812345678", "x"))
    )
    assert result.errors[0].row == 3


def test_five_hundred_rows_report_errors_per_row() -> None:
    """B07 acceptance: a 500-row file reports errors per row."""
    rows = []
    for index in range(500):
        phone = f"+9198{index:08d}"
        if index % 10 == 0:
            rows.append(f"Broken {index},not-a-phone-{index},B200,28.5,77.3")
        else:
            rows.append(f"Person {index},{phone},B200,28.5,77.3,,5,no")

    result = parse_csv(csv_of(*rows))

    assert result.total_rows == 500
    assert result.valid_rows == 450
    assert len(result.errors) == 50
    assert {error.field for error in result.errors} == {"phone"}
    # Every reported row really is one of the broken ones.
    assert all((error.row - 2) % 10 == 0 for error in result.errors)
