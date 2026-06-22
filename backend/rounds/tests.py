from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from chapters.models import Chapter
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
