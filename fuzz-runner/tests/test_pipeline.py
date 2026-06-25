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
    "sec-xss-001", "sec-secrets-001", "sec-session-001", "sec-session-002", "sec-csrf-001",
    "sec-headers-001", "qa-errhyg-001", "perf-ttfb-001",
    "sec-exposure-001", "sec-exposure-002", "sec-exposure-003",  # .env + .git
    "sec-idor-001",  # horizontal IDOR (self-as-oracle, two accounts)
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
    # sec-headers-001 fans across every discovered route (now 9: + /dom):
    header_hits = [x for x in report.outcomes if x.probe_id == "sec-headers-001"]
    assert len(header_hits) == 9 and all(x.outcome == "slop_detected" for x in header_hits)
    # sec-xss-001 fans across discovered forms (/login, /search, /register, /notes); only /search reflects:
    xss_hits = [x for x in report.outcomes if x.probe_id == "sec-xss-001"]
    assert {x.target for x in xss_hits} == {"/login", "/search", "/register", "/notes"}
    assert any(x.outcome == "slop_detected" and x.target == "/search" for x in xss_hits)
    # sec-secrets-001 finds the leaked AWS key in /config.js (variant-grouped -> one penalty):
    assert any(x.outcome == "slop_detected" and x.target == "/config.js"
               for x in report.outcomes if x.probe_id == "sec-secrets-001")
    # sec-session-001/002 (self-as-oracle): the session cookie lacks HttpOnly and SameSite:
    assert o["sec-session-001"] == "slop_detected" and o["sec-session-002"] == "slop_detected"
    # sec-csrf-001 (self-as-oracle): a cross-site POST is accepted with no token and no SameSite:
    assert o["sec-csrf-001"] == "slop_detected"
    # sec-idor-001 (self-as-oracle, 2 accounts): B can read A's note -> broken access control:
    assert o["sec-idor-001"] == "slop_detected"
    # sec-domxss-001 is browser-only -> N/A in this (no-browser) run; the browser run is in test_browser:
    assert o["sec-domxss-001"] == "not_applicable"
    # sec-exposure-* find the served .env and .git files (.git config+HEAD share a variant group):
    exposure_hits = {x.target for x in report.outcomes
                     if x.probe_id.startswith("sec-exposure") and x.outcome == "slop_detected"}
    assert exposure_hits == {"/.env", "/.git/config", "/.git/HEAD"}
    # sqli 40 + secrets 35 + xss 30 + idor 40 + csrf 25 + errhyg 8 + ttfb 5.
    # session: httponly 20 + samesite 15 diminished -> 20 + 15*.6 = 29.
    # security-headers: 9 fires -> 7.42. crash: 3 fires -> 11.76. exposure: 35 + 30*.6 = 53.
    # Total 40+35+30+40+25+29+8+5+7.42+11.76+53 = 284.18 -> 284.
    assert report.slop_score == 284


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
    assert o["sec-session-001"] == "not_applicable"  # no password form -> can't self-register
    assert o["sec-session-002"] == "not_applicable"
    assert o["sec-csrf-001"] == "not_applicable"
    assert o["sec-idor-001"] == "not_applicable"      # same gate
    assert o["sec-domxss-001"] == "not_applicable"    # browser-gated
    assert report.slop_score == 0
