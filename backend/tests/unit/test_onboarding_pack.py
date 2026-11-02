"""The pilot onboarding pack check (R03), tested without a database.

The rule that matters, as for the employee import: every problem is reported in one pass, so an
operator fixes the whole list instead of running the check forty times.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from app.domain.onboarding_pack import (
    CLIENTS,
    DRIVERS,
    EMPLOYEES,
    OFFICES,
    POLICIES,
    VEHICLES,
    ZONES,
    PackReport,
    parse_boundary,
    validate_pack,
)
from app.onboarding import PackUnreadableError, load_pack, main, render

TEMPLATES = Path(__file__).resolve().parents[3] / "docs" / "onboarding" / "templates"

EMPLOYEE_HEADER = (
    "client_name,name,phone,office_name,home_lat,home_lng,landmark,priority,"
    "is_vip,night_escort_required,gender"
)


def good_pack() -> dict[str, str]:
    """A small pack with nothing wrong and nothing that looks like a template example."""
    return {
        CLIENTS: "name,contact_name,contact_phone\nAcme,Ravi,+919811111111\n",
        OFFICES: "client_name,name,lat,lng,address_text\nAcme,Tower A,28.57,77.32,Sector 62\n",
        ZONES: 'name,boundary\nNorth,"28.64 77.34; 28.64 77.38; 28.60 77.38; 28.60 77.34"\n',
        POLICIES: (
            "client_name,pooling_allowed,employee_opt_out_allowed,night_safety_enabled,"
            "night_start,night_end,max_detour_factor,max_detour_minutes,"
            "pickup_window_minutes,no_show_wait_minutes\n"
            "Acme,yes,yes,yes,20:00,06:00,1.3,15,10,5\n"
        ),
        VEHICLES: (
            "registration_no,model,vehicle_type,seat_capacity,tracker_type\n"
            "DL1CAB1001,Dzire,sedan_4,4,app\n"
            "DL1CAB1002,Innova,suv_6,6,app\n"
        ),
        DRIVERS: (
            "name,phone,licence_last4,vehicle_registration\n"
            "Mohan,+919822222221,1234,DL1CAB1001\n"
            "Sunil,+919822222222,5678,DL1CAB1002\n"
        ),
        EMPLOYEES: (
            f"{EMPLOYEE_HEADER}\n"
            "Acme,Asha,+919833333331,Tower A,28.62,77.36,Metro,5,no,no,female\n"
            "Acme,Bala,+919833333332,Tower A,28.61,77.35,Park,5,no,no,male\n"
        ),
    }


def errors_of(report: PackReport) -> list[str]:
    return [f"{i.file}:{i.row}:{i.field}:{i.message}" for i in report.errors]


def only_error(report: PackReport) -> str:
    assert len(report.errors) == 1, errors_of(report)
    return report.errors[0].message


def with_file(name: str, text: str) -> dict[str, str]:
    pack = good_pack()
    pack[name] = text
    return pack


# --- the happy path and the shipped templates -------------------------------------------


def test_a_clean_pack_has_no_errors_and_no_warnings() -> None:
    report = validate_pack(good_pack())
    assert report.ok
    assert report.issues == []
    assert report.rows[VEHICLES] == 2
    assert report.rows[EMPLOYEES] == 2


def test_the_shipped_templates_pass_and_warn_only_that_they_are_examples() -> None:
    files = {p.name: p.read_text(encoding="utf-8") for p in TEMPLATES.glob("*.csv")}
    assert set(files) == {
        "clients.csv",
        "offices.csv",
        "zones.csv",
        "client_policies.csv",
        "vehicles.csv",
        "drivers.csv",
        "employees.csv",
    }
    report = validate_pack(files)
    assert report.ok, errors_of(report)
    assert report.warnings
    assert all("template example" in w.message for w in report.warnings), report.warnings


def test_the_optional_files_may_be_left_out() -> None:
    pack = good_pack()
    del pack[ZONES], pack[POLICIES]
    report = validate_pack(pack)
    assert report.ok
    assert report.issues == []


# --- the file as a whole ------------------------------------------------------------------


@pytest.mark.parametrize("name", [CLIENTS, OFFICES, VEHICLES, DRIVERS, EMPLOYEES])
def test_a_missing_required_file_is_an_error(name: str) -> None:
    pack = good_pack()
    del pack[name]
    report = validate_pack(pack)
    assert any(i.file == name and "missing" in i.message for i in report.errors)


def test_an_empty_file_and_a_header_only_file_are_errors() -> None:
    assert "empty" in only_error(validate_pack(with_file(VEHICLES, "")))
    header_only = "registration_no,model,vehicle_type,seat_capacity,tracker_type\n"
    report = validate_pack(with_file(VEHICLES, header_only))
    assert any("no rows" in e.message for e in report.errors)


def test_a_missing_column_names_the_column_and_the_expected_header() -> None:
    report = validate_pack(with_file(VEHICLES, "registration_no,model\nDL1CAB1001,Dzire\n"))
    message = next(e.message for e in report.errors if e.file == VEHICLES)
    assert "vehicle_type" in message and "seat_capacity" in message
    assert "Expected header" in message


def test_unknown_files_and_columns_are_warnings_not_errors() -> None:
    pack = good_pack()
    pack["notes.csv"] = "a,b\n1,2\n"
    pack[CLIENTS] = "name,contact_name,contact_phone,favourite_colour\nAcme,Ravi,,blue\n"
    report = validate_pack(pack)
    assert report.ok
    assert {w.file for w in report.warnings} == {"notes.csv", CLIENTS}


def test_an_excel_byte_order_mark_and_blank_lines_are_tolerated() -> None:
    pack = with_file(
        VEHICLES,
        "﻿registration_no,model,vehicle_type,seat_capacity,tracker_type\n"
        "DL1CAB1001,Dzire,sedan_4,4,app\n\n"
        "DL1CAB1002,Innova,suv_6,6,app\n",
    )
    assert validate_pack(pack).ok


# --- clients and offices --------------------------------------------------------------------


def test_a_bad_client_phone_and_a_repeated_client_are_reported() -> None:
    report = validate_pack(
        with_file(CLIENTS, "name,contact_name,contact_phone\nAcme,Ravi,98111\nacme,Ravi,\n")
    )
    messages = errors_of(report)
    assert any("international format" in m for m in messages)
    assert any("repeats row 2" in m for m in messages)


def test_an_office_of_an_unknown_client_and_a_bad_coordinate_are_reported() -> None:
    report = validate_pack(
        with_file(
            OFFICES,
            "client_name,name,lat,lng,address_text\n"
            "Nobody,Tower A,28.57,77.32,\n"
            "Acme,Tower B,95,77.32,\n"
            "Acme,Tower C,abc,77.32,\n",
        )
    )
    messages = errors_of(report)
    assert any("No client 'Nobody'" in m for m in messages)
    assert any("lat must be between" in m for m in messages)
    assert any("lat must be a number" in m for m in messages)


def test_a_client_with_no_office_is_an_error() -> None:
    pack = with_file(CLIENTS, "name\nAcme\nBeta\n")
    report = validate_pack(pack)
    assert any("'beta' has no office" in e.message for e in report.errors)


def test_the_same_office_twice_for_a_client_is_a_duplicate() -> None:
    report = validate_pack(
        with_file(
            OFFICES,
            "client_name,name,lat,lng,address_text\n"
            "Acme,Tower A,28.57,77.32,\nAcme,tower a,28.58,77.33,\n",
        )
    )
    assert "repeats row 2" in only_error(report)


# --- zones ------------------------------------------------------------------------------------


def test_zone_boundaries_parse_with_either_separator() -> None:
    assert parse_boundary("28.1 77.1; 28.2,77.1 ;28.2 77.2") == [
        (28.1, 77.1),
        (28.2, 77.1),
        (28.2, 77.2),
    ]
    with pytest.raises(ValueError, match="not 'lat lng'"):
        parse_boundary("28.1 77.1 5")
    with pytest.raises(ValueError, match="outside the world"):
        parse_boundary("128.1 77.1")


@pytest.mark.parametrize(
    ("boundary", "expected"),
    [
        ("28.1 77.1; 28.2 77.1", "three distinct corners"),
        ("28.1 77.1; 28.1 77.1; 28.2 77.1", "three distinct corners"),
        ("28.0 77.0; 28.1 77.1; 28.1 77.0; 28.0 77.1", "crosses itself"),
        ("north of the river", "not 'lat lng'"),
    ],
)
def test_a_bad_zone_outline_is_reported(boundary: str, expected: str) -> None:
    report = validate_pack(with_file(ZONES, f'name,boundary\nNorth,"{boundary}"\n'))
    assert expected in only_error(report)


def test_an_employee_outside_every_zone_is_a_warning() -> None:
    pack = good_pack()
    pack[EMPLOYEES] += "Acme,Chitra,+919833333333,Tower A,19.07,72.87,,5,no,no,female\n"
    report = validate_pack(pack)
    assert report.ok
    assert [w.row for w in report.warnings] == [4]
    assert "outside every zone" in report.warnings[0].message


# --- client policies ------------------------------------------------------------------------------


def test_policy_values_are_checked_against_the_database_limits() -> None:
    header = good_pack()[POLICIES].splitlines()[0]
    report = validate_pack(
        with_file(
            POLICIES,
            f"{header}\nAcme,maybe,yes,yes,8pm,06:00,3.5,61,31,0\n",
        )
    )
    messages = errors_of(report)
    assert any("pooling_allowed" in m and "yes/no" in m for m in messages)
    assert any("night_start" in m and "time like 20:00" in m for m in messages)
    assert any("max_detour_factor must be between" in m for m in messages)
    assert any("max_detour_minutes must be between" in m for m in messages)
    assert any("pickup_window_minutes must be between" in m for m in messages)
    assert any("no_show_wait_minutes must be between" in m for m in messages)


def test_a_whole_number_column_refuses_a_fraction() -> None:
    header = good_pack()[POLICIES].splitlines()[0]
    report = validate_pack(with_file(POLICIES, f"{header}\nAcme,yes,yes,no,,,,7.5,,\n"))
    assert "whole number" in only_error(report)


def test_a_policy_for_an_unknown_or_repeated_client_is_an_error() -> None:
    header = good_pack()[POLICIES].splitlines()[0]
    report = validate_pack(
        with_file(
            POLICIES,
            f"{header}\nNobody,yes,yes,no,,,,,,\nAcme,yes,yes,no,,,,,,\nacme,yes,yes,no,,,,,,\n",
        )
    )
    messages = errors_of(report)
    assert any("No client 'Nobody'" in m for m in messages)
    assert any("repeats row 3" in m for m in messages)


def test_night_safety_without_a_window_warns() -> None:
    header = good_pack()[POLICIES].splitlines()[0]
    report = validate_pack(with_file(POLICIES, f"{header}\nAcme,yes,yes,yes,,,,,,\n"))
    assert report.ok
    assert "operator's window" in report.warnings[0].message


def test_a_night_client_with_riders_of_unknown_gender_warns() -> None:
    pack = good_pack()
    pack[EMPLOYEES] += "Acme,Dev,+919833333334,Tower A,28.62,77.36,,5,no,no,\n"
    report = validate_pack(pack)
    assert report.ok
    assert "1 employee(s) of 'Acme' have no gender" in report.warnings[0].message


def test_unknown_gender_is_fine_when_the_client_has_no_night_safety() -> None:
    pack = good_pack()
    del pack[POLICIES]
    pack[EMPLOYEES] += "Acme,Dev,+919833333334,Tower A,28.62,77.36,,5,no,no,\n"
    assert validate_pack(pack).issues == []


# --- vehicles and drivers ------------------------------------------------------------------------


def test_every_bad_vehicle_field_is_reported() -> None:
    report = validate_pack(
        with_file(
            VEHICLES,
            "registration_no,model,vehicle_type,seat_capacity,tracker_type\n"
            "DL1CAB1001,Dzire,hatchback,4,app\n"
            "DL1CAB1002,Innova,suv_6,13,app\n"
            "DL1CAB1003,Dzire,sedan_4,four,app\n"
            "DL1CAB1004,Dzire,sedan_4,4,gps\n",
        )
    )
    messages = errors_of(report)
    assert any("Expected one of sedan_4, suv_6, vip" in m for m in messages)
    assert sum("seat_capacity must be a whole number" in m for m in messages) == 2
    assert any("Expected app or esp32" in m for m in messages)


def test_registration_numbers_that_differ_only_in_spacing_are_one_cab() -> None:
    report = validate_pack(
        with_file(
            VEHICLES,
            "registration_no,model,vehicle_type,seat_capacity,tracker_type\n"
            "DL 1C AB 1001,Dzire,sedan_4,4,app\n"
            "dl1c-ab1001,Dzire,sedan_4,4,app\n",
        )
    )
    assert any("repeats row 2" in e.message for e in report.errors)


def test_a_driver_with_a_bad_phone_licence_or_unknown_cab_is_reported() -> None:
    report = validate_pack(
        with_file(
            DRIVERS,
            "name,phone,licence_last4,vehicle_registration\n"
            "Mohan,9822222221,12,DL1CAB1001\n"
            "Sunil,+919822222222,5678,DL1CAB9999\n"
            "Raju,+919822222222,5678,\n",
        )
    )
    messages = errors_of(report)
    assert any("international format" in m for m in messages)
    assert any("last four" in m for m in messages)
    assert any("No vehicle 'DL1CAB9999'" in m for m in messages)
    assert any("Driver phone repeats row 3" in m for m in messages)


def test_a_cab_without_a_driver_is_a_warning() -> None:
    report = validate_pack(
        with_file(
            DRIVERS,
            "name,phone,licence_last4,vehicle_registration\nMohan,+919822222221,1234,dl1cab1001\n",
        )
    )
    assert report.ok
    assert "DL1CAB1002 has no driver" in report.warnings[0].message


# --- employees ------------------------------------------------------------------------------------


def test_employee_rows_follow_the_real_import_rules() -> None:
    pack = good_pack()
    pack[EMPLOYEES] += (
        "Acme,,+919833333339,Tower A,28.62,77.36,,5,no,no,female\n"
        "Acme,Eve,+91983,Tower A,28.62,77.36,,5,no,no,female\n"
        "Acme,Fay,+919833333340,Tower A,28.62,77.36,,15,no,no,female\n"
        "Acme,Gus,+919833333341,Tower A,28.62,77.36,,5,no,no,robot\n"
        "Acme,Hal,+919833333331,Tower A,28.62,77.36,,5,no,no,male\n"
    )
    messages = errors_of(validate_pack(pack))
    assert any("Name is required" in m for m in messages)
    assert any("Phone must have" in m for m in messages)
    assert any("Priority must be between" in m for m in messages)
    assert any("Expected female, male or other" in m for m in messages)
    assert any("Duplicate of row 2" in m for m in messages)


def test_an_employee_of_an_unknown_client_or_office_is_reported() -> None:
    pack = good_pack()
    pack[EMPLOYEES] += (
        "Nobody,Ila,+919833333350,Tower A,28.62,77.36,,5,no,no,female\n"
        "Acme,Jay,+919833333351,Tower Z,28.62,77.36,,5,no,no,male\n"
    )
    messages = errors_of(validate_pack(pack))
    assert any("No client 'Nobody'" in m for m in messages)
    assert any("has no office 'Tower Z'" in m for m in messages)


def test_an_office_of_another_client_does_not_count() -> None:
    pack = good_pack()
    pack[CLIENTS] += "Beta,,\n"
    pack[OFFICES] += "Beta,Tower B,28.50,77.30,\n"
    pack[EMPLOYEES] += "Beta,Ila,+919833333350,Tower A,28.62,77.36,,5,no,no,female\n"
    assert any("Client 'Beta' has no office 'Tower A'" in m for m in errors_of(validate_pack(pack)))


def test_an_employee_sharing_a_driver_phone_is_a_warning() -> None:
    pack = good_pack()
    pack[EMPLOYEES] += "Acme,Kim,+919822222221,Tower A,28.62,77.36,,5,no,no,male\n"
    report = validate_pack(pack)
    assert report.ok
    assert "Same phone as drivers.csv row 2" in report.warnings[0].message


def test_all_problems_come_back_in_one_pass() -> None:
    pack = good_pack()
    pack[VEHICLES] = "registration_no,vehicle_type,seat_capacity\nDL1,coupe,0\n"
    pack[DRIVERS] = "name,phone\nMohan,123\n"
    pack[EMPLOYEES] += "Acme,,x,Nowhere,200,300,,0,,,\n"
    report = validate_pack(pack)
    assert {e.file for e in report.errors} == {VEHICLES, DRIVERS, EMPLOYEES}
    assert len(report.errors) >= 8


# --- the command ------------------------------------------------------------


def write_pack(directory: Path, pack: dict[str, str]) -> None:
    for name, text in pack.items():
        (directory / name).write_text(text, encoding="utf-8")


def test_a_folder_loads_and_main_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_pack(tmp_path, good_pack())
    assert main(["onboarding", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "0 error(s), 0 warning(s) - PASS" in out
    assert "vehicles.csv" in out


def test_main_fails_with_status_1_and_lists_the_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_pack(
        tmp_path, with_file(VEHICLES, "registration_no,vehicle_type,seat_capacity\nX,bus,99\n")
    )
    assert main(["onboarding", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "ERROR   vehicles.csv:2 [vehicle_type]" in out
    assert "FAIL" in out


def test_a_zip_loads_even_with_a_folder_inside_and_mac_litter(tmp_path: Path) -> None:
    archive = tmp_path / "pack.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        for name, text in good_pack().items():
            handle.writestr(f"MyPack/{name}", text)
        handle.writestr("__MACOSX/MyPack/._clients.csv", "garbage")
    files, problems = load_pack(archive)
    assert problems == []
    assert validate_pack(files).issues == []


def test_file_names_are_case_insensitive(tmp_path: Path) -> None:
    pack = {name.upper().replace(".CSV", ".csv"): text for name, text in good_pack().items()}
    write_pack(tmp_path, pack)
    files, _ = load_pack(tmp_path)
    assert validate_pack(files).issues == []


def test_a_file_that_is_not_utf8_is_reported_not_crashed_on(tmp_path: Path) -> None:
    write_pack(tmp_path, good_pack())
    (tmp_path / "clients.csv").write_bytes("name\nCaf\xe9 Cabs\n".encode("cp1252"))
    files, problems = load_pack(tmp_path)
    assert "clients.csv" not in files
    assert "CSV UTF-8" in problems[0].message


def test_a_path_that_is_neither_folder_nor_zip_is_refused(tmp_path: Path) -> None:
    with pytest.raises(PackUnreadableError):
        load_pack(tmp_path / "nothing-here")
    notes = tmp_path / "notes.txt"
    notes.write_text("hi", encoding="utf-8")
    with pytest.raises(PackUnreadableError):
        load_pack(notes)


def test_render_lists_errors_before_warnings() -> None:
    pack = good_pack()
    pack[EMPLOYEES] += "Acme,Kim,+919822222221,Tower A,19.0,72.8,,5,no,no,male\n"
    pack[VEHICLES] = pack[VEHICLES].replace("sedan_4", "coupe")
    text = render(validate_pack(pack))
    assert text.index("ERROR") < text.index("WARNING")
    assert text.rstrip().endswith("FAIL: fix the errors and run again")


def test_an_unreadable_reference_file_does_not_flood_the_others_with_errors() -> None:
    report = validate_pack(with_file(VEHICLES, ""))
    assert [e.file for e in report.errors] == [VEHICLES]
    report = validate_pack(with_file(CLIENTS, ""))
    assert [e.file for e in report.errors] == [CLIENTS]
