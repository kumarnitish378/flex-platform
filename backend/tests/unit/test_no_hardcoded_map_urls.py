"""Guard rail: map service URLs live in configuration, never in code.

ADR-0010 rule 1. This is the test form of the CI `policy-guards` job, so the rule is
enforced locally too — before a hard-coded URL ever reaches a pull request.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

SCANNED_DIRS = ("backend/app", "backend/alembic", "simulator", "app/lib", "infra")
SCANNED_SUFFIXES = {".py", ".dart", ".yml", ".yaml", ".toml", ".conf"}

# Any host that is donated OSM infrastructure.
FORBIDDEN = re.compile(
    r"https?://(?:[a-z]\.)?(?:router\.project-osrm\.org"
    r"|tile\.openstreetmap\.org"
    r"|nominatim\.openstreetmap\.org"
    r"|nominatim\.osm\.org)",
    re.IGNORECASE,
)

# settings.py legitimately holds the defaults these URLs are read from.
ALLOWED_FILES = {
    Path("backend/app/core/settings.py"),
}


def scanned_files() -> list[Path]:
    files: list[Path] = []
    for directory in SCANNED_DIRS:
        root = REPO_ROOT / directory
        if not root.exists():
            continue
        files.extend(
            path for path in root.rglob("*") if path.is_file() and path.suffix in SCANNED_SUFFIXES
        )
    return files


def test_repository_layout_is_as_expected() -> None:
    """If this fails the scan below is silently checking nothing."""
    assert (REPO_ROOT / "backend" / "app").is_dir()
    assert len(scanned_files()) > 5


def test_no_hardcoded_public_osm_urls_in_code() -> None:
    offenders: list[str] = []

    for path in scanned_files():
        relative = path.relative_to(REPO_ROOT)
        if relative in ALLOWED_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for number, line in enumerate(text.splitlines(), start=1):
            code = line.split("#", 1)[0]  # a URL inside a comment is documentation
            if FORBIDDEN.search(code):
                offenders.append(f"{relative}:{number}: {line.strip()}")

    assert not offenders, (
        "Map service URLs must come from configuration (OSRM_URL / TILES_URL), "
        "never be written in code - ADR-0010 rule 1:\n  " + "\n  ".join(offenders)
    )


def test_settings_is_the_only_place_holding_defaults() -> None:
    """The allow-list must stay tiny; widening it is the thing to notice in review."""
    assert sorted(p.as_posix() for p in ALLOWED_FILES) == ["backend/app/core/settings.py"]
