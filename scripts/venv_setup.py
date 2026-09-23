"""Create the project virtual environment and install backend + simulator dependencies.

Everything is installed INSIDE .venv at the repo root; nothing is installed system-wide.

    python scripts/venv_setup.py --create    # create .venv if missing
    python scripts/venv_setup.py --install   # create if missing, then install dependencies
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv"


def venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def create() -> None:
    if venv_python().exists():
        print(f"virtual environment already present: {VENV_DIR}")
        return
    print(f"creating virtual environment: {VENV_DIR}")
    venv.EnvBuilder(with_pip=True, upgrade_deps=True).create(VENV_DIR)


def run(args: list[str]) -> None:
    print("$ " + " ".join(str(a) for a in args))
    subprocess.run(args, check=True)


def install() -> None:
    create()
    python = str(venv_python())
    backend = ROOT / "backend"
    simulator = ROOT / "simulator"
    if (backend / "pyproject.toml").exists():
        run([python, "-m", "pip", "install", "-e", f"{backend}[dev]"])
    else:
        print("backend/pyproject.toml missing — skipping backend (task B01)")
    if (simulator / "pyproject.toml").exists():
        run([python, "-m", "pip", "install", "-e", f"{simulator}[dev]"])
    else:
        print("simulator/pyproject.toml missing — skipping simulator (task M01)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create", action="store_true", help="create .venv if missing")
    parser.add_argument("--install", action="store_true", help="create, then install dependencies")
    args = parser.parse_args()

    if args.install:
        install()
    elif args.create:
        create()
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
