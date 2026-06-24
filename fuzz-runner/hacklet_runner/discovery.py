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

from .schema import Form, Profile

_LINK = re.compile(r'href=["\']([^"\']+)["\']', re.I)
_FORM = re.compile(r"<form\b([^>]*)>(.*?)</form>", re.I | re.S)
_ACTION = re.compile(r'action=["\']([^"\']*)["\']', re.I)
_METHOD = re.compile(r'method=["\']([^"\']*)["\']', re.I)
_FIELD = re.compile(r'<(?:input|textarea|select)\b[^>]*\bname=["\']([^"\']+)["\']', re.I)

MAX_PAGES = 25
MAX_DEPTH = 2


def _same_origin_path(href: str, base_url: str, page_path: str) -> str | None:
    """Resolve href against the current page; return its path if same-origin, else None."""
    href = href.split("#")[0].strip()
    if not href or href.startswith(("mailto:", "javascript:", "tel:", "data:")):
        return None
    base = urlparse(base_url)
    page_abs = urljoin(f"{base.scheme}://{base.netloc}", page_path)
    target = urlparse(urljoin(page_abs, href))
    if target.netloc != base.netloc:
        return None
    return target.path or "/"


def _parse_forms(matches, base_url: str, page_path: str) -> list[Form]:
    forms = []
    for attrs, body in matches:
        am, mm = _ACTION.search(attrs), _METHOD.search(attrs)
        raw_action = am.group(1).strip() if am else ""
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


def discover(base_url: str, max_pages: int = MAX_PAGES, max_depth: int = MAX_DEPTH) -> Profile:
    routes: dict[str, None] = {}      # insertion-ordered set
    forms: list[Form] = []
    seen_forms: set[tuple] = set()
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [("/", 0)]
    any_response = False

    with httpx.Client(base_url=base_url, timeout=5.0, follow_redirects=True) as c:
        while queue and len(visited) < max_pages:
            path, depth = queue.pop(0)
            if path in visited:
                continue
            visited.add(path)
            try:
                resp = c.get(path)
            except httpx.HTTPError:
                continue
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
            if depth < max_depth:
                for href in _LINK.findall(html):
                    p = _same_origin_path(href, base_url, path)
                    if p:
                        routes.setdefault(p, None)
                        if p not in visited:
                            queue.append((p, depth + 1))

    capabilities = {
        "at_least_one_http_endpoint_exists": any_response,
        "any_endpoint_accepts_text_input": any(f.fields for f in forms),
    }
    return Profile(base_url=base_url, routes=list(routes), forms=forms, capabilities=capabilities)
