"""Detection primitives.

- MATCHERS: declarative conditions, (response, arg) -> True when slop is present.
- PREDICATES: oracle conditions for hidden sinks, (ctx) -> True when slop is present.

Slop is always the *presence* of a problem (deduction-only): a matcher/predicate returning True
means the probe fires and adds its penalty.
"""
from __future__ import annotations

import re
import statistics
import urllib.parse
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


def response_uncompressed(resp, arg=1024) -> bool:
    # Slop: a sizeable TEXT response served with no Content-Encoding (gzip/br/deflate) -> wasted
    # bandwidth and slower loads. Gate on size — small bodies don't benefit from compression, so a
    # server that skips them is correct, not slop. httpx always sends Accept-Encoding and keeps the
    # Content-Encoding header, so its presence means the server compressed.
    ctype = resp.headers.get("content-type", "").lower()
    if not any(t in ctype for t in ("text/", "javascript", "json", "xml", "svg")):
        return False
    if "content-encoding" in resp.headers:
        return False
    return len(resp.content) > int(arg)


def response_has_header(resp, arg) -> bool:
    return str(arg) in resp.headers  # presence is the slop (e.g. X-Powered-By leaks the stack)


def response_is_aws_credentials(resp, arg=None) -> bool:
    # an AWS credentials file served at the webroot — content-signatured so an SPA catch-all 200 (the
    # index shell) doesn't false-positive the way a bare 200 check would.
    t = resp.text.lower()
    return "aws_access_key_id" in t or "aws_secret_access_key" in t


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


# Credential material an API response must never contain: a populated password-family field, or a
# password-hash signature. High precision by design — password fields are NEVER a legitimate part of
# a response (unlike access/refresh tokens, which ARE the auth flow and are excluded). Masked values
# (***, xxxx, [REDACTED]) and the OpenAPI spec's own schema examples are excluded.
_CRED_FIELD = re.compile(
    r'"(?:password|passwd|pwd|hashed_password|password_hash|pwd_hash|user_password|'
    r'plaintext_password)"\s*:\s*"(?!\s*(?:\*{2,}|x{4,}|redacted|hidden|\.{3})\s*")[^"]{2,}"',
    re.IGNORECASE,
)
_CRED_HASH = re.compile(
    r"\$2[aby]\$\d\d\$[./A-Za-z0-9]{53}"   # bcrypt
    r"|\$argon2(?:id|i|d)\$"                # argon2
    r"|\$6\$[./A-Za-z0-9]{8,}"             # sha512crypt
    r"|\$1\$[./A-Za-z0-9]{6,}"             # md5crypt
    r"|\bpbkdf2_sha256\$\d+\$"             # Django PBKDF2
)
_OPENAPI_DOC = re.compile(r'"(?:openapi|swagger)"\s*:\s*"')


def response_leaks_credentials(resp, arg=None) -> bool:
    if resp.status_code != 200:
        return False
    body = resp.text
    if _OPENAPI_DOC.search(body[:4000]):
        return False  # a served spec naming a "password" field in its schema isn't a data leak
    return bool(_CRED_FIELD.search(body) or _CRED_HASH.search(body))


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
    "response_uncompressed": response_uncompressed,
    "response_has_header": response_has_header,
    "response_is_aws_credentials": response_is_aws_credentials,
    "response_leaks_secret": response_leaks_secret,
    "response_leaks_credentials": response_leaks_credentials,
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


# Error-based SQL injection over the API surface discovered from the OpenAPI spec (path params, query
# params, JSON body fields) — the injection points a form-crawler never sees on a JSON API. Precision
# comes from a differential + a DB-error signature: an unbalanced quote must induce a database error
# string the benign baseline never shows. Only GET/POST are probed (never PUT/PATCH/DELETE), so
# grading can't destroy the target's state.
_SQL_ERROR = re.compile(
    r"SQL syntax|SQLITE_ERROR|sqlite3\.(?:Operational|Integrity|Programming|Interface)Error|"
    r"sqlalchemy\.exc|unrecognized token|unterminated quoted string|"
    r"quoted string not properly terminated|you have an error in your sql syntax|mysqlsyntaxerror|"
    r"com\.mysql|psycopg2|PG::\w*Error|PostgreSQL query failed|ORA-\d{5}|Microsoft OLE DB|"
    r"ODBC SQL Server|SQLSTATE\[|Npgsql\.|unclosed quotation mark|incorrect syntax near|\[SQL:\s",
    re.IGNORECASE,
)
_SQLI_BENIGN = "1"
_SQLI_PAYLOAD = "1'"  # a lone quote breaks unparameterized string SQL -> a detectable DB error


def _sqli_slots(ep) -> list[tuple[str, str]]:
    """Injectable positions on an endpoint as (kind, name): path params, query params, body fields."""
    return ([("path", n) for n in ep.path_params]
            + [("query", n) for n in ep.query_params]
            + [("body", n) for n in ep.body_fields])


def _sqli_request(ep, poison, value: str):
    """(path, query_dict, json_body) for ep with the single `poison` slot set to `value` and every
    other slot benign; poison=None yields the all-benign baseline."""
    def sv(kind, name):
        return value if poison == (kind, name) else _SQLI_BENIGN
    path = ep.raw_path
    for n in ep.path_params:
        path = path.replace("{" + n + "}", urllib.parse.quote(sv("path", n), safe=""))
    query = {n: sv("query", n) for n in ep.query_params}
    body = {n: sv("body", n) for n in ep.body_fields} or None
    return path, query, body


def api_sqli(ctx, probe) -> bool | None:
    """Error-based SQLi across spec-discovered API endpoints. Per injectable slot: benign baseline vs.
    unbalanced-quote payload; slop iff the payload induces a DB-error signature the baseline lacks.
    N/A when no injectable GET/POST endpoint exists (e.g. no spec, or a purely form-based app)."""
    targets = [e for e in ctx.profile.endpoints
               if e.method.lower() in ("get", "post") and _sqli_slots(e)]
    if not targets:
        return None
    budget = probe.probe.get("max_attempts", 80)
    tested = False
    with httpx.Client(base_url=ctx.base_url, timeout=10.0, follow_redirects=False,
                      headers=ctx.headers) as c:
        for ep in targets:
            method = ep.method.upper()
            bpath, bquery, bbody = _sqli_request(ep, None, _SQLI_BENIGN)
            try:
                base = c.request(method, bpath, params=bquery, json=bbody)
            except (httpx.HTTPError, httpx.InvalidURL):
                continue
            if _SQL_ERROR.search(base.text):
                continue  # baseline already errors for unrelated reasons -> can't attribute injection
            for slot in _sqli_slots(ep):
                if budget <= 0:
                    return False if tested else None
                budget -= 1
                tested = True
                ppath, pquery, pbody = _sqli_request(ep, slot, _SQLI_PAYLOAD)
                try:
                    r = c.request(method, ppath, params=pquery, json=pbody)
                except (httpx.HTTPError, httpx.InvalidURL):
                    continue
                if _SQL_ERROR.search(r.text):
                    return True  # a quote induced a DB error the baseline lacked -> injectable
    return False if tested else None


def session_cookie_missing_flag(ctx, probe) -> bool | None:
    """Self-as-oracle: register an account, then inspect the session cookie it sets. Slop if it lacks
    the hardening flag named in the probe (httponly | samesite | secure). Returns None (-> N/A) when
    self-registration couldn't establish a session (CSRF/JSON-API app) — a false 'clean' would be a
    missed finding, not a pass."""
    flag = probe.probe.get("flag", "httponly")
    account = auth.register_account(ctx.base_url, ctx.profile)
    if account is None:
        return None  # couldn't self-register -> couldn't test
    try:
        cookie = auth.session_cookie(account.register_response)
        if cookie is None:
            return None  # registration yielded no recognizable session cookie -> couldn't test
        return not cookie[flag]
    finally:
        account.client.close()


def login_no_rate_limit(ctx, probe) -> bool | None:
    """Self-as-oracle: fire N wrong-password logins at the login form; slop if NONE is throttled
    (HTTP 429/423). With no brute-force protection every attempt returns the same auth-failure status,
    enabling credential stuffing / password spraying. Uses its own username so a per-account lockout
    can't collide with other probes that hit /login (e.g. sqli_auth_bypass). N/A when no login form."""
    form = auth.login_form(ctx.profile.forms)
    if form is None:
        return _login_rate_limit_json(ctx, probe)  # no HTML login form -> try a JSON login endpoint
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
                return None  # login endpoint unreachable -> couldn't test
            if resp.status_code in (429, 423):
                return False  # throttled -> brute-force protection present -> clean
    return True  # N attempts, never throttled -> no rate limiting -> slop


def _login_rate_limit_json(ctx, probe) -> bool | None:
    """JSON-API fallback for login_no_rate_limit: find a JSON login endpoint (Juice Shop /rest/user/
    login, /api/login, ...) and hammer it with wrong creds. N/A when no JSON login endpoint responds."""
    attempts = probe.probe.get("attempts", 10)
    with httpx.Client(base_url=ctx.base_url, timeout=15.0, follow_redirects=False,
                      headers=ctx.headers) as c:
        path, creds, first = auth.find_json_login(c)
        if path is None:
            return None  # no login surface at all -> couldn't test
        if first.status_code in (429, 423):
            return False  # already throttling
        for _ in range(attempts - 1):  # find_json_login already made the first attempt
            try:
                r = c.post(path, json=creds)
            except (httpx.HTTPError, httpx.InvalidURL):
                return None
            if r.status_code in (429, 423):
                return False
    return True


# Redirect destinations that signal a CSRF REJECTION (request not honored) rather than acceptance.
_CSRF_REJECT_HINTS = ("login", "signin", "sign-in", "sign_in", "auth", "error",
                      "denied", "forbidden", "unauthorized")


def csrf_missing(ctx, probe) -> bool | None:
    """Self-as-oracle: a state-changing POST that succeeds cross-site with no CSRF token and no
    SameSite cookie -> no CSRF defense. Skips when the form carries a token or the session cookie is
    SameSite (both valid defenses), so only genuinely cross-site-exploitable requests are flagged.
    N/A when there's no form / no session to test against (not a false clean)."""
    form = auth.create_form(ctx.profile.forms)
    if form is None:
        return None  # no state-changing form to test -> N/A
    if any(auth.is_csrf_field(f) for f in form.fields):
        return False  # the form already carries a CSRF token -> defended (clean)
    account = auth.register_account(ctx.base_url, ctx.profile, suffix="_csrf")
    if account is None:
        return None  # couldn't self-register -> couldn't test
    try:
        cookie = auth.session_cookie(account.register_response)
        if cookie is None:
            return None  # no session established -> couldn't test CSRF
        if cookie["samesite"]:
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
    return browser.dom_xss_executes(ctx.base_url, ctx.profile.routes, headers=ctx.headers)


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
    samples = [browser.first_contentful_paint(url, headers=ctx.headers) for _ in range(3)]
    vals = [s for s in samples if isinstance(s, (int, float))]
    if not vals:
        return False
    return statistics.median(vals) > probe.probe.get("threshold_ms", 1000)


def console_errors_present(ctx, probe) -> bool:
    """Browser oracle: the page throws an uncaught JavaScript error on load — broken regardless of
    intent. Browser-gated."""
    url = ctx.base_url.rstrip("/") + probe.probe.get("target", "/")
    n = browser.console_errors(url, headers=ctx.headers)
    return isinstance(n, (int, float)) and n > 0


def a11y_violations_present(ctx, probe) -> bool:
    """Browser oracle: presence-based accessibility violations (missing lang / alt / field label /
    control name) above the threshold. Browser-gated; presence only, so intent-independent."""
    url = ctx.base_url.rstrip("/") + probe.probe.get("target", "/")
    n = browser.a11y_violations(url, headers=ctx.headers)
    return isinstance(n, (int, float)) and n > probe.probe.get("threshold", 0)


_REDIRECT_PARAMS = ("next", "url", "redirect", "return", "dest", "continue", "to", "r")
_REDIRECT_PROBE_HOST = "hacklet-redirect-probe.example"
_REDIRECT_ENDPOINTS = ("/redirect", "/login", "/logout", "/go", "/out", "/auth/callback", "/sso")


def open_redirect(ctx, probe) -> bool:
    """A user-controlled redirect param that sends the browser to an arbitrary EXTERNAL host -> open
    redirect (phishing / OAuth-token theft). Intent-independent: fires only on a 3xx whose Location
    host is our foreign probe host. Tests discovered routes plus common redirect endpoints/params."""
    evil = {p: "https://" + _REDIRECT_PROBE_HOST + "/x" for p in _REDIRECT_PARAMS}
    seen = set()
    with httpx.Client(base_url=ctx.base_url, timeout=10.0, follow_redirects=False,
                      headers=ctx.headers) as c:
        for path in list(ctx.profile.routes) + list(_REDIRECT_ENDPOINTS):
            if path in seen:
                continue
            seen.add(path)
            try:
                resp = c.get(path, params=evil)
            except (httpx.HTTPError, httpx.InvalidURL):
                continue
            if resp.is_redirect and urllib.parse.urlparse(
                    resp.headers.get("location", "")).hostname == _REDIRECT_PROBE_HOST:
                return True
    return False


def idor_horizontal(ctx, probe) -> bool | None:
    """Self-as-oracle: register A and B, A creates a resource, B fetches it by URL. If B can read
    A's content, object-level access control is broken (horizontal IDOR). N/A when we can't register
    both accounts or A can't create a distinct resource to test against (not a false clean)."""
    form = auth.create_form(ctx.profile.forms)
    if form is None:
        return None
    a = auth.register_account(ctx.base_url, ctx.profile, suffix="_a")
    b = auth.register_account(ctx.base_url, ctx.profile, suffix="_b")
    if a is None or b is None:
        for acct in (a, b):
            if acct:
                acct.client.close()
        return None
    # extract each session cookie (jar iteration avoids CookieConflict) and re-send it plainly, so an
    # authed create/read isn't dropped over http when the app sets a Secure cookie (that's tested by
    # sec-session-003, separately). Same approach race_resource_ids already uses.
    a_cookies = {c.name: c.value for c in a.client.cookies.jar}
    b_cookies = {c.name: c.value for c in b.client.cookies.jar}
    try:
        marker = "hl-idor-7a3f9c"
        with httpx.Client(base_url=ctx.base_url, timeout=10.0, follow_redirects=True,
                          cookies=a_cookies) as ac:
            resource = ac.post(form.action, data={n: marker for n in form.fields}).url.path
        if not resource or resource == form.action:  # no distinct resource created -> couldn't test
            return None
        with httpx.Client(base_url=ctx.base_url, timeout=10.0, cookies=b_cookies) as bc:
            leaked = bc.get(resource)
        return leaked.status_code == 200 and marker in leaked.text
    except (httpx.HTTPError, httpx.InvalidURL):
        return None
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


def race_resource_ids(ctx, probe) -> bool | None:
    """Self-as-oracle: register, fire N concurrent resource creates, and inspect the assigned IDs.
    Duplicate IDs mean id allocation isn't atomic under concurrency — a race condition. N distinct
    creates must yield N distinct ids, so a collision is provable without knowing the app's intent.
    N/A when there's no create form or we can't self-register (not a false clean)."""
    form = auth.create_form(ctx.profile.forms)
    if form is None:
        return None
    account = auth.register_account(ctx.base_url, ctx.profile, suffix="_race")
    if account is None:
        return None
    try:
        # iterate the jar, not dict(cookies) — dict() raises httpx.CookieConflict when the session
        # cookie was set on multiple paths/domains during the register redirect chain.
        cookies = {c.name: c.value for c in account.client.cookies.jar}
        # fill the form's ACTUAL fields (was hardcoded {"text": ...}); a real create form named
        # content/body/title would otherwise get an empty POST and the race would never be detected.
        data = {f: "hl-race" for f in form.fields}
        urls = _concurrent_creates(ctx.base_url, form.action, cookies, data)
        # a redirect to a login/error page (an unauthenticated/rejected create) is NOT a created
        # resource -> exclude it, so uniform redirects don't look like duplicate ids (a false race).
        created = [u for u in urls if u and u != form.action
                   and not any(h in u.lower() for h in _CSRF_REJECT_HINTS)]
        if len(created) < 2:
            return None  # couldn't create ≥2 resources (CSRF/session) -> couldn't test
        return len(set(created)) < len(created)
    finally:
        account.client.close()


def _concurrent_get(base_url, path, n: int = 20, headers=None):
    def get():
        try:
            with httpx.Client(base_url=base_url, timeout=15.0, headers=headers) as c:
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
        statuses = _concurrent_get(ctx.base_url, target, headers=ctx.headers)
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
    "api_sqli": api_sqli,
    "session_cookie_missing_flag": session_cookie_missing_flag,
    "login_no_rate_limit": login_no_rate_limit,
    "csrf_missing": csrf_missing,
    "idor_horizontal": idor_horizontal,
    "dom_xss": dom_xss,
    "race_resource_ids": race_resource_ids,
    "load_resilience": load_resilience,
    "slow_first_paint": slow_first_paint,
    "console_errors_present": console_errors_present,
    "a11y_violations_present": a11y_violations_present,
    "open_redirect": open_redirect,
}


# Human-readable "why it fired" reasons for verbose / --failed output, derived from the probe's check.
_MATCHER_REASONS = {
    "response_leaks_stack_trace": "leaked a stack trace",
    "ttfb_at_least": "slow time-to-first-byte (>{arg}s)",
    "response_contains": "reflected the probe payload unescaped",
    "response_missing_header": "missing header: {arg}",
    "response_missing_clickjacking_defense": "no clickjacking defense (X-Frame-Options / CSP frame-ancestors)",
    "response_cors_misconfigured": "reflects an arbitrary Origin with credentials (CORS)",
    "response_server_error": "returned a 5xx server error",
    "response_uncompressed": "sizeable text served without gzip (no Content-Encoding)",
    "response_has_header": "leaks the {arg} header (stack / version disclosure)",
    "response_is_aws_credentials": "served an AWS credentials file at the webroot",
    "response_leaks_credentials": "returned password/credential material in a response body",
    "response_leaks_secret": "leaked a secret (private key / cloud or API token)",
    "response_is_dotenv": "served a .env secrets file",
    "response_is_git_config": "served .git/config (source repo exposed)",
    "response_is_git_head": "served .git/HEAD (source repo exposed)",
}

_PREDICATE_REASONS = {
    "sqli_auth_bypass": "login bypassed by a SQL-injection payload",
    "api_sqli": "an API parameter is SQL-injectable (an unbalanced quote induced a database error)",
    "session_cookie_missing_flag": "session cookie missing the {flag} flag",
    "csrf_missing": "state-changing POST accepted cross-site with no token / SameSite",
    "idor_horizontal": "another account's object was readable by id (broken access control)",
    "dom_xss": "an injected payload executed in the DOM",
    "race_resource_ids": "concurrent creates collided on one id (non-atomic allocation)",
    "load_resilience": "endpoint 5xx'd under a concurrent burst",
    "slow_first_paint": "First Contentful Paint exceeded the gate",
    "login_no_rate_limit": "repeated wrong-password logins were never throttled",
    "console_errors_present": "threw an uncaught JavaScript error on load",
    "a11y_violations_present": "accessibility violations (missing alt / form label / lang / control name)",
    "open_redirect": "a user-controlled parameter redirects to an arbitrary external host",
}


def describe(probe) -> str:
    """Short human reason a probe fires (for verbose / --failed), derived from its predicate or
    slop_if conditions — not live evidence, but enough to know what failed and act on it."""
    p = probe.probe
    if "predicate" in p:
        return _PREDICATE_REASONS.get(p["predicate"], p["predicate"]).format(flag=p.get("flag", ""))
    parts = []
    for cond in probe.slop_if:
        if isinstance(cond, str):
            parts.append(_MATCHER_REASONS.get(cond, cond))
        else:
            ((name, arg),) = cond.items()
            parts.append(_MATCHER_REASONS.get(name, name).format(arg=arg))
    return "; ".join(parts)
