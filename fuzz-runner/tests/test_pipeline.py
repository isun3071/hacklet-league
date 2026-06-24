"""Three-way reference calibration = the runner's regression suite.

The catalog must read slop_detected on the vulnerable app, clean on the hardened app (same
surface), and not_applicable on the minimal app where the surface is absent. This batch also
exercises both aggregation dampers end-to-end: a SQLi variant group (fires once) and a
crash-resistance category (diminishing returns).
"""
import pathlib

from hacklet_runner.catalog import load_catalog
from hacklet_runner.deploy import SubprocessDeployer
from hacklet_runner.pipeline import run

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
REFS = ROOT / "references"

ALL_PROBES = [
    "sec-sqli-001", "sec-sqli-002", "sec-sqli-003",  # variant group
    "sec-xss-001", "sec-headers-001", "qa-errhyg-001", "perf-ttfb-001",
    "qa-crash-001", "qa-crash-002", "qa-crash-003",  # crash-resistance category
]
SURFACE_PROBES = ["sec-sqli-001", "sec-sqli-002", "sec-sqli-003", "sec-xss-001"]


def _run(app: str):
    return run(SubprocessDeployer(str(REFS / app / "app.py")), load_catalog(CATALOG))


def test_vulnerable_app_accrues_slop():
    report = _run("vulnerable")
    o = report.by_id
    for probe in ALL_PROBES:
        assert o[probe] == "slop_detected", f"{probe} should fire on the vulnerable app"
    # sec-headers-001 fans across every discovered route (/, /login, /search, /crash, /heavy):
    header_hits = [x for x in report.outcomes if x.probe_id == "sec-headers-001"]
    assert len(header_hits) == 5 and all(x.outcome == "slop_detected" for x in header_hits)
    # SQLi: 3 variants fire, group collapses to one penalty (40, not 120).
    # security-headers: 5 fan-out fires, diminished: 3 + 3*.6 + 3*.36 + 3*.216 + 3*.1296 = 6.92.
    # crash-resistance: 3 fire, diminished: 6 + 6*.6 + 6*.36 = 11.76. xss 30 + errhyg 8 + ttfb 5.
    # Total 40 + 30 + 6.92 + 8 + 5 + 11.76 = 101.68 -> 102.
    assert report.slop_score == 102


def test_hardened_app_is_clean():
    report = _run("hardened")
    o = report.by_id
    for probe in ALL_PROBES:
        assert o[probe] == "clean", f"{probe} should be clean on the hardened app"
    assert report.slop_score == 0


def test_minimal_app_resolves_surface_probes_na():
    report = _run("minimal")
    o = report.by_id
    for probe in SURFACE_PROBES:  # no form/text input -> input-dependent probes don't apply
        assert o[probe] == "not_applicable"
    assert o["sec-headers-001"] == "clean"  # universal probe applies; minimal sets the header
    assert report.slop_score == 0
