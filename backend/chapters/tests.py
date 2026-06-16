import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from chapters.models import Chapter, ChapterMembership

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

    membership = ChapterMembership.objects.get(chapter=chapter, user=user)
    assert ChapterMembership.Role.OWNER in membership.roles
    assert membership.status == ChapterMembership.Status.ACTIVE


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
