"""Probe schema + runtime structures. Probe mirrors FUZZ_RUNNER_SPEC's YAML schema (trimmed
to what the vertical slice exercises)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class Applicability(BaseModel):
    requires: list[str] = Field(default_factory=list)


class Probe(BaseModel):
    id: str
    bundle: str  # security | qa | performance
    category: str = ""
    pool: str = "public"  # public | hidden
    evidence_model: str = "provable"  # provable | oracle (detection hint only)
    penalty: int  # slop added when the probe fires; deduction-only, so always positive
    applicability: Applicability = Field(default_factory=Applicability)
    # Either {"predicate": name} for oracle probes, or {"method", "target"} for declarative ones.
    probe: dict[str, Any] = Field(default_factory=dict)
    # Declarative conditions; ALL must match for slop. Each is a matcher name or {name: arg}.
    slop_if: list[Any] = Field(default_factory=list)


@dataclass
class Profile:
    """The stack-agnostic surface map produced by discovery."""
    base_url: str
    endpoints: list[str] = field(default_factory=list)
    form_endpoints: list[str] = field(default_factory=list)
    capabilities: dict[str, bool] = field(default_factory=dict)


@dataclass
class Outcome:
    probe_id: str
    bundle: str
    outcome: str  # slop_detected | clean | not_applicable
    penalty: int


@dataclass
class Report:
    slop_score: int
    outcomes: list[Outcome] = field(default_factory=list)

    @property
    def by_id(self) -> dict[str, str]:
        return {o.probe_id: o.outcome for o in self.outcomes}
