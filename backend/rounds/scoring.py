"""Round scoring engine (format_spec.md §4).

Two independent axes, never summed into one number (§4.1):

  - **Slop Score** — the objective axis. The fuzz runner's damped total, imported onto
    `Submission.slop_score` (import_fuzz_results). Deduction-only, [0, +∞), **lower is better**
    (0 = clean). Ungraded / deploy-failed submissions carry no score and rank **below** every
    graded one (§4.2: a DNF is never a clean zero).
  - **Communication Score** — the human axis, [0, 100], **higher is better**. A weighted
    composite of four judge roles across two rubrics (§4.1): Tester 30, UI/UX 20, General 20,
    Nontech stakeholder 30. Each judge scores the player's pitch + cross-examination; a judge's
    contribution is their mean over those dimensions, roles are combined by ROLE_WEIGHTS
    **normalized over the roles actually present**, and when no judge carries a specialization it
    degrades to a flat mean (so a small/unspecialized panel still scores sensibly). Two judges in
    one role are averaged into that role before weighting — the weight is on the role, not the
    headcount.

The role weights are a single league-wide default here, deliberately NOT a per-event knob:
per-event weights would make a Communication score from one panel mean something different from
another's and break the cross-event comparability the persistent leaderboards rest on. Retuning
them is a versioned league-wide change (the "NFL rule change" model), not an organizer setting.

Best Overall is the rank-sum composite (§4.3): rank on each axis (standard competition / "1224"
ranking, direction per axis), sum the two ranks, lowest wins, then progressive tiebreakers —
smallest |slop_rank − communication_rank|, then best slop rank, then best communication rank; a
full tie is co-Champions.
"""
from events.models import EventParticipant

from .models import Score

# Communication is scored across pitch + cross-examination; each judge scores both (§4.1).
COMMUNICATION_DIMENSIONS = [
    Score.ScoreType.PITCH_QUALITY,
    Score.ScoreType.CROSS_EXAMINATION,
]

# format_spec §4.1 — the default role weighting (70 technical / 30 stakeholder). League-wide;
# see the module docstring for why this is not per-event configurable.
ROLE_WEIGHTS = {
    EventParticipant.JudgeSpecialization.TESTER: 30,
    EventParticipant.JudgeSpecialization.UX_DESIGNER: 20,
    EventParticipant.JudgeSpecialization.GENERAL: 20,
    EventParticipant.JudgeSpecialization.STAKEHOLDER: 30,
}


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


def _communication(judge_rows):
    """Communication score for one submission from its judge score rows.

    Each row is {judge_participant_id, role, score_type, value}. Returns
    (communication_score, dimension_averages). Role-weighted over present roles when every
    scoring judge carries a specialization; otherwise a role-blind flat mean.
    """
    per_judge = {}   # judge_id -> {"role": role, "vals": [comm values]}
    per_dim = {}     # score_type -> [values]  (informational breakdown)
    for row in judge_rows:
        j = per_judge.setdefault(row["judge_participant_id"], {"role": row["role"], "vals": []})
        j["vals"].append(row["value"])
        per_dim.setdefault(row["score_type"], []).append(row["value"])

    judge_means = {jid: (j["role"], _mean(j["vals"])) for jid, j in per_judge.items()}
    dim_averages = {st: _mean(vs) for st, vs in per_dim.items()}
    if not judge_means:
        return 0.0, dim_averages

    # Role-weight only when the panel is fully specialized; a partial/unset panel is not a valid
    # role-weighted panel, so it falls back to a flat mean rather than pretending otherwise.
    if all(role in ROLE_WEIGHTS for role, _ in judge_means.values()):
        by_role = {}
        for role, mean in judge_means.values():
            by_role.setdefault(role, []).append(mean)
        numerator = sum(ROLE_WEIGHTS[role] * _mean(means) for role, means in by_role.items())
        denominator = sum(ROLE_WEIGHTS[role] for role in by_role)
        communication = numerator / denominator if denominator else 0.0
    else:
        communication = _mean([mean for _, mean in judge_means.values()])
    return communication, dim_averages


def compute_round_results(rnd):
    """Return computed standings + categorical awards for a round. A submission is ranked if it
    was graded (has a slop_score) or received any communication score."""
    submissions = list(rnd.submissions.select_related("player").all())

    comm_rows = {}  # submission_id -> [judge rows]
    for row in (
        Score.objects.filter(
            submission__round=rnd, score_type__in=COMMUNICATION_DIMENSIONS
        ).values(
            "submission_id",
            "judge_participant_id",
            "judge_participant__judge_specialization",
            "score_type",
            "value",
        )
    ):
        comm_rows.setdefault(row["submission_id"], []).append({
            "judge_participant_id": row["judge_participant_id"],
            "role": row["judge_participant__judge_specialization"],
            "score_type": row["score_type"],
            "value": float(row["value"]),
        })

    rows = []
    for sub in submissions:
        judge_rows = comm_rows.get(sub.id, [])
        if sub.slop_score is None and not judge_rows:
            continue  # never evaluated on either axis
        communication, dim_averages = _communication(judge_rows)
        rows.append({
            "submission": sub,
            "slop_score": sub.slop_score,  # int, or None for ungraded / deploy-failed
            "communication_score": communication,
            "dimension_averages": dim_averages,
        })

    # Objective axis: lower slop wins; an ungraded/DNF submission (None) sorts last (§4.2).
    slop_ranks = _ranks(
        [
            (r["submission"].id, r["slop_score"] if r["slop_score"] is not None else float("inf"))
            for r in rows
        ],
        reverse=False,
    )
    comm_ranks = _ranks(
        [(r["submission"].id, r["communication_score"]) for r in rows], reverse=True
    )
    for r in rows:
        sid = r["submission"].id
        r["slop_rank"] = slop_ranks[sid]
        r["communication_rank"] = comm_ranks[sid]
        r["rank_sum"] = slop_ranks[sid] + comm_ranks[sid]

    overall_ranks = _ranks(
        [
            (
                r["submission"].id,
                (
                    r["rank_sum"],
                    abs(r["slop_rank"] - r["communication_rank"]),
                    r["slop_rank"],
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
            "slop_score": r["slop_score"],
            "communication_score": round(r["communication_score"], 2),
            "dimension_averages": {k: round(v, 2) for k, v in r["dimension_averages"].items()},
            "slop_rank": r["slop_rank"],
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
            # Slopless Builder — lowest raw Slop Score. Guarded so an all-ungraded field does not
            # hand everyone the award on a tie at infinity.
            "slopless_builder": [
                r["player_id"] for r in standings
                if r["slop_rank"] == 1 and r["slop_score"] is not None
            ],
            "best_communicator": [r["player_id"] for r in standings if r["communication_rank"] == 1],
            "best_overall": [r["player_id"] for r in standings if r["overall_rank"] == 1],
        },
    }
