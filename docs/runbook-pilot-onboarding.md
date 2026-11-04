# Runbook: onboarding a pilot operator

For the platform admin and the operator's owner. Goal: the operator's cabs, drivers, clients and riders are in
the system, a supervisor knows what to press, and the first real day is safe to start. Work top to bottom and
tick the boxes; nothing here needs more than the repository and a running backend.

Status: this kit is built and tested, but **R03 stays open** until a real pilot operator's data has been loaded
in production and supervisors have been trained (see `docs/06-phases/phase-1-tasks.md`). Not yet in the kit:
one-page role guides in Hindi and English, the support contact, and the baseline-vs-pilot dashboard.

## 0. Before you start (decisions, not code)

- [ ] The pilot operator and the corporate client(s) have agreed to the pilot (Phase 0 exit).
- [ ] A **production-like environment exists** with HTTPS, a real SMS provider and push - see "Production
      readiness" in `PROGRESS.md`. Until then use `make phone-dev` and the demo logins; do not invite real riders.
- [ ] You know the **billing rate per km** (Rs 8 so far) and **which client is the default** when a cab serves
      several in a day (OQ-40).
- [ ] You know each client's **night window** (the shipped default is 20:00-06:00) and whether the employer
      wants the night escort rule on.
- [ ] You have said, in writing, what the app does with location data (driver GPS while on duty; no rider
      tracking beyond the trip) - this is the privacy policy URL the Play listing needs.

## 1. Collect the data (the operator's office, about a day)

Copy `docs/onboarding/templates` to a new folder and fill the seven CSVs (column rules: the README in that
folder). Who normally has what:

| File | From | Notes |
|---|---|---|
| `vehicles.csv`, `drivers.csv` | the operator's owner / fleet manager | registration numbers as on the RC; the phone of the person who will actually carry the phone in the cab |
| `clients.csv`, `offices.csv`, `client_policies.csv` | the owner + the client's transport desk | office lat/lng from OpenStreetMap; the policy file is optional - leave a client out to use the operator's defaults |
| `employees.csv` | the client's HR / transport desk | home lat/lng and a landmark per rider; **gender** if the employer wants the escort rule |
| `zones.csv` | the operator's dispatcher | rough areas they already think in (sectors, localities); optional - can be drawn later |

Tips: one person fills the whole pack; delete every "Example" row; keep a copy of what you were given.

## 2. Check it - as often as you like

```
make onboard-dry-run FILE=C:\path\to\pack-folder      (or a .zip of the CSVs)
```

It reads the pack, **changes nothing**, and lists every problem at once as `ERROR file:row [column] message`
or `WARNING ...`, then `PASS` or `FAIL`. Exit status 0 means no errors. Fix the errors, run again, repeat until
PASS. Read the warnings: typical ones are an example row left in, a cab with no driver, a rider outside every
zone, riders of a night-safety client with no gender.

What it checks: required files and columns; phone format and repeats; coordinates; vehicle type and seats;
that every driver, rider and office reference points at a row that exists; zone outlines (3+ corners, not
self-crossing); client policy ranges. The rider rules are the real import's own, so a pack that passes here
passes there.

- [ ] `PASS` with zero errors, and every warning understood.

## 3. Load it (platform admin + operator admin, about half a day)

Order matters - later steps point at earlier rows.

1. [ ] **Create the operator and its first admin** (platform admin, on the server):
       `make create-operator NAME="Sharma Cabs" ADMIN_NAME="R. Sharma" ADMIN_PHONE=+919812345678 RATE=8`
       Safe to repeat. The admin logs in with that phone.
2. [ ] **Settings** (operator admin, A-08): confirm `billing_rate_per_km`, the night window, and the GPS values
       (`gps_distance_filter_m` 5, `gps_heartbeat_seconds` 60, `stale_gps_seconds` 150). Set
       `billing_default_client_id` once there is more than one client.
3. [ ] **Clients and offices** (A-04) from `clients.csv` and `offices.csv`; then each client's **policy**
       from `client_policies.csv` with `PUT /admin/clients/{id}/policy` (the app has no policy screen yet - use
       the API docs page, `https://<host>/docs`, logged in as the operator admin).
4. [ ] **Zones** from `zones.csv` with `POST /admin/zones` (also no app screen yet; `boundary` becomes the list
       of `{lat, lng}` corners).
5. [ ] **Vehicles** (A-02), then **drivers** (A-03), from `vehicles.csv` and `drivers.csv` (the driver form links
       the cab). Drivers appear on the broker only while on duty.
6. [ ] **Riders**: each client admin imports their own rows (L-01 "Import CSV"). The import takes the
       `employees.csv` columns, **one client's rows per file**, so split the file by `client_name` first. The
       import has its own dry-run: read its validation report, fix, then confirm.
7. [ ] **Supervisors and client admins**: invite by phone (A-05).

Thirty-five cabs and a few hundred riders are an afternoon of this. Steps 3-5 are one record at a time; a bulk
loader that reads the pack (and screens for policies and zones) is a follow-up, listed in `PROGRESS.md`.

- [ ] Spot-check: the vehicle count, the driver count, and three riders' home pins on the map.

## 4. Train and rehearse (about half a day)

- [ ] Each supervisor: log in, find the queue, assign a ride by hand, read an alert, use the pause switch.
- [ ] Each driver: log in, go on duty (**type the opening odometer**), accept a trip, mark the stops, go off duty
      (**type the closing odometer**). A driver who cannot grant "location always" will not appear on the map.
- [ ] One rider per client: request a ride, watch the cab.
- [ ] Run `make smoke` against the environment (staging) and keep the PASS output.
- [ ] Rehearsal day: the operator sends 5-10 real trips through the app while still dispatching by phone.

## 5. Go live

- [ ] Mode stays **manual** for week one (supervisors assign), then `semi_auto` per zone (`control-model.md`).
- [ ] A named person at the operator answers "the app does not work"; the support contact is on the role guides.
- [ ] Billing: after the first full day open Reports -> Billing and compare **cab km to the driver's odometer
      and the owner's own record**; resolve any flagged row (gap over 10%).
- [ ] Review after one week: wait times against the Phase 0 baseline, SOS and alerts handled, riders who could
      not log in.

## Appendix: what each tool changes

| Command | Writes to the database? |
|---|---|
| `make onboard-dry-run FILE=...` | never |
| `make create-operator ...` | one operator, one user, one role, optionally the rate; safe to repeat |
| `make seed-demo` | demo data only; **dev, test and sim** environments only |
