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
