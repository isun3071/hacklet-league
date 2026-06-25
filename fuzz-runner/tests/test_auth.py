"""Self-as-oracle auth helpers — pure functions, no server."""
import httpx

from hacklet_runner.auth import _fill, _password_form, parse_set_cookies, session_cookie
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
