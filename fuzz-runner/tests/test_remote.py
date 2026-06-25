"""RemoteDeployer tests — point the runner at an already-running endpoint (no Docker).

Reuses SubprocessDeployer to host a reference app, then targets its URL with RemoteDeployer: the
score must match (same app, same catalog), and teardown must NOT stop the target.
"""
import pathlib

import httpx
import pytest

from hacklet_runner.catalog import load_catalog
from hacklet_runner.deploy import RemoteDeployer, SubprocessDeployer
from hacklet_runner.pipeline import run

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
REFS = ROOT / "references"


@pytest.fixture
def running_vulnerable():
    host = SubprocessDeployer(str(REFS / "vulnerable" / "app.py"))
    handle = host.deploy()
    try:
        yield handle.base_url
    finally:
        host.teardown()


def test_remote_fuzzes_running_target(running_vulnerable):
    report = run(RemoteDeployer(running_vulnerable), load_catalog(CATALOG))
    assert report.slop_score == 358  # same app, same catalog -> same score as SubprocessDeployer


def test_remote_teardown_does_not_stop_target(running_vulnerable):
    d = RemoteDeployer(running_vulnerable)
    d.deploy()
    d.teardown()  # must be a no-op
    assert httpx.get(running_vulnerable + "/", timeout=2.0).status_code < 500


def test_remote_unreachable_raises():
    with pytest.raises(RuntimeError):
        RemoteDeployer("http://127.0.0.1:1", health_timeout=1.0).deploy()
