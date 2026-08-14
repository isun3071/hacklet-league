"""The PSI / local-lighthouse accessors must read EITHER shape: PSI nests the Lighthouse report under
`lighthouseResult`, the local CLI returns it top-level. Audit ids are pinned + verified against a live
13.4.1 response in lighthouse.py (they rename between versions); this locks the extraction + the id set."""
from sloptic import lighthouse as lh

_REPORT = {"audits": {"font-display-insight": {"score": 1, "scoreDisplayMode": "metricSavings"},
                      "dom-size-insight": {"score": 1, "scoreDisplayMode": "informative", "numericValue": 660},
                      "largest-contentful-paint": {"score": 0.41, "numericValue": 4338.0}},
           "categories": {"performance": {"score": 0.72}}}


def test_reads_local_cli_top_level_shape():
    assert lh.perf_score(_REPORT) == 0.72
    assert lh.audits(_REPORT)["font-display-insight"]["score"] == 1
    assert lh.metric_ms(_REPORT, "largest-contentful-paint") == 4338.0


def test_reads_psi_wrapped_shape():
    psi = {"lighthouseResult": _REPORT}
    assert lh.perf_score(psi) == 0.72
    assert lh.audits(psi)["dom-size-insight"]["numericValue"] == 660


def test_missing_report_is_empty_not_crash():
    assert lh.audits({}) == {}
    assert lh.perf_score({}) is None
    assert lh.metric_ms({}, "largest-contentful-paint") is None


def test_mapped_audit_ids_are_declared_and_versions_pinned():
    ids = lh.INSIGHT_AUDITS + lh.NUMERIC_AUDITS + lh.METRIC_AUDITS
    assert len(ids) == 19 and all(isinstance(a, str) and a for a in ids)
    assert lh.LIGHTHOUSE_VERSION  # never track "latest" -> audit ids would drift
