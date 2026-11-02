# Onboarding pack templates

Seven CSV files, each with a header and **example rows** (every example name starts with "Example", and the
check warns until you delete them). Copy this folder, replace the examples with real rows, then check it:

```
make onboard-dry-run FILE=path\to\your\folder-or-zip
```

Full steps: `docs/runbook-pilot-onboarding.md`.

| File | Required | One row per | Columns (bold = must be filled) |
|---|---|---|---|
| `clients.csv` | yes | corporate client | **name**, contact_name, contact_phone |
| `offices.csv` | yes | client office | **client_name**, **name**, **lat**, **lng**, address_text |
| `zones.csv` | no | operating zone | **name**, **boundary** = `lat lng; lat lng; lat lng; ...` (3+ corners, in order, not crossing) |
| `client_policies.csv` | no | client | **client_name**, pooling_allowed, employee_opt_out_allowed, night_safety_enabled, night_start, night_end, max_detour_factor (1.0-3.0), max_detour_minutes (0-60), pickup_window_minutes (0-30), no_show_wait_minutes (1-15) |
| `vehicles.csv` | yes | cab | **registration_no**, model, **vehicle_type** (`sedan_4`, `suv_6`, `vip`), **seat_capacity** (1-12, passenger seats), tracker_type (`app`) |
| `drivers.csv` | yes | driver | **name**, **phone**, licence_last4, vehicle_registration (a registration from `vehicles.csv`) |
| `employees.csv` | yes | rider | **client_name**, **name**, **phone**, **office_name**, **home_lat**, **home_lng**, landmark, priority (1-10, 1 = highest, default 5), is_vip, night_escort_required, gender (`female`, `male`, `other`) |

Rules that apply everywhere:

* Phones are international: `+919812345678`. Latitude/longitude are decimal degrees (right-click a place in
  OpenStreetMap and choose "Show address" to read them). Yes/no columns accept `yes`/`no`/`true`/`false`.
* Save from Excel as **CSV UTF-8 (Comma delimited)**. Keep the header row exactly as in the template.
* Names that link files must match (not case-sensitive): a driver's `vehicle_registration` is a registration in
  `vehicles.csv`; an employee's `client_name` and `office_name` are a client and one of *its* offices.
* `gender` is only used by the night escort rule. Leave it empty if you do not have it - but then that rider is
  never flagged for an escort (the check warns when a night-safety client has riders without it).
* Never put a driver's full licence number anywhere: `licence_last4` is the last four characters only.
