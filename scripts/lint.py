"""Run ruff check, ruff format --check and mypy over every Python package in the repo.

Runs each tool over each package that exists, reports a summary, and exits non-zero if
anything failed. Uses .venv when present so `make lint` behaves the same as CI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ["backend", "simulator"]


def interpreter() -> str:
    candidate = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    return str(candidate) if candidate.exists() else sys.executable


def run(python: str, args: list[str], cwd: Path) -> tuple[str, int]:
    label = " ".join(args[1:3])
    print(f"\n=== {cwd.name}: {label} ===", flush=True)
    result = subprocess.run([python, *args], cwd=cwd)
    return f"{cwd.name}: {label}", result.returncode


def main() -> int:
    python = interpreter()
    results: list[tuple[str, int]] = []

    for package in PACKAGES:
        directory = ROOT / package
        if not (directory / "pyproject.toml").exists():
            print(f"skipping {package} (no pyproject.toml yet)")
            continue
        results.append(run(python, ["-m", "ruff", "check", "."], directory))
        results.append(run(python, ["-m", "ruff", "format", "--check", "."], directory))
        results.append(run(python, ["-m", "mypy", "."], directory))

    if not results:
        print("nothing to lint yet")
        return 0

    print("\n=== summary ===")
    for label, code in results:
        print(f"  {'PASS' if code == 0 else 'FAIL'}  {label}")
    return 0 if all(code == 0 for _, code in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
