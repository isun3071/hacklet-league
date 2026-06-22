from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient

from chapters.models import Chapter, ChapterStaff
from events.models import Event, EventParticipant
from rounds.models import Round, Score, Submission

User = get_user_model()


@pytest.fixture
def event(db):
    owner = User.objects.create_user(email="owner@example.com", password="pw")
    chapter = Chapter.objects.create(name="C", slug="c", created_by=owner)
    start = timezone.now() + timedelta(days=1)
    return Event.objects.create(
        chapter=chapter, name="E", slug="e", created_by=owner,
        scheduled_start=start, scheduled_end=start + timedelta(hours=2),
    )


@pytest.mark.django_db
def test_round_number_unique_per_event(event):
    Round.objects.create(event=event, round_number=1)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Round.objects.create(event=event, round_number=1)


@pytest.mark.django_db
def test_submission_unique_per_player(event):
    rnd = Round.objects.create(event=event, round_number=1)
    player = User.objects.create_user(email="p@example.com", password="pw")
    Submission.objects.create(round=rnd, player=player)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Submission.objects.create(round=rnd, player=player)


@pytest.mark.django_db
def test_score_links_judge_participant(event):
    rnd = Round.objects.create(event=event, round_number=1)
    player = User.objects.create_user(email="p2@example.com", password="pw")
    sub = Submission.objects.create(round=rnd, player=player)
    judge_user = User.objects.create_user(email="j@example.com", password="pw")
    judge = EventParticipant.objects.create(
        event=event, user=judge_user, role="judge", source="corps", status="registered",
    )
    score = Score.objects.create(
        submission=sub, judge_participant=judge, score_type="pitch_quality", value=80,
    )
    assert score.value == 80
    assert sub.scores.count() == 1


# ===========================================================================
# increment 2 — round lifecycle API
# ===========================================================================

@pytest.fixture
def mgr_event(db):
    mgr = User.objects.create_user(email="mgr@example.com", password="pw")
    chapter = Chapter.objects.create(
        name="BU", slug="bu", created_by=mgr,
        verification_status=Chapter.VerificationStatus.VERIFIED,
    )
    ChapterStaff.objects.create(
        user=mgr, chapter=chapter,
        roles=[ChapterStaff.Role.OWNER], status=ChapterStaff.Status.ACTIVE,
    )
    start = timezone.now() + timedelta(days=1)
    ev = Event.objects.create(
        chapter=chapter, name="E", slug="e", created_by=mgr,
        scheduled_start=start, scheduled_end=start + timedelta(hours=2),
    )
    return {"mgr": mgr, "chapter": chapter, "event": ev}


def _client(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def _registered_player(event, email):
    user = User.objects.create_user(email=email, password="pw")
    EventParticipant.objects.create(
        event=event, user=user, role="player", source="applied", status="registered",
    )
    return user


@pytest.mark.django_db
def test_manager_creates_round(mgr_event):
    r = _client(mgr_event["mgr"]).post(
        "/api/rounds/",
        {"event": str(mgr_event["event"].id), "timing_profile": "tier_c_mvr"},
        format="json",
    )
    assert r.status_code == 201
    assert r.data["round_number"] == 1
    assert r.data["status"] == "scheduled"
    assert r.data["phase"] == "scheduled"


@pytest.mark.django_db
def test_round_number_auto_increments(mgr_event):
    c = _client(mgr_event["mgr"])
    eid = str(mgr_event["event"].id)
    c.post("/api/rounds/", {"event": eid}, format="json")
    r2 = c.post("/api/rounds/", {"event": eid}, format="json")
    assert r2.data["round_number"] == 2


@pytest.mark.django_db
def test_non_manager_cannot_create_round(mgr_event):
    other = _client(User.objects.create_user(email="x@example.com", password="pw"))
    r = other.post("/api/rounds/", {"event": str(mgr_event["event"].id)}, format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_schedule_computes_absolute_timeline(mgr_event):
    rnd = Round.objects.create(
        event=mgr_event["event"], round_number=1, timing_profile="tier_c_mvr",
    )
    opening = (timezone.now() + timedelta(hours=1)).replace(microsecond=0)
    r = _client(mgr_event["mgr"]).post(
        f"/api/rounds/{rnd.id}/schedule/", {"opening_at": opening.isoformat()}, format="json",
    )
    assert r.status_code == 200
    rnd.refresh_from_db()
    assert rnd.build_end_at == opening + timedelta(minutes=29)  # code-freeze
    assert parse_datetime(rnd.phase_schedule["awards_end"]) == opening + timedelta(minutes=60)


@pytest.mark.django_db
def test_phase_is_derived_from_clock(mgr_event):
    c = _client(mgr_event["mgr"])
    rnd = Round.objects.create(
        event=mgr_event["event"], round_number=1, timing_profile="tier_c_mvr",
    )
    # opened 10 min ago -> inside the build window (build = T+5..T+29)
    c.post(
        f"/api/rounds/{rnd.id}/schedule/",
        {"opening_at": (timezone.now() - timedelta(minutes=10)).isoformat()}, format="json",
    )
    poll = c.get(f"/api/rounds/{rnd.id}/")
    assert poll.data["phase"] == "build"
    assert "server_time" in poll.data
    # opened 2h ago -> every boundary passed -> completed
    c.post(
        f"/api/rounds/{rnd.id}/schedule/",
        {"opening_at": (timezone.now() - timedelta(hours=2)).isoformat()}, format="json",
    )
    assert c.get(f"/api/rounds/{rnd.id}/").data["phase"] == "completed"


@pytest.mark.django_db
def test_start_makes_round_live(mgr_event):
    rnd = Round.objects.create(
        event=mgr_event["event"], round_number=1, timing_profile="tier_c_mvr",
    )
    r = _client(mgr_event["mgr"]).post(f"/api/rounds/{rnd.id}/start/", {}, format="json")
    assert r.status_code == 200
    assert r.data["phase"] == "opening"  # now < build_start (opening + 5m)


@pytest.mark.django_db
def test_registered_player_checks_in(mgr_event):
    now = timezone.now()
    rnd = Round.objects.create(
        event=mgr_event["event"], round_number=1, timing_profile="tier_c_mvr",
        opening_at=now - timedelta(minutes=2),
        build_start_at=now + timedelta(minutes=3),
        build_end_at=now + timedelta(minutes=20),
    )
    player = _registered_player(mgr_event["event"], "pl@example.com")
    r = _client(player).post(f"/api/rounds/{rnd.id}/check-in/", {}, format="json")
    assert r.status_code == 200
    assert r.data["checked_in"] is True
    assert Submission.objects.filter(round=rnd, player=player).exists()


@pytest.mark.django_db
def test_check_in_rejects_non_player(mgr_event):
    rnd = Round.objects.create(event=mgr_event["event"], round_number=1)
    stranger = _client(User.objects.create_user(email="s@example.com", password="pw"))
    r = stranger.post(f"/api/rounds/{rnd.id}/check-in/", {}, format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_check_in_closed_after_freeze(mgr_event):
    now = timezone.now()
    rnd = Round.objects.create(
        event=mgr_event["event"], round_number=1, timing_profile="tier_c_mvr",
        opening_at=now - timedelta(minutes=40),
        build_start_at=now - timedelta(minutes=35),
        build_end_at=now - timedelta(minutes=11),  # freeze already passed
    )
    player = _registered_player(mgr_event["event"], "late@example.com")
    r = _client(player).post(f"/api/rounds/{rnd.id}/check-in/", {}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_public_can_poll_round(mgr_event):
    rnd = Round.objects.create(event=mgr_event["event"], round_number=1)
    r = APIClient().get(f"/api/rounds/{rnd.id}/")
    assert r.status_code == 200
    assert r.data["phase"] == "scheduled"
    assert "server_time" in r.data


@pytest.mark.django_db
def test_prompt_gated_until_build(mgr_event):
    c = _client(mgr_event["mgr"])
    rnd = Round.objects.create(
        event=mgr_event["event"], round_number=1, timing_profile="tier_c_mvr",
        prompt_revealed="Build a todo app",
    )
    c.post(
        f"/api/rounds/{rnd.id}/schedule/",
        {"opening_at": (timezone.now() + timedelta(hours=1)).isoformat()}, format="json",
    )
    assert c.get(f"/api/rounds/{rnd.id}/").data["prompt_revealed"] == ""  # scheduled
    c.post(
        f"/api/rounds/{rnd.id}/schedule/",
        {"opening_at": (timezone.now() - timedelta(minutes=10)).isoformat()}, format="json",
    )
    assert c.get(f"/api/rounds/{rnd.id}/").data["prompt_revealed"] == "Build a todo app"


@pytest.mark.django_db
def test_complete_and_cancel(mgr_event):
    c = _client(mgr_event["mgr"])
    rnd = Round.objects.create(event=mgr_event["event"], round_number=1)
    assert c.post(f"/api/rounds/{rnd.id}/complete/", {}, format="json").data["phase"] == "completed"
    rnd2 = Round.objects.create(event=mgr_event["event"], round_number=2)
    assert c.post(f"/api/rounds/{rnd2.id}/cancel/", {}, format="json").data["phase"] == "cancelled"
