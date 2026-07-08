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


# Contrast is the ONE accessibility check that needs the CASCADE: the effective text and background
# colors come from stylesheets + inheritance, which only a rendered DOM resolves (getComputedStyle) --
# the static probe can only see inline styles. We compute the WCAG contrast ratio and count text that
# fails the universal 3:1 FLOOR (fails even for large text, so it's unarguable regardless of font size),
# matching the static inline-contrast threshold. Background is the first opaque ancestor (default white).
_CONTRAST_JS = r"""() => {
  const lum = c => { const f = x => { x/=255; return x<=0.03928 ? x/12.92 : Math.pow((x+0.055)/1.055,2.4); };
    return 0.2126*f(c[0]) + 0.7152*f(c[1]) + 0.0722*f(c[2]); };
  const parse = s => { const m = (s||'').match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/);
    return m ? [+m[1],+m[2],+m[3], m[4]===undefined?1:+m[4]] : null; };
  const bg = el => { while (el) { const c = parse(getComputedStyle(el).backgroundColor);
    if (c && c[3] !== 0) return c; el = el.parentElement; } return [255,255,255]; };
  let v = 0;
  document.querySelectorAll('body *').forEach(el => {
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!own) return;                                    // only elements with their OWN visible text
    const st = getComputedStyle(el);
    if (st.visibility === 'hidden' || st.display === 'none' || +st.opacity === 0) return;
    const fg = parse(st.color); if (!fg || fg[3] === 0) return;
    const ratio = (Math.max(lum(fg), lum(bg(el))) + 0.05) / (Math.min(lum(fg), lum(bg(el))) + 0.05);
    if (ratio < 3.0) v++;
  });
  return v;
}"""


def _eval_page(url, headers, timeout, js_list):
    """Render url once and return the summed result of each JS expression, or None if no browser/render."""
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
                return sum(page.evaluate(js) for js in js_list)
            finally:
                b.close()
    except Exception:
        return None


def a11y_violations(url: str, headers=None, timeout: float = 12.0) -> int | None:
    """Render url and count accessibility violations: presence-based (missing lang / alt / field label /
    control name) plus computed-style contrast below the 3:1 floor. None if no browser/render fails."""
    return _eval_page(url, headers, timeout, [_A11Y_JS, _CONTRAST_JS])


def contrast_violations(url: str, headers=None, timeout: float = 12.0) -> int | None:
    """Render url and count text whose computed contrast is below the 3:1 floor (needs the cascade -> a
    real browser). Isolated from the presence checks for direct testing. None if no browser/render."""
    return _eval_page(url, headers, timeout, [_CONTRAST_JS])


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
