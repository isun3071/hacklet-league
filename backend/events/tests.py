from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from chapters.models import Chapter, ChapterStaff
from events.models import Event

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
