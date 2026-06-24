"""The five-phase run: deploy -> discover -> applicability -> execute -> aggregate (+report).

Aggregation here is a plain penalty sum (slice scope). The composition dampers from the spec
(variant-group-once, diminishing-returns-within-category, per-bundle scale) land as the catalog
grows; with three single probes there is nothing yet to dampen.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

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
    resp = client.request(method, target, params=probe.probe.get("query"))
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
    handle = deployer.deploy()
    try:
        profile = discover(handle.base_url)
        outcomes: list[Outcome] = []
        with httpx.Client(base_url=handle.base_url, timeout=15.0, follow_redirects=True) as client:
            ctx = _Ctx(handle.base_url, client, profile)
            for probe in catalog:
                if not _applicable(probe, profile):
                    outcomes.append(Outcome(probe.id, probe.bundle, "not_applicable", 0))
                    continue
                if "predicate" in probe.probe:
                    slop = PREDICATES[probe.probe["predicate"]](ctx)
                else:
                    slop = _run_declarative(probe, client)
                outcomes.append(
                    Outcome(
                        probe.id,
                        probe.bundle,
                        "slop_detected" if slop else "clean",
                        probe.penalty if slop else 0,
                    )
                )
        return Report(slop_score=sum(o.penalty for o in outcomes), outcomes=outcomes)
    finally:
        deployer.teardown()
