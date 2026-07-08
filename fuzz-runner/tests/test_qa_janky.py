"""The qa-janky reference anchors the QA + performance probes in ISOLATION: it is security-clean but
deliberately bad on quality/perf, so those probes must fire while every security probe stays clean."""
import pathlib

from hacklet_runner.catalog import load_catalog
from hacklet_runner.deploy import SubprocessDeployer
from hacklet_runner.pipeline import run

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_qa_janky_fires_qa_and_perf_but_not_security():
    report = run(SubprocessDeployer(str(ROOT / "references" / "qa-janky" / "app.py")),
                 load_catalog(ROOT / "catalog"))
    fired = {o.probe_id for o in report.outcomes if o.outcome == "slop_detected"}
    # QA + performance jank is caught (non-browser subset; console/a11y/cwv need --browser)
    assert {"qa-crash-001", "qa-crash-007", "qa-errhyg-001"} <= fired          # crash + error hygiene
    assert {"perf-compress-001", "perf-ttfb-001", "perf-load-001"} <= fired    # compression / speed / load
    # but the app is security-clean: NO security probe fires
    sec = {o.probe_id for o in report.outcomes
           if o.bundle == "security" and o.outcome == "slop_detected"}
    assert sec == set(), f"security must be clean on qa-janky, got {sec}"
