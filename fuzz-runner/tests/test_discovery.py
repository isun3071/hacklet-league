"""Discovery tests — the crawl must build the right surface map (routes + structured forms) from
the reference apps. No Docker: a reference app is hosted via SubprocessDeployer and crawled.
"""
import pathlib

import pytest

from hacklet_runner.deploy import SubprocessDeployer
from hacklet_runner.discovery import (
    _ACTION, _FIELD, _FORM, _LINK, _SRC, _parse_forms, _same_origin_path, discover,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
REFS = ROOT / "references"


@pytest.fixture
def serve():
    deployers = []

    def _serve(app: str) -> str:
        d = SubprocessDeployer(str(REFS / app / "app.py"))
        deployers.append(d)
        return d.deploy().base_url

    yield _serve
    for d in deployers:
        d.teardown()


def test_discovers_routes_and_login_form(serve):
    profile = discover(serve("vulnerable"))
    assert {"/", "/login", "/search", "/crash", "/heavy", "/config.js", "/register"} <= set(profile.routes)
    logins = [f for f in profile.forms if f.action == "/login"]
    assert logins, "should discover the /login form"
    assert logins[0].method == "post"
    assert set(logins[0].fields) == {"username", "password"}
    searches = [f for f in profile.forms if f.action == "/search"]
    assert searches and searches[0].method == "get" and searches[0].fields == ["q"]
    registers = [f for f in profile.forms if f.action == "/register"]
    assert registers and "password" in registers[0].fields
    assert profile.capabilities["any_endpoint_accepts_text_input"] is True
    assert profile.capabilities["any_form_has_password"] is True
    assert {"/login", "/search", "/register"} <= set(profile.form_endpoints)  # back-compat property


def test_self_submitting_form_resolves_to_current_page():
    # action="#" (DVWA, many CMS forms) submits back to the current page, not a dead fragment
    html = '<form action="#" method="get"><input name="id"><input type="submit" name="Submit"></form>'
    forms = _parse_forms(_FORM.findall(html), "http://x", "/vulnerabilities/sqli/")
    assert len(forms) == 1
    assert forms[0].action == "/vulnerabilities/sqli/" and forms[0].fields == ["id", "Submit"]


def test_logout_links_are_excluded_from_the_crawl():
    # following a logout link would destroy the runner's own authenticated session
    for href in ("/logout.php", "logout", "/auth/sign-out", "/user_logout", "/logoff"):
        assert _same_origin_path(href, "http://x", "/") is None, href
    # ordinary links (incl. lookalikes that merely contain 'log') are kept
    assert _same_origin_path("/dashboard", "http://x", "/") == "/dashboard"
    assert _same_origin_path("/blog/post", "http://x", "/") == "/blog/post"


def test_template_literal_artifacts_are_excluded_from_the_crawl():
    # un-rendered client-side templates leaked into markup are ghost routes, not real endpoints
    for href in ("/api/${apiBase}/items", "/{{userId}}/profile", "/list/{{i}}", "/x/`tpl`/y"):
        assert _same_origin_path(href, "http://x", "/") is None, href
    # a real route that merely contains a dollar sign or braces-free path is kept
    assert _same_origin_path("/api/v1/items", "http://x", "/") == "/api/v1/items"
    assert _same_origin_path("/prices$", "http://x", "/") == "/prices$"  # lone $, not a ${...} artifact


def test_attribute_regexes_ignore_data_attrs():
    # data-* attributes must not be mistaken for href/name/action (no leading boundary -> phantoms).
    assert _LINK.findall('<a href="/real">x</a>') == ["/real"]
    assert _LINK.findall('<div data-href="/phantom"></div>') == []
    assert _FIELD.findall('<input data-name="phantom" name="real">') == ["real"]
    assert _FIELD.findall('<input data-name="phantom" type="text">') == []
    assert _ACTION.findall('<form data-action="/x" action="/real">') == ["/real"]


def test_src_extraction_spans_tags():
    assert _SRC.findall('<img src="/api/avatar/5"><iframe src="/embed"><script src="/app.js">') == \
        ["/api/avatar/5", "/embed", "/app.js"]
    assert _SRC.findall('<img data-src="/lazy">') == []  # data-src guarded (no leading boundary)


def test_minimal_has_no_forms(serve):
    profile = discover(serve("minimal"))
    assert profile.routes == ["/"]  # no links, no forms
    assert profile.forms == []
    assert profile.capabilities["any_endpoint_accepts_text_input"] is False
    assert profile.capabilities["any_form_has_password"] is False


def test_hardened_same_surface_as_vulnerable(serve):
    profile = discover(serve("hardened"))
    assert {"/", "/login", "/search", "/crash", "/heavy"} <= set(profile.routes)
    assert any(
        f.action == "/login" and set(f.fields) == {"username", "password"} for f in profile.forms
    )
