import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from chapters.models import Chapter, ChapterStaff

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="founder@example.com", password="pw")


def _names(data):
    rows = data["results"] if isinstance(data, dict) and "results" in data else data
    return [c["name"] for c in rows]


@pytest.mark.django_db
def test_create_requires_auth():
    r = APIClient().post("/api/chapters/", {"name": "BU"}, format="json")
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_create_sets_owner_pending_and_slug(user):
    client = APIClient()
    client.force_authenticate(user)
    r = client.post("/api/chapters/", {"name": "Boston University", "tier": "C"}, format="json")
    assert r.status_code == 201
    assert r.data["slug"] == "boston-university"

    chapter = Chapter.objects.get(name="Boston University")
    assert chapter.created_by == user
    assert chapter.verification_status == Chapter.VerificationStatus.PENDING
    assert chapter.mode == Chapter.Mode.SIGNUP

    staff = ChapterStaff.objects.get(chapter=chapter, user=user)
    assert ChapterStaff.Role.OWNER in staff.roles
    assert staff.status == ChapterStaff.Status.ACTIVE


@pytest.mark.django_db
def test_directory_lists_only_verified(user):
    Chapter.objects.create(
        name="Pending One", slug="pending-one", created_by=user,
        verification_status=Chapter.VerificationStatus.PENDING,
    )
    Chapter.objects.create(
        name="Verified One", slug="verified-one", created_by=user,
        verification_status=Chapter.VerificationStatus.VERIFIED,
    )
    names = _names(APIClient().get("/api/chapters/").data)
    assert "Verified One" in names
    assert "Pending One" not in names


@pytest.mark.django_db
def test_slug_collisions_are_disambiguated(user):
    client = APIClient()
    client.force_authenticate(user)
    client.post("/api/chapters/", {"name": "Dup"}, format="json")
    client.post("/api/chapters/", {"name": "Dup"}, format="json")
    slugs = sorted(Chapter.objects.filter(name="Dup").values_list("slug", flat=True))
    assert slugs == ["dup", "dup-2"]


@pytest.mark.django_db
def test_creator_can_retrieve_own_pending_chapter(user):
    client = APIClient()
    client.force_authenticate(user)
    client.post("/api/chapters/", {"name": "Mine"}, format="json")
    # anonymous can't see the pending chapter
    assert APIClient().get("/api/chapters/mine/").status_code in (401, 403)
    mine = client.get("/api/chapters/mine/")
    assert mine.status_code == 200
    assert _names(mine.data) == ["Mine"]


@pytest.mark.django_db
def test_owner_can_update_and_delete_own_chapter(user):
    client = APIClient()
    client.force_authenticate(user)
    slug = client.post("/api/chapters/", {"name": "Editable"}, format="json").data["slug"]

    r = client.patch(f"/api/chapters/{slug}/", {"name": "Renamed", "tier": "B"}, format="json")
    assert r.status_code == 200
    chapter = Chapter.objects.get(slug=slug)
    assert chapter.name == "Renamed"
    assert chapter.tier == "B"
    assert chapter.slug == slug  # slug stays stable across a rename

    r = client.delete(f"/api/chapters/{slug}/")
    assert r.status_code == 204
    assert not Chapter.objects.filter(slug=slug).exists()


@pytest.mark.django_db
def test_non_owner_cannot_edit_or_delete(user):
    owner = APIClient()
    owner.force_authenticate(user)
    slug = owner.post("/api/chapters/", {"name": "Theirs"}, format="json").data["slug"]

    other = APIClient()
    other.force_authenticate(User.objects.create_user(email="other@example.com", password="pw"))

    # Non-owner gets 404 (existence not leaked), not 403 — and the chapter survives.
    assert other.patch(f"/api/chapters/{slug}/", {"name": "Hijack"}, format="json").status_code == 404
    assert other.delete(f"/api/chapters/{slug}/").status_code == 404
    assert Chapter.objects.filter(slug=slug, name="Theirs").exists()


@pytest.mark.django_db
def test_contact_email_visible_only_to_owner(user):
    client = APIClient()
    client.force_authenticate(user)
    slug = client.post(
        "/api/chapters/",
        {"name": "Contactable", "contact_email": "hi@chapter.org"},
        format="json",
    ).data["slug"]

    # Owner sees their own contact email...
    assert client.get("/api/chapters/mine/").data[0]["contact_email"] == "hi@chapter.org"

    # ...but a public (anonymous) viewer of the verified chapter does not.
    Chapter.objects.filter(slug=slug).update(
        verification_status=Chapter.VerificationStatus.VERIFIED
    )
    assert APIClient().get(f"/api/chapters/{slug}/").data["contact_email"] == ""


# ===========================================================================
# 2c — chapter staff management (/api/chapter-staff/)
# ===========================================================================

@pytest.fixture
def owner(db):
    return User.objects.create_user(email="owner@example.com", password="pw")


@pytest.fixture
def owned_chapter(db, owner):
    ch = Chapter.objects.create(
        name="Owned", slug="owned", created_by=owner,
        verification_status=Chapter.VerificationStatus.VERIFIED,
    )
    ChapterStaff.objects.create(
        user=owner, chapter=ch,
        roles=[ChapterStaff.Role.OWNER], status=ChapterStaff.Status.ACTIVE,
    )
    return ch


def _client(u):
    c = APIClient()
    c.force_authenticate(u)
    return c


@pytest.mark.django_db
def test_owner_adds_organizer_by_email(owner, owned_chapter):
    bob = User.objects.create_user(email="bob@example.com", password="pw")
    r = _client(owner).post(
        "/api/chapter-staff/",
        {"chapter": "owned", "email": "bob@example.com", "roles": ["organizer"]},
        format="json",
    )
    assert r.status_code == 201
    s = ChapterStaff.objects.get(chapter=owned_chapter, user=bob)
    assert s.roles == ["organizer"]
    assert s.status == "active"
    assert s.approved_by_id == owner.id


@pytest.mark.django_db
def test_add_staff_requires_existing_account(owner, owned_chapter):
    r = _client(owner).post(
        "/api/chapter-staff/",
        {"chapter": "owned", "email": "ghost@example.com", "roles": ["judge"]},
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_non_manager_cannot_add_staff(owner, owned_chapter):
    stranger = User.objects.create_user(email="stranger@example.com", password="pw")
    User.objects.create_user(email="victim@example.com", password="pw")
    r = _client(stranger).post(
        "/api/chapter-staff/",
        {"chapter": "owned", "email": "victim@example.com", "roles": ["judge"]},
        format="json",
    )
    assert r.status_code == 403


@pytest.mark.django_db
def test_organizer_cannot_grant_owner(owner, owned_chapter):
    org = User.objects.create_user(email="org@example.com", password="pw")
    ChapterStaff.objects.create(
        user=org, chapter=owned_chapter,
        roles=[ChapterStaff.Role.ORGANIZER], status=ChapterStaff.Status.ACTIVE,
    )
    User.objects.create_user(email="target@example.com", password="pw")
    r = _client(org).post(
        "/api/chapter-staff/",
        {"chapter": "owned", "email": "target@example.com", "roles": ["owner"]},
        format="json",
    )
    assert r.status_code == 403


@pytest.mark.django_db
def test_owner_can_grant_owner(owner, owned_chapter):
    User.objects.create_user(email="co@example.com", password="pw")
    r = _client(owner).post(
        "/api/chapter-staff/",
        {"chapter": "owned", "email": "co@example.com", "roles": ["owner"]},
        format="json",
    )
    assert r.status_code == 201


@pytest.mark.django_db
def test_duplicate_staff_rejected(owner, owned_chapter):
    User.objects.create_user(email="dup@example.com", password="pw")
    c = _client(owner)
    c.post(
        "/api/chapter-staff/",
        {"chapter": "owned", "email": "dup@example.com", "roles": ["judge"]},
        format="json",
    )
    r = c.post(
        "/api/chapter-staff/",
        {"chapter": "owned", "email": "dup@example.com", "roles": ["organizer"]},
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_list_staff_is_manager_only(owner, owned_chapter):
    assert _client(owner).get("/api/chapter-staff/?chapter=owned").status_code == 200
    stranger = User.objects.create_user(email="s2@example.com", password="pw")
    assert _client(stranger).get("/api/chapter-staff/?chapter=owned").status_code == 403


@pytest.mark.django_db
def test_update_staff_roles(owner, owned_chapter):
    judge = User.objects.create_user(email="j@example.com", password="pw")
    s = ChapterStaff.objects.create(
        user=judge, chapter=owned_chapter,
        roles=[ChapterStaff.Role.JUDGE], status=ChapterStaff.Status.ACTIVE,
    )
    r = _client(owner).patch(
        f"/api/chapter-staff/{s.id}/", {"roles": ["organizer", "judge"]}, format="json"
    )
    assert r.status_code == 200
    s.refresh_from_db()
    assert set(s.roles) == {"organizer", "judge"}


@pytest.mark.django_db
def test_cannot_delete_last_owner(owner, owned_chapter):
    s = ChapterStaff.objects.get(chapter=owned_chapter, user=owner)
    r = _client(owner).delete(f"/api/chapter-staff/{s.id}/")
    assert r.status_code == 400
    assert ChapterStaff.objects.filter(id=s.id).exists()


@pytest.mark.django_db
def test_cannot_demote_last_owner(owner, owned_chapter):
    s = ChapterStaff.objects.get(chapter=owned_chapter, user=owner)
    r = _client(owner).patch(f"/api/chapter-staff/{s.id}/", {"roles": ["organizer"]}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_organizer_cannot_remove_owner(owner, owned_chapter):
    org = User.objects.create_user(email="o3@example.com", password="pw")
    ChapterStaff.objects.create(
        user=org, chapter=owned_chapter,
        roles=[ChapterStaff.Role.ORGANIZER], status=ChapterStaff.Status.ACTIVE,
    )
    owner_row = ChapterStaff.objects.get(chapter=owned_chapter, user=owner)
    r = _client(org).delete(f"/api/chapter-staff/{owner_row.id}/")
    assert r.status_code == 403


@pytest.mark.django_db
def test_remove_staff(owner, owned_chapter):
    judge = User.objects.create_user(email="j2@example.com", password="pw")
    s = ChapterStaff.objects.create(
        user=judge, chapter=owned_chapter,
        roles=[ChapterStaff.Role.JUDGE], status=ChapterStaff.Status.ACTIVE,
    )
    r = _client(owner).delete(f"/api/chapter-staff/{s.id}/")
    assert r.status_code == 204
    assert not ChapterStaff.objects.filter(id=s.id).exists()


@pytest.mark.django_db
def test_mine_lists_my_staff_rows(owner, owned_chapter):
    r = _client(owner).get("/api/chapter-staff/mine/")
    assert r.status_code == 200
    assert len(r.data) == 1
    assert r.data[0]["chapter_slug"] == "owned"


@pytest.mark.django_db
def test_chapter_stats_endpoint(user):
    from datetime import timedelta

    from django.utils import timezone

    from events.models import Event, EventParticipant
    from rounds.models import Round

    chapter = Chapter.objects.create(
        name="BU", slug="bu", created_by=user, tier="A",
        verification_status=Chapter.VerificationStatus.VERIFIED,
    )
    ChapterStaff.objects.create(
        user=user, chapter=chapter, roles=[ChapterStaff.Role.OWNER],
        status=ChapterStaff.Status.ACTIVE,
    )
    corps = User.objects.create_user(email="cj@example.com", password="pw")
    ChapterStaff.objects.create(
        user=corps, chapter=chapter, roles=[ChapterStaff.Role.JUDGE],
        status=ChapterStaff.Status.ACTIVE,
    )
    start = timezone.now() + timedelta(days=1)
    event = Event.objects.create(
        chapter=chapter, name="E", slug="e", created_by=user,
        scheduled_start=start, scheduled_end=start + timedelta(hours=2),
    )
    for i, role in enumerate(["player", "player", "judge"]):
        u = User.objects.create_user(email=f"sp{i}@example.com", password="pw")
        EventParticipant.objects.create(
            event=event, user=u, role=role, source="applied",
            status=EventParticipant.Status.REGISTERED,
        )
    Round.objects.create(event=event, round_number=1)

    client = APIClient()
    client.force_authenticate(user)
    r = client.get("/api/chapters/stats/")
    assert r.status_code == 200
    row = next(x for x in r.data if x["slug"] == "bu")
    assert row["events_total"] == 1
    assert row["players"] == 2
    assert row["judges"] == 1
    assert row["participants_total"] == 3
    assert row["members_total"] == 2
    assert row["organizers"] == 1
    assert row["corps_judges"] == 1
    assert row["rounds_total"] == 1
    assert row["tier"] == "A"


@pytest.mark.django_db
def test_chapter_stats_requires_auth():
    assert APIClient().get("/api/chapters/stats/").status_code in (401, 403)
