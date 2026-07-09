"""Aggregation dampers (format_spec §4.2 composition rules)."""
from hacklet_runner.aggregate import compute_axis_slop, compute_slop_score
from hacklet_runner.schema import Outcome


def _o(pid, category, penalty, outcome="slop_detected", group=None, bundle="security"):
    return Outcome(
        probe_id=pid, bundle=bundle, category=category,
        outcome=outcome, penalty=penalty, variant_group_id=group,
    )


def test_variant_group_fires_once():
    # two syntactic variants of one logical flaw -> one penalty, not two
    outs = [_o("sqli-1", "sql-injection", 40, group="g1"),
            _o("sqli-2", "sql-injection", 40, group="g1")]
    assert compute_slop_score(outs) == 40


def test_diminishing_returns_within_category():
    # 10 + 10*0.6 + 10*0.36 = 19.6 -> 20
    outs = [_o("a", "crash", 10), _o("b", "crash", 10), _o("c", "crash", 10)]
    assert compute_slop_score(outs) == 20


def test_distinct_categories_sum_in_full():
    outs = [_o("a", "cat1", 10), _o("b", "cat2", 10)]
    assert compute_slop_score(outs) == 20


def test_clean_and_na_contribute_zero():
    outs = [_o("a", "cat1", 10, outcome="clean"),
            _o("b", "cat2", 10, outcome="not_applicable")]
    assert compute_slop_score(outs) == 0


def test_highest_penalty_anchors_a_category():
    # within a category the worst counts full, the cheaper one decays: 40 + 8*0.6 = 44.8 -> 45
    outs = [_o("a", "injection", 8), _o("b", "injection", 40)]
    assert compute_slop_score(outs) == 45


def test_axis_slop_decomposes_and_sums_to_total():
    # per-bundle damped subtotals in the same units; they sum to the total slop score (no reweighting)
    outs = [_o("s1", "sql-injection", 40, bundle="security"),
            _o("q1", "crash", 30, bundle="qa"), _o("q2", "crash", 30, bundle="qa"),  # 30 + 30*0.6 = 48
            _o("p1", "speed", 12, bundle="performance"),
            _o("c1", "cat", 10, outcome="clean", bundle="qa")]  # clean -> contributes nothing
    axis = compute_axis_slop(outs)
    assert axis == {"security": 40, "qa": 48, "performance": 12}
    assert sum(axis.values()) == compute_slop_score(outs)
