"""The API contract has to survive being read (`api-spec.yaml`, CLAUDE.md hard rule 1).

`yaml.safe_load` resolves a duplicate key **silently**, keeping the last one. So a
schema defined twice parses, validates, and generates a client - against whichever
definition happened to come second. B24 added a `ModeSetting` that already existed a
hundred lines further down, with a different `weekdays` type, and nothing said a word.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import yaml

SPEC = Path(__file__).resolve().parents[3] / "docs" / "03-architecture" / "api-spec.yaml"


# `yaml` ships no type information, so its SafeLoader is `Any` and mypy cannot check
# a subclass of it. The alternative is not subclassing, which means no duplicate-key
# detection at all.
class _DuplicateKeyLoader(yaml.SafeLoader):  # type: ignore[misc]
    """A loader that refuses what `safe_load` quietly tolerates."""


def _no_duplicates(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False) -> Any:
    seen: Counter[str] = Counter()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        seen[str(key)] += 1
    repeated = sorted(key for key, count in seen.items() if count > 1)
    if repeated:
        mark = node.start_mark
        raise AssertionError(
            f"duplicate keys {repeated} in the mapping starting at line {mark.line + 1}"
        )
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


_DuplicateKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    return loaded


def test_the_spec_has_no_duplicate_keys() -> None:
    """Found the hard way: two `ModeSetting` schemas, one bitmask and one array.

    `safe_load` took the second, so the generated client and the implementation
    disagreed about a field type and both looked correct.
    """
    yaml.load(SPEC.read_text(encoding="utf-8"), Loader=_DuplicateKeyLoader)


def test_every_ref_resolves(spec: dict[str, Any]) -> None:
    """A `$ref` to something that does not exist breaks the client generator, which is
    a long way from where the typo is."""
    text = SPEC.read_text(encoding="utf-8")
    import re

    missing: list[str] = []
    for ref in sorted(set(re.findall(r"#/components/(\w+)/(\w+)", text))):
        section, name = ref
        if name not in (spec.get("components", {}).get(section) or {}):
            missing.append(f"#/components/{section}/{name}")

    assert not missing, f"these $refs point at nothing: {missing}"


def test_every_path_declares_at_least_one_operation(spec: dict[str, Any]) -> None:
    verbs = {"get", "post", "put", "patch", "delete", "head", "options"}
    empty = [path for path, item in spec["paths"].items() if not verbs & set(item)]

    assert not empty, f"these paths define no operation: {empty}"
