"""The five-phase run: deploy -> discover -> applicability -> execute -> aggregate (+report).

Aggregation applies the spec's composition dampers (variant-group-once and
diminishing-returns-within-category) via aggregate.compute_slop_score; per-bundle ordering is
encoded in the penalty magnitudes, not a runtime multiplier.
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


def _run_declarative(probe: Probe, client: httpx.Client) -> bool:
    method = probe.probe.get("method", "GET").upper()
    target = probe.probe.get("target", "/")
    resp = client.request(
        method, target, params=probe.probe.get("query"), data=probe.probe.get("data")
    )
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
                if not _applicable(probe, profile):
                    outcomes.append(_outcome(probe, "not_applicable", 0))
                    continue
                if "predicate" in probe.probe:
                    slop = PREDICATES[probe.probe["predicate"]](ctx, probe)
                else:
                    slop = _run_declarative(probe, client)
                outcomes.append(
                    _outcome(probe, "slop_detected" if slop else "clean", probe.penalty if slop else 0)
                )
        return Report(slop_score=compute_slop_score(outcomes), outcomes=outcomes)
    finally:
        deployer.teardown()


def _outcome(probe: Probe, outcome: str, penalty: int) -> Outcome:
    return Outcome(
        probe_id=probe.id,
        bundle=probe.bundle,
        category=probe.category,
        outcome=outcome,
        penalty=penalty,
        variant_group_id=probe.variant_group_id,
    )
