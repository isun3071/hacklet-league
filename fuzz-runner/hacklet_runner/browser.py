"""Headless-browser harness (Playwright). Renders a page so discovery sees client-rendered forms
and routes a static crawl misses (SPAs), and (later) so DOM/stored XSS and Core Web Vitals can be
measured. Optional: every entry point degrades to None when no browser is available, so the rest of
the runner is unaffected.

Browser-agnostic: tries Playwright's pinned bundled Chromium first (reproducible), then any system
browser (chromium / chrome / msedge channels), so it works wherever one is available.
"""
from __future__ import annotations

import contextlib


def browser_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


# Pinned bundled Chromium first (reproducible), then any system browser. Bundled Chromium for
# Ubuntu 26.04 needs Playwright >= 1.61 (microsoft/playwright#40117); until that releases (latest is
# 1.60) the bundled launch fails here and a system Chrome/Edge channel is used instead.
_LAUNCH_ORDER = ({}, {"channel": "chromium"}, {"channel": "chrome"}, {"channel": "msedge"})


def _launch(p):
    for kwargs in _LAUNCH_ORDER:
        with contextlib.suppress(Exception):
            return p.chromium.launch(headless=True, **kwargs)
    return None


def render_html(url: str, timeout: float = 15.0) -> str | None:
    """Load url in a headless browser and return the rendered DOM. None if no browser is available
    or rendering fails (the caller falls back to the static crawl)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as p:
            browser = _launch(p)
            if browser is None:
                return None
            try:
                page = browser.new_page()
                page.goto(url, timeout=timeout * 1000, wait_until="load")
                page.wait_for_timeout(300)  # let client JS settle
                return page.content()
            finally:
                browser.close()
    except Exception:
        return None
