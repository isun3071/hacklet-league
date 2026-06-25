"""Detection primitives.

- MATCHERS: declarative conditions, (response, arg) -> True when slop is present.
- PREDICATES: oracle conditions for hidden sinks, (ctx) -> True when slop is present.

Slop is always the *presence* of a problem (deduction-only): a matcher/predicate returning True
means the probe fires and adds its penalty.
"""
from __future__ import annotations

import re

from . import auth

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


def session_cookie_insecure(ctx, probe) -> bool:
    """Self-as-oracle: register an account, then inspect the session cookie it sets. Slop if that
    cookie lacks HttpOnly — an XSS could then steal the session."""
    account = auth.register_account(ctx.base_url, ctx.profile)
    if account is None:
        return False  # registration not possible (applicability gates this) -> treat as clean
    try:
        cookie = auth.session_cookie(account.register_response)
        return cookie is not None and not cookie["httponly"]
    finally:
        account.client.close()


PREDICATES = {
    "sqli_auth_bypass": sqli_auth_bypass,
    "session_cookie_insecure": session_cookie_insecure,
}
