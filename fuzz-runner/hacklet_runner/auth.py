"""Self-as-oracle: register the runner's own account so it can test the authenticated surface.

Account creation is just an HTTP POST to a registration form — discover the form (a password field),
fill it heuristically, submit, and hold the resulting session. Reusable by the auth-mechanics probes
(cookie hygiene now; logout-invalidation, login rate-limit, two-account IDOR next).
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from .schema import Form, Profile

# Common session cookie names. Excludes CSRF tokens, which are intentionally readable by JS (not
# HttpOnly) — flagging those would be a false positive.
SESSION_COOKIE_NAMES = {
    "session", "sessionid", "session_id", "sid", "connect.sid", "phpsessid",
    "jsessionid", "_session", "auth", "auth_token", "access_token", "token", "jwt",
}

_REGISTER_HINTS = ("register", "signup", "sign-up", "sign_up", "join", "create-account")


@dataclass
class Account:
    username: str
    password: str
    client: httpx.Client          # carries the session cookie jar (for later authed probes)
    register_response: httpx.Response


def _password_form(forms: list[Form]) -> Form | None:
    pw = [f for f in forms if any("pass" in name.lower() for name in f.fields)]
    if not pw:
        return None
    return next((f for f in pw if any(h in f.action.lower() for h in _REGISTER_HINTS)), pw[0])


def _fill(form: Form, username: str, password: str) -> dict[str, str]:
    data = {}
    for name in form.fields:
        low = name.lower()
        if "pass" in low:
            data[name] = password
        elif "email" in low or "mail" in low:
            data[name] = username + "@example.com"
        else:
            data[name] = username
    return data


_CREATE_HINTS = ("note", "post", "item", "todo", "comment", "message", "create", "add", "new")
_NON_CREATE = ("login", "signin", "sign-in", "register", "signup", "sign-up", "search", "query", "logout")


def create_form(forms: list[Form]) -> Form | None:
    """A content-creation form: a POST form with a non-password field that isn't auth/search."""
    cands = [
        f for f in forms
        if (f.method or "post").lower() == "post"
        and f.fields
        and not any(h in f.action.lower() for h in _NON_CREATE)
        and not all("pass" in n.lower() for n in f.fields)
    ]
    if not cands:
        return None
    return next((f for f in cands if any(h in f.action.lower() for h in _CREATE_HINTS)), cands[0])


def register_account(base_url: str, profile: Profile, suffix: str = "") -> Account | None:
    """Create a fresh account via the discovered registration form. Returns None when there's no
    usable form or registration fails (email verification / CAPTCHA), so the caller treats it as N/A."""
    form = _password_form(profile.forms)
    if form is None:
        return None
    username = "hacklet_probe" + suffix
    password = "Hl-Probe-Passw0rd!"
    client = httpx.Client(base_url=base_url, timeout=15.0, follow_redirects=True)
    try:
        resp = client.request("POST", form.action, data=_fill(form, username, password))
    except httpx.HTTPError:
        client.close()
        return None
    return Account(username=username, password=password, client=client, register_response=resp)


def parse_set_cookies(resp: httpx.Response) -> list[dict]:
    """Each Set-Cookie header -> {name, httponly, secure, samesite}. Flags are read from the raw
    header because cookie jars drop them."""
    out = []
    for raw in resp.headers.get_list("set-cookie"):
        first, _, rest = raw.partition(";")
        if "=" not in first:
            continue
        name = first.split("=", 1)[0].strip()
        attrs = {a.split("=", 1)[0].strip().lower() for a in rest.split(";") if a.strip()}
        out.append({
            "name": name,
            "httponly": "httponly" in attrs,
            "secure": "secure" in attrs,
            "samesite": "samesite" in attrs,
        })
    return out


def session_cookie(resp: httpx.Response) -> dict | None:
    return next((c for c in parse_set_cookies(resp) if c["name"].lower() in SESSION_COOKIE_NAMES), None)
