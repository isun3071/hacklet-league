"""Headless-browser harness (Playwright). Renders a page so discovery sees client-rendered forms
and routes a static crawl misses (SPAs), and (later) so DOM/stored XSS and Core Web Vitals can be
measured. Optional: every entry point degrades to None when no browser is available, so the rest of
the runner is unaffected.

Browser-agnostic: tries Playwright's pinned bundled Chromium first (reproducible), then any system
browser (chromium / chrome / msedge channels), so it works wherever one is available.
"""
from __future__ import annotations

import contextlib
import time
import urllib.parse

# An <img onerror> payload executes when inserted into the DOM (unlike a bare <script>), so it fires
# for both reflected-that-executes and DOM-sink XSS. The marker is read back from window.
_XSS_PAYLOAD = "<img src=x onerror=\"window.__hl_domxss='hl-domxss-9a2b'\">"
_XSS_MARKER = "hl-domxss-9a2b"


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


def _apply_auth(page, url: str, headers) -> None:
    """Send caller-supplied auth on browser requests so the browser probes reach a session/SSO-gated
    authenticated surface: a Cookie header -> the browser cookie jar, everything else (e.g. a Bearer
    Authorization) -> extra HTTP headers."""
    if not headers:
        return
    extra = {k: v for k, v in headers.items() if k.lower() != "cookie"}
    if extra:
        page.set_extra_http_headers(extra)
    cookie = next((v for k, v in headers.items() if k.lower() == "cookie"), None)
    if cookie:
        host = urllib.parse.urlparse(url).hostname
        jar = []
        for part in cookie.split(";"):
            if "=" in part:
                name, _, val = part.strip().partition("=")
                jar.append({"name": name, "value": val, "domain": host, "path": "/"})
        if jar:
            page.context.add_cookies(jar)


def render_html(url: str, headers=None, timeout: float = 15.0) -> str | None:
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
                _apply_auth(page, url, headers)
                page.goto(url, timeout=timeout * 1000, wait_until="load")
                page.wait_for_timeout(300)  # let client JS settle
                return page.content()
            finally:
                browser.close()
    except Exception:
        return None


def first_contentful_paint(url: str, headers=None, timeout: float = 12.0) -> float | None:
    """Render url and return First Contentful Paint in milliseconds (the user-facing 'time to see
    something' metric). None if no browser, render fails, or nothing ever paints."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as pw:
            b = _launch(pw)
            if b is None:
                return None
            try:
                page = b.new_page()
                _apply_auth(page, url, headers)
                page.goto(url, timeout=timeout * 1000, wait_until="load")
                page.wait_for_timeout(2500)  # allow delayed/contentful paint to occur
                return page.evaluate(
                    "() => { const e = performance.getEntriesByName('first-contentful-paint')[0];"
                    " return e ? e.startTime : null; }"
                )
            finally:
                b.close()
    except Exception:
        return None


# Hand-rolled presence-based accessibility checks (no axe-core dependency): missing lang, images with
# no alt attribute, form fields with no accessible name, and icon-only controls with no name. Presence
# only — the *content* of alt text etc. is intent-dependent (the judge's domain), not ours.
_A11Y_JS = """() => {
  let v = 0;
  const root = document.documentElement;
  if (!root.lang || !root.lang.trim()) v++;
  v += document.querySelectorAll('img:not([alt])').length;
  const fields = document.querySelectorAll(
    'input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=image]), textarea, select');
  fields.forEach(el => {
    const named = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')
      || el.getAttribute('title') || (el.id && document.querySelector('label[for="' + el.id + '"]'))
      || el.closest('label');
    if (!named) v++;
  });
  document.querySelectorAll('button, a[href]').forEach(el => {
    const txt = (el.textContent || '').trim();
    const named = el.getAttribute('aria-label') || el.getAttribute('title')
      || el.querySelector('img[alt]:not([alt=""])');
    if (!txt && !named) v++;
  });
  return v;
}"""


def a11y_violations(url: str, headers=None, timeout: float = 12.0) -> int | None:
    """Render url and count presence-based accessibility violations (missing lang / alt / field label /
    control name). None if no browser or the render fails."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as pw:
            b = _launch(pw)
            if b is None:
                return None
            try:
                page = b.new_page()
                _apply_auth(page, url, headers)
                page.goto(url, timeout=timeout * 1000, wait_until="load")
                page.wait_for_timeout(300)
                return page.evaluate(_A11Y_JS)
            finally:
                b.close()
    except Exception:
        return None


def console_errors(url: str, headers=None, timeout: float = 12.0) -> int | None:
    """Render url and count uncaught JavaScript errors thrown on load (pageerror) — a page that throws
    as it renders is broken regardless of intent. None if no browser or the render fails."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as pw:
            b = _launch(pw)
            if b is None:
                return None
            try:
                page = b.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                _apply_auth(page, url, headers)
                page.goto(url, timeout=timeout * 1000, wait_until="load")
                page.wait_for_timeout(500)  # let late/async errors surface
                return len(errors)
            finally:
                b.close()
    except Exception:
        return None


def dom_xss_executes(base_url: str, paths, params=("q",), max_attempts: int = 24,
                     total_timeout: float = 45.0, headers=None) -> bool:
    """Inject an executing payload into candidate query params of each path, render, and return True
    if it ran (the payload's JS set a window global) — i.e. XSS that *executes* in the DOM, which a
    source-only reflection check misses (reflected-that-executes and DOM-sink XSS). False if no
    browser or nothing executed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as pw:
            b = _launch(pw)
            if b is None:
                return False
            try:
                page = b.new_page()
                _apply_auth(page, base_url, headers)
                attempts = 0
                deadline = time.monotonic() + total_timeout  # overall wall-clock cap: a slow-loris
                for path in paths:                            # target that stalls each goto can't tie
                    for param in params:                      # up the probe (24 x 8s would be ~3 min)
                        if attempts >= max_attempts or time.monotonic() > deadline:
                            return False
                        attempts += 1
                        url = f"{base_url.rstrip('/')}{path}?{param}={urllib.parse.quote(_XSS_PAYLOAD)}"
                        with contextlib.suppress(Exception):
                            page.goto(url, timeout=8000, wait_until="load")
                            page.wait_for_timeout(150)
                            if page.evaluate("() => window.__hl_domxss") == _XSS_MARKER:
                                return True  # fresh document each goto, so a hit is this page's
                return False
            finally:
                b.close()
    except Exception:
        return False
