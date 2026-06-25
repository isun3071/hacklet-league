"""Detection primitives.

- MATCHERS: declarative conditions, (response, arg) -> True when slop is present.
- PREDICATES: oracle conditions for hidden sinks, (ctx) -> True when slop is present.

Slop is always the *presence* of a problem (deduction-only): a matcher/predicate returning True
means the probe fires and adds its penalty.
"""
from __future__ import annotations

import re
import statistics
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


def response_missing_clickjacking_defense(resp, arg=None) -> bool:
    # Clickjacking is defended by EITHER X-Frame-Options OR a CSP frame-ancestors directive;
    # checking only one header would false-positive on an app that uses the other.
    if "x-frame-options" in resp.headers:
        return False
    return "frame-ancestors" not in resp.headers.get("content-security-policy", "").lower()


def response_cors_misconfigured(resp, arg=None) -> bool:
    # Slop when the app reflects the request Origin into Access-Control-Allow-Origin AND allows
    # credentials: any site can then make credentialed cross-origin reads. Bare ACAO:* is excluded
    # (browsers refuse credentials with *), so this flags only the genuinely exploitable case.
    sent_origin = resp.request.headers.get("origin", "")
    acao = resp.headers.get("access-control-allow-origin", "")
    creds = resp.headers.get("access-control-allow-credentials", "").lower() == "true"
    return bool(sent_origin) and acao == sent_origin and creds


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
    "response_missing_clickjacking_defense": response_missing_clickjacking_defense,
    "response_cors_misconfigured": response_cors_misconfigured,
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


def login_no_rate_limit(ctx, probe) -> bool:
    """Self-as-oracle: fire N wrong-password logins at the login form; slop if NONE is throttled
    (HTTP 429/423). With no brute-force protection every attempt returns the same auth-failure status,
    enabling credential stuffing / password spraying. Uses its own username so a per-account lockout
    can't collide with other probes that hit /login (e.g. sqli_auth_bypass)."""
    form = auth.login_form(ctx.profile.forms)
    if form is None:
        return False
    data = {}
    for name in form.fields:
        low = name.lower()
        if "pass" in low:
            data[name] = "hl-wrong-password"
        elif "email" in low or "mail" in low:
            data[name] = "hacklet_probe_rl@example.com"
        else:
            data[name] = "hacklet_probe_rl"
    attempts = probe.probe.get("attempts", 10)
    with httpx.Client(base_url=ctx.base_url, timeout=15.0, follow_redirects=False) as c:
        for _ in range(attempts):
            try:
                resp = c.request((form.method or "post").upper(), form.action, data=data)
            except (httpx.HTTPError, httpx.InvalidURL):
                return False  # login endpoint unreachable -> can't prove a missing control
            if resp.status_code in (429, 423):
                return False  # throttled -> brute-force protection present -> clean
    return True  # N attempts, never throttled -> no rate limiting -> slop


# Redirect destinations that signal a CSRF REJECTION (request not honored) rather than acceptance.
_CSRF_REJECT_HINTS = ("login", "signin", "sign-in", "sign_in", "auth", "error",
                      "denied", "forbidden", "unauthorized")


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
            data={f: "hl-csrf" for f in form.fields},
            headers={"Origin": "https://evil.example"},
            follow_redirects=False,
        )
        if resp.is_redirect:
            # a redirect to a login/auth/error page is a CSRF REJECTION, not an accepted state change
            # (the vulnerable success path redirects to the created resource instead). Without this,
            # a defended app that 302s a forged POST to /login is falsely flagged (false-positive 25).
            dest = resp.headers.get("location", "").lower()
            return not any(h in dest for h in _CSRF_REJECT_HINTS)
        return resp.status_code < 400  # 2xx, no token, no SameSite -> accepted cross-site -> CSRF
    except (httpx.HTTPError, httpx.InvalidURL):
        return False  # transport/URL failure mid-POST -> can't prove CSRF (clean), don't crash run()
    finally:
        account.client.close()


def dom_xss(ctx, probe) -> bool:
    """Browser oracle: inject an executing payload across discovered routes and render — fires when
    it runs in the DOM, catching reflected-that-executes and DOM-sink XSS a source check misses.
    Gated on the `browser` capability, so it's N/A unless the run enabled rendering."""
    return browser.dom_xss_executes(ctx.base_url, ctx.profile.routes)


def _served(ctx, path: str) -> bool:
    """Does the target path exist (not 404)? Lets a probe fall back from a declared endpoint a real
    target doesn't serve to a representative one (the homepage), instead of silently no-opping."""
    try:
        return ctx.client.get(path).status_code != 404
    except (httpx.HTTPError, httpx.InvalidURL):
        return False


def slow_first_paint(ctx, probe) -> bool:
    """Browser oracle: render and read First Contentful Paint; slop if it exceeds the gate — the
    user-facing 'slow app' signal (client render delay, distinct from server TTFB). Browser-gated.
    Measures the declared page if served, else the homepage (real apps don't serve the reference path)."""
    target = probe.probe.get("target", "/")
    if not _served(ctx, target):
        target = "/"
    url = ctx.base_url.rstrip("/") + target
    # median of N renders, not one sample: FCP is wall-clock timing (JIT warmup, CPU/network jitter),
    # so a single sample near the gate flips between runs -> non-deterministic score. The isinstance
    # filter also drops any non-numeric value a hostile page could inject (would raise TypeError).
    samples = [browser.first_contentful_paint(url) for _ in range(3)]
    vals = [s for s in samples if isinstance(s, (int, float))]
    if not vals:
        return False
    return statistics.median(vals) > probe.probe.get("threshold_ms", 1000)


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


def _fanout(work, n: int):
    """Run `work` (a no-arg callable) n times concurrently; return the n results in submit order.
    The shared concurrency primitive for the self-as-oracle race/load probes."""
    with ThreadPoolExecutor(max_workers=n) as ex:
        return [f.result() for f in [ex.submit(work) for _ in range(n)]]


def _concurrent_creates(base_url, path, cookies, data, n: int = 12):
    def create():
        try:
            with httpx.Client(base_url=base_url, timeout=10.0, follow_redirects=True, cookies=cookies) as c:
                return c.post(path, data=data).url.path
        except Exception:
            return None
    return _fanout(create, n)


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
        # fill the form's ACTUAL fields (was hardcoded {"text": ...}); a real create form named
        # content/body/title would otherwise get an empty POST and the race would never be detected.
        data = {f: "hl-race" for f in form.fields}
        urls = _concurrent_creates(ctx.base_url, form.action, cookies, data)
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
    return _fanout(get, n)


def load_resilience(ctx, probe) -> bool:
    """Fire a concurrent burst at an endpoint; slop if it falls over (>10% 5xx) under load — the
    resource-exhaustion / unsynchronized-shared-state failure that only surfaces under concurrency."""
    target = probe.probe.get("target", "/")
    if not _served(ctx, target):
        # declared endpoint not served (real app) -> burst the homepage, the representative
        # always-present endpoint. NEVER fan across all routes: concurrent bursts at every endpoint
        # of a live target is a DoS.
        target = "/"
    ratios = []
    for _ in range(3):  # median of N bursts, not one: a target near the 10% gate flips between runs
        statuses = _concurrent_get(ctx.base_url, target)
        if statuses:
            # None = connection refused/dropped/timeout — a HARDER fall-over than a 500, counted over
            # the whole burst so an app that crashes the connection can't read cleaner than one that 500s.
            failures = sum(1 for s in statuses if s is None or s >= 500)
            ratios.append(failures / len(statuses))
    if not ratios:
        return False
    return statistics.median(ratios) > 0.1


PREDICATES = {
    "sqli_auth_bypass": sqli_auth_bypass,
    "session_cookie_missing_flag": session_cookie_missing_flag,
    "login_no_rate_limit": login_no_rate_limit,
    "csrf_missing": csrf_missing,
    "idor_horizontal": idor_horizontal,
    "dom_xss": dom_xss,
    "race_resource_ids": race_resource_ids,
    "load_resilience": load_resilience,
    "slow_first_paint": slow_first_paint,
}
