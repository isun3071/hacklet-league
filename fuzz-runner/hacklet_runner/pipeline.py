"""The five-phase run: deploy -> discover -> applicability -> execute -> aggregate (+report).

Declarative probes target either a literal path or a discovered-surface selector (`routes`), and the
executor fans the probe across each concrete target — one outcome per (probe x target). The
diminishing-returns-within-category damper (aggregate.compute_slop_score) handles the multiplicity,
so multiple vulnerable endpoints cost more than one but less than linearly.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

from .aggregate import compute_slop_score
from .deploy import Deployer
from .discovery import discover
from .net import make_client
from .probes import MATCHERS, PREDICATES, describe
from .schema import Form, Outcome, Probe, Profile, Report


@dataclass
class _Ctx:
    base_url: str
    client: httpx.Client
    profile: Profile
    headers: dict | None = None


def _applicable(probe: Probe, profile: Profile) -> bool:
    return all(profile.capabilities.get(req, False) for req in probe.applicability.requires)


def _fetch_path(probe: Probe, client: httpx.Client, path: str) -> httpx.Response:
    p = probe.probe
    method = p.get("method", "GET").upper()
    kwargs = {"params": p.get("query"), "headers": p.get("headers")}
    if "body" in p:
        kwargs["content"] = p["body"]   # raw request body (e.g. a malformed-JSON crash probe)
    else:
        kwargs["data"] = p.get("data")  # form-encoded
    return client.request(method, path, **kwargs)


def _fetch_form(probe: Probe, client: httpx.Client, form: Form) -> httpx.Response:
    # Fill every field with the probe's payload, then submit the form the way it declares.
    payload = {field: probe.probe.get("fill", "") for field in form.fields}
    if (form.method or "get").upper() == "GET":
        return client.request("GET", form.action, params=payload)
    return client.request(form.method.upper(), form.action, data=payload)


def _expand(probe: Probe, profile: Profile):
    """Concrete (label, fetch) targets for a declarative probe: a selector fans across discovered
    surface; a literal path is a single target."""
    target = probe.probe.get("target", "/")
    if target == "routes":
        return [(r, lambda c, r=r: _fetch_path(probe, c, r)) for r in profile.routes]
    if target == "forms":
        return [(f.action, lambda c, f=f: _fetch_form(probe, c, f)) for f in profile.forms]
    return [(target, lambda c: _fetch_path(probe, c, target))]


def _matches(probe: Probe, resp: httpx.Response) -> bool:
    for cond in probe.slop_if:  # ALL conditions must match -> slop present
        if isinstance(cond, str):
            if not MATCHERS[cond](resp):
                return False
        elif isinstance(cond, dict):
            ((name, arg),) = cond.items()
            if not MATCHERS[name](resp, arg):
                return False
    return bool(probe.slop_if)


def _run_probe(probe: Probe, ctx: _Ctx, client: httpx.Client, profile: Profile) -> list[Outcome]:
    """Resolve one probe to its outcome(s): applicability gate, then an oracle predicate or a
    declarative fan-out across discovered targets. One Outcome per (probe x target)."""
    client.cookies.clear()  # each probe starts from a clean session (no cross-probe leak)
    target = probe.probe.get("target", "")
    if not _applicable(probe, profile):
        return [_outcome(probe, "not_applicable", 0, target)]
    if "predicate" in probe.probe:
        try:
            slop = PREDICATES[probe.probe["predicate"]](ctx, probe)
        except Exception:
            # a predicate drives an UNTRUSTED target; a hostile/edge-case response must degrade this
            # one probe to N/A, never crash the whole grade (run must not DNF). Calibration is the
            # backstop: a predicate that ALWAYS raises fails the suite.
            return [_outcome(probe, "not_applicable", 0, target)]
        if slop is None:
            # the predicate couldn't establish the conditions to test (e.g. self-registration failed
            # on a CSRF/JSON-API app) -> N/A, NOT a false "clean". A false clean is a missed finding.
            return [_outcome(probe, "not_applicable", 0, target)]
        return [_outcome(probe, "slop_detected" if slop else "clean", probe.penalty if slop else 0,
                         target, reason=describe(probe) if slop else "")]
    na_if_absent = probe.probe.get("na_if_absent", False)
    produced: list[Outcome] = []
    for label, fetch in _expand(probe, profile):
        try:
            resp = fetch(client)
        except (httpx.HTTPError, httpx.InvalidURL):
            continue  # unreachable / malformed-URL (control-char path) target -> next
        client.cookies.clear()  # form-fan submissions stay independent (no session leak)
        # endpoint-specific probe: 404/405/501 means the target endpoint/method isn't served here,
        # so it's N/A — not a clean pass (a fake "handled gracefully").
        if na_if_absent and resp.status_code in (404, 405, 501):
            continue
        slop = _matches(probe, resp)
        produced.append(_outcome(
            probe, "slop_detected" if slop else "clean", probe.penalty if slop else 0, label,
            reason=describe(probe) if slop else "",
        ))
    if not produced:  # no targets, every fetch failed, or endpoint absent -> inconclusive
        return [_outcome(probe, "not_applicable", 0, target)]
    return produced


def run(deployer: Deployer, catalog: list[Probe], render=None, headers=None, on_progress=None) -> Report:
    """on_progress(done, total, probe, outcomes): called twice per probe — before it runs with
    outcomes=None (so a caller can show what's currently testing), and after with its outcomes."""
    try:
        handle = deployer.deploy()  # inside try so teardown runs even if deploy/health fails
        profile = discover(handle.base_url, render=render, headers=headers)
        outcomes: list[Outcome] = []
        total = len(catalog)
        with make_client(handle.base_url, headers, timeout=15.0, follow_redirects=True) as client:
            ctx = _Ctx(handle.base_url, client, profile, headers)
            for i, probe in enumerate(catalog):
                if on_progress:
                    on_progress(i, total, probe, None)              # starting probe i (0-indexed)
                probe_outcomes = _run_probe(probe, ctx, client, profile)
                outcomes.extend(probe_outcomes)
                if on_progress:
                    on_progress(i + 1, total, probe, probe_outcomes)  # done: i+1 probes completed
        return Report(slop_score=compute_slop_score(outcomes), outcomes=outcomes)
    finally:
        deployer.teardown()


def _outcome(probe: Probe, outcome: str, penalty: int, target: str = "", reason: str = "") -> Outcome:
    return Outcome(
        probe_id=probe.id,
        bundle=probe.bundle,
        category=probe.category,
        outcome=outcome,
        penalty=penalty,
        variant_group_id=probe.variant_group_id,
        target=target,
        reason=reason,
    )
