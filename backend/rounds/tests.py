from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient

from chapters.models import Chapter, ChapterStaff
from events.models import Event, EventParticipant
import json

from django.core.management import call_command

from rounds.models import FuzzResult, Round, Score, Submission
from rounds.services import SUBMISSION_GRACE

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


# ===========================================================================
# increment 3 — submission upload (zip, server-side freeze) + download
# ===========================================================================

ZIP_BYTES = b"PK\x03\x04" + b"x" * 128  # valid zip magic prefix


def _zip(name="app.zip"):
    return SimpleUploadedFile(name, ZIP_BYTES, content_type="application/zip")


def _live_round(event, number=1):
    """A round currently in its build window (before code-freeze)."""
    now = timezone.now()
    return Round.objects.create(
        event=event, round_number=number, timing_profile="tier_c_mvr",
        opening_at=now - timedelta(minutes=10),
        build_start_at=now - timedelta(minutes=5),
        build_end_at=now + timedelta(minutes=15),
    )


@pytest.mark.django_db
def test_player_submits_zip_before_freeze(mgr_event, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    rnd = _live_round(mgr_event["event"])
    player = _registered_player(mgr_event["event"], "p@example.com")
    r = _client(player).post(
        f"/api/rounds/{rnd.id}/submit/",
        {"archive": _zip(), "readme_content": "hi"}, format="multipart",
    )
    assert r.status_code == 200
    assert r.data["status"] == "submitted"
    assert r.data["has_archive"] is True
    sub = Submission.objects.get(round=rnd, player=player)
    assert sub.submitted_at is not None
    assert sub.archive_filename == "app.zip"


@pytest.mark.django_db
def test_submit_ignores_grading_pipeline_fields_if_a_client_sends_them(
    mgr_event, settings, tmp_path
):
    """deployed_url and attack_surface_coverage are pipeline outputs, not player input. The
    model fields still exist for the Stage 5 pass to write, so a client posting them must not
    be able to set its own attack surface — that metric exists to check the submitter."""
    settings.MEDIA_ROOT = str(tmp_path)
    rnd = _live_round(mgr_event["event"])
    player = _registered_player(mgr_event["event"], "liar@example.com")
    r = _client(player).post(
        f"/api/rounds/{rnd.id}/submit/",
        {
            "archive": _zip(),
            "deployed_url": "https://evil.example.com",
            "attack_surface_coverage": "broad",
        },
        format="multipart",
    )
    assert r.status_code == 200
    sub = Submission.objects.get(round=rnd, player=player)
    assert sub.deployed_url == ""
    assert sub.attack_surface_coverage == ""


@pytest.mark.django_db
def test_submit_accepted_inside_the_grace_window(mgr_event, settings, tmp_path):
    """Build time is up but the upload window is not. The buzzer ends the build; the grace
    exists so a slow upload doesn't cost a player work they finished in time."""
    settings.MEDIA_ROOT = str(tmp_path)
    now = timezone.now()
    rnd = Round.objects.create(
        event=mgr_event["event"], round_number=1, timing_profile="tier_c_mvr",
        opening_at=now - timedelta(minutes=30),
        build_start_at=now - timedelta(minutes=25),
        build_end_at=now - timedelta(minutes=1),  # past build end, inside the 3-min grace
    )
    player = _registered_player(mgr_event["event"], "grace@example.com")
    r = _client(player).post(
        f"/api/rounds/{rnd.id}/submit/", {"archive": _zip()}, format="multipart",
    )
    assert r.status_code == 200
    assert Submission.objects.get(round=rnd, player=player).submitted_at is not None


@pytest.mark.django_db
def test_submit_rejected_after_the_grace_window(mgr_event, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    now = timezone.now()
    rnd = Round.objects.create(
        event=mgr_event["event"], round_number=1, timing_profile="tier_c_mvr",
        opening_at=now - timedelta(minutes=40),
        build_start_at=now - timedelta(minutes=35),
        build_end_at=now - timedelta(minutes=11),  # well past build end + grace
    )
    player = _registered_player(mgr_event["event"], "late@example.com")
    r = _client(player).post(
        f"/api/rounds/{rnd.id}/submit/", {"archive": _zip()}, format="multipart",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_round_payload_exposes_the_submission_deadline(mgr_event):
    """The client gates its upload form on this, not on the phase — the phase flips to
    evaluation at the buzzer while uploads stay open."""
    rnd = _live_round(mgr_event["event"])
    r = APIClient().get(f"/api/rounds/{rnd.id}/")
    assert r.status_code == 200
    deadline = parse_datetime(r.data["submission_deadline"])
    assert deadline == rnd.build_end_at + SUBMISSION_GRACE


@pytest.mark.django_db
def test_submit_rejected_for_non_player(mgr_event, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    rnd = _live_round(mgr_event["event"])
    stranger = _client(User.objects.create_user(email="s@example.com", password="pw"))
    r = stranger.post(
        f"/api/rounds/{rnd.id}/submit/", {"archive": _zip()}, format="multipart",
    )
    assert r.status_code == 403


@pytest.mark.django_db
def test_submit_rejects_non_zip(mgr_event, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    rnd = _live_round(mgr_event["event"])
    player = _registered_player(mgr_event["event"], "p2@example.com")
    not_zip = SimpleUploadedFile("app.txt", b"hello not a zip", content_type="text/plain")
    r = _client(player).post(
        f"/api/rounds/{rnd.id}/submit/", {"archive": not_zip}, format="multipart",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_submit_rejected_when_unscheduled(mgr_event, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    rnd = Round.objects.create(event=mgr_event["event"], round_number=1)  # no build_end_at
    player = _registered_player(mgr_event["event"], "p3@example.com")
    r = _client(player).post(
        f"/api/rounds/{rnd.id}/submit/", {"archive": _zip()}, format="multipart",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_submission_download_access(mgr_event, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    rnd = _live_round(mgr_event["event"])
    player = _registered_player(mgr_event["event"], "dl@example.com")
    _client(player).post(
        f"/api/rounds/{rnd.id}/submit/", {"archive": _zip()}, format="multipart",
    )
    sub = Submission.objects.get(round=rnd, player=player)
    assert _client(player).get(f"/api/submissions/{sub.id}/download/").status_code == 200
    assert _client(mgr_event["mgr"]).get(f"/api/submissions/{sub.id}/download/").status_code == 200
    stranger = _client(User.objects.create_user(email="x@example.com", password="pw"))
    assert stranger.get(f"/api/submissions/{sub.id}/download/").status_code == 404


@pytest.mark.django_db
def test_round_submissions_visibility(mgr_event, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    rnd = _live_round(mgr_event["event"])
    p1 = _registered_player(mgr_event["event"], "p1@example.com")
    p2 = _registered_player(mgr_event["event"], "p2b@example.com")
    Submission.objects.create(round=rnd, player=p1, status="submitted")
    Submission.objects.create(round=rnd, player=p2, status="submitted")
    judge_user = User.objects.create_user(email="j@example.com", password="pw")
    EventParticipant.objects.create(
        event=mgr_event["event"], user=judge_user, role="judge",
        source="corps", status="registered",
    )
    # a judge sees every submission in the round
    assert len(_client(judge_user).get(f"/api/submissions/?round={rnd.id}").data) == 2
    # a player sees only their own
    pr = _client(p1).get(f"/api/submissions/?round={rnd.id}")
    assert len(pr.data) == 1
    assert pr.data[0]["player_email"] == "p1@example.com"


# ===========================================================================
# increment 4 — scoring API + composite + awards
# ===========================================================================

def _judge(event, email="j@example.com", specialization=""):
    user = User.objects.create_user(email=email, password="pw")
    return EventParticipant.objects.create(
        event=event, user=user, role="judge", source="corps", status="registered",
        judge_specialization=specialization,
    )


def _scored_submission(rnd, player, judge, scores):
    sub = Submission.objects.create(round=rnd, player=player, status="submitted")
    for score_type, value in scores.items():
        Score.objects.create(
            submission=sub, judge_participant=judge, score_type=score_type, value=value,
        )
    return sub


@pytest.mark.django_db
def test_judge_submits_and_updates_score(mgr_event):
    rnd = _live_round(mgr_event["event"])  # status scheduled -> scoring open
    player = _registered_player(mgr_event["event"], "p@example.com")
    sub = Submission.objects.create(round=rnd, player=player, status="submitted")
    judge = _judge(mgr_event["event"])
    jc = _client(judge.user)
    r = jc.post(
        "/api/scores/",
        {"submission": str(sub.id), "score_type": "pitch_quality", "value": "80"},
        format="json",
    )
    assert r.status_code == 201
    # re-scoring the same dimension upserts (one row, updated value)
    r2 = jc.post(
        "/api/scores/",
        {"submission": str(sub.id), "score_type": "pitch_quality", "value": "85"},
        format="json",
    )
    assert r2.status_code == 201
    qs = Score.objects.filter(submission=sub, score_type="pitch_quality")
    assert qs.count() == 1
    assert float(qs.get().value) == 85.0


@pytest.mark.django_db
def test_non_judge_cannot_score(mgr_event):
    rnd = _live_round(mgr_event["event"])
    player = _registered_player(mgr_event["event"], "p@example.com")
    sub = Submission.objects.create(round=rnd, player=player, status="submitted")
    stranger = _client(User.objects.create_user(email="s@example.com", password="pw"))
    r = stranger.post(
        "/api/scores/",
        {"submission": str(sub.id), "score_type": "pitch_quality", "value": "80"},
        format="json",
    )
    assert r.status_code == 403


@pytest.mark.django_db
def test_scoring_closed_when_round_completed(mgr_event):
    rnd = Round.objects.create(
        event=mgr_event["event"], round_number=1, status=Round.Status.COMPLETED,
    )
    player = _registered_player(mgr_event["event"], "p@example.com")
    sub = Submission.objects.create(round=rnd, player=player, status="submitted")
    judge = _judge(mgr_event["event"])
    r = _client(judge.user).post(
        "/api/scores/",
        {"submission": str(sub.id), "score_type": "pitch_quality", "value": "80"},
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_score_value_out_of_range(mgr_event):
    rnd = _live_round(mgr_event["event"])
    player = _registered_player(mgr_event["event"], "p@example.com")
    sub = Submission.objects.create(round=rnd, player=player, status="submitted")
    judge = _judge(mgr_event["event"])
    r = _client(judge.user).post(
        "/api/scores/",
        {"submission": str(sub.id), "score_type": "pitch_quality", "value": "150"},
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_scores_list_is_manager_or_judge_only(mgr_event):
    rnd = _live_round(mgr_event["event"])
    player = _registered_player(mgr_event["event"], "p@example.com")
    Submission.objects.create(round=rnd, player=player, status="submitted")
    assert _client(mgr_event["mgr"]).get(f"/api/scores/?round={rnd.id}").status_code == 200
    assert _client(player).get(f"/api/scores/?round={rnd.id}").status_code == 403


@pytest.mark.django_db
def test_results_composite_and_awards(mgr_event):
    rnd = Round.objects.create(event=mgr_event["event"], round_number=1)
    judge = _judge(mgr_event["event"])
    a = _registered_player(mgr_event["event"], "a@example.com")
    b = _registered_player(mgr_event["event"], "b@example.com")
    # A: clean build (low slop), weak communication. B: the reverse.
    a_sub = _scored_submission(rnd, a, judge, {"pitch_quality": 60, "cross_examination": 60})
    a_sub.slop_score = 10
    a_sub.save(update_fields=["slop_score"])
    b_sub = _scored_submission(rnd, b, judge, {"pitch_quality": 90, "cross_examination": 90})
    b_sub.slop_score = 100
    b_sub.save(update_fields=["slop_score"])
    r = _client(mgr_event["mgr"]).get(f"/api/rounds/{rnd.id}/results/")
    assert r.status_code == 200
    standings = {s["player_id"]: s for s in r.data["standings"]}
    assert standings[str(a.id)]["slop_rank"] == 1  # lowest slop wins
    assert standings[str(b.id)]["communication_rank"] == 1
    # rank-sum ties 3-3; tiebreak (|diff| equal, then best slop rank) -> A overall #1
    assert standings[str(a.id)]["overall_rank"] == 1
    assert standings[str(b.id)]["overall_rank"] == 2
    assert r.data["awards"]["slopless_builder"] == [str(a.id)]
    assert r.data["awards"]["best_communicator"] == [str(b.id)]
    assert r.data["awards"]["best_overall"] == [str(a.id)]


@pytest.mark.django_db
def test_communication_is_role_weighted_over_present_roles(mgr_event):
    rnd = Round.objects.create(event=mgr_event["event"], round_number=1)
    player = _registered_player(mgr_event["event"], "p@example.com")
    tester = _judge(mgr_event["event"], "t@example.com", specialization="tester")  # weight 30
    ux = _judge(mgr_event["event"], "u@example.com", specialization="ux_designer")  # weight 20
    sub = Submission.objects.create(round=rnd, player=player, status="submitted")
    for st in ("pitch_quality", "cross_examination"):
        Score.objects.create(submission=sub, judge_participant=tester, score_type=st, value=100)
        Score.objects.create(submission=sub, judge_participant=ux, score_type=st, value=0)
    r = _client(mgr_event["mgr"]).get(f"/api/rounds/{rnd.id}/results/")
    s = r.data["standings"][0]
    # weighted over the two present roles: (30*100 + 20*0)/(30+20) = 60, NOT the flat mean of 50.
    assert s["communication_score"] == 60.0


@pytest.mark.django_db
def test_communication_falls_back_to_flat_mean_without_roles(mgr_event):
    rnd = Round.objects.create(event=mgr_event["event"], round_number=1)
    player = _registered_player(mgr_event["event"], "p@example.com")
    j1 = _judge(mgr_event["event"], "j1@example.com")  # no specialization
    j2 = _judge(mgr_event["event"], "j2@example.com")  # no specialization
    sub = Submission.objects.create(round=rnd, player=player, status="submitted")
    for st in ("pitch_quality", "cross_examination"):
        Score.objects.create(submission=sub, judge_participant=j1, score_type=st, value=100)
        Score.objects.create(submission=sub, judge_participant=j2, score_type=st, value=0)
    r = _client(mgr_event["mgr"]).get(f"/api/rounds/{rnd.id}/results/")
    s = r.data["standings"][0]
    assert s["communication_score"] == 50.0  # role-blind flat mean


@pytest.mark.django_db
def test_ungraded_submission_ranks_last_on_slop(mgr_event):
    rnd = Round.objects.create(event=mgr_event["event"], round_number=1)
    judge = _judge(mgr_event["event"])
    a = _registered_player(mgr_event["event"], "a@example.com")
    b = _registered_player(mgr_event["event"], "b@example.com")
    a_sub = _scored_submission(rnd, a, judge, {"pitch_quality": 50, "cross_examination": 50})
    a_sub.slop_score = 80  # graded; even a high slop beats not being graded at all
    a_sub.save(update_fields=["slop_score"])
    # B deploy-failed: no slop_score, though judges still scored a pitch.
    _scored_submission(rnd, b, judge, {"pitch_quality": 90, "cross_examination": 90})
    r = _client(mgr_event["mgr"]).get(f"/api/rounds/{rnd.id}/results/")
    standings = {s["player_id"]: s for s in r.data["standings"]}
    assert standings[str(a.id)]["slop_rank"] == 1
    assert standings[str(b.id)]["slop_rank"] == 2  # ungraded sorts last (§4.2)
    assert standings[str(b.id)]["slop_score"] is None
    # Slopless Builder goes to the graded low-slop build, never to the ungraded one.
    assert r.data["awards"]["slopless_builder"] == [str(a.id)]


@pytest.mark.django_db
def test_results_hidden_until_revealed(mgr_event):
    rnd = Round.objects.create(event=mgr_event["event"], round_number=1)
    judge = _judge(mgr_event["event"])
    p = _registered_player(mgr_event["event"], "p@example.com")
    _scored_submission(rnd, p, judge, {"technical_execution": 70, "pitch_quality": 70})
    # not revealed yet -> public gets 403, but a manager can preview
    assert APIClient().get(f"/api/rounds/{rnd.id}/results/").status_code == 403
    assert _client(mgr_event["mgr"]).get(f"/api/rounds/{rnd.id}/results/").status_code == 200
    # completing the round reveals results publicly
    _client(mgr_event["mgr"]).post(f"/api/rounds/{rnd.id}/complete/", {}, format="json")
    pub = APIClient().get(f"/api/rounds/{rnd.id}/results/")
    assert pub.status_code == 200
    assert pub.data["revealed"] is True


# ---- fuzz grade import (manual-bridge grading path) ------------------------


@pytest.mark.django_db
def test_import_fuzz_results_sets_slop_score_and_findings(event, tmp_path):
    rnd = Round.objects.create(event=event, round_number=1)
    player = User.objects.create_user(email="graded@example.com", password="pw")
    sub = Submission.objects.create(round=rnd, player=player, status=Submission.Status.SUBMITTED)

    # The runner writes JSONL keyed by `repo` = the submission id (dir named by its uuid).
    rec = {
        "repo": f"/runs/{sub.id}", "deployed": True, "slop_score": 42,
        "axis_slop": {"security": 30, "qa": 12},
        "findings": [
            {"probe_id": "sec-sqli-001", "bundle": "security", "category": "sql-injection",
             "outcome": "slop_detected", "penalty": 30, "reason": "boolean differential"},
            {"probe_id": "qa-crash-003", "bundle": "qa", "category": "crash",
             "outcome": "slop_detected", "penalty": 12},
        ],
    }
    f = tmp_path / "results.jsonl"
    f.write_text(json.dumps(rec) + "\n")

    call_command("import_fuzz_results", str(f))

    sub.refresh_from_db()
    assert sub.slop_score == 42
    assert sub.status == Submission.Status.SUBMITTED_DEPLOYED
    assert sub.fuzz_results.count() == 2
    sqli = sub.fuzz_results.get(probe_id="sec-sqli-001")
    assert sqli.penalty_contributed == 30
    assert sqli.bundle == "security"
    assert sqli.evidence["reason"] == "boolean differential"


@pytest.mark.django_db
def test_import_fuzz_results_deploy_failed_record(event, tmp_path):
    rnd = Round.objects.create(event=event, round_number=1)
    player = User.objects.create_user(email="dnf@example.com", password="pw")
    sub = Submission.objects.create(round=rnd, player=player, status=Submission.Status.SUBMITTED)

    rec = {"repo": str(sub.id), "deployed": False}
    f = tmp_path / "r.jsonl"
    f.write_text(json.dumps(rec) + "\n")
    call_command("import_fuzz_results", str(f))

    sub.refresh_from_db()
    assert sub.slop_score is None
    assert sub.status == Submission.Status.SUBMITTED_FAILED


@pytest.mark.django_db
def test_import_fuzz_results_is_idempotent(event, tmp_path):
    rnd = Round.objects.create(event=event, round_number=1)
    player = User.objects.create_user(email="idem@example.com", password="pw")
    sub = Submission.objects.create(round=rnd, player=player)

    def write(score, probes):
        rec = {"repo": str(sub.id), "deployed": True, "slop_score": score,
               "findings": [{"probe_id": p, "bundle": "security", "outcome": "slop_detected",
                             "penalty": 10} for p in probes]}
        f = tmp_path / "r.jsonl"
        f.write_text(json.dumps(rec) + "\n")
        return f

    call_command("import_fuzz_results", str(write(50, ["a", "b", "c"])))
    assert sub.fuzz_results.count() == 3
    # Re-import with a corrected grade: fewer findings, new score — no stale rows left behind.
    call_command("import_fuzz_results", str(write(20, ["a"])))
    sub.refresh_from_db()
    assert sub.slop_score == 20
    assert sub.fuzz_results.count() == 1


@pytest.mark.django_db
def test_import_fuzz_results_skips_unknown_submission(tmp_path):
    import uuid as _uuid
    rec = {"repo": str(_uuid.uuid4()), "deployed": True, "slop_score": 5, "findings": []}
    f = tmp_path / "r.jsonl"
    f.write_text(json.dumps(rec) + "\n")
    # No matching submission -> no crash, nothing created.
    call_command("import_fuzz_results", str(f))
    assert FuzzResult.objects.count() == 0
