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
    variant_group_id: str | None = None  # probes sharing one fire once (same logical flaw)
    pool: str = "public"  # public | hidden
    evidence_model: str = "provable"  # provable | oracle (detection hint only)
    penalty: int  # slop added when the probe fires; deduction-only, so always positive
    applicability: Applicability = Field(default_factory=Applicability)
    # Either {"predicate": name} for oracle probes, or {"method", "target"} for declarative ones.
    probe: dict[str, Any] = Field(default_factory=dict)
    # Declarative conditions; ALL must match for slop. Each is a matcher name or {name: arg}.
    slop_if: list[Any] = Field(default_factory=list)


@dataclass
class Form:
    """A discovered HTML form: where it submits, how, and its input field names."""
    action: str
    method: str = "get"
    fields: list[str] = field(default_factory=list)
    enctype: str = ""                                     # e.g. multipart/form-data (file uploads)
    file_fields: list[str] = field(default_factory=list)  # names of <input type=file> controls


@dataclass
class Endpoint:
    """An API operation discovered from a served OpenAPI/Swagger spec — the JSON-API analogue of a
    Form. Feeds the declarative fan-out (headers/crash/exposure across real endpoints) and the
    injection probes (concrete query params / JSON body fields to inject into)."""
    path: str                                              # concretized path ({id}->1) for fetches
    method: str = "get"                                    # get/post/put/patch/delete
    query_params: list[str] = field(default_factory=list)  # query parameter names
    body_fields: list[str] = field(default_factory=list)   # JSON/form request-body property names
    path_params: list[str] = field(default_factory=list)   # path-template param names (BOLA/IDOR)
    raw_path: str = ""                                      # original template, e.g. /users/v1/{username}


@dataclass
class Profile:
    """The stack-agnostic surface map produced by discovery."""
    base_url: str
    routes: list[str] = field(default_factory=list)        # discovered paths (incl "/")
    forms: list[Form] = field(default_factory=list)         # discovered forms with their fields
    capabilities: dict[str, bool] = field(default_factory=dict)
    endpoints: list[Endpoint] = field(default_factory=list)  # API operations from an OpenAPI spec

    @property
    def form_endpoints(self) -> list[str]:  # back-compat for predicates that target form actions
        return [f.action for f in self.forms]


@dataclass
class Outcome:
    probe_id: str
    bundle: str
    category: str
    outcome: str  # slop_detected | clean | not_applicable
    penalty: int
    variant_group_id: str | None = None
    target: str = ""  # the concrete path/form this outcome ran against (fan-out)
    reason: str = ""  # short human "why it fired" (slop only); derived from the probe's check


@dataclass
class Report:
    slop_score: int
    outcomes: list[Outcome] = field(default_factory=list)

    @property
    def by_id(self) -> dict[str, str]:
        # A probe may fan across many targets; collapse to the strongest status seen.
        rank = {"not_applicable": 0, "clean": 1, "slop_detected": 2}
        status: dict[str, str] = {}
        for o in self.outcomes:
            if o.probe_id not in status or rank[o.outcome] > rank[status[o.probe_id]]:
                status[o.probe_id] = o.outcome
        return status
