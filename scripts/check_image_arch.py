"""Every image a compose file pulls must exist for linux/arm64 (Oracle Cloud Always Free is aarch64).

    python scripts/check_image_arch.py infra/docker-compose.yml infra/docker-compose.staging.yml

Reads the `image:` lines, skips the project's own image (built from `backend/`, and built for arm64
by its own CI job), asks the registry for each manifest (`docker manifest inspect`) and fails naming
every image with no linux/arm64 entry. Exit status 0 when all have one.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

OWN_IMAGES = ("smartcab-backend",)
IMAGE_LINE = re.compile(r"^\s*image:\s*([^\s#]+)", re.MULTILINE)


def images_in(text: str) -> list[str]:
    """Registry images named in a compose file, in order, without repeats; our own build excluded."""
    found: list[str] = []
    for raw in IMAGE_LINE.findall(text):
        image = raw.strip("\"'")
        if image.startswith(OWN_IMAGES) or "${" in image:
            continue
        if image not in found:
            found.append(image)
    return found


def platforms_of(manifest: dict[str, object]) -> set[str]:
    """`os/arch` pairs of a manifest list; a single-image manifest reports its own platform."""
    entries = manifest.get("manifests")
    if isinstance(entries, list):
        return {
            f"{m['platform']['os']}/{m['platform']['architecture']}"
            for m in entries
            if isinstance(m, dict) and m.get("platform", {}).get("architecture") != "unknown"
        }
    if "architecture" in manifest:
        return {f"{manifest.get('os', 'linux')}/{manifest['architecture']}"}
    return set()


def has_arm64(manifest: dict[str, object]) -> bool:
    return "linux/arm64" in platforms_of(manifest)


def inspect(image: str) -> dict[str, object]:
    done = subprocess.run(
        ["docker", "manifest", "inspect", image], capture_output=True, text=True, check=False
    )
    if done.returncode != 0:
        raise RuntimeError(f"{image}: {done.stderr.strip()[:200]}")
    loaded: dict[str, object] = json.loads(done.stdout)
    return loaded


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    wanted: list[str] = []
    for name in argv:
        for image in images_in(Path(name).read_text(encoding="utf-8")):
            if image not in wanted:
                wanted.append(image)
    missing: list[str] = []
    for image in wanted:
        try:
            platforms = platforms_of(inspect(image))
        except (RuntimeError, ValueError) as exc:
            print(f"ERROR {exc}")
            missing.append(image)
            continue
        ok = "linux/arm64" in platforms
        print(f"{'ok   ' if ok else 'MISSING'} {image}  {', '.join(sorted(platforms))}")
        if not ok:
            missing.append(image)
    if missing:
        print(f"\nNo linux/arm64 image for: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
