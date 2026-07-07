"""API-injection path: OpenAPI-driven discovery + error-based SQLi over the discovered surface.
Uses the stdlib `jsonapi` reference (a form-less API that publishes a spec) so the JSON-API recall
path is locked in CI, not just validated against live third-party apps."""
import pathlib

import httpx
import pytest

from hacklet_runner.catalog import load_catalog
from hacklet_runner.deploy import SubprocessDeployer
from hacklet_runner.discovery import discover
from hacklet_runner.pipeline import run
from hacklet_runner.probes import api_sqli, response_leaks_credentials
from hacklet_runner.schema import Endpoint, Profile

CATALOG = pathlib.Path(__file__).resolve().parent.parent / "catalog"

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


# --- excessive data exposure (response_leaks_credentials) ---

def _resp(text, status=200):
    return httpx.Response(status, text=text)


def test_credential_leak_fires_on_password_field_and_hash():
    assert response_leaks_credentials(_resp('{"user":"a","password":"hunter2"}')) is True
    assert response_leaks_credentials(_resp('{"pw":"$2b$12$' + "a" * 53 + '"}')) is True  # bcrypt hash


def test_credential_leak_precision_no_false_positives():
    # access/refresh tokens ARE the auth flow, not a leak
    assert response_leaks_credentials(_resp('{"access_token":"eyJhbGci.abc.def","token_type":"bearer"}')) is False
    # masked / empty values are not a leak
    assert response_leaks_credentials(_resp('{"password":"****"}')) is False
    assert response_leaks_credentials(_resp('{"password":""}')) is False
    # the served OpenAPI spec naming a password field in its schema is not a data leak
    assert response_leaks_credentials(_resp('{"openapi":"3.0.0","paths":{"x":{"password":"string"}}}')) is False
    # non-200 (e.g. a 401 body that happens to mention a password) is not a leak
    assert response_leaks_credentials(_resp('{"password":"secret"}', status=401)) is False


def test_data_exposure_probe_fires_on_leaky_endpoint():
    report = run(SubprocessDeployer(str(REFS / "jsonapi" / "app.py")), load_catalog(CATALOG))
    assert report.by_id["sec-exposure-005"] == "slop_detected"  # /api/dump leaks passwords
