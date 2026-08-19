"""v2 authority-anchored severity: the range + evidence-ladder resolver (SCORING_V2_SPEC.md).

Covers the resolver (`_severity_penalty`), the model's range-consistency validator, and that a Probe
parses a `severity:` block from the same dict shape catalog.py builds (`Probe(**yaml.safe_load(...))`).
"""
import pytest
from pydantic import ValidationError

from sloptic.pipeline import _severity_penalty
from sloptic.schema import Escalator, Probe, Severity


def _sev(**kw):
    base = dict(cvss="CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N", cvss_score=6.5,
                vrt="P1", range=(30, 85), default=30)
    base.update(kw)
    return Severity(**base)


# --- the resolver: default low, evidence lifts, highest rung wins, clamp ---

def test_default_when_no_evidence():
    # no escalator flag set -> the abstention floor (default = range low)
    sev = _sev(escalators=[Escalator(evidence="cross_user_read", point=55)])
    assert _severity_penalty(sev, {}) == 30


def test_single_escalator_lifts():
    sev = _sev(escalators=[Escalator(evidence="cross_user_read", point=55),
                           Escalator(evidence="sensitive_fields", point=68)])
    assert _severity_penalty(sev, {"cross_user_read": True}) == 55


def test_highest_matched_rung_wins_never_sums():
    sev = _sev(escalators=[Escalator(evidence="cross_user_read", point=55),
                           Escalator(evidence="sensitive_fields", point=68),
                           Escalator(evidence="cross_user_write", point=85)])
    ev = {"cross_user_read": True, "cross_user_write": True}   # two rungs matched
    assert _severity_penalty(sev, ev) == 85                    # the max, not 55+85


def test_top_rung_hits_range_high():
    sev = _sev(escalators=[Escalator(evidence="cross_user_write", point=85)])
    assert _severity_penalty(sev, {"cross_user_write": True}) == 85


def test_falsy_flag_does_not_lift():
    sev = _sev(escalators=[Escalator(evidence="cross_user_read", point=55)])
    assert _severity_penalty(sev, {"cross_user_read": False}) == 30
    assert _severity_penalty(sev, {"cross_user_read": 0}) == 30
    assert _severity_penalty(sev, {"cross_user_read": ""}) == 30


def test_unknown_flag_ignored():
    sev = _sev(escalators=[Escalator(evidence="cross_user_read", point=55)])
    assert _severity_penalty(sev, {"some_other_flag": True}) == 30


# --- the validator: range must be consistent (default and every rung inside [lo, hi]) ---

def test_validator_rejects_default_below_low():
    with pytest.raises(ValidationError):
        Severity(range=(30, 85), default=10)


def test_validator_rejects_default_above_high():
    with pytest.raises(ValidationError):
        Severity(range=(30, 85), default=90)


def test_validator_rejects_escalator_outside_range():
    with pytest.raises(ValidationError):
        Severity(range=(30, 85), default=30, escalators=[Escalator(evidence="x", point=99)])


def test_validator_rejects_inverted_range():
    with pytest.raises(ValidationError):
        Severity(range=(85, 30), default=40)


def test_validator_accepts_default_equal_to_low():
    # the abstention default should equal range low; that is the intended, valid case
    Severity(range=(30, 85), default=30)


# --- Probe parses a severity block from the YAML dict shape catalog.py loads ---

def test_probe_parses_severity_from_yaml_shape():
    data = {
        "id": "sec-idor-001", "bundle": "security", "category": "access-control", "penalty": 30,
        "severity": {
            "cvss": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N", "cvss_score": 6.5,
            "vrt": "P1", "range": [30, 85], "default": 30,
            "escalators": [
                {"evidence": "cross_user_read", "point": 55},
                {"evidence": "sensitive_fields", "point": 68, "vrt_variant": "IDOR view sensitive iterable"},
            ],
        },
    }
    p = Probe(**data)
    assert p.severity is not None
    assert p.severity.range == (30, 85)         # list coerced to tuple[int, int]
    assert len(p.severity.escalators) == 2
    assert p.severity.escalators[1].point == 68
    assert p.severity.escalators[1].vrt_variant == "IDOR view sensitive iterable"
    assert _severity_penalty(p.severity, {"sensitive_fields": True}) == 68


def test_probe_without_severity_is_none():
    # backwards compat: an un-migrated probe (no severity block) parses fine and uses the nominal penalty
    p = Probe(id="sec-x", bundle="security", penalty=40)
    assert p.severity is None


def test_chore_floor_severity_no_escalators():
    # a Tier-4 chore: cvss n/a, tier marked, no ladder -> always the fixed floor
    sev = Severity(cvss="n/a", vrt="P5", range=(8, 8), default=8, tier="chore-floor")
    assert _severity_penalty(sev, {}) == 8
    assert _severity_penalty(sev, {"cross_user_read": True}) == 8   # nothing to lift to


# --- the first migrated class: access-control (sec-idor-001..005), verified end to end ---

def test_idor_class_carries_shared_severity_and_resolves_by_evidence():
    from sloptic.catalog import default_catalog_dir, load_catalog
    by_id = {p.id: p for p in load_catalog(default_catalog_dir())}
    ids = ["sec-idor-001", "sec-idor-002", "sec-idor-003", "sec-idor-004", "sec-idor-005"]
    for pid in ids:
        p = by_id[pid]
        assert p.severity is not None, pid
        assert p.severity.range == (30, 85), pid
        assert p.penalty == 40, f"{pid}: nominal fallback preserved"        # unchanged; severity wins at runtime
        flags = {e.evidence for e in p.severity.escalators}
        assert {"cross_user_read", "sensitive_fields", "bulk_read", "cross_user_write"} <= flags, pid
    # the ladder differentiates by observed impact (was a flat 40 for all five)
    sev = by_id["sec-idor-003"].severity
    assert _severity_penalty(sev, {}) == 30                                                   # abstention floor
    assert _severity_penalty(sev, {"cross_user_read": True}) == 55                            # bare cross-user read
    assert _severity_penalty(sev, {"cross_user_read": True, "sensitive_fields": True}) == 68  # a PII record
    assert _severity_penalty(sev, {"cross_user_read": True, "bulk_read": True}) == 78         # a collection leak
