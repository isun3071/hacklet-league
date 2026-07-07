"""Discover an SPA's backend API surface by mining its JavaScript bundles for path literals.

A single-page app (Angular/React/Vue) serves a static HTML shell and calls its backend from compiled
JS — so the HTML crawl, and even a browser render, see only the shell, never the API. But the bundle
embeds the API paths as string literals ('/rest/products', '/api/Users', ...). Mining them makes that
surface visible to the fan-out probes (headers / data-exposure / crash) — the only way to grade a
form-less SPA whose backend isn't published as an OpenAPI spec (e.g. Juice Shop).
"""
from __future__ import annotations

import re

import httpx

from .schema import Endpoint

# Quoted absolute paths under an UNAMBIGUOUS API root. Precision over recall: rest/api/graphql/vN are
# backend roots, so this avoids the noise of mining every '/...' string (client-router paths, CSS
# selectors, i18n keys). A path built by concatenation ('/rest/products/' + id) mines as its literal base.
_API_PATH = re.compile(r"""['"`](/(?:rest|api|graphql|v[1-9]\d?)(?:/[A-Za-z0-9_./-]*)?)['"`]""")
_STATIC_EXT = (".js", ".css", ".map", ".json", ".png", ".jpg", ".jpeg", ".svg", ".gif",
               ".woff", ".woff2", ".ttf", ".ico", ".html")

MAX_JS_FILES = 8
MAX_JS_BYTES = 15_000_000
MAX_PATHS = 200


def mine_paths(js: str) -> list[str]:
    """API path literals in one JS blob, deduped, static-asset paths excluded."""
    out = []
    for raw in _API_PATH.findall(js):
        p = raw.rstrip("/") or raw
        if not p.lower().endswith(_STATIC_EXT):
            out.append(p)
    return list(dict.fromkeys(out))


def ingest(client: httpx.Client, js_urls: list[str]) -> list[Endpoint]:
    """Fetch each JS asset (bounded) and mine its API path literals into GET endpoints."""
    paths: list[str] = []
    budget = MAX_JS_BYTES
    for url in js_urls[:MAX_JS_FILES]:
        try:
            r = client.get(url)
        except (httpx.HTTPError, httpx.InvalidURL):
            continue
        is_js = "javascript" in r.headers.get("content-type", "").lower() or url.split("?")[0].endswith(".js")
        if r.status_code != 200 or not is_js:
            continue
        body = r.text[:budget]
        budget -= len(body)
        paths.extend(mine_paths(body))
        if budget <= 0 or len(paths) >= MAX_PATHS:
            break
    paths = list(dict.fromkeys(paths))[:MAX_PATHS]
    return [Endpoint(path=p, method="get", raw_path=p) for p in paths]
