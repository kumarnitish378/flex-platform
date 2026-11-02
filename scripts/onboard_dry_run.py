"""`make onboard-dry-run FILE=<folder-or-zip>`: validate a pilot onboarding pack.

The backend runs from `backend/`, so a relative FILE is resolved here, against the directory the
developer typed the command in, before it is handed over.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import venv_exec  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].strip():
        print(
            "usage: make onboard-dry-run FILE=<folder or .zip with the pack's CSV files>\n"
            "       (templates with example rows: docs/onboarding/templates)",
            file=sys.stderr,
        )
        return 2
    pack = Path(argv[1].strip().strip('"')).resolve()
    return venv_exec.main(["venv_exec.py", "--cwd", "backend", "-m", "app.onboarding", str(pack)])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
