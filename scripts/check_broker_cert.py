"""Check the MQTT broker presents a certificate valid for the name a phone connects to.

    python scripts/check_broker_cert.py 129-151-20-9.sslip.io [8883]

Opens a TLS connection with normal verification (trusted chain AND hostname match, which is what
the phone does) and prints the certificate's names and expiry. Exit 0 only when it validates.
"""

from __future__ import annotations

import socket
import ssl
import sys
from datetime import UTC, datetime


def names_in(certificate: dict[str, object]) -> list[str]:
    """The DNS names a certificate is valid for (its subjectAltName entries)."""
    alt = certificate.get("subjectAltName", ())
    return [value for kind, value in alt if kind == "DNS"] if isinstance(alt, tuple) else []


def check(host: str, port: int = 8883, timeout: float = 10.0) -> dict[str, object]:
    context = ssl.create_default_context()
    with (
        socket.create_connection((host, port), timeout=timeout) as raw,
        context.wrap_socket(raw, server_hostname=host) as tls,
    ):
        certificate = tls.getpeercert()
    return certificate or {}


def main(argv: list[str]) -> int:
    if not argv or len(argv) > 2:
        print("usage: python scripts/check_broker_cert.py <host> [port]", file=sys.stderr)
        return 2
    host, port = argv[0], int(argv[1]) if len(argv) == 2 else 8883
    try:
        certificate = check(host, port)
    except (ssl.SSLError, OSError) as exc:
        print(f"FAIL {host}:{port}: {exc}")
        return 1
    expiry = ssl.cert_time_to_seconds(str(certificate["notAfter"]))
    days = (datetime.fromtimestamp(expiry, UTC) - datetime.now(UTC)).days
    print(f"OK   {host}:{port} valid for {', '.join(names_in(certificate))}; expires in {days} days")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
