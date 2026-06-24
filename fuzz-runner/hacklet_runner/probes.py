"""Detection primitives.

- MATCHERS: declarative conditions, (response, arg) -> True when slop is present.
- PREDICATES: oracle conditions for hidden sinks, (ctx) -> True when slop is present.

Slop is always the *presence* of a problem (deduction-only): a matcher/predicate returning True
means the probe fires and adds its penalty.
"""
from __future__ import annotations

import re

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


MATCHERS = {
    "response_leaks_stack_trace": response_leaks_stack_trace,
    "ttfb_at_least": ttfb_at_least,
    "response_contains": response_contains,
    "response_missing_header": response_missing_header,
    "response_server_error": response_server_error,
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


PREDICATES = {
    "sqli_auth_bypass": sqli_auth_bypass,
}
