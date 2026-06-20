from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from chapters.models import Chapter, ChapterStaff
from events.models import Event, EventParticipant

User = get_user_model()


# ---- fixtures / helpers ----------------------------------------------------

@pytest.fixture
def manager(db):
    return User.objects.create_user(email="mgr@example.com", password="pw")


@pytest.fixture
def chapter(db, manager):
    """A VERIFIED chapter with `manager` as its active owner."""
    return _chapter_with_owner(manager, "BU", "bu", Chapter.VerificationStatus.VERIFIED)


def _chapter_with_owner(owner, name, slug, verification):
    ch = Chapter.objects.create(
        name=name, slug=slug, created_by=owner, verification_status=verification
    )
    ChapterStaff.objects.create(
        user=owner, chapter=ch,
        roles=[ChapterStaff.Role.OWNER], status=ChapterStaff.Status.ACTIVE,
    )
    return ch


def _payload(chapter_slug, **over):
    start = timezone.now() + timedelta(days=7)
    data = {
        "chapter": chapter_slug,
        "name": "Spring Classic",
        "format": "vibe",
        "timer": "sprint",
        "scheduled_start": start.isoformat(),
        "scheduled_end": (start + timedelta(hours=2)).isoformat(),
    }
    data.update(over)
    return data


def _mk_event(chapter, name, slug, creator, **over):
    start = timezone.now() + timedelta(days=3)
    return Event.objects.create(
        chapter=chapter, name=name, slug=slug, created_by=creator,
        scheduled_start=start, scheduled_end=start + timedelta(hours=2), **over,
    )


def _names(data):
    rows = data["results"] if isinstance(data, dict) and "results" in data else data
    return [e["name"] for e in rows]


# ---- create ----------------------------------------------------------------

@pytest.mark.django_db
def test_create_requires_auth(chapter):
    r = APIClient().post("/api/events/", _payload("bu"), format="json")
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_non_manager_cannot_create(chapter):
    other = APIClient()
    other.force_authenticate(User.objects.create_user(email="x@example.com", password="pw"))
    r = other.post("/api/events/", _payload("bu"), format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_manager_creates_event(manager, chapter):
    c = APIClient()
    c.force_authenticate(manager)
    r = c.post("/api/events/", _payload("bu"), format="json")
    assert r.status_code == 201
    assert r.data["slug"] == "spring-classic"
    assert r.data["status"] == "scheduled"          # model default
    assert r.data["chapter"]["slug"] == "bu"
    assert Event.objects.get(id=r.data["id"]).created_by == manager


@pytest.mark.django_db
def test_slug_unique_per_chapter(manager, chapter):
    c = APIClient()
    c.force_authenticate(manager)
    c.post("/api/events/", _payload("bu", name="Dup"), format="json")
    c.post("/api/events/", _payload("bu", name="Dup"), format="json")
    slugs = sorted(Event.objects.filter(name="Dup").values_list("slug", flat=True))
    assert slugs == ["dup", "dup-2"]


@pytest.mark.django_db
def test_end_must_be_after_start(manager, chapter):
    c = APIClient()
    c.force_authenticate(manager)
    start = (timezone.now() + timedelta(days=1)).isoformat()
    r = c.post(
        "/api/events/",
        _payload("bu", scheduled_start=start, scheduled_end=start),
        format="json",
    )
    assert r.status_code == 400


# ---- read visibility -------------------------------------------------------

@pytest.mark.django_db
def test_public_list_only_verified_chapter_events(manager, chapter):
    _mk_event(chapter, "Visible", "visible", manager)
    pending = _chapter_with_owner(
        manager, "Pending", "pending", Chapter.VerificationStatus.PENDING
    )
    _mk_event(pending, "Hidden", "hidden", manager)
    names = _names(APIClient().get("/api/events/").data)
    assert "Visible" in names
    assert "Hidden" not in names


@pytest.mark.django_db
def test_list_filters_by_chapter(manager, chapter):
    _mk_event(chapter, "BU Event", "bu-event", manager)
    other = _chapter_with_owner(
        manager, "MIT", "mit", Chapter.VerificationStatus.VERIFIED
    )
    _mk_event(other, "MIT Event", "mit-event", manager)
    names = _names(APIClient().get("/api/events/?chapter=bu").data)
    assert names == ["BU Event"]


@pytest.mark.django_db
def test_manager_sees_own_pending_chapter_events_via_mine(manager):
    pending = _chapter_with_owner(
        manager, "Planning", "planning", Chapter.VerificationStatus.PENDING
    )
    _mk_event(pending, "Planned", "planned", manager)
    c = APIClient()
    c.force_authenticate(manager)
    assert "Planned" in _names(c.get("/api/events/mine/").data)


@pytest.mark.django_db
def test_retrieve_visibility(manager):
    pending = _chapter_with_owner(
        manager, "Secret Chapter", "secret-ch", Chapter.VerificationStatus.PENDING
    )
    ev = _mk_event(pending, "Secret", "secret", manager)
    # public can't retrieve an event of a non-verified chapter
    assert APIClient().get(f"/api/events/{ev.id}/").status_code == 404
    # ...but its manager can
    c = APIClient()
    c.force_authenticate(manager)
    assert c.get(f"/api/events/{ev.id}/").status_code == 200


# ---- update / delete -------------------------------------------------------

@pytest.mark.django_db
def test_manager_can_update_and_delete(manager, chapter):
    ev = _mk_event(chapter, "Editable", "editable", manager)
    c = APIClient()
    c.force_authenticate(manager)
    r = c.patch(
        f"/api/events/{ev.id}/",
        {"name": "Renamed", "status": "registration_open"},
        format="json",
    )
    assert r.status_code == 200
    assert r.data["name"] == "Renamed"
    assert r.data["status"] == "registration_open"
    assert c.delete(f"/api/events/{ev.id}/").status_code == 204
    assert not Event.objects.filter(id=ev.id).exists()


@pytest.mark.django_db
def test_non_manager_cannot_update_or_delete(manager, chapter):
    ev = _mk_event(chapter, "Theirs", "theirs", manager)
    other = APIClient()
    other.force_authenticate(User.objects.create_user(email="o@example.com", password="pw"))
    # 404 (existence not leaked), not 403 — and the event survives
    assert other.patch(f"/api/events/{ev.id}/", {"name": "X"}, format="json").status_code == 404
    assert other.delete(f"/api/events/{ev.id}/").status_code == 404
    assert Event.objects.filter(id=ev.id, name="Theirs").exists()


@pytest.mark.django_db
def test_event_cannot_be_moved_between_chapters(manager, chapter):
    other = _chapter_with_owner(manager, "Other", "other", Chapter.VerificationStatus.VERIFIED)
    ev = _mk_event(chapter, "Stuck", "stuck", manager)
    c = APIClient()
    c.force_authenticate(manager)
    r = c.patch(f"/api/events/{ev.id}/", {"chapter": "other"}, format="json")
    assert r.status_code == 400


# ===========================================================================
# 2b — participant flows (apply / invite / corps-judge / respond / decide)
# ===========================================================================

@pytest.fixture
def player(db):
    return User.objects.create_user(email="player@example.com", password="pw")


@pytest.fixture
def app_event(db, manager, chapter):
    return _mk_event(
        chapter, "Open Event", "open-event", manager,
        access_mode=Event.AccessMode.APPLICATION,
    )


@pytest.fixture
def invite_event(db, manager, chapter):
    return _mk_event(
        chapter, "Closed Event", "closed-event", manager,
        access_mode=Event.AccessMode.INVITE_ONLY,
    )


# ---- apply -----------------------------------------------------------------

@pytest.mark.django_db
def test_apply_as_player_is_pending(player, app_event):
    c = APIClient()
    c.force_authenticate(player)
    r = c.post(f"/api/events/{app_event.id}/apply/", {"role": "player"}, format="json")
    assert r.status_code == 201
    assert r.data["status"] == "pending"
    assert r.data["source"] == "applied"
    assert r.data["role"] == "player"


@pytest.mark.django_db
def test_apply_as_audience_auto_registers(player, app_event):
    c = APIClient()
    c.force_authenticate(player)
    r = c.post(f"/api/events/{app_event.id}/apply/", {"role": "audience"}, format="json")
    assert r.status_code == 201
    assert r.data["status"] == "registered"


@pytest.mark.django_db
def test_cannot_apply_to_invite_only_event(player, invite_event):
    c = APIClient()
    c.force_authenticate(player)
    r = c.post(f"/api/events/{invite_event.id}/apply/", {"role": "player"}, format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_cannot_apply_twice(player, app_event):
    c = APIClient()
    c.force_authenticate(player)
    c.post(f"/api/events/{app_event.id}/apply/", {"role": "player"}, format="json")
    r = c.post(f"/api/events/{app_event.id}/apply/", {"role": "judge"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_apply_requires_auth(app_event):
    r = APIClient().post(f"/api/events/{app_event.id}/apply/", {"role": "player"}, format="json")
    assert r.status_code in (401, 403)


# ---- invite ----------------------------------------------------------------

@pytest.mark.django_db
def test_manager_invites_by_email_unregistered(manager, app_event):
    c = APIClient()
    c.force_authenticate(manager)
    r = c.post(
        f"/api/events/{app_event.id}/invite/",
        {"email": "newjudge@example.com", "role": "judge", "judge_specialization": "tester"},
        format="json",
    )
    assert r.status_code == 201
    assert r.data["status"] == "pending"
    assert r.data["source"] == "invited"
    p = EventParticipant.objects.get(id=r.data["id"])
    assert p.user is None
    assert p.email == "newjudge@example.com"
    assert p.token
    assert p.judge_specialization == "tester"


@pytest.mark.django_db
def test_invite_by_user_id_links_account(manager, app_event, player):
    c = APIClient()
    c.force_authenticate(manager)
    r = c.post(
        f"/api/events/{app_event.id}/invite/",
        {"user_id": str(player.id), "role": "player"}, format="json",
    )
    assert r.status_code == 201
    p = EventParticipant.objects.get(id=r.data["id"])
    assert p.user_id == player.id


@pytest.mark.django_db
def test_invite_existing_email_links_account(manager, app_event, player):
    c = APIClient()
    c.force_authenticate(manager)
    r = c.post(
        f"/api/events/{app_event.id}/invite/",
        {"email": "player@example.com", "role": "player"}, format="json",
    )
    assert r.status_code == 201
    p = EventParticipant.objects.get(id=r.data["id"])
    assert p.user_id == player.id
    assert p.email == ""


@pytest.mark.django_db
def test_invite_requires_exactly_one_of_email_or_user_id(manager, app_event):
    c = APIClient()
    c.force_authenticate(manager)
    r = c.post(f"/api/events/{app_event.id}/invite/", {"role": "player"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_non_manager_cannot_invite(player, app_event):
    c = APIClient()
    c.force_authenticate(player)
    r = c.post(
        f"/api/events/{app_event.id}/invite/",
        {"email": "x@example.com", "role": "player"}, format="json",
    )
    assert r.status_code == 403


# ---- corps judge -----------------------------------------------------------

@pytest.mark.django_db
def test_add_corps_judge(manager, chapter, app_event):
    judge_user = User.objects.create_user(email="corps@example.com", password="pw")
    staff = ChapterStaff.objects.create(
        user=judge_user, chapter=chapter,
        roles=[ChapterStaff.Role.JUDGE], status=ChapterStaff.Status.ACTIVE,
    )
    c = APIClient()
    c.force_authenticate(manager)
    r = c.post(
        f"/api/events/{app_event.id}/add-corps-judge/",
        {"chapter_staff_id": str(staff.id), "judge_specialization": "ux_designer"},
        format="json",
    )
    assert r.status_code == 201
    assert r.data["role"] == "judge"
    assert r.data["source"] == "corps"
    assert r.data["status"] == "registered"
    p = EventParticipant.objects.get(id=r.data["id"])
    assert p.user_id == judge_user.id
    assert p.chapter_staff_id == staff.id


@pytest.mark.django_db
def test_add_corps_judge_rejects_non_judge_staff(manager, chapter, app_event):
    org = User.objects.create_user(email="org@example.com", password="pw")
    staff = ChapterStaff.objects.create(
        user=org, chapter=chapter,
        roles=[ChapterStaff.Role.ORGANIZER], status=ChapterStaff.Status.ACTIVE,
    )
    c = APIClient()
    c.force_authenticate(manager)
    r = c.post(
        f"/api/events/{app_event.id}/add-corps-judge/",
        {"chapter_staff_id": str(staff.id)}, format="json",
    )
    assert r.status_code == 400


# ---- participant listing visibility ---------------------------------------

@pytest.mark.django_db
def test_participants_visibility(manager, app_event, player):
    EventParticipant.objects.create(
        event=app_event, user=player, role="player",
        source="applied", status=EventParticipant.Status.REGISTERED,
    )
    pending_user = User.objects.create_user(email="pend@example.com", password="pw")
    EventParticipant.objects.create(
        event=app_event, user=pending_user, role="player",
        source="applied", status=EventParticipant.Status.PENDING,
    )
    # public: only the registered one, and no email
    pub = APIClient().get(f"/api/events/{app_event.id}/participants/")
    assert pub.status_code == 200
    assert len(pub.data) == 1
    assert pub.data[0]["email"] == ""
    # manager: both, with email
    c = APIClient()
    c.force_authenticate(manager)
    mgr = c.get(f"/api/events/{app_event.id}/participants/")
    assert len(mgr.data) == 2
    assert {row["email"] for row in mgr.data} == {"player@example.com", "pend@example.com"}


# ---- mine / respond / decide / withdraw -----------------------------------

@pytest.mark.django_db
def test_mine_includes_account_and_email_invites(player, manager, app_event):
    EventParticipant.objects.create(
        event=app_event, user=player, role="player", source="applied", status="pending",
    )
    other_ch = _chapter_with_owner(manager, "C2", "c2", Chapter.VerificationStatus.VERIFIED)
    other_event = _mk_event(other_ch, "E2", "e2", manager)
    EventParticipant.objects.create(
        event=other_event, email="player@example.com", role="judge",
        source="invited", status="pending", token="t",
    )
    c = APIClient()
    c.force_authenticate(player)
    r = c.get("/api/event-participants/mine/")
    assert r.status_code == 200
    assert len(r.data) == 2


@pytest.mark.django_db
def test_respond_accept_claims_email_invite(player, app_event):
    p = EventParticipant.objects.create(
        event=app_event, email="player@example.com", role="judge",
        source="invited", status="pending", token="t",
    )
    c = APIClient()
    c.force_authenticate(player)
    r = c.post(f"/api/event-participants/{p.id}/respond/", {"action": "accept"}, format="json")
    assert r.status_code == 200
    p.refresh_from_db()
    assert p.status == "registered"
    assert p.user_id == player.id
    assert p.email == ""


@pytest.mark.django_db
def test_respond_decline(player, app_event):
    p = EventParticipant.objects.create(
        event=app_event, user=player, role="player", source="invited", status="pending",
    )
    c = APIClient()
    c.force_authenticate(player)
    r = c.post(f"/api/event-participants/{p.id}/respond/", {"action": "decline"}, format="json")
    assert r.status_code == 200
    p.refresh_from_db()
    assert p.status == "declined"


@pytest.mark.django_db
def test_only_invitee_can_respond(player, app_event):
    p = EventParticipant.objects.create(
        event=app_event, user=player, role="player", source="invited", status="pending",
    )
    other = APIClient()
    other.force_authenticate(User.objects.create_user(email="z@example.com", password="pw"))
    r = other.post(f"/api/event-participants/{p.id}/respond/", {"action": "accept"}, format="json")
    assert r.status_code == 404


@pytest.mark.django_db
def test_manager_decides_application(player, manager, app_event):
    p = EventParticipant.objects.create(
        event=app_event, user=player, role="player", source="applied", status="pending",
    )
    c = APIClient()
    c.force_authenticate(manager)
    r = c.post(f"/api/event-participants/{p.id}/decide/", {"action": "approve"}, format="json")
    assert r.status_code == 200
    p.refresh_from_db()
    assert p.status == "registered"
    assert p.decided_by_id == manager.id


@pytest.mark.django_db
def test_non_manager_cannot_decide(player, app_event):
    p = EventParticipant.objects.create(
        event=app_event, user=player, role="player", source="applied", status="pending",
    )
    c = APIClient()
    c.force_authenticate(player)  # the applicant is not a manager
    r = c.post(f"/api/event-participants/{p.id}/decide/", {"action": "approve"}, format="json")
    assert r.status_code == 404


@pytest.mark.django_db
def test_withdraw(player, app_event):
    p = EventParticipant.objects.create(
        event=app_event, user=player, role="player", source="applied", status="pending",
    )
    c = APIClient()
    c.force_authenticate(player)
    r = c.post(f"/api/event-participants/{p.id}/withdraw/", {}, format="json")
    assert r.status_code == 200
    p.refresh_from_db()
    assert p.status == "withdrawn"
