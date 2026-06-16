import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_create_user_is_email_based():
    u = User.objects.create_user(email="a@example.com", password="pw")
    assert u.email == "a@example.com"
    assert u.check_password("pw")
    assert not u.is_staff
    assert not u.is_superadmin


@pytest.mark.django_db
def test_create_superuser_flags():
    u = User.objects.create_superuser(email="admin@example.com", password="pw")
    assert u.is_staff and u.is_superuser and u.is_superadmin


@pytest.mark.django_db
def test_me_requires_auth():
    assert APIClient().get("/api/me/").status_code in (401, 403)


@pytest.mark.django_db
def test_me_returns_and_updates_profile():
    u = User.objects.create_user(email="a@example.com", password="pw", display_name="A")
    client = APIClient()
    client.force_authenticate(u)

    r = client.get("/api/me/")
    assert r.status_code == 200
    assert r.data["email"] == "a@example.com"

    r = client.patch("/api/me/", {"display_name": "Renamed"}, format="json")
    assert r.status_code == 200
    u.refresh_from_db()
    assert u.display_name == "Renamed"
