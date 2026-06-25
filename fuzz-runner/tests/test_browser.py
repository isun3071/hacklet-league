"""Browser-harness discovery — the rendered DOM exposes a client-rendered form a static crawl
misses. Requires a headless browser (system Chrome on the dev box); skipped where none is available.
"""
import pathlib

import pytest

from hacklet_runner import browser
from hacklet_runner.deploy import SubprocessDeployer
from hacklet_runner.discovery import discover

ROOT = pathlib.Path(__file__).resolve().parent.parent
REFS = ROOT / "references"

pytestmark = pytest.mark.skipif(not browser.browser_available(), reason="no headless browser")


@pytest.fixture
def spa_url():
    d = SubprocessDeployer(str(REFS / "spa" / "app.py"))
    handle = d.deploy()
    try:
        yield handle.base_url
    finally:
        d.teardown()


def test_static_discovery_misses_spa_form(spa_url):
    # the form is built by JS, so it isn't in the static HTML source
    assert discover(spa_url).capabilities["any_form_has_password"] is False


def test_browser_discovery_finds_spa_form(spa_url):
    profile = discover(spa_url, render=browser.render_html)
    assert profile.capabilities["any_form_has_password"] is True
    assert any(f.action == "/register" and "password" in f.fields for f in profile.forms)


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


def test_dom_xss_detects_sink(serve):
    # vulnerable /dom innerHTMLs the q param (the payload executes); hardened uses textContent (safe)
    assert browser.dom_xss_executes(serve("vulnerable"), ["/dom"]) is True
    assert browser.dom_xss_executes(serve("hardened"), ["/dom"]) is False


def test_cwv_detects_slow_paint(serve):
    # vulnerable /slow injects content late (high FCP); hardened has it in the initial HTML (fast)
    slow = browser.first_contentful_paint(serve("vulnerable") + "/slow")
    assert slow is not None and slow > 1000
    fast = browser.first_contentful_paint(serve("hardened") + "/slow")
    assert fast is not None and fast < 1000
