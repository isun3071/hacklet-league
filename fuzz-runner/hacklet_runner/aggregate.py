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


def compute_slop_score(outcomes: list[Outcome], decay: float = CATEGORY_DECAY) -> int:
    fired = [o for o in outcomes if o.outcome == "slop_detected"]

    # Variant group fires once: keep the highest-penalty member per group.
    groups: dict[str, Outcome] = {}
    singles: list[Outcome] = []
    for o in fired:
        if o.variant_group_id:
            cur = groups.get(o.variant_group_id)
            if cur is None or o.penalty > cur.penalty:
                groups[o.variant_group_id] = o
        else:
            singles.append(o)

    # Diminishing returns within each category; categories sum in full.
    by_category: dict[str, list[int]] = defaultdict(list)
    for o in (*singles, *groups.values()):
        by_category[o.category].append(o.penalty)

    total = 0.0
    for penalties in by_category.values():
        for i, penalty in enumerate(sorted(penalties, reverse=True)):
            total += penalty * (decay ** i)
    return round(total)
