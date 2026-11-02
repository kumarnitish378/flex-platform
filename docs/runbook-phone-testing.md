# Runbook: testing the app on a real phone

Goal: a phone on your Wi-Fi runs the Flutter app against the stack on your laptop - login without an
SMS, live GPS from the phone to the backend, a driver, a supervisor and a rider all on real screens.

Everything here is **development only**. The test login (no OTP) exists only because
`AUTH_TEST_LOGIN=true` with `APP_ENV=dev`; the backend refuses to start with it in staging or prod.

## 1. Once per machine

1. Docker Desktop must be **running** (it does not start with Windows):
   `C:\Users\nitis\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe`.
2. `make install` (creates `.venv`), and the phone must be on the **same Wi-Fi** as the laptop. Guest
   networks and some corporate Wi-Fi block device-to-device traffic ("client isolation"): if the phone
   cannot open the API docs page in step 4, use your phone's hotspot for the laptop instead.
3. Open the firewall for the three ports (PowerShell **as administrator**; once):

```powershell
New-NetFirewallRule -DisplayName "SmartCab API"   -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
New-NetFirewallRule -DisplayName "SmartCab MQTT"  -Direction Inbound -Protocol TCP -LocalPort 1883 -Action Allow -Profile Private
New-NetFirewallRule -DisplayName "SmartCab Tiles" -Direction Inbound -Protocol TCP -LocalPort 8081 -Action Allow -Profile Private
```

`-Profile Private` means they only apply when Windows has classed the Wi-Fi as **Private**
(Settings -> Network -> Wi-Fi -> your network -> Network profile type). If the network is "Public",
either switch it to Private or drop the `-Profile` argument. Remove the rules when you are done:
`Remove-NetFirewallRule -DisplayName "SmartCab*"`.

## 2. Every session

```powershell
make phone-dev        # or: python scripts/phone_dev.py up   /   .\scripts\dev.ps1 phone-dev
make seed-demo        # idempotent - safe to run every time
```

`make phone-dev` starts Postgres, Redis, the MQTT broker and (if the map data was prepared) the OSRM
and tile servers in Docker, applies migrations, then starts the API on `0.0.0.0:8000`, the GPS
ingestor, a Celery worker and beat. It prints the URLs and the exact build command. Logs are in
`.phone-dev/*.log`. Stop with `make phone-dev-stop`; `make phone-dev-info` prints the URLs again.

### Finding the LAN IP yourself

`make phone-dev` detects it. If it picks the wrong adapter (VPN, virtual switch), find the right one:

```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" } |
  Select-Object InterfaceAlias, IPAddress
```

then force it: `$env:PHONE_DEV_HOST = "192.168.1.57"; make phone-dev`. The address changes when you
change networks or your router renews the lease - re-run `make phone-dev` and **rebuild the app**,
because the address is baked into the build.

## 3. Build the app

`make phone-dev` prints this with your address filled in. For `192.168.1.57`:

```text
flutter run \
  --dart-define=API_BASE_URL=http://192.168.1.57:8000/api/v1 \
  --dart-define=MQTT_HOST=192.168.1.57 \
  --dart-define=MQTT_PORT=1883 \
  --dart-define=TILES_URL=http://192.168.1.57:8081/styles/basic/{z}/{x}/{y}.png \
  --dart-define=OSM_CONTACT_EMAIL=you@example.com \
  --dart-define=APP_TESTING=true
```

- `APP_TESTING=true` turns the login screen into the one-step "type a phone number" test login.
- If self-hosted tiles are not prepared (`infra/maps/tiles/ncr.mbtiles` missing), `TILES_URL` is
  `https://tile.openstreetmap.org/{z}/{x}/{y}.png` - the app sends its own User-Agent and caches
  (usage policy, ADR-0010).
- The phone needs USB debugging on, or build an APK (`flutter build apk --debug` with the same
  defines) and install it.
- Plain `http://` works on Android debug builds. A release build would need HTTPS.

## 4. Check before opening the app

On the **phone's browser** open `http://<LAN IP>:8000/docs`. If it loads, API + firewall + Wi-Fi are fine.
If it does not: wrong IP, firewall rule missing/Public profile, or client isolation (section 1).

## 5. Demo logins (after `make seed-demo`)

Type the phone number on the test login screen. Numbers are fixed so you can memorise them.

| Role | Name | Phone |
|---|---|---|
| operator_admin | Demo Operator Admin | +919100000001 |
| supervisor | Demo Supervisor | +919100000002 |
| client_admin | Demo Client Admin | +919100000003 |
| driver (cab DL01DEMO01) | Demo Driver 1 | +919100000101 |
| driver (cab DL01DEMO02) | Demo Driver 2 | +919100000102 |
| driver (cab DL01DEMO03) | Demo Driver 3 | +919100000103 |
| driver (cab DL01DEMO04) | Demo Driver 4 | +919100000104 |
| driver (cab DL01DEMO05) | Demo Driver 5 | +919100000105 |
| employee (woman) | Demo Rider 01 | +919100000201 |
| employee (man) | Demo Rider 02 | +919100000202 |
| ... employees | Demo Rider 03 - 20 | +919100000203 ... +919100000220 |

Odd-numbered riders are women, even-numbered are men. The demo client has **night safety on**
(20:00-06:00 Asia/Kolkata), the rate is **Rs 8/km**. See section 7 for a script of the night-escort flow.

## 6. A two-phone / one-phone walk-through

1. Phone A: log in as **Demo Rider 01**, request a ride to the office. (One phone is enough: log out and
   in again to switch roles.)
2. Laptop or phone B: log in as **Demo Supervisor**, open the queue, assign Rider 01 to a cab.
3. Phone: log in as **Demo Driver 1**, go on duty (enter the opening odometer), allow location, start the
   trip, mark arrived/picked up, drive (or walk) toward the office, drop, complete, go off duty (closing
   odometer).
4. Supervisor/operator: Reports -> billing shows one row for that cab and day.

The driver app publishes GPS to the broker address it is given by `/driver/duty` (your LAN IP), after
moving about 5 m or every 60 s while still.

## 7. Seeing the night escort gate

The gate fires after 20:00 Asia/Kolkata when a woman would be the only rider. To try it in the daytime,
set the demo client's night window to include now (operator admin: client policy `night_start` /
`night_end`) - or run `python scripts/smoke.py --night`, which does it with a fake clock-free window.
Then request a ride as a woman (odd-numbered rider), assign her alone to a cab, and try to start the
trip as the driver: it is refused until the supervisor confirms "Escort arranged" or "Male co-rider
present" on the trip.

## 8. When something does not work

| Symptom | Likely cause |
|---|---|
| Phone browser cannot open `/docs` | Firewall/profile, client isolation, wrong IP |
| App login says "Not found" | Backend not started with `AUTH_TEST_LOGIN=true` (use `make phone-dev`, not `make backend-dev`) |
| App login says "Invalid phone" | Run `make seed-demo`; use a number from section 5 |
| Cab never appears on the map | Driver not on duty, location permission denied, or port 1883 blocked |
| Cab goes "stale" | Phone suspended the app: keep it in the foreground; the heartbeat is 60 s, stale after 150 s |
| `make phone-dev` says port 8000 in use | `make phone-dev-stop`, or stop the other backend |
| Everything worked, then stopped | The laptop's IP changed - re-run `make phone-dev` and rebuild the app |
