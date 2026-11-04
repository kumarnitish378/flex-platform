"""The arm64 guard for compose images (scripts/check_image_arch.py), and the images themselves."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location(
    "check_image_arch", ROOT / "scripts" / "check_image_arch.py"
)
assert _spec and _spec.loader
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

COMPOSE_FILES = [
    ROOT / "infra" / "docker-compose.yml",
    ROOT / "infra" / "docker-compose.staging.yml",
]


def listed(*architectures: str) -> dict[str, object]:
    return {
        "manifests": [{"platform": {"os": "linux", "architecture": a}} for a in architectures]
        + [{"platform": {"os": "unknown", "architecture": "unknown"}}]
    }


def test_a_multi_arch_manifest_with_arm64_passes() -> None:
    assert guard.has_arm64(listed("amd64", "arm64"))


def test_an_amd64_only_manifest_list_fails() -> None:
    assert not guard.has_arm64(listed("amd64"))


def test_a_single_image_manifest_reports_its_own_platform() -> None:
    assert guard.platforms_of({"architecture": "amd64", "os": "linux"}) == {"linux/amd64"}
    assert not guard.has_arm64({"architecture": "amd64", "os": "linux"})


def test_images_are_read_from_a_compose_file_without_our_own_build_or_repeats() -> None:
    text = """
x-backend: &backend
  image: smartcab-backend:${IMAGE_TAG:-local}
services:
  a:
    image: redis:7-alpine   # comment
  b:
    image: redis:7-alpine
  c:
    image: "alpine:3.20"
  d:
    image: caddy:2-alpine
"""
    assert guard.images_in(text) == ["redis:7-alpine", "alpine:3.20", "caddy:2-alpine"]


def test_the_compose_files_name_images_and_none_is_the_amd64_only_postgis() -> None:
    """`postgis/postgis` publishes amd64 only; the multi-arch build is used everywhere instead."""
    named = [image for path in COMPOSE_FILES for image in guard.images_in(path.read_text("utf-8"))]
    assert named, "the guard would check nothing"
    assert not [image for image in named if image.startswith("postgis/postgis")]


def test_no_workflow_or_doc_still_points_at_the_amd64_only_image() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for pattern in (".github/workflows/*.yml", "docs/05-engineering/*.md", "infra/*.yml")
        for path in ROOT.glob(pattern)
        if "postgis/postgis" in path.read_text("utf-8").replace("imresamu/postgis", "")
    ]
    assert offenders == []


def test_ci_builds_and_runs_the_backend_for_arm64() -> None:
    """The regression guard for aarch64 is a CI job, so the job itself must not be dropped."""
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text("utf-8")
    assert "\n  arm64:\n" in ci
    assert "platforms: linux/arm64" in ci
    assert "check_image_arch.py" in ci
    assert "alembic upgrade head" in ci


def test_the_oracle_runbook_uses_commands_and_files_that_exist() -> None:
    """A runbook that names a make target or script that is gone is worse than none."""
    runbook = (ROOT / "docs" / "runbook-oracle-free.md").read_text("utf-8")
    makefile = (ROOT / "Makefile").read_text("utf-8")
    import re

    for target in set(re.findall(r"\bmake (?:-s )?(staging-[a-z-]+|smoke)\b", runbook)):
        assert f"\n{target}:" in makefile, f"make {target} is in the runbook but not the Makefile"
    for script in set(re.findall(r"python scripts/([a-z_]+\.py)", runbook)):
        assert (ROOT / "scripts" / script).exists(), script
    for port in ("22", "80", "443", "8883"):
        assert f"| {port} |" in runbook
