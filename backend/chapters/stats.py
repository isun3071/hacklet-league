"""Per-managed-chapter dashboard aggregates — the command-center stats.

Scoped to chapters the user actively manages (owner/organizer), not just ones they created, so
co-organizers see the numbers too. A handful of grouped COUNT queries (one per metric family)
rather than per-chapter fan-out. See DATA_MODEL.md.
"""
from collections import defaultdict

from django.db.models import Count

from events.models import Event, EventParticipant
from rankings.models import Ranking
from rounds.models import Round

from .models import Chapter, ChapterStaff
from .permissions import managed_chapter_ids


def chapter_stats(user):
    ids = managed_chapter_ids(user)
    if not ids:
        return []
    chapters = Chapter.objects.filter(id__in=ids)

    events_total, events_completed = defaultdict(int), defaultdict(int)
    for row in (
        Event.objects.filter(chapter_id__in=ids)
        .values("chapter_id", "status").annotate(c=Count("id"))
    ):
        events_total[row["chapter_id"]] += row["c"]
        if row["status"] == Event.Status.COMPLETED:
            events_completed[row["chapter_id"]] += row["c"]

    players, judges, audience = defaultdict(int), defaultdict(int), defaultdict(int)
    for row in (
        EventParticipant.objects.filter(
            event__chapter_id__in=ids, status=EventParticipant.Status.REGISTERED
        ).values("event__chapter_id", "role").annotate(c=Count("id"))
    ):
        cid = row["event__chapter_id"]
        if row["role"] == EventParticipant.Role.PLAYER:
            players[cid] += row["c"]
        elif row["role"] == EventParticipant.Role.JUDGE:
            judges[cid] += row["c"]
        elif row["role"] == EventParticipant.Role.AUDIENCE:
            audience[cid] += row["c"]

    members, organizers, corps_judges = defaultdict(int), defaultdict(int), defaultdict(int)
    mgr_roles = {ChapterStaff.Role.OWNER.value, ChapterStaff.Role.ORGANIZER.value}
    for s in ChapterStaff.objects.filter(
        chapter_id__in=ids, status=ChapterStaff.Status.ACTIVE
    ).values("chapter_id", "roles"):
        cid = s["chapter_id"]
        members[cid] += 1
        roles = set(s["roles"] or [])
        if mgr_roles & roles:
            organizers[cid] += 1
        if ChapterStaff.Role.JUDGE.value in roles:
            corps_judges[cid] += 1

    rounds_total, rounds_completed = defaultdict(int), defaultdict(int)
    for row in (
        Round.objects.filter(event__chapter_id__in=ids)
        .values("event__chapter_id", "status").annotate(c=Count("id"))
    ):
        cid = row["event__chapter_id"]
        rounds_total[cid] += row["c"]
        if row["status"] == Round.Status.COMPLETED:
            rounds_completed[cid] += row["c"]

    ranked = defaultdict(int)
    for row in (
        Ranking.objects.filter(
            scope=Ranking.Scope.CHAPTER, scope_reference_id__in=ids,
            period=Ranking.Period.ALL_TIME,
        ).values("scope_reference_id").annotate(c=Count("id"))
    ):
        ranked[row["scope_reference_id"]] += row["c"]

    out = [
        {
            "chapter_id": str(c.id),
            "slug": c.slug,
            "name": c.name,
            "tier": c.tier,
            "verification_status": c.verification_status,
            "events_total": events_total[c.id],
            "events_completed": events_completed[c.id],
            "members_total": members[c.id],
            "organizers": organizers[c.id],
            "corps_judges": corps_judges[c.id],
            "players": players[c.id],
            "judges": judges[c.id],
            "audience": audience[c.id],
            "participants_total": players[c.id] + judges[c.id] + audience[c.id],
            "rounds_total": rounds_total[c.id],
            "rounds_completed": rounds_completed[c.id],
            "ranked_players": ranked[c.id],
        }
        for c in chapters
    ]
    out.sort(key=lambda r: r["name"].lower())
    return out
