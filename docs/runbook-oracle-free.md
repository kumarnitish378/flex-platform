# Runbook: staging on an Oracle Cloud Always Free ARM VM

Goal: the whole staging stack (API, GPS ingestor, worker, MQTT over TLS, Caddy with a real HTTPS
certificate, Prometheus/Grafana/Loki, daily backups) on one free **Ampere A1** VM, reachable from a
phone, with **no purchased domain** (a `<ip>.sslip.io` name) and the **public OSM servers** for maps
(no self-hosted tiles or routing).

Nothing here costs money while you stay inside Oracle's Always Free limits (check their current page;
the A1 allowance has been 4 OCPU / 24 GB in total across your instances, and up to 200 GB of block
storage). This runbook uses 2 OCPU / 12 GB.

All images the stack uses have a linux/arm64 build (`scripts/check_image_arch.py`, enforced in CI by the
`arm64` job, which also builds and runs the backend and migrates PostGIS as arm64).

## 0. Decide what this box is

It is **staging**: it has the public internet in front of it, `OTP_PROVIDER=console` (the login code is
printed in the API log, because there is no SMS provider yet, OQ-16) and push notifications off. Use it
with known testers and the demo operator, not with a real operator's riders. The no-OTP "test login" that
`make phone-dev` uses **does not exist here**: the settings refuse it outside dev, test and sim, on purpose.

## 1. Create the VM

1. Sign up at oracle.com/cloud/free. Pick the **home region** carefully - it cannot be changed and A1
   capacity differs by region.
2. Console -> **Compute -> Instances -> Create instance**.
   - Name `smartcab-staging`.
   - **Image:** Canonical **Ubuntu 24.04** (the aarch64 build; it is offered for Ampere shapes).
   - **Shape:** Ampere -> `VM.Standard.A1.Flex`, **2 OCPU, 12 GB**.
   - **Networking:** create a new VCN with a **public subnet**, **assign a public IPv4**.
   - **SSH keys:** paste your public key (the default login user is `ubuntu`).
   - **Boot volume:** 100 GB (free allowance is 200 GB in total).
3. "Out of host capacity" is common for free A1 shapes: try another availability domain, or retry later.
4. **Keep the address.** The certificate, the broker name and the phone build all contain it. Console ->
   Networking -> **Reserved public IPs** -> create one and attach it to the instance's VNIC, otherwise
   a stop/start can change it (and then the name, the certificate and the app build all change too).
5. Oracle can reclaim a free instance it finds idle for a week. Upgrading the account to pay-as-you-go
   removes that risk and still charges nothing inside the free limits; read their current terms.

Write the public address down; below it is `IP` (for example `129.151.20.9`).

## 2. Open ports 22, 80, 443, 8883 - in **both** places

Oracle blocks twice: the cloud firewall in front of the VM, and iptables inside Ubuntu. Both must allow
the port, or it silently times out.

### a. The VCN security list (cloud side)

Console -> Networking -> Virtual cloud networks -> your VCN -> the public subnet -> **Default Security
List** -> **Add ingress rules**. One rule per port: Source CIDR `0.0.0.0/0`, IP protocol **TCP**,
destination port **80**, then **443**, then **8883**. (22 is there already; restrict its source to your
own address if you can.)

| Port | What | Who connects |
|---|---|---|
| 22 | SSH | you |
| 80 | HTTP - Let's Encrypt's challenge and the redirect to HTTPS | Let's Encrypt, browsers |
| 443 | HTTPS - API, WebSocket, Grafana | phones, browsers |
| 8883 | MQTT over TLS - the drivers' GPS | driver phones |

### b. Ubuntu's iptables (VM side)

Oracle's Ubuntu images ship with an iptables policy that rejects everything but SSH. On the VM:

```bash
ssh ubuntu@IP
sudo iptables -L INPUT -n --line-numbers      # note the line of the final REJECT rule (usually 5)
sudo iptables -I INPUT 5 -m state --state NEW -p tcp --dport 80   -j ACCEPT
sudo iptables -I INPUT 5 -m state --state NEW -p tcp --dport 443  -j ACCEPT
sudo iptables -I INPUT 5 -m state --state NEW -p tcp --dport 8883 -j ACCEPT
sudo apt-get install -y iptables-persistent   # answer Yes to saving the current rules, if asked
sudo netfilter-persistent save                # survive a reboot
sudo iptables -L INPUT -n --line-numbers      # the three ACCEPTs sit above the REJECT
```

Docker publishes container ports through its own NAT rules, so this is belt and braces for some
setups - but it is what blocks you when it is missing, so do it. Do **not** use `ufw` here (it fights
the pre-installed rules).

You will check the ports from outside after the stack is up (section 6).

## 3. Install Docker, git, make

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git make python3
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu
exit        # log in again so the group applies
```

Check: `ssh ubuntu@IP`, then `docker run --rm hello-world` and `uname -m` (it says `aarch64`).

## 4. Get the code and configure it

```bash
git clone https://github.com/kumarnitish378/flex-platform.git
cd flex-platform
git checkout dev/overnight-1        # or main once the pull request is merged
```

(A private repository needs a deploy key or a token: `git clone https://<token>@github.com/...`.)

The public name and the secrets:

```bash
make staging-addresses IP=IP          # prints SITE_ADDRESS=... and MONITORING_ADDRESS=...
cp infra/.env.staging.example infra/.env.staging
nano infra/.env.staging
```

In `infra/.env.staging` set:

| Key | Value |
|---|---|
| `SITE_ADDRESS`, `MONITORING_ADDRESS` | the two lines `make staging-addresses` printed, e.g. `129-151-20-9.sslip.io` and `grafana.129-151-20-9.sslip.io` |
| `ACME_EMAIL`, `OSM_CONTACT_EMAIL` | a mailbox somebody reads (the OSM usage policy requires it; the API refuses to start without it) |
| `JWT_SECRET` | `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `POSTGRES_PASSWORD`, `MQTT_INGESTOR_PASSWORD`, `GRAFANA_ADMIN_PASSWORD` | `python3 -c "import secrets; print(secrets.token_urlsafe(24))"` each |
| `DEMO_DATA_ALLOWED` | `true` while you want the demo operator (section 7); remove it before real data |
| everything else | leave as in the example: `OSRM_URL` and `TILES_URL` already point at the public OSM servers (ADR-0010: identifying user agent, 1 request/second, cached) |

`infra/.env.staging` is git-ignored. Never commit it.

## 5. Start the stack

```bash
make staging-up        # builds the image natively on arm64 (several minutes the first time) and starts everything
make staging-ps        # wait until api is (healthy)
make staging-logs      # follow the application logs; Ctrl-C to leave
```

Caddy obtains the certificate for your `sslip.io` name on first boot (it needs ports 80 and 443 open from
the internet); `mqtt-certs` then publishes that same certificate to the broker. If `mqtt-certs` reports
"no certificate", the challenge failed: `docker compose -f infra/docker-compose.staging.yml logs caddy`
(almost always a closed port 80 - recheck section 2).

## 6. Check it from outside (from your laptop)

```text
curl -fsS https://SITE_ADDRESS/health/ready          # {"status":"ok",...}
curl -s -o /dev/null -w "%{http_code}\n" https://SITE_ADDRESS/metrics      # must be 404
python scripts/check_broker_cert.py SITE_ADDRESS     # OK ... valid for SITE_ADDRESS (the check a phone makes)
```

If one times out, that port is blocked in one of the two places in section 2. Grafana is at
`https://MONITORING_ADDRESS` (user `admin`, password `GRAFANA_ADMIN_PASSWORD`).

Let's Encrypt limits certificates per registered domain, and every sslip.io user shares `sslip.io`. If
the limit is hit Caddy falls back to ZeroSSL by itself; if both fail, wait a few hours and run
`make staging-up` again.

## 7. Demo data and the smoke test

On the VM (needs `DEMO_DATA_ALLOWED=true` in `infra/.env.staging`, then `make staging-up` once to pick it up):

```bash
make staging-seed-demo          # the demo operator, 5 cabs, 20 riders, a login per role (idempotent)
```

Logins are the numbers in `docs/runbook-phone-testing.md` section 5 (supervisor `+919100000002`, driver
`+919100000101`, rider `+919100000201`...). Here each login needs a **code**: the app asks for it, the
API logs it. Fetch it on the VM with

```bash
make -s staging-otp PHONE=+919100000101      # prints the newest code sent to that number
```

(the log masks numbers to their last four digits, so the lookup matches on those).

The smoke test drives the real stack from your laptop - the same 22 steps as locally - fetching each
code over SSH. From the repository root on the laptop (backend installed with `make install`):

```text
make smoke ARGS="--api https://SITE_ADDRESS/api/v1 --otp-command \"ssh -i ~/.ssh/KEY ubuntu@IP 'cd flex-platform && make -s staging-otp PHONE={phone}'\""
```

It prints PASS or FAIL per step and takes about four minutes. It publishes GPS over MQTT-TLS on 8883, so
it also proves the broker, its certificate and the ports.

## 8. The phone build

The values are the same shape as `docs/runbook-phone-testing.md`, with HTTPS and the public tiles
(`SITE_ADDRESS` as above):

```text
flutter run \
  --dart-define=API_BASE_URL=https://SITE_ADDRESS/api/v1 \
  --dart-define=MQTT_HOST=SITE_ADDRESS \
  --dart-define=MQTT_PORT=8883 \
  --dart-define=TILES_URL=https://tile.openstreetmap.org/{z}/{x}/{y}.png \
  --dart-define=OSM_CONTACT_EMAIL=you@example.com
```

Leave `APP_TESTING` **out**: it switches the login screen to the no-OTP test login, which this box refuses.
The driver app takes the broker host, port and TLS from `/driver/duty`, so a mismatch there is harmless;
the build values above match it. A release build (`flutter build apk`) uses the same defines.

Log in on the phone with a demo number, read the code with `make -s staging-otp PHONE=...` over SSH, type it in.

## 9. Looking after it

| Task | Command (on the VM, in `flex-platform/`) |
|---|---|
| Update to new code | `git pull && make staging-up` |
| After a certificate renewal (about every 60 days) | `make staging-mqtt-cert` |
| Backups | taken by the `backup` container every 24 hours, 14 days kept, in the `backups` volume on this VM (copy them off the box: a free VM can be reclaimed); `docs/05-engineering/deployment.md` |
| Stop, keeping data | `make staging-down` |
| Is it healthy | `make staging-ps`; Grafana |

Oracle's free block storage and network egress have monthly limits; keep an eye on them in the console.

## 10. When it stops working

| Symptom | Likely cause |
|---|---|
| `curl https://SITE_ADDRESS/...` times out | port 443 not open in the security list, or not in iptables (section 2) |
| Certificate error in the browser or on the phone | the stack came up before port 80 was open; open it, then `docker compose -f infra/docker-compose.staging.yml restart caddy` |
| `make staging-up` fails building on a Python package | out of memory during the build: add 4 GB of swap (`sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`) |
| `mqtt-certs` exits 1 after 300 s | Caddy has no certificate: read the Caddy log (usually a blocked port 80, or the name does not resolve - `getent hosts SITE_ADDRESS` should print your IP) |
| Drivers connect but no GPS | port 8883 blocked, or the broker certificate is stale: `make staging-broker-cert HOST=SITE_ADDRESS` from outside, `make staging-mqtt-cert` on the VM |
| The IP changed after a restart | you did not reserve it (section 1.4): new IP means a new `SITE_ADDRESS`, a new certificate, and a new phone build |
| `seed-demo refuses to run with APP_ENV=staging` | add `DEMO_DATA_ALLOWED=true` to `infra/.env.staging` and `make staging-up` |
| Login says the code is wrong | codes are short-lived and single-use; request a new one and fetch the newest |

## 11. Before real people use it

This box is not production. Still to do (see "Before a real pilot" in `PROGRESS.md`): a real SMS provider
(OQ-16) so nobody needs the log, push notifications (OQ-20), removing `DEMO_DATA_ALLOWED`, an off-site
backup copy, alerts that reach a person, and self-hosted maps once the fleet is large enough that the
public OSM servers' usage policy no longer fits.
