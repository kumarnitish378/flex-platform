"""Run a command with the project virtual environment's interpreter.

Make targets call `python scripts/venv_exec.py -m pytest ...`. Whichever `python` is on
PATH, the command itself runs under `.venv` when that exists, so `make test` cannot
silently use a system interpreter that has none of the dependencies installed.

Optional first argument `--cwd <dir>` runs the command in that directory (relative to the
repo root).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def venv_python() -> Path | None:
    candidate = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    return candidate if candidate.exists() else None


def main(argv: list[str]) -> int:
    args = argv[1:]
    cwd = ROOT

    if args[:1] == ["--cwd"]:
        if len(args) < 2:
            print("usage: venv_exec.py [--cwd <dir>] <args...>", file=sys.stderr)
            return 2
        cwd = ROOT / args[1]
        args = args[2:]

    if not args:
        print("usage: venv_exec.py [--cwd <dir>] <args...>", file=sys.stderr)
        return 2

    python = venv_python()
    if python is None:
        print(
            "No .venv found - falling back to the current interpreter.\n"
            "Run 'make install' first if imports fail.",
            file=sys.stderr,
        )
        python = Path(sys.executable)

    return subprocess.run([str(python), *args], cwd=cwd).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
