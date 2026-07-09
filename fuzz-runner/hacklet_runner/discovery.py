"""Phase 1: discovery. Build a stack-agnostic surface map by crawling the live app over HTTP.

A bounded, same-origin breadth-first crawl from the homepage: it records every reachable route and
every HTML form (action, method, field names). Stays polite and bounded — page and depth caps, same
origin only. Production adds browser-driven discovery (Playwright) for SPA routes this static crawl
can't see (client-rendered forms), plus per-endpoint baselines for oracle differentials.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

import httpx

from . import jsmine, openapi
from .auth import is_password_change_form
from .net import make_client
from .schema import Endpoint, Form, Profile

_LINK = re.compile(r'(?<![-\w])href=["\']([^"\']+)["\']', re.I)
_SRC = re.compile(r'(?<![-\w])src=["\']([^"\']+)["\']', re.I)  # any tag: img / iframe / script / source / ...
_FORM = re.compile(r"<form\b([^>]*)>(.*?)</form>", re.I | re.S)
_ACTION = re.compile(r'(?<![-\w])action=["\']([^"\']*)["\']', re.I)
_METHOD = re.compile(r'(?<![-\w])method=["\']([^"\']*)["\']', re.I)
_ENCTYPE = re.compile(r'(?<![-\w])enctype=["\']([^"\']*)["\']', re.I)
_FIELD = re.compile(r'<(?:input|textarea|select)\b[^>]*(?<![-\w])name=["\']([^"\']+)["\']', re.I)
_INPUT_TAG = re.compile(r"<input\b[^>]*>", re.I)
_IS_FILE = re.compile(r'(?<![-\w])type=["\']?file\b', re.I)

MAX_PAGES = 25
MAX_DEPTH = 2


# A logout/sign-out link must never be crawled or probed: following it destroys the runner's own
# authenticated session, silently de-authing the rest of an --header'd crawl (the classic auth-crawl
# footgun — it's why an authed DVWA crawl kept dropping to the login page mid-run).
_LOGOUT = re.compile(r"(?:^|[/_-])(?:logout|log-?out|log_?out|signout|sign-?out|sign_?out|logoff)\b", re.I)

# Un-rendered client-side template syntax leaking into markup: `${x}` (JS template literal), `{{x}}`
# (Angular/Vue/Handlebars/Jinja), or a stray backtick. A target that ships these in an href/name has a
# rendering bug — they are never real server routes or params, so probing them chases ghost endpoints.
# (`#{x}` Pug/Ruby needs no handling here: `#` is the URL-fragment delimiter, stripped before this check.)
_TEMPLATE_ARTIFACT = re.compile(r"\$\{|\{\{|\}\}|`")


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
    if _TEMPLATE_ARTIFACT.search(path):
        return None  # an un-rendered template literal in the href -> a ghost route, not a real endpoint
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
        em = _ENCTYPE.search(attrs)
        file_fields = [nm.group(1) for tag in _INPUT_TAG.findall(body) if _IS_FILE.search(tag)
                       for nm in [_FIELD.search(tag)] if nm]
        forms.append(Form(
            action=action,
            method=method if method in ("get", "post") else "get",
            fields=_FIELD.findall(body),
            enctype=em.group(1).lower() if em else "",
            file_fields=file_fields,
        ))
    return forms


def discover(base_url: str, render=None, max_pages: int = MAX_PAGES, max_depth: int = MAX_DEPTH,
             headers=None) -> Profile:
    routes: dict[str, None] = {}      # insertion-ordered set
    forms: list[Form] = []
    seen_forms: set[tuple] = set()
    visited: set[str] = set()
    # Split a path-bearing --target into ORIGIN + entry path. The client and probes bind to the origin
    # (a path-bearing base_url breaks httpx's relative-redirect resolution -> loops, and breaks the
    # `base_url + "/probe/path"` construction probes rely on), while the crawl SEEDS at the entry path so
    # a --target pointing at a specific page (e.g. bWAPP's /sqli_1.php, whose "/" only redirects to a
    # login/portal the crawler can't navigate) gets THAT page discovered. A bare origin still starts at "/".
    _parsed = urlparse(base_url)
    start_path = _parsed.path or "/"
    base_url = f"{_parsed.scheme}://{_parsed.netloc}" if _parsed.netloc else base_url
    queue: list[tuple[str, int]] = [(start_path, 0)]
    any_response = False
    endpoints: list = []
    js_urls: list[str] = []           # same-origin .js assets to mine for an SPA's API paths
    link_params: dict[str, set] = {}  # path -> query-param NAMES seen in links (?page=, ?id=, ...)

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
                        # capture query-param NAMES from the link (?page=, ?id=, ...) so a reflected /
                        # includable GET param is testable — the crawl otherwise drops the query string
                        if "?" in href:
                            for name in parse_qs(href.split("?", 1)[1].split("#")[0], keep_blank_values=True):
                                if not _TEMPLATE_ARTIFACT.search(name):  # skip a `${x}`/`{{x}}` param name
                                    link_params.setdefault(p, set()).add(name)
                        if p not in visited:
                            queue.append((p, depth + 1))

        # API surface from a served OpenAPI/Swagger spec, plus paths mined from an SPA's JS bundles.
        # Both surface a form-less API the HTML crawl can't see; the fan-out and injection probes target
        # them. Neither present -> [] (the HTML-only path is unchanged). Dedup by (method, raw_path).
        endpoints = openapi.ingest(base_url, c) + jsmine.ingest(c, js_urls)
        endpoints += [Endpoint(path=p, method="get", query_params=sorted(params), raw_path=p)
                      for p, params in link_params.items()]
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

    # Withhold password-CHANGE forms from the whole surface (like logout links above): probes SUBMIT
    # discovered forms (and fold GET forms into query-param injection targets), so a `password_new`/
    # `password_conf` form would get posted with our own session cookie and reset — and lock out — the
    # account we're grading. DVWA's /vulnerabilities/csrf/ is exactly this. They stay in `routes` (safe
    # to have crawled); only their submittable form/param projection is dropped.
    forms = [f for f in forms if not is_password_change_form(f)]

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
