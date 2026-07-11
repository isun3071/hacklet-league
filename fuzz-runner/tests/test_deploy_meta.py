"""deploy_and_grade plumbing: a failed clone is a recordable signal (not a crash), and the LLM's
identification (kind/stack/features) is copied onto the record. No network/LLM/Docker."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from deploy_and_grade import CloneError, _record_plan_meta, _trigger_str, clone  # noqa: E402


def test_trigger_str_surfaces_the_payload_but_not_config_checks():
    # a payload-bearing finding shows WHAT triggered it; a config check (headers) has none -> no line
    assert _trigger_str({"via": "malformed-json", "target": "/api/chat", "payload": "{not valid json"}) \
        == "@/api/chat  payload={not valid json"
    assert "technique=error" in _trigger_str({"technique": "error", "where": "query", "param": "q"})
    assert _trigger_str({"status": 200, "elapsed_ms": 17}) == ""      # header/perf check -> no trigger line


def test_clone_raises_cloneerror_instead_of_crashing():
    # a bad repo must raise CloneError (caught + recorded in main), not an uncaught TimeoutExpired/SystemExit
    with pytest.raises(CloneError):
        clone("file:///nonexistent/hl-does-not-exist.git", timeout=20)


def test_record_plan_meta_copies_kind_stack_and_features():
    result = {}
    _record_plan_meta(result, {
        "app_kind": "mobile", "web_gradeable": False, "stack": "iOS SwiftUI app",
        "stack_profile": {"framework": "SwiftUI"}, "expected_surface": {"login": False},
        "features": [{"name": "scan", "kind": "other"}], "dockerfile": "IGNORED"})
    assert result["app_kind"] == "mobile" and result["web_gradeable"] is False
    assert result["features"] == [{"name": "scan", "kind": "other"}]
    assert result["stack_profile"] == {"framework": "SwiftUI"}
    assert "dockerfile" not in result       # only the identification fields ride onto the record
