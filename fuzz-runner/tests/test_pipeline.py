"""Three-way reference calibration = the runner's regression suite.

The catalog must read slop_detected on the vulnerable app, clean on the hardened app (same
surface), and not_applicable on the minimal app where the surface is absent. If a probe can't
separate those, it isn't honest.
"""
import pathlib

from hacklet_runner.catalog import load_catalog
from hacklet_runner.deploy import SubprocessDeployer
from hacklet_runner.pipeline import run

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
REFS = ROOT / "references"

PROBES = ["sec-sqli-001", "sec-xss-001", "sec-headers-001", "qa-errhyg-001", "perf-ttfb-001"]


def _run(app: str):
    return run(SubprocessDeployer(str(REFS / app / "app.py")), load_catalog(CATALOG))


def test_vulnerable_app_accrues_slop():
    report = _run("vulnerable")
    outcomes = report.by_id
    for probe in PROBES:
        assert outcomes[probe] == "slop_detected", f"{probe} should fire on the vulnerable app"
    assert report.slop_score == 40 + 30 + 3 + 8 + 5  # = 86


def test_hardened_app_is_clean():
    report = _run("hardened")
    outcomes = report.by_id
    for probe in PROBES:
        assert outcomes[probe] == "clean", f"{probe} should be clean on the hardened app"
    assert report.slop_score == 0


def test_minimal_app_resolves_surface_probes_na():
    report = _run("minimal")
    outcomes = report.by_id
    # no form / text input -> the input-dependent probes do not apply
    assert outcomes["sec-sqli-001"] == "not_applicable"
    assert outcomes["sec-xss-001"] == "not_applicable"
    # the universal header probe still applies, and the minimal app sets the header -> clean
    assert outcomes["sec-headers-001"] == "clean"
    assert report.slop_score == 0


def test_discovery_finds_the_login_form():
    report = _run("vulnerable")
    assert report.by_id["sec-sqli-001"] != "not_applicable"
