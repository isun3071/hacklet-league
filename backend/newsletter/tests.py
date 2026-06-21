import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

URL = "/api/newsletter/subscribe/"


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    # AnonRateThrottle counts live in the cache; reset so tests don't trip the limit.
    cache.clear()
    yield
    cache.clear()


class _FakeResp:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text or str(payload or "")

    def json(self):
        return self._payload


@pytest.mark.django_db
def test_subscribe_success(settings, monkeypatch):
    settings.BUTTONDOWN_API_KEY = "k"
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(url=url, headers=headers, json=json)
        return _FakeResp(201, {"email_address": "a@b.com"})

    monkeypatch.setattr("newsletter.views.requests.post", fake_post)
    r = APIClient().post(URL, {"email": "a@b.com"}, format="json")
    assert r.status_code == 201
    assert "confirm" in r.data["detail"].lower()
    assert captured["json"] == {"email_address": "a@b.com"}
    assert captured["headers"]["Authorization"] == "Token k"
    assert captured["url"].endswith("/subscribers")


@pytest.mark.django_db
def test_invalid_email_never_calls_buttondown(settings, monkeypatch):
    settings.BUTTONDOWN_API_KEY = "k"
    calls = {"n": 0}
    monkeypatch.setattr(
        "newsletter.views.requests.post",
        lambda *a, **k: calls.__setitem__("n", calls["n"] + 1),
    )
    r = APIClient().post(URL, {"email": "not-an-email"}, format="json")
    assert r.status_code == 400
    assert calls["n"] == 0


@pytest.mark.django_db
def test_missing_key_returns_unavailable(settings):
    settings.BUTTONDOWN_API_KEY = ""
    r = APIClient().post(URL, {"email": "a@b.com"}, format="json")
    assert r.status_code == 503


@pytest.mark.django_db
def test_already_subscribed_is_friendly(settings, monkeypatch):
    settings.BUTTONDOWN_API_KEY = "k"
    monkeypatch.setattr(
        "newsletter.views.requests.post",
        lambda *a, **k: _FakeResp(
            400, {"code": "email_already_exists"},
            '{"code":"email_already_exists","detail":"already subscribed"}',
        ),
    )
    r = APIClient().post(URL, {"email": "a@b.com"}, format="json")
    assert r.status_code == 200
    assert "already" in r.data["detail"].lower()


@pytest.mark.django_db
def test_upstream_failure_is_502(settings, monkeypatch):
    settings.BUTTONDOWN_API_KEY = "k"
    monkeypatch.setattr(
        "newsletter.views.requests.post", lambda *a, **k: _FakeResp(500, {}, "boom")
    )
    r = APIClient().post(URL, {"email": "a@b.com"}, format="json")
    assert r.status_code == 502
