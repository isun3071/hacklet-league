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
