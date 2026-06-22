from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from chapters.models import Chapter, ChapterStaff
from events.models import Event, EventParticipant
from rankings.models import Ranking
from rounds.models import Round, Score, Submission

User = get_user_model()


@pytest.mark.django_db
def test_create_ranking():
    user = User.objects.create_user(email="r@example.com", password="pw")
    ranking = Ranking.objects.create(
        user=user, scope="chapter", period="all_time", rank=1, rank_points=100,
    )
    assert ranking.rank == 1
    assert user.rankings.count() == 1


# ===========================================================================
# increment 5 — rankings + leaderboards
# ===========================================================================

def _client(user=None):
    c = APIClient()
    if user:
        c.force_authenticate(user)
    return c


def _scored_round(tier=Chapter.Tier.C, verified=True, event_tier=Event.EventTier.CHAPTER,
                  slug="bu"):
    """A round with two scored submissions (A strictly beats B) ready to complete.

    Returns a dict with the manager, chapter, event, round, and the two players."""
    mgr = User.objects.create_user(email=f"mgr-{slug}@example.com", password="pw")
    chapter = Chapter.objects.create(
        name=slug.upper(), slug=slug, created_by=mgr, tier=tier,
        verification_status=(
            Chapter.VerificationStatus.VERIFIED if verified
            else Chapter.VerificationStatus.PENDING
        ),
    )
    ChapterStaff.objects.create(
        user=mgr, chapter=chapter,
        roles=[ChapterStaff.Role.OWNER], status=ChapterStaff.Status.ACTIVE,
    )
    start = timezone.now() + timedelta(days=1)
    event = Event.objects.create(
        chapter=chapter, name="E", slug="e", created_by=mgr, event_tier=event_tier,
        scheduled_start=start, scheduled_end=start + timedelta(hours=2),
    )
    rnd = Round.objects.create(event=event, round_number=1)
    judge_user = User.objects.create_user(email=f"j-{slug}@example.com", password="pw")
    judge = EventParticipant.objects.create(
        event=event, user=judge_user, role="judge", source="corps", status="registered",
    )
    players = {}
    for key, email, scores in (
        ("a", f"a-{slug}@example.com", {"technical_execution": 90, "pitch_quality": 90,
                                         "cross_examination": 90}),
        ("b", f"b-{slug}@example.com", {"technical_execution": 60, "pitch_quality": 60,
                                         "cross_examination": 60}),
    ):
        user = User.objects.create_user(email=email, password="pw")
        EventParticipant.objects.create(
            event=event, user=user, role="player", source="applied", status="registered",
        )
        sub = Submission.objects.create(round=rnd, player=user, status="submitted")
        for score_type, value in scores.items():
            Score.objects.create(
                submission=sub, judge_participant=judge, score_type=score_type, value=value,
            )
        players[key] = user
    return {"mgr": mgr, "chapter": chapter, "event": event, "round": rnd, **players}


@pytest.mark.django_db
def test_completing_round_builds_chapter_rankings():
    s = _scored_round()
    _client(s["mgr"]).post(f"/api/rounds/{s['round'].id}/complete/", {}, format="json")

    rows = {r.user_id: r for r in Ranking.objects.filter(
        scope=Ranking.Scope.CHAPTER, scope_reference_id=s["chapter"].id,
    )}
    assert rows[s["a"].id].rank == 1
    assert float(rows[s["a"].id].rank_points) == 2.0  # 1st of a 2-player field
    assert rows[s["b"].id].rank == 2
    assert float(rows[s["b"].id].rank_points) == 1.0
    assert rows[s["a"].id].events_competed == 1
    assert rows[s["a"].id].last_event_at is not None


@pytest.mark.django_db
def test_global_board_includes_tier_a_only():
    tier_a = _scored_round(tier=Chapter.Tier.A, slug="alpha")
    tier_c = _scored_round(tier=Chapter.Tier.C, slug="gamma")
    _client(tier_a["mgr"]).post(f"/api/rounds/{tier_a['round'].id}/complete/", {}, format="json")
    _client(tier_c["mgr"]).post(f"/api/rounds/{tier_c['round'].id}/complete/", {}, format="json")

    global_users = set(
        Ranking.objects.filter(
            scope=Ranking.Scope.GLOBAL, scope_reference_id__isnull=True
        ).values_list("user_id", flat=True)
    )
    assert tier_a["a"].id in global_users
    assert tier_c["a"].id not in global_users  # Tier C never reaches the global board
    # but the Tier C players still have a chapter board
    assert Ranking.objects.filter(
        scope=Ranking.Scope.CHAPTER, scope_reference_id=tier_c["chapter"].id,
    ).count() == 2


@pytest.mark.django_db
def test_event_tier_weights_points():
    champ = _scored_round(event_tier=Event.EventTier.CHAMPIONSHIP, slug="champ")
    _client(champ["mgr"]).post(f"/api/rounds/{champ['round'].id}/complete/", {}, format="json")
    winner = Ranking.objects.get(
        scope=Ranking.Scope.CHAPTER, scope_reference_id=champ["chapter"].id,
        user_id=champ["a"].id,
    )
    assert float(winner.rank_points) == 6.0  # 2 placement points × 3.0 championship weight


@pytest.mark.django_db
def test_cancelling_completed_round_drops_it():
    s = _scored_round()
    rid = s["round"].id
    _client(s["mgr"]).post(f"/api/rounds/{rid}/complete/", {}, format="json")
    assert Ranking.objects.filter(scope=Ranking.Scope.CHAPTER,
                                  scope_reference_id=s["chapter"].id).exists()
    _client(s["mgr"]).post(f"/api/rounds/{rid}/cancel/", {}, format="json")
    assert not Ranking.objects.filter(scope=Ranking.Scope.CHAPTER,
                                      scope_reference_id=s["chapter"].id).exists()


@pytest.mark.django_db
def test_public_chapter_leaderboard_endpoint():
    s = _scored_round()
    _client(s["mgr"]).post(f"/api/rounds/{s['round'].id}/complete/", {}, format="json")
    r = _client().get(f"/api/rankings/?scope=chapter&chapter={s['chapter'].id}")
    assert r.status_code == 200
    assert [row["rank"] for row in r.data] == [1, 2]
    assert r.data[0]["user_id"] == str(s["a"].id)
    assert float(r.data[0]["rank_points"]) == 2.0


@pytest.mark.django_db
def test_global_leaderboard_endpoint():
    s = _scored_round(tier=Chapter.Tier.A, slug="alpha")
    _client(s["mgr"]).post(f"/api/rounds/{s['round'].id}/complete/", {}, format="json")
    r = _client().get("/api/rankings/?scope=global")
    assert r.status_code == 200
    assert {row["user_id"] for row in r.data} == {str(s["a"].id), str(s["b"].id)}
    assert all(row["scope"] == "global" for row in r.data)


@pytest.mark.django_db
def test_unverified_chapter_board_hidden_from_public_but_visible_to_manager():
    s = _scored_round(verified=False)
    _client(s["mgr"]).post(f"/api/rounds/{s['round'].id}/complete/", {}, format="json")
    url = f"/api/rankings/?scope=chapter&chapter={s['chapter'].id}"
    assert _client().get(url).status_code == 403
    assert _client(s["mgr"]).get(url).status_code == 200


@pytest.mark.django_db
def test_chapter_scope_requires_chapter_param():
    assert _client().get("/api/rankings/?scope=chapter").status_code == 400
