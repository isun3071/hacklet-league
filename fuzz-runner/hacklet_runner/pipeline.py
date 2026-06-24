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
from .probes import MATCHERS, PREDICATES
from .schema import Outcome, Probe, Profile, Report


@dataclass
class _Ctx:
    base_url: str
    client: httpx.Client
    profile: Profile


def _applicable(probe: Probe, profile: Profile) -> bool:
    return all(profile.capabilities.get(req, False) for req in probe.applicability.requires)


def _fetch_path(probe: Probe, client: httpx.Client, path: str) -> httpx.Response:
    method = probe.probe.get("method", "GET").upper()
    return client.request(method, path, params=probe.probe.get("query"), data=probe.probe.get("data"))


def _expand(probe: Probe, profile: Profile):
    """Concrete (label, fetch) targets for a declarative probe: a selector fans across discovered
    surface; a literal path is a single target."""
    target = probe.probe.get("target", "/")
    if target == "routes":
        return [(r, lambda c, r=r: _fetch_path(probe, c, r)) for r in profile.routes]
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


def run(deployer: Deployer, catalog: list[Probe]) -> Report:
    try:
        handle = deployer.deploy()  # inside try so teardown runs even if deploy/health fails
        profile = discover(handle.base_url)
        outcomes: list[Outcome] = []
        with httpx.Client(base_url=handle.base_url, timeout=15.0, follow_redirects=True) as client:
            ctx = _Ctx(handle.base_url, client, profile)
            for probe in catalog:
                target = probe.probe.get("target", "")
                if not _applicable(probe, profile):
                    outcomes.append(_outcome(probe, "not_applicable", 0, target))
                    continue
                if "predicate" in probe.probe:
                    slop = PREDICATES[probe.probe["predicate"]](ctx, probe)
                    outcomes.append(_outcome(
                        probe, "slop_detected" if slop else "clean", probe.penalty if slop else 0, target
                    ))
                    continue
                expanded = _expand(probe, profile)
                if not expanded:
                    outcomes.append(_outcome(probe, "not_applicable", 0, target))
                    continue
                for label, fetch in expanded:
                    try:
                        resp = fetch(client)
                    except httpx.HTTPError:
                        continue  # unreachable target -> no outcome for it
                    slop = _matches(probe, resp)
                    outcomes.append(_outcome(
                        probe, "slop_detected" if slop else "clean", probe.penalty if slop else 0, label
                    ))
        return Report(slop_score=compute_slop_score(outcomes), outcomes=outcomes)
    finally:
        deployer.teardown()


def _outcome(probe: Probe, outcome: str, penalty: int, target: str = "") -> Outcome:
    return Outcome(
        probe_id=probe.id,
        bundle=probe.bundle,
        category=probe.category,
        outcome=outcome,
        penalty=penalty,
        variant_group_id=probe.variant_group_id,
        target=target,
    )
