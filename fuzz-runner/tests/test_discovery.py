"""Discovery tests — the crawl must build the right surface map (routes + structured forms) from
the reference apps. No Docker: a reference app is hosted via SubprocessDeployer and crawled.
"""
import pathlib

import pytest

from hacklet_runner.deploy import SubprocessDeployer
from hacklet_runner.discovery import discover

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
    assert {"/", "/login", "/search", "/crash", "/heavy"} <= set(profile.routes)
    logins = [f for f in profile.forms if f.action == "/login"]
    assert logins, "should discover the /login form"
    assert logins[0].method == "post"
    assert set(logins[0].fields) == {"username", "password"}
    assert profile.capabilities["any_endpoint_accepts_text_input"] is True
    assert profile.form_endpoints == ["/login"]  # back-compat property


def test_minimal_has_no_forms(serve):
    profile = discover(serve("minimal"))
    assert profile.routes == ["/"]  # no links, no forms
    assert profile.forms == []
    assert profile.capabilities["any_endpoint_accepts_text_input"] is False


def test_hardened_same_surface_as_vulnerable(serve):
    profile = discover(serve("hardened"))
    assert {"/", "/login", "/search", "/crash", "/heavy"} <= set(profile.routes)
    assert any(
        f.action == "/login" and set(f.fields) == {"username", "password"} for f in profile.forms
    )
