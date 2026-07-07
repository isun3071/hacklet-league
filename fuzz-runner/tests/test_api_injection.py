"""API-injection path: OpenAPI-driven discovery + error-based SQLi over the discovered surface.
Uses the stdlib `jsonapi` reference (a form-less API that publishes a spec) so the JSON-API recall
path is locked in CI, not just validated against live third-party apps."""
import pathlib

import pytest

from hacklet_runner.deploy import SubprocessDeployer
from hacklet_runner.discovery import discover
from hacklet_runner.probes import api_sqli
from hacklet_runner.schema import Endpoint, Profile

ROOT = pathlib.Path(__file__).resolve().parent.parent
REFS = ROOT / "references"


@pytest.fixture
def jsonapi():
    d = SubprocessDeployer(str(REFS / "jsonapi" / "app.py"))
    url = d.deploy().base_url
    yield url
    d.teardown()


class _Ctx:
    """Minimal pipeline context: api_sqli reads base_url, profile.endpoints, and headers."""
    def __init__(self, base_url, profile):
        self.base_url = base_url
        self.profile = profile
        self.headers = None
        self.client = None


class _Probe:
    probe = {"max_attempts": 80}


def test_discovers_api_endpoints_from_spec(jsonapi):
    p = discover(jsonapi)
    raws = {e.raw_path for e in p.endpoints}
    assert "/api/items/{id}" in raws and "/api/notes" in raws
    assert p.capabilities["any_endpoint_accepts_text_input"] is True


def test_api_sqli_fires_on_injectable_endpoint(jsonapi):
    p = discover(jsonapi)
    assert api_sqli(_Ctx(jsonapi, p), _Probe()) is True


def test_api_sqli_clean_on_parameterized_endpoint_only(jsonapi):
    # only the safe endpoint in scope -> the quote never errors -> clean (differential precision)
    safe = Profile(base_url=jsonapi, endpoints=[
        Endpoint(path="/api/notes", method="get", query_params=["q"], raw_path="/api/notes")])
    assert api_sqli(_Ctx(jsonapi, safe), _Probe()) is False


def test_api_sqli_na_when_no_endpoints(jsonapi):
    assert api_sqli(_Ctx(jsonapi, Profile(base_url=jsonapi, endpoints=[])), _Probe()) is None
