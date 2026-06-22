"""Round scoring engine (format_spec.md §4).

Each judge scores a submission on several dimensions; we panel-average per dimension, then
collapse into two axes:

  - communication_score = mean of the communication dimensions (pitch + cross-examination)
  - engineering_score   = mean of the engineering/product dimensions

In Stage 3 there is no fuzz runner, so the **engineering axis is the manual stand-in for the
Fuzz Score** — judges score it by hand. When the Stage 5 fuzz runner lands, the real Fuzz
Score replaces this axis; the rank-sum math below is unchanged.

Best Overall is the rank-sum composite (§4.3): rank players on each axis (standard
competition / "1224" ranking), sum the two ranks, lowest wins, then progressive tiebreakers
— smallest |engineering_rank − communication_rank|, then best engineering rank, then best
communication rank; a full tie is co-Champions.
"""
from django.db.models import Avg

from .models import Score

COMMUNICATION_DIMENSIONS = [
    Score.ScoreType.PITCH_QUALITY,
    Score.ScoreType.CROSS_EXAMINATION,
]
ENGINEERING_DIMENSIONS = [
    Score.ScoreType.TECHNICAL_EXECUTION,
    Score.ScoreType.CREATIVE_COHERENCE,
    Score.ScoreType.UX_QUALITY,
    Score.ScoreType.DOCUMENTATION,
]


def _mean(values):
    values = [v for v in values if v is not None]
    return float(sum(values) / len(values)) if values else 0.0


def _ranks(pairs, reverse):
    """Standard competition ranking (1-2-2-4) over (id, sort_value). reverse=True → higher
    value is rank 1; reverse=False → lower value is rank 1. Equal values share a rank."""
    ranks = {}
    prev_value = object()  # sentinel so the first item always starts a new rank
    current = 0
    for position, (ident, value) in enumerate(
        sorted(pairs, key=lambda p: p[1], reverse=reverse), start=1
    ):
        if value != prev_value:
            current = position
            prev_value = value
        ranks[ident] = current
    return ranks


def compute_round_results(rnd):
    """Return computed standings + categorical awards for a round. Only submissions with at
    least one score are ranked."""
    submissions = list(rnd.submissions.select_related("player").all())
    averages = {}
    for row in (
        Score.objects.filter(submission__round=rnd)
        .values("submission_id", "score_type")
        .annotate(avg=Avg("value"))
    ):
        averages.setdefault(row["submission_id"], {})[row["score_type"]] = float(row["avg"])

    rows = []
    for sub in submissions:
        dims = averages.get(sub.id)
        if not dims:
            continue
        rows.append(
            {
                "submission": sub,
                "dimensions": dims,
                "communication_score": _mean(
                    [dims[d] for d in COMMUNICATION_DIMENSIONS if d in dims]
                ),
                "engineering_score": _mean(
                    [dims[d] for d in ENGINEERING_DIMENSIONS if d in dims]
                ),
            }
        )

    eng_ranks = _ranks([(r["submission"].id, r["engineering_score"]) for r in rows], reverse=True)
    comm_ranks = _ranks([(r["submission"].id, r["communication_score"]) for r in rows], reverse=True)
    for r in rows:
        sid = r["submission"].id
        r["engineering_rank"] = eng_ranks[sid]
        r["communication_rank"] = comm_ranks[sid]
        r["rank_sum"] = eng_ranks[sid] + comm_ranks[sid]

    overall_ranks = _ranks(
        [
            (
                r["submission"].id,
                (
                    r["rank_sum"],
                    abs(r["engineering_rank"] - r["communication_rank"]),
                    r["engineering_rank"],
                    r["communication_rank"],
                ),
            )
            for r in rows
        ],
        reverse=False,
    )
    for r in rows:
        r["overall_rank"] = overall_ranks[r["submission"].id]
    rows.sort(key=lambda r: r["overall_rank"])

    standings = [
        {
            "submission_id": str(r["submission"].id),
            "player_id": str(r["submission"].player_id),
            "player_display": r["submission"].player.display_name or "",
            "engineering_score": round(r["engineering_score"], 2),
            "communication_score": round(r["communication_score"], 2),
            "dimension_averages": {k: round(v, 2) for k, v in r["dimensions"].items()},
            "engineering_rank": r["engineering_rank"],
            "communication_rank": r["communication_rank"],
            "rank_sum": r["rank_sum"],
            "overall_rank": r["overall_rank"],
        }
        for r in rows
    ]
    return {
        "round_id": str(rnd.id),
        "standings": standings,
        "awards": {
            # People's Hacklet (audience vote) is out of scope until broadcast features.
            "most_resilient": [r["player_id"] for r in standings if r["engineering_rank"] == 1],
            "best_communicator": [r["player_id"] for r in standings if r["communication_rank"] == 1],
            "best_overall": [r["player_id"] for r in standings if r["overall_rank"] == 1],
        },
    }
