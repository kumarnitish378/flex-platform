"""Write Mosquitto's password and ACL files from the vehicle registry (R01).

**Why this exists.** B11 generates the exact file contents
(`DutyService.broker_files`) and deliberately stops there: its docstring says "where the
files live and how the broker is told to reload them is deployment configuration, not
application logic". That is correct, and it left `broker_files` with **no caller
anywhere in the system** - so on a real deployment the broker's `password_file` never
existed, Mosquitto refused to start, and the ingestor's own credential was configured in
two places that never met. Found by running the staging stack end to end for the first
time; the same shape as B20, where three sweeps had one caller between them.

Two modes, because the broker needs the files at two different moments:

* `once` runs before Mosquitto starts, so the files exist for it to open. It must not
  need the broker to be up, and it does not.
* `loop` runs beside it and rewrites them when a driver goes on or off duty, then sends
  **SIGHUP**, which is how Mosquitto reloads both files. It shares Mosquitto's PID
  namespace (`pid: "service:mosquitto"` in the compose) so it can signal PID 1 - rather
  than being handed the Docker socket, which would be a far larger grant for a far
  smaller job.

Writes are atomic (write a temp file, then rename) and only happen when the content
actually changed. A half-written password file is one Mosquitto may read mid-reload, and
a needless SIGHUP drops nothing but is noise in the log.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import os
import signal
import sys
from pathlib import Path
from typing import Any

from app import models as _all_models  # noqa: F401 - resolve every FK before querying
from app.core.clock import SystemClock
from app.core.db import create_engine, create_session_factory
from app.core.logging import configure_logging, get_logger
from app.core.settings import Settings, get_settings
from app.domain.mqtt_credentials import hash_password, verify_password

logger = get_logger(__name__)

PASSWORD_FILE = "passwd"
ACL_FILE = "acl"

#: `signal.SIGHUP` is POSIX-only, and mypy runs on whichever machine a developer has -
#: here Windows, where it does not exist. This module only ever runs inside a Linux
#: container, so it is looked up rather than imported: the alternative is a
#: `type: ignore` that would also hide a real typo.
_SIGHUP: Any = getattr(signal, "SIGHUP", None)

#: How often `loop` checks for a change. A driver going on duty waits at most this long
#: for their credential to work, and the check is two queries against an indexed column.
DEFAULT_INTERVAL_SECONDS = 15


async def render(settings: Settings, existing_passwd: str = "") -> tuple[str, str]:
    """The two file contents, including the ingestor's own credential.

    The ingestor is configured by environment variable on both sides - it connects with
    `MQTT_INGESTOR_USER`/`_PASSWORD`, and the broker has to be told the same thing. That
    is this function's job; nothing else closes the loop.

    `existing_passwd` is what is already on disk, so an unchanged password can keep its
    existing hash - see `stable_ingestor_hash`.
    """
    from app.modules.fleet.duty_service import DutyService

    engine = create_engine(settings)
    try:
        async with create_session_factory(engine)() as session:
            service = DutyService(session, SystemClock(), settings)
            passwd, acl = await service.broker_files()
    finally:
        await engine.dispose()

    if settings.mqtt_ingestor_user and settings.mqtt_ingestor_password:
        ingestor_hash = stable_ingestor_hash(settings, existing_passwd)
        ingestor_line = f"{settings.mqtt_ingestor_user}:{ingestor_hash}"
        passwd = (passwd.rstrip("\n") + "\n" + ingestor_line + "\n").lstrip("\n")
        acl = acl.replace("user ingestor", f"user {settings.mqtt_ingestor_user}")
    else:
        # Refusing is better than writing a file that leaves the broker up and the
        # ingestor permanently unable to connect - GPS would stop with no error anywhere
        # except a connection refusal nobody is watching.
        raise SystemExit(
            "MQTT_INGESTOR_USER and MQTT_INGESTOR_PASSWORD must both be set: the broker "
            "runs with allow_anonymous false, so without them the GPS ingestor cannot "
            "authenticate and no position is ever recorded."
        )
    return passwd, acl


def stable_ingestor_hash(settings: Settings, existing_passwd: str) -> str:
    """The ingestor's stored hash, reusing the one on disk when it still matches.

    `hash_password` salts randomly, so hashing the same password twice gives different
    bytes. Re-deriving it on every pass therefore made the file look changed every time:
    the loop rewrote both files and SIGHUPped the broker every fifteen seconds, forever,
    for a configuration nobody had touched. Reuse the stored hash while it still
    verifies, and only mint a new one when the password actually changed.
    """
    prefix = f"{settings.mqtt_ingestor_user}:"
    for line in existing_passwd.splitlines():
        if line.startswith(prefix):
            stored = line[len(prefix) :]
            if verify_password(settings.mqtt_ingestor_password, stored):
                return stored
            break
    return hash_password(settings.mqtt_ingestor_password)


def write_if_changed(directory: Path, name: str, content: str) -> bool:
    """Atomic write. True when the file actually changed."""
    target = directory / name
    if target.exists() and target.read_text(encoding="utf-8") == content:
        return False

    temp = target.with_suffix(".tmp")
    temp.write_text(content, encoding="utf-8")
    # 0640 and not 0644: the password file is hashes, but there is no reason for every
    # process in the container to read it.
    temp.chmod(0o640)
    # No chown here. The deployment makes the directory setgid to the broker's group
    # (see `broker-files-init` in docker-compose.staging.yml), so a file created in it
    # already belongs to that group and 0640 is readable by Mosquitto. Calling chown as
    # a non-root user would only fail and be suppressed, which reads like it worked.
    temp.replace(target)
    return True


def digest(*parts: str) -> str:
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()[:12]


def read_if_present(path: Path) -> str:
    """The file's contents, or empty if it is not there yet."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError):
        return ""


def write_both(directory: Path, passwd: str, acl: str) -> bool:
    """Both files, atomically. Synchronous, and called off the event loop."""
    directory.mkdir(parents=True, exist_ok=True)
    changed = write_if_changed(directory, PASSWORD_FILE, passwd)
    changed |= write_if_changed(directory, ACL_FILE, acl)
    return changed


async def sync(settings: Settings, directory: Path, *, reload_broker: bool) -> bool:
    """One pass. True when something changed."""
    existing = await asyncio.to_thread(read_if_present, directory / PASSWORD_FILE)
    passwd, acl = await render(settings, existing)
    # Off the loop: these are small files, but the loop in `loop` mode also serves the
    # signal handlers, and blocking it on a filesystem that has stalled is how a
    # container stops responding to SIGTERM.
    changed = await asyncio.to_thread(write_both, directory, passwd, acl)

    vehicles = sum(1 for line in passwd.splitlines() if line.startswith("veh-"))
    if changed:
        logger.info(
            "broker_files_written",
            directory=str(directory),
            vehicles=vehicles,
            checksum=digest(passwd, acl),
        )
        if reload_broker:
            signal_broker()
    return changed


def signal_broker() -> None:
    """SIGHUP to PID 1, which reloads `password_file` and `acl_file`.

    Only meaningful when this process shares Mosquitto's PID namespace. If it does not,
    PID 1 is this container's own init and the signal goes nowhere useful, so say so
    rather than pretending the reload happened.
    """
    if _SIGHUP is None:
        logger.warning("broker_reload_unsupported", detail="SIGHUP does not exist here")
        return
    try:
        os.kill(1, _SIGHUP)
    except (ProcessLookupError, PermissionError, OSError) as exc:
        logger.warning("broker_reload_failed", error=f"{type(exc).__name__}: {exc}")
        return
    logger.info("broker_reloaded")


async def run_loop(settings: Settings, directory: Path, interval: float) -> None:
    stopping = asyncio.Event()

    def stop(*_: object) -> None:
        stopping.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError, ValueError):
            asyncio.get_running_loop().add_signal_handler(sig, stop)

    logger.info("broker_sync_started", directory=str(directory), interval_seconds=interval)
    while not stopping.is_set():
        try:
            await sync(settings, directory, reload_broker=True)
        except Exception as exc:  # noqa: BLE001 - a bad pass must not end the loop
            logger.exception("broker_sync_failed", error=type(exc).__name__)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stopping.wait(), timeout=interval)
    logger.info("broker_sync_stopped")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    mode = args[0] if args else "once"

    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)

    directory = Path(settings.mqtt_generated_dir or "/mosquitto/generated")
    interval = float(os.environ.get("BROKER_SYNC_INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS))

    if mode == "once":
        # No reload: `once` runs *before* the broker exists, so there is nothing to
        # signal, and signalling PID 1 of this container would terminate it.
        asyncio.run(sync(settings, directory, reload_broker=False))
        return 0
    if mode == "loop":
        asyncio.run(run_loop(settings, directory, interval))
        return 0

    print(f"usage: python -m app.broker_sync [once|loop]  (got {mode!r})", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
