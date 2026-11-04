"""Every declared config key is read by something, or says it is Phase 2 (ADR-0023).

`enroute_reuse_max_eta_minutes` was declared in B05 and read by nothing for three
milestones, so a cab 25 minutes off its route was offered exactly like one passing the
rider's door. `alert_wait_minutes` was worse: **all seven scenarios set it**, several with
comments explaining why the value mattered to their assertion, and the platform ignored it.

A key nobody reads is not harmless. It is a promise in the configuration UI that the
product does not keep, and - as ADR-0015 says about scenario features - a run that
measures the wrong thing produces confident wrong answers.

This is a source audit rather than a runtime check, because "is this value ever read" is a
question about the code, not about any particular request.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.domain.config_keys import PHASE_2_KEYS, defaults

#: Where a key could legitimately be read: the backend's own code, and the simulator,
#: which configures operators through `/config` and reads some of the same numbers back.
SOURCE_ROOTS = ("backend/app", "simulator/sim")

REPO_ROOT = Path(__file__).resolve().parents[3]
#: The declaration itself is not a reader.
DECLARATION = "config_keys.py"


def source_files() -> list[Path]:
    found: list[Path] = []
    for root in SOURCE_ROOTS:
        directory = REPO_ROOT / root
        if not directory.exists():  # pragma: no cover - the repo always has both
            continue
        found.extend(
            path
            for path in directory.rglob("*.py")
            if DECLARATION not in path.name and "__pycache__" not in path.parts
        )
    return found


def keys_read_in_source() -> set[str]:
    """Keys that appear as a **quoted string** in the source, i.e. as a lookup.

    Deliberately not a plain substring search. The first version of this guard did that
    and passed happily when the only remaining mention of `alert_wait_minutes` was the
    sentence in a docstring describing it - a guard that cannot fail is worse than no
    guard, because it is believed. Prose in this codebase cites config keys in backticks;
    code reads them as `values["key"]`.
    """
    declared = set(defaults())
    read: set[str] = set()
    for path in source_files():
        text = path.read_text(encoding="utf-8")
        read |= {key for key in declared if f'"{key}"' in text or f"'{key}'" in text}
    return read


def test_every_declared_key_is_read_or_declared_phase_2() -> None:
    declared = set(defaults())
    unread = declared - keys_read_in_source() - set(PHASE_2_KEYS)

    assert not unread, (
        "these config keys are declared and read by nothing: "
        f"{sorted(unread)}. Either read them, or add them to PHASE_2_KEYS with the "
        "reason in the module comment. A key the product ignores is a promise it breaks."
    )


def test_phase_2_keys_are_really_declared() -> None:
    """A typo in the exemption list would silently exempt nothing."""
    unknown = set(PHASE_2_KEYS) - set(defaults())

    assert not unknown, f"PHASE_2_KEYS names keys that do not exist: {sorted(unknown)}"


def test_phase_2_keys_are_not_actually_read() -> None:
    """The exemption list must shrink as the phases land.

    If a key here is now read, the comment above it is out of date and the next reader
    will trust a stale map of what the product does.
    """
    now_read = set(PHASE_2_KEYS) & keys_read_in_source()

    assert not now_read, (
        f"these keys are listed as Phase 2 but something reads them now: {sorted(now_read)}. "
        "Remove them from PHASE_2_KEYS."
    )


def test_the_audit_can_actually_see_a_read() -> None:
    """Guard against the audit passing vacuously - a path mistake would exempt everything."""
    read = keys_read_in_source()

    assert "candidate_max_eta_minutes" in read, "the source scan found nothing; check SOURCE_ROOTS"
    assert len(read) > 5


def test_the_keys_scenarios_configure_are_read() -> None:
    """The specific failure that prompted this: seven scenarios set `alert_wait_minutes`
    and nothing read it."""
    scenarios = REPO_ROOT / "simulator" / "scenarios"
    configured: set[str] = set()
    declared = set(defaults())
    for path in scenarios.glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        block = re.search(r"config_overrides:(.*?)(?:\n\w|\Z)", text, re.DOTALL)
        if block is None:
            continue
        # A YAML mapping key, not a mention in one of the block's comments.
        configured |= {
            key
            for key in declared
            if re.search(rf"^\s+{re.escape(key)}\s*:", block.group(1), re.MULTILINE)
        }

    assert configured, "no scenario sets any config override; this guard would pass vacuously"
    ignored = configured - keys_read_in_source()
    assert not ignored, (
        f"scenarios configure these keys and the platform ignores them: {sorted(ignored)}. "
        "The run would be quoted as though the setting had applied."
    )
