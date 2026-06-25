"""Self-as-oracle auth helpers — pure functions, no server."""
import httpx

from hacklet_runner.auth import (
    _fill,
    _password_form,
    create_form,
    is_csrf_field,
    parse_set_cookies,
    session_cookie,
)
from hacklet_runner.schema import Form


def _resp(set_cookies):
    return httpx.Response(200, headers=[("set-cookie", c) for c in set_cookies])


def test_parse_set_cookies_reads_flags():
    by = {c["name"]: c for c in parse_set_cookies(
        _resp(["session=abc; HttpOnly; SameSite=Lax", "csrftoken=xyz"])
    )}
    assert by["session"]["httponly"] and by["session"]["samesite"]
    assert not by["csrftoken"]["httponly"]


def test_session_cookie_picks_session_not_csrf():
    c = session_cookie(_resp(["csrftoken=xyz", "session=abc; HttpOnly"]))
    assert c["name"] == "session" and c["httponly"]


def test_password_form_prefers_register():
    forms = [
        Form(action="/login", method="post", fields=["username", "password"]),
        Form(action="/register", method="post", fields=["username", "email", "password"]),
    ]
    assert _password_form(forms).action == "/register"


def test_password_form_none_without_password():
    assert _password_form([Form(action="/search", method="get", fields=["q"])]) is None


def test_fill_maps_fields_by_name():
    data = _fill(Form(action="/register", method="post", fields=["username", "email", "password"]),
                 "bob", "pw")
    assert data == {"username": "bob", "email": "bob@example.com", "password": "pw"}


def test_create_form_picks_content_form():
    forms = [
        Form(action="/login", method="post", fields=["username", "password"]),
        Form(action="/register", method="post", fields=["username", "password"]),
        Form(action="/search", method="get", fields=["q"]),
        Form(action="/notes", method="post", fields=["text"]),
    ]
    assert create_form(forms).action == "/notes"


def test_create_form_none_when_only_auth_and_search():
    forms = [
        Form(action="/login", method="post", fields=["username", "password"]),
        Form(action="/search", method="get", fields=["q"]),
    ]
    assert create_form(forms) is None


def test_is_csrf_field():
    assert is_csrf_field("csrf_token") and is_csrf_field("authenticity_token") and is_csrf_field("_token")
    assert not is_csrf_field("username") and not is_csrf_field("text")
