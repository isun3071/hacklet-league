"""Phase 1: discovery. Build a stack-agnostic surface profile from the live app over HTTP.

Slice scope: fetch the homepage, extract internal links + form endpoints, and note whether any
form takes text input. Production adds browser-driven discovery (Playwright) for SPA routes and
per-endpoint baselines for oracle differentials.
"""
from __future__ import annotations

import re

import httpx

from .schema import Profile

_LINK = re.compile(r'href=["\']([^"\']+)["\']', re.I)
_FORM = re.compile(r"<form[^>]*action=[\"']([^\"']+)[\"'][^>]*>(.*?)</form>", re.I | re.S)
_INPUT = re.compile(r"<input\b", re.I)


def discover(base_url: str) -> Profile:
    endpoints: set[str] = {"/"}
    form_endpoints: set[str] = set()
    has_text_input = False

    with httpx.Client(base_url=base_url, timeout=5.0, follow_redirects=True) as c:
        try:
            html = c.get("/").text
        except httpx.HTTPError:
            html = ""

    for href in _LINK.findall(html):
        if href.startswith("/"):
            endpoints.add(href.split("?")[0])
    for action, body in _FORM.findall(html):
        if action.startswith("/"):
            endpoints.add(action)
            form_endpoints.add(action)
            if _INPUT.search(body):
                has_text_input = True

    capabilities = {
        "at_least_one_http_endpoint_exists": len(endpoints) > 0,
        "any_endpoint_accepts_text_input": has_text_input,
    }
    return Profile(
        base_url=base_url,
        endpoints=sorted(endpoints),
        form_endpoints=sorted(form_endpoints),
        capabilities=capabilities,
    )
