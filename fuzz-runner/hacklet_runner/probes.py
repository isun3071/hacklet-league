"""Detection primitives.

- MATCHERS: declarative conditions, (response, arg) -> True when slop is present.
- PREDICATES: oracle conditions for hidden sinks, (ctx) -> True when slop is present.

Slop is always the *presence* of a problem (deduction-only): a matcher/predicate returning True
means the probe fires and adds its penalty.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

import httpx

from . import auth, browser

_TRACE = re.compile(
    r"Traceback \(most recent call last\)|File \"[^\"]+\", line \d+, in |"
    r"\bat [\w.$]+\([\w.]+:\d+\)"
)


# ---- declarative matchers -------------------------------------------------------------------

def response_leaks_stack_trace(resp, arg=None) -> bool:
    return bool(_TRACE.search(resp.text))


def ttfb_at_least(resp, arg) -> bool:
    # Slice uses one sample; production samples N and takes the median (see FUZZ_RUNNER_SPEC).
    return resp.elapsed.total_seconds() >= float(arg)


def response_contains(resp, arg) -> bool:
    # Reflection check (e.g. an injected XSS marker echoed back unescaped).
    return str(arg) in resp.text


def response_missing_header(resp, arg) -> bool:
    return str(arg) not in resp.headers  # httpx headers are case-insensitive


def response_server_error(resp, arg=None) -> bool:
    # A crash is a 5xx the app caused, not 501 (method not implemented) or 405.
    return resp.status_code in (500, 502, 503, 504)


# High-confidence server secrets that must never reach a client. Precision over recall: we skip
# public-by-design values (Firebase apiKey AIza..., Stripe publishable pk_..., generic JWT session
# tokens), because a false positive wrongly penalizes a non-flaw.
_SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),               # AWS access key id
    re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{16,}"),  # Stripe live secret / restricted key
    re.compile(r"\bsk_test_[0-9A-Za-z]{16,}"),         # Stripe test secret key
    re.compile(r"\bghp_[0-9A-Za-z]{36}\b"),            # GitHub personal access token
    re.compile(r"\bgithub_pat_[0-9A-Za-z_]{20,}"),     # GitHub fine-grained PAT
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}"),     # Slack token
]


def response_leaks_secret(resp, arg=None) -> bool:
    return any(p.search(resp.text) for p in _SECRET_PATTERNS)


# Files that must never be served at the webroot (deploying with .env / .git present is classic
# slop). Each requires status 200 AND a content signature, so a 404 / redirect reads clean.
_DOTENV = re.compile(r"(?im)^[ \t]*(?:export[ \t]+)?[A-Z0-9_]*(?:SECRET|PASSWORD|TOKEN|KEY|CREDENTIAL|DATABASE_URL)[A-Z0-9_]*[ \t]*=")


def response_is_dotenv(resp, arg=None) -> bool:
    return resp.status_code == 200 and bool(_DOTENV.search(resp.text))


def response_is_git_config(resp, arg=None) -> bool:
    return resp.status_code == 200 and "[core]" in resp.text and "repositoryformatversion" in resp.text


def response_is_git_head(resp, arg=None) -> bool:
    # symbolic ref (ref: refs/...) OR a detached-HEAD raw commit SHA
    return resp.status_code == 200 and bool(re.fullmatch(r"ref: refs/\S+|[0-9a-f]{40}", resp.text.strip()))


MATCHERS = {
    "response_leaks_stack_trace": response_leaks_stack_trace,
    "ttfb_at_least": ttfb_at_least,
    "response_contains": response_contains,
    "response_missing_header": response_missing_header,
    "response_server_error": response_server_error,
    "response_leaks_secret": response_leaks_secret,
    "response_is_dotenv": response_is_dotenv,
    "response_is_git_config": response_is_git_config,
    "response_is_git_head": response_is_git_head,
}


# ---- oracle predicates ----------------------------------------------------------------------

def _authed(resp) -> bool:
    return resp.status_code == 200 and "welcome" in resp.text.lower()


def sqli_auth_bypass(ctx, probe) -> bool:
    """Boolean/auth-bypass oracle: a benign login fails, an injection payload succeeds. The
    divergence (only possible if the input reaches a live, unparameterized query) is the slop.
    The payload comes from the probe, so variant-group members reuse one oracle with different
    syntaxes."""
    payload = probe.probe.get("payload", "' OR '1'='1' -- ")
    for endpoint in ctx.profile.form_endpoints or ["/login"]:
        baseline = ctx.client.post(
            endpoint, data={"username": "zzz_no_such_user", "password": "x"}
        )
        attack = ctx.client.post(endpoint, data={"username": payload, "password": "x"})
        if _authed(attack) and not _authed(baseline):
            return True
    return False


def session_cookie_missing_flag(ctx, probe) -> bool:
    """Self-as-oracle: register an account, then inspect the session cookie it sets. Slop if it
    lacks the hardening flag named in the probe (httponly | samesite)."""
    flag = probe.probe.get("flag", "httponly")
    account = auth.register_account(ctx.base_url, ctx.profile)
    if account is None:
        return False  # registration not possible (applicability gates this) -> treat as clean
    try:
        cookie = auth.session_cookie(account.register_response)
        return cookie is not None and not cookie[flag]
    finally:
        account.client.close()


def csrf_missing(ctx, probe) -> bool:
    """Self-as-oracle: a state-changing POST that succeeds cross-site with no CSRF token and no
    SameSite cookie -> no CSRF defense. Skips when the form carries a token or the session cookie is
    SameSite (both valid defenses), so only genuinely cross-site-exploitable requests are flagged."""
    form = auth.create_form(ctx.profile.forms)
    if form is None:
        return False
    if any(auth.is_csrf_field(f) for f in form.fields):
        return False
    account = auth.register_account(ctx.base_url, ctx.profile, suffix="_csrf")
    if account is None:
        return False
    try:
        cookie = auth.session_cookie(account.register_response)
        if cookie is None or cookie["samesite"]:
            return False  # a SameSite cookie blocks cross-site sending -> already defended
        resp = account.client.request(
            "POST", form.action,
            data={n: "hl-csrf" for n in form.fields},
            headers={"Origin": "https://evil.example"},
            follow_redirects=False,
        )
        return resp.status_code < 400  # accepted cross-site, no token, no SameSite -> CSRF
    except (httpx.HTTPError, httpx.InvalidURL):
        return False  # transport/URL failure mid-POST -> can't prove CSRF (clean), don't crash run()
    finally:
        account.client.close()


def dom_xss(ctx, probe) -> bool:
    """Browser oracle: inject an executing payload across discovered routes and render — fires when
    it runs in the DOM, catching reflected-that-executes and DOM-sink XSS a source check misses.
    Gated on the `browser` capability, so it's N/A unless the run enabled rendering."""
    return browser.dom_xss_executes(ctx.base_url, ctx.profile.routes)


def slow_first_paint(ctx, probe) -> bool:
    """Browser oracle: render and read First Contentful Paint; slop if it exceeds the gate — the
    user-facing 'slow app' signal (client render delay, distinct from server TTFB). Browser-gated."""
    fcp = browser.first_contentful_paint(ctx.base_url.rstrip("/") + probe.probe.get("target", "/"))
    # isinstance guard (not just None): a hostile page can redefine performance.* so FCP marshals
    # back as a non-numeric value, which would make `fcp > threshold` raise TypeError and DNF the run.
    return isinstance(fcp, (int, float)) and fcp > probe.probe.get("threshold_ms", 1000)


def idor_horizontal(ctx, probe) -> bool:
    """Self-as-oracle: register A and B, A creates a resource, B fetches it by URL. If B can read
    A's content, object-level access control is broken (horizontal IDOR)."""
    form = auth.create_form(ctx.profile.forms)
    if form is None:
        return False
    a = auth.register_account(ctx.base_url, ctx.profile, suffix="_a")
    b = auth.register_account(ctx.base_url, ctx.profile, suffix="_b")
    if a is None or b is None:
        for acct in (a, b):
            if acct:
                acct.client.close()
        return False
    try:
        marker = "hl-idor-7a3f9c"
        created = a.client.request("POST", form.action, data={n: marker for n in form.fields})
        resource = created.url.path
        if not resource or resource == form.action:  # no redirect to a distinct resource -> N/A
            return False
        leaked = b.client.get(resource)
        return leaked.status_code == 200 and marker in leaked.text
    except (httpx.HTTPError, httpx.InvalidURL):
        return False
    finally:
        a.client.close()
        b.client.close()


def _concurrent_creates(base_url, path, cookies, n: int = 12):
    def create():
        try:
            with httpx.Client(base_url=base_url, timeout=10.0, follow_redirects=True, cookies=cookies) as c:
                return c.post(path, data={"text": "race"}).url.path
        except Exception:
            return None
    with ThreadPoolExecutor(max_workers=n) as ex:
        return [f.result() for f in [ex.submit(create) for _ in range(n)]]


def race_resource_ids(ctx, probe) -> bool:
    """Self-as-oracle: register, fire N concurrent resource creates, and inspect the assigned IDs.
    Duplicate IDs mean id allocation isn't atomic under concurrency — a race condition. N distinct
    creates must yield N distinct ids, so a collision is provable without knowing the app's intent."""
    form = auth.create_form(ctx.profile.forms)
    if form is None:
        return False
    account = auth.register_account(ctx.base_url, ctx.profile, suffix="_race")
    if account is None:
        return False
    try:
        # iterate the jar, not dict(cookies) — dict() raises httpx.CookieConflict when the session
        # cookie was set on multiple paths/domains during the register redirect chain.
        cookies = {c.name: c.value for c in account.client.cookies.jar}
        urls = _concurrent_creates(ctx.base_url, form.action, cookies)
        created = [u for u in urls if u and u != form.action]
        return len(created) >= 2 and len(set(created)) < len(created)
    finally:
        account.client.close()


def _concurrent_get(base_url, path, n: int = 20):
    def get():
        try:
            with httpx.Client(base_url=base_url, timeout=15.0) as c:
                return c.get(path).status_code
        except Exception:
            return None
    with ThreadPoolExecutor(max_workers=n) as ex:
        return [f.result() for f in [ex.submit(get) for _ in range(n)]]


def load_resilience(ctx, probe) -> bool:
    """Fire a concurrent burst at an endpoint; slop if it falls over (>10% 5xx) under load — the
    resource-exhaustion / unsynchronized-shared-state failure that only surfaces under concurrency."""
    statuses = _concurrent_get(ctx.base_url, probe.probe.get("target", "/"))
    done = [s for s in statuses if s is not None]
    errors = sum(1 for s in done if s >= 500)
    return bool(done) and errors / len(done) > 0.1


PREDICATES = {
    "sqli_auth_bypass": sqli_auth_bypass,
    "session_cookie_missing_flag": session_cookie_missing_flag,
    "csrf_missing": csrf_missing,
    "idor_horizontal": idor_horizontal,
    "dom_xss": dom_xss,
    "race_resource_ids": race_resource_ids,
    "load_resilience": load_resilience,
    "slow_first_paint": slow_first_paint,
}
