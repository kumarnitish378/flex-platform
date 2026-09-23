"""Fail with a clear message for make targets whose implementing task is not done yet.

Usage: python scripts/not_ready.py <target-name> <task-id>
"""

from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: not_ready.py <target-name> <task-id>", file=sys.stderr)
        return 2
    target, task_id = argv[1], argv[2]
    print(
        f"'make {target}' is not implemented yet.\n"
        f"It is created by task {task_id} in docs/06-phases/phase-1-tasks.md.\n"
        f"Run 'make help' to see which targets are usable right now.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
