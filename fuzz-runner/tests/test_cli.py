"""CLI output renderers — pure text builders, no server/Docker, so they run on the dev box."""
from hacklet_runner.cli import _failed_text, _fmt_evidence, _report_payload, _summary_text
from hacklet_runner.schema import Outcome, Report


def _report() -> Report:
    return Report(slop_score=102, outcomes=[
        Outcome("sec-xss-001", "security", "xss", "slop_detected", 30, target="/search"),
        Outcome("sec-xss-001", "security", "xss", "clean", 0, target="/login"),
        Outcome("sec-headers-001", "security", "security-headers", "slop_detected", 3, target="/"),
        Outcome("perf-ttfb-001", "performance", "speed", "not_applicable", 0, target="/heavy"),
    ])


def test_summary_shows_score_and_tally():
    t = _summary_text(_report(), "references/vulnerable/app.py")
    assert "Slop score: 102" in t
    assert "2 slop · 1 clean · 1 n/a" in t
    assert "security/xss" in t and "security/security-headers" in t


def test_summary_clean_app():
    r = Report(slop_score=0, outcomes=[Outcome("x", "security", "xss", "clean", 0, target="/")])
    t = _summary_text(r, "hardened")
    assert "Slop score: 0" in t
    assert "no slop detected" in t


def test_failed_lists_only_slop():
    t = _failed_text(_report(), "vuln")
    assert "sec-xss-001" in t and "/search" in t
    assert "sec-headers-001" in t
    assert "/login" not in t       # the clean xss outcome is excluded
    assert "perf-ttfb-001" not in t  # the n/a outcome is excluded


def test_report_payload_shape():
    p = _report_payload(_report())
    assert p["slop_score"] == 102
    assert len(p["outcomes"]) == 4
    assert p["outcomes"][0]["probe_id"] == "sec-xss-001"
    assert p["outcomes"][0]["target"] == "/search"


def test_report_payload_carries_evidence():
    # evidence rides on every outcome (clean/n/a too) so a display can show what was measured
    r = Report(slop_score=0, outcomes=[Outcome(
        "perf-loadtime-001", "performance", "speed", "clean", 0, target="/",
        evidence={"load_time_s": 0.35, "ceiling_s": 5.0})])
    ev = _report_payload(r)["outcomes"][0]["evidence"]
    assert ev == {"load_time_s": 0.35, "ceiling_s": 5.0}


def test_fmt_evidence():
    assert _fmt_evidence({"ttfb_s": 0.03, "threshold_s": 0.8}) == "ttfb_s=0.03  threshold_s=0.8"
    assert _fmt_evidence({}) == ""
