"""Every dashboard panel and alert rule queries a metric that exists (R01).

Two failure directions, and both are quiet:

* A panel or rule over a metric nobody emits renders as **zero**, not as "not
  measured" — which is how a blank GPS panel reads as "no cabs reporting" during an
  incident. That is the whole reason R01 built the metrics before the dashboards.
* A metric defined and used by nothing is dead weight that still costs a time series on
  every scrape, forever.

Checked here rather than only in CI so `make test` catches a rename before the push,
and because `infra/` is as much part of the deliverable as `app/`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.core import metrics

REPO_ROOT = Path(__file__).resolve().parents[3]
DASHBOARDS = REPO_ROOT / "infra" / "grafana" / "dashboards"
ALERTS = REPO_ROOT / "infra" / "prometheus" / "alerts.yml"

#: Suffixes Prometheus generates for a histogram, which a query names but the code does
#: not: `smartcab_x_bucket` comes from a histogram registered as `smartcab_x`.
GENERATED_SUFFIXES = re.compile(r"_(bucket|count|sum|total)$")

METRIC_NAME = re.compile(r"smartcab_[a-z_]+")


def defined_metrics() -> set[str]:
    """Metric names as the registry reports them, not as the source spells them.

    Read from the live registry rather than by grepping `metrics.py`: a counter
    registered as `smartcab_http_requests_total` is exported with that name, and only
    the registry knows the suffix rules.
    """
    names: set[str] = set()
    for metric in metrics.REGISTRY.collect():
        names.add(metric.name)
        for sample in metric.samples:
            names.add(sample.name)
    return names


def queried_metrics(text: str) -> set[str]:
    return set(METRIC_NAME.findall(text))


def resolve(name: str, defined: set[str]) -> bool:
    return name in defined or GENERATED_SUFFIXES.sub("", name) in defined


def dashboard_files() -> list[Path]:
    return sorted(DASHBOARDS.glob("*.json"))


def test_there_are_dashboards_to_check() -> None:
    """Without this, every test below passes by finding nothing."""
    assert dashboard_files(), f"no dashboards in {DASHBOARDS}"
    assert ALERTS.exists(), f"no alert rules at {ALERTS}"


@pytest.mark.parametrize("board", dashboard_files(), ids=lambda p: p.name)
def test_every_dashboard_panel_queries_a_metric_that_exists(board: Path) -> None:
    defined = defined_metrics()
    unknown = sorted(
        name
        for name in queried_metrics(board.read_text(encoding="utf-8"))
        if not resolve(name, defined)
    )
    assert not unknown, (
        f"{board.name} queries metrics the backend does not emit: {unknown}. "
        "A panel over a missing metric renders as zero, not as 'not measured'."
    )


def test_every_alert_rule_queries_a_metric_that_exists() -> None:
    defined = defined_metrics()
    unknown = sorted(
        name
        for name in queried_metrics(ALERTS.read_text(encoding="utf-8"))
        if not resolve(name, defined)
    )
    assert not unknown, (
        f"alerts.yml references metrics the backend does not emit: {unknown}. "
        "An alert that can never fire is worse than no alert."
    )


def test_every_metric_is_used_somewhere() -> None:
    """The other direction: a metric nothing reads costs a time series forever."""
    queried: set[str] = set(queried_metrics(ALERTS.read_text(encoding="utf-8")))
    for board in dashboard_files():
        queried |= queried_metrics(board.read_text(encoding="utf-8"))
    # Reduce the queried names to the base names the code registers.
    queried |= {GENERATED_SUFFIXES.sub("", name) for name in queried}

    registered = {
        metric.name for metric in metrics.REGISTRY.collect() if metric.name.startswith("smartcab_")
    }
    unused = sorted(registered - queried)
    assert not unused, (
        f"these metrics are emitted but no dashboard or alert reads them: {unused}. "
        "Add a panel, or stop collecting them."
    )


def test_dashboards_reference_the_provisioned_datasource_uid() -> None:
    """A generated uid makes every panel say "datasource not found" on a rebuilt box."""
    provisioned = (
        REPO_ROOT / "infra" / "grafana" / "provisioning" / "datasources" / "datasources.yml"
    ).read_text(encoding="utf-8")
    uids = set(re.findall(r"^\s*uid:\s*(\S+)\s*$", provisioned, re.MULTILINE))
    assert uids, "the provisioned data sources declare no fixed uid"

    for board in dashboard_files():
        panels = json.loads(board.read_text(encoding="utf-8"))["panels"]
        for panel in panels:
            source = panel.get("datasource")
            if source is None:  # rows carry no datasource
                continue
            assert source["uid"] in uids, (
                f"{board.name} panel {panel.get('title')!r} points at datasource "
                f"{source['uid']!r}, which is not provisioned ({sorted(uids)})"
            )


@pytest.mark.parametrize("board", dashboard_files(), ids=lambda p: p.name)
def test_no_two_panels_occupy_the_same_cell(board: Path) -> None:
    """Grafana honours `gridPos` literally and silently stacks overlapping panels.

    Adding a panel without re-flowing the ones below it therefore hides one behind
    another, and the dashboard looks fine to whoever added it. Found exactly that way:
    two tracking panels landed on `y=23, x=0` and only one was visible.
    """
    occupied: dict[tuple[int, int], str] = {}
    for panel in json.loads(board.read_text(encoding="utf-8"))["panels"]:
        pos = panel["gridPos"]
        title = panel.get("title", panel["type"])
        for column in range(pos["x"], pos["x"] + pos["w"]):
            for row in range(pos["y"], pos["y"] + pos["h"]):
                clash = occupied.get((column, row))
                assert clash is None, (
                    f"{board.name}: {title!r} overlaps {clash!r} at column {column}, row {row}"
                )
                occupied[(column, row)] = title


@pytest.mark.parametrize("board", dashboard_files(), ids=lambda p: p.name)
def test_every_panel_fits_the_grid(board: Path) -> None:
    """Grafana's grid is 24 columns wide; a wider panel is clipped, not scaled."""
    for panel in json.loads(board.read_text(encoding="utf-8"))["panels"]:
        pos = panel["gridPos"]
        assert pos["x"] + pos["w"] <= 24, (
            f"{board.name}: {panel.get('title')!r} runs off the grid (x={pos['x']}, w={pos['w']})"
        )
