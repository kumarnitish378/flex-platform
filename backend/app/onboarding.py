"""`make onboard-dry-run FILE=...`: check a pilot onboarding pack and report every problem.

FILE is a folder holding the CSV files, or a .zip of them. Nothing is written anywhere - the
pack is only read and checked (`domain/onboarding_pack.py` has the rules). Exit status 0 means
no errors (warnings may remain), 1 means the pack would not load cleanly, 2 means it could not
be read at all.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from app.domain.onboarding_pack import (
    COLUMNS,
    REQUIRED_FILES,
    Issue,
    PackReport,
    validate_pack,
)


class PackUnreadableError(Exception):
    """The path is not a folder or a zip, or does not exist."""


def load_pack(path: Path) -> tuple[dict[str, str], list[Issue]]:
    """File name -> text, plus problems reading the files themselves (encoding)."""
    raw: dict[str, bytes] = {}
    if path.is_dir():
        for entry in sorted(path.iterdir()):
            if entry.is_file() and entry.suffix.lower() == ".csv":
                raw[entry.name.lower()] = entry.read_bytes()
    elif path.is_file() and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                name = Path(info.filename).name.lower()
                if (
                    not info.is_dir()
                    and name.endswith(".csv")
                    and "__macosx" not in info.filename.lower()
                ):
                    raw[name] = archive.read(info)
    else:
        raise PackUnreadableError(f"{path} is not a folder or a .zip file")

    files: dict[str, str] = {}
    problems: list[Issue] = []
    for name, data in raw.items():
        try:
            files[name] = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            problems.append(
                Issue(
                    name,
                    None,
                    "",
                    "Not UTF-8 text. In Excel use 'Save as -> CSV UTF-8 (Comma delimited)'",
                )
            )
    return files, problems


def render(report: PackReport) -> str:
    lines: list[str] = []
    for name in (*REQUIRED_FILES, *(n for n in COLUMNS if n not in REQUIRED_FILES)):
        if name in report.rows:
            lines.append(f"  {name:22} {report.rows[name]:5} row(s)")
    lines.append("")
    # Errors first, then warnings, each in file order so one file's fixes sit together.
    order = {name: i for i, name in enumerate(COLUMNS)}
    for severity in ("error", "warning"):
        for issue in sorted(
            (i for i in report.issues if i.severity == severity),
            key=lambda i: (order.get(i.file, 99), i.row or 0),
        ):
            lines.append(issue.line())
    lines.append("")
    lines.append(
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s) - "
        + ("PASS: the pack is ready to load" if report.ok else "FAIL: fix the errors and run again")
    )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m app.onboarding <folder-or-zip>", file=sys.stderr)
        return 2
    try:
        files, problems = load_pack(Path(argv[1]))
    except PackUnreadableError as exc:
        print(f"Cannot read the pack: {exc}", file=sys.stderr)
        return 2

    report = validate_pack(files)
    report.issues[:0] = [Issue(p.file, p.row, p.field, p.message, "error") for p in problems]
    print(f"Onboarding pack: {argv[1]}")
    print(render(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
