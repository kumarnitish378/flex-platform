"""Print the available `make` targets, their description and whether they are usable yet.

Descriptions come from the `## <text>` comment directly above each target in the Makefile,
so this help can never drift from the Makefile itself.

Usable yet? Each target names the path it needs (see REQUIREMENTS). A target whose path is
missing still exists, but it belongs to a phase-1 task that is not done — the task ID is
shown so you know what to build first.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# target -> (path that must exist for the target to work, task id that creates it)
REQUIREMENTS: dict[str, tuple[str, str]] = {
    "venv": ("backend/pyproject.toml", "B01"),
    "install": ("backend/pyproject.toml", "B01"),
    "up": ("infra/docker-compose.yml", "I01"),
    "down": ("infra/docker-compose.yml", "I01"),
    "up-maps": ("infra/docker-compose.maps.yml", "I02b"),
    "migrate": ("backend/alembic.ini", "B01"),
    "seed": ("backend/app/cli.py", "B02"),
    "backend-dev": ("backend/app/main.py", "B01"),
    "ingestor": ("backend/app/ingestor", "B12"),
    "worker": ("backend/app/workers/celery_app.py", "B01"),
    "beat": ("backend/app/workers/celery_app.py", "B01"),
    "test": ("backend/pyproject.toml", "B01"),
    "lint": ("backend/pyproject.toml", "B01"),
    "format": ("backend/pyproject.toml", "B01"),
    "api-client": ("app/pubspec.yaml", "A02"),
    "sim-quick": ("simulator/sim/cli.py", "M01"),
    "sim-full": ("simulator/sim/cli.py", "M01"),
    "maps": ("infra/scripts/prepare_maps.sh", "I02b"),
}

TARGET_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):")


def parse_makefile(path: Path) -> list[tuple[str, str]]:
    """Return [(target, description)] in Makefile order."""
    targets: list[tuple[str, str]] = []
    description = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            description = line[3:].strip()
            continue
        match = TARGET_RE.match(line)
        if match and description:
            targets.append((match.group(1), description))
            description = ""
        elif match:
            description = ""
    return targets


def main() -> int:
    makefile = ROOT / "Makefile"
    if not makefile.exists():
        print("Makefile not found at repo root", file=sys.stderr)
        return 1

    targets = parse_makefile(makefile)
    width = max(len(name) for name, _ in targets)

    print("Smart Cab - make targets\n")
    for name, description in targets:
        requirement = REQUIREMENTS.get(name)
        status = "ready"
        if requirement is not None:
            required_path, task_id = requirement
            if not (ROOT / required_path).exists():
                status = f"needs {task_id}"
        print(f"  {name.ljust(width)}  {description}")
        if status != "ready":
            print(f"  {' ' * width}  -> not usable yet: {status} ({requirement[0]} missing)")

    print("\nOn Windows you can use scripts\\dev.ps1 instead, e.g.:  .\\scripts\\dev.ps1 test")
    print("Task IDs refer to docs/06-phases/phase-1-tasks.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
