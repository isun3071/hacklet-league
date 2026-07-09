"""Phase 4 aggregation: sum fired-probe penalties into a slop score, with the composition
dampers from format_spec §4.2.

- **Variant group fires once.** Probes sharing a `variant_group_id` are one logical flaw probed
  via different syntaxes; if any fire, the group contributes its penalty once (its max), never
  once per syntactic variant.
- **Diminishing returns within a category.** Repeated fired instances in the same category have
  decaying marginal penalty (the worst counts full; each additional one at `decay**i`), so a
  class of mistake is noted with breadth rather than multiplied linearly.

Per-bundle ordering (security >> qa > performance) is NOT a runtime multiplier here — it is
encoded in the per-probe penalty magnitudes (calibration), so applying it again would
double-count.
"""
from __future__ import annotations

from collections import defaultdict

from .schema import Outcome

CATEGORY_DECAY = 0.6


def _damped_total(counted: list[Outcome], decay: float) -> float:
    """The composition dampers applied to a list of outcomes treated as fired: a variant group counts
    once (its highest-penalty member), then per-category diminishing returns (sorted desc, penalty *
    decay**i); categories sum in full. Shared by the raw slop score and the per-axis normalization."""
    groups: dict[str, Outcome] = {}
    singles: list[Outcome] = []
    for o in counted:
        if o.variant_group_id:
            cur = groups.get(o.variant_group_id)
            if cur is None or o.penalty > cur.penalty:
                groups[o.variant_group_id] = o
        else:
            singles.append(o)

    by_category: dict[str, list[int]] = defaultdict(list)
    for o in (*singles, *groups.values()):
        by_category[o.category].append(o.penalty)

    total = 0.0
    for penalties in by_category.values():
        for i, penalty in enumerate(sorted(penalties, reverse=True)):
            total += penalty * (decay ** i)
    return total


def compute_slop_score(outcomes: list[Outcome], decay: float = CATEGORY_DECAY) -> int:
    fired = [o for o in outcomes if o.outcome == "slop_detected"]
    return round(_damped_total(fired, decay))


def compute_axis_slop(outcomes: list[Outcome], decay: float = CATEGORY_DECAY) -> dict[str, int]:
    """The damped slop subtotal per bundle (security / qa / performance) — unbounded, lower = better, in
    the SAME units as slop_score. A pure decomposition, not a reweighting: every category belongs to one
    bundle, so the subtotals sum to slop_score. No caps, no axis multipliers, no 0-100 normalization."""
    fired = [o for o in outcomes if o.outcome == "slop_detected"]
    by_bundle: dict[str, list[Outcome]] = defaultdict(list)
    for o in fired:
        by_bundle[o.bundle].append(o)
    return {bundle: round(_damped_total(outs, decay)) for bundle, outs in by_bundle.items()}
