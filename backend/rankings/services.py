"""Leaderboard aggregation (DATA_MODEL.md Ranking, format_spec §7).

Players accumulate rank points through round placement, weighted by event tier. Rankings are
recomputed from FINALIZED (completed) rounds whenever a round completes or is cancelled — each
recompute fully rebuilds the affected scope from the underlying rounds, so it's idempotent and
self-healing if a result later changes (e.g. a completed round is cancelled).

Scopes built in Stage 3:
  - CHAPTER — one all-time leaderboard per chapter (every event that chapter runs).
  - GLOBAL  — one all-time leaderboard across Tier A chapters ONLY. Credentialing integrity:
              only controlled-workstation Tier A events carry credentialing weight, so only
              they feed the global board (DATA_MODEL.md / format_spec §7).

Regional scope and the current_season period are modeled but deferred (no season entity yet);
the recompute below grows to cover them without schema change.
"""
from django.db import transaction

from chapters.models import Chapter
from events.models import Event
from rounds.models import Round
from rounds.scoring import compute_round_results

from .models import Ranking

# Placement points are weighted by the event's tier (format_spec §7: "weighted by event
# tier"). Higher-stakes events accumulate more credentialing signal per placement.
EVENT_TIER_WEIGHT = {
    Event.EventTier.CHAPTER: 1.0,
    Event.EventTier.REGIONAL: 2.0,
    Event.EventTier.CHAMPIONSHIP: 3.0,
}


def placement_points(overall_rank, field_size):
    """Points a placement earns in one round: 1st of N → N, last → 1. Ties share a rank (1224)
    so they share points. An empty/unscored field earns nothing."""
    if field_size <= 0:
        return 0.0
    return float(max(0, field_size - overall_rank + 1))


def _aggregate(rounds):
    """Roll completed rounds into per-user totals: {user_id: {points, events, last_at}}."""
    totals = {}
    for rnd in rounds:
        standings = compute_round_results(rnd)["standings"]
        field = len(standings)
        weight = EVENT_TIER_WEIGHT.get(rnd.event.event_tier, 1.0)
        when = rnd.build_end_at or rnd.event.actual_end or rnd.created_at
        for s in standings:
            agg = totals.setdefault(
                s["player_id"], {"points": 0.0, "events": set(), "last_at": None}
            )
            agg["points"] += placement_points(s["overall_rank"], field) * weight
            agg["events"].add(str(rnd.event_id))
            if when and (agg["last_at"] is None or when > agg["last_at"]):
                agg["last_at"] = when
    return totals


def _rank_descending(totals):
    """Standard competition ranking (1224) by points desc → {user_id: rank}."""
    ranks = {}
    prev = object()  # sentinel so the first row always opens a new rank
    current = 0
    for position, (uid, agg) in enumerate(
        sorted(totals.items(), key=lambda kv: kv[1]["points"], reverse=True), start=1
    ):
        if agg["points"] != prev:
            current = position
            prev = agg["points"]
        ranks[uid] = current
    return ranks


def _write_scope(scope, scope_reference_id, totals):
    """Idempotently replace the all-time Ranking rows for one scope slot."""
    ranks = _rank_descending(totals)
    keep = set()
    for uid, agg in totals.items():
        Ranking.objects.update_or_create(
            user_id=uid,
            scope=scope,
            scope_reference_id=scope_reference_id,
            period=Ranking.Period.ALL_TIME,
            season_year=None,
            defaults={
                "rank": ranks[uid],
                "rank_points": round(agg["points"], 2),
                "events_competed": len(agg["events"]),
                "last_event_at": agg["last_at"],
            },
        )
        keep.add(uid)
    # Drop anyone who no longer places here (e.g. their only round was cancelled).
    Ranking.objects.filter(
        scope=scope, scope_reference_id=scope_reference_id,
        period=Ranking.Period.ALL_TIME, season_year=None,
    ).exclude(user_id__in=keep).delete()


@transaction.atomic
def recompute_rankings(chapter):
    """Recompute the leaderboards a finished round can move: the round's own chapter board, and
    the global board (rebuilt from all Tier A chapters). Called on round complete/cancel."""
    chapter_rounds = list(
        Round.objects.filter(
            event__chapter=chapter, status=Round.Status.COMPLETED
        ).select_related("event")
    )
    _write_scope(Ranking.Scope.CHAPTER, chapter.id, _aggregate(chapter_rounds))
    recompute_global_rankings()


def recompute_global_rankings():
    """Rebuild the global all-time board from completed rounds at Tier A chapters only."""
    rounds = list(
        Round.objects.filter(
            event__chapter__tier=Chapter.Tier.A, status=Round.Status.COMPLETED
        ).select_related("event")
    )
    _write_scope(Ranking.Scope.GLOBAL, None, _aggregate(rounds))
