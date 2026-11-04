"""Hostnames for a staging box that has an IP address and no purchased domain (sslip.io).

    python scripts/sslip.py 129.151.20.9          # prints the two lines for infra/.env.staging
    make staging-addresses IP=129.151.20.9

`sslip.io` answers DNS for any name that spells an address: `129-151-20-9.sslip.io` resolves to
129.151.20.9, and so does `grafana.129-151-20-9.sslip.io`. Let's Encrypt will issue a certificate for
such a name once the box answers the HTTP challenge on port 80, which gives Caddy a real certificate
without buying anything. The broker's certificate is the one Caddy obtained for SITE_ADDRESS, so its
SAN is the same name and the phone's MQTT host (also SITE_ADDRESS) validates against it.

The dashed form is used: it is one DNS label, so no `1.2.3.4.sslip.io` ambiguity with a real name.
Only a public IPv4 address is accepted - a private one resolves, but no certificate authority can
reach it to validate the name.
"""

from __future__ import annotations

import ipaddress
import sys

DOMAIN = "sslip.io"


def site_address(ip: str) -> str:
    """`129.151.20.9` -> `129-151-20-9.sslip.io`. Raises ValueError for anything unusable."""
    try:
        address = ipaddress.ip_address(ip.strip())
    except ValueError as exc:
        raise ValueError(f"{ip!r} is not an IP address") from exc
    if address.version != 4:
        raise ValueError("sslip.io names are built from an IPv4 address")
    if not address.is_global:
        raise ValueError(
            f"{address} is not a public address; Let's Encrypt cannot reach it to issue a certificate"
        )
    return f"{str(address).replace('.', '-')}.{DOMAIN}"


def monitoring_address(ip: str) -> str:
    """Grafana's own hostname: a label in front of the same name resolves to the same IP."""
    return f"grafana.{site_address(ip)}"


def env_lines(ip: str) -> str:
    return f"SITE_ADDRESS={site_address(ip)}\nMONITORING_ADDRESS={monitoring_address(ip)}\n"


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python scripts/sslip.py <public IPv4>", file=sys.stderr)
        return 2
    try:
        print(env_lines(argv[0]), end="")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
