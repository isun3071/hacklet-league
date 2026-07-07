"""Phase 1: discovery. Build a stack-agnostic surface map by crawling the live app over HTTP.

A bounded, same-origin breadth-first crawl from the homepage: it records every reachable route and
every HTML form (action, method, field names). Stays polite and bounded — page and depth caps, same
origin only. Production adds browser-driven discovery (Playwright) for SPA routes this static crawl
can't see (client-rendered forms), plus per-endpoint baselines for oracle differentials.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx

from . import jsmine, openapi
from .net import make_client
from .schema import Form, Profile

_LINK = re.compile(r'(?<![-\w])href=["\']([^"\']+)["\']', re.I)
_SRC = re.compile(r'(?<![-\w])src=["\']([^"\']+)["\']', re.I)  # any tag: img / iframe / script / source / ...
_FORM = re.compile(r"<form\b([^>]*)>(.*?)</form>", re.I | re.S)
_ACTION = re.compile(r'(?<![-\w])action=["\']([^"\']*)["\']', re.I)
_METHOD = re.compile(r'(?<![-\w])method=["\']([^"\']*)["\']', re.I)
_FIELD = re.compile(r'<(?:input|textarea|select)\b[^>]*(?<![-\w])name=["\']([^"\']+)["\']', re.I)

MAX_PAGES = 25
MAX_DEPTH = 2


# A logout/sign-out link must never be crawled or probed: following it destroys the runner's own
# authenticated session, silently de-authing the rest of an --header'd crawl (the classic auth-crawl
# footgun — it's why an authed DVWA crawl kept dropping to the login page mid-run).
_LOGOUT = re.compile(r"(?:^|[/_-])(?:logout|log-?out|log_?out|signout|sign-?out|sign_?out|logoff)\b", re.I)


def _same_origin_path(href: str, base_url: str, page_path: str) -> str | None:
    """Resolve href against the current page; return its path if same-origin (and not a logout link),
    else None."""
    href = href.split("#")[0].strip()
    if not href or href.startswith(("mailto:", "javascript:", "tel:", "data:")):
        return None
    base = urlparse(base_url)
    page_abs = urljoin(f"{base.scheme}://{base.netloc}", page_path)
    target = urlparse(urljoin(page_abs, href))
    if target.netloc != base.netloc:
        return None
    path = target.path or "/"
    if _LOGOUT.search(path):
        return None  # crawling logout would destroy the authenticated session
    return path


def _parse_forms(matches, base_url: str, page_path: str) -> list[Form]:
    forms = []
    for attrs, body in matches:
        am, mm = _ACTION.search(attrs), _METHOD.search(attrs)
        # a "#..."/empty action submits back to the CURRENT page (very common: DVWA, many CMS forms) —
        # strip the fragment so it resolves to page_path instead of being dropped as un-resolvable.
        raw_action = (am.group(1).strip() if am else "").split("#")[0]
        action = _same_origin_path(raw_action, base_url, page_path) if raw_action else page_path
        if action is None:  # cross-origin action — not our target
            continue
        method = mm.group(1).lower() if mm else "get"
        forms.append(Form(
            action=action,
            method=method if method in ("get", "post") else "get",
            fields=_FIELD.findall(body),
        ))
    return forms


def discover(base_url: str, render=None, max_pages: int = MAX_PAGES, max_depth: int = MAX_DEPTH,
             headers=None) -> Profile:
    routes: dict[str, None] = {}      # insertion-ordered set
    forms: list[Form] = []
    seen_forms: set[tuple] = set()
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [("/", 0)]
    any_response = False
    endpoints: list = []
    js_urls: list[str] = []           # same-origin .js assets to mine for an SPA's API paths

    with make_client(base_url, headers, timeout=5.0, follow_redirects=True) as c:
        while queue and len(visited) < max_pages:
            path, depth = queue.pop(0)
            if path in visited:
                continue
            visited.add(path)
            try:
                resp = c.get(path)
            except (httpx.HTTPError, httpx.InvalidURL):
                continue  # InvalidURL isn't an HTTPError: a hostile target served a control-char path
            any_response = True
            routes[path] = None
            if "html" not in resp.headers.get("content-type", "").lower():
                continue
            html = resp.text
            for form in _parse_forms(_FORM.findall(html), base_url, path):
                key = (form.action, form.method, tuple(form.fields))
                if key not in seen_forms:
                    seen_forms.add(key)
                    forms.append(form)
                    routes.setdefault(form.action, None)
            for src in _SRC.findall(html):  # tag srcs (img/iframe/script/...) are scan targets, not crawled
                p = _same_origin_path(src, base_url, path)
                if p:
                    routes.setdefault(p, None)
                    if p.split("?")[0].endswith(".js"):
                        js_urls.append(p)
            if depth < max_depth:
                for href in _LINK.findall(html):
                    p = _same_origin_path(href, base_url, path)
                    if p:
                        routes.setdefault(p, None)
                        if p not in visited:
                            queue.append((p, depth + 1))

        # API surface from a served OpenAPI/Swagger spec, plus paths mined from an SPA's JS bundles.
        # Both surface a form-less API the HTML crawl can't see; the fan-out and injection probes target
        # them. Neither present -> [] (the HTML-only path is unchanged). Dedup by (method, raw_path).
        endpoints = openapi.ingest(base_url, c) + jsmine.ingest(c, js_urls)
        seen_eps: set[tuple] = set()
        endpoints = [e for e in endpoints
                     if (e.method, e.raw_path) not in seen_eps and not seen_eps.add((e.method, e.raw_path))]
        for ep in endpoints:
            routes.setdefault(ep.path, None)

    browser_ok = False
    if render is not None:  # browser-rendered DOM: client-rendered forms/routes a static crawl misses
        dom = render(base_url.rstrip("/") + "/", headers=headers)
        if dom:
            browser_ok = True  # a real render returned HTML -> the browser actually launched/works
            any_response = True
            for form in _parse_forms(_FORM.findall(dom), base_url, "/"):
                key = (form.action, form.method, tuple(form.fields))
                if key not in seen_forms:
                    seen_forms.add(key)
                    forms.append(form)
                    routes.setdefault(form.action, None)
            for ref in _SRC.findall(dom) + _LINK.findall(dom):
                p = _same_origin_path(ref, base_url, "/")
                if p:
                    routes.setdefault(p, None)

    capabilities = {
        "at_least_one_http_endpoint_exists": any_response,
        # text-input surface = HTML form fields OR API query params / JSON body fields (so the
        # injection probes become applicable on a form-less JSON API discovered via its spec).
        "any_endpoint_accepts_text_input": (
            any(f.fields for f in forms)
            or any(ep.query_params or ep.body_fields for ep in endpoints)
        ),
        "any_form_has_password": any(
            any("pass" in name.lower() for name in form.fields) for form in forms
        ),
        # gate on an ACTUAL successful render, not just --browser: if Playwright/Chrome can't launch,
        # render returns None and browser probes must read N/A, not silently 'clean' (false negative).
        "browser": browser_ok,
        # HSTS and other transport-security headers are meaningless over plain HTTP -> gate on this so
        # those probes read N/A (not a false positive) against an http:// target.
        "served_over_https": base_url.lower().startswith("https"),
    }
    return Profile(base_url=base_url, routes=list(routes), forms=forms, capabilities=capabilities,
                   endpoints=endpoints)
