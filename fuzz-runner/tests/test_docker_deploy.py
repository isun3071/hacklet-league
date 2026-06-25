"""Docker calibration: the same three-way reference suite, deployed via DockerDeployer instead of
SubprocessDeployer, must produce identical slop scores (vulnerable 190, hardened 0, minimal 0).

This is the proof that the production deployer is behavior-equivalent to the dev/CI one — same
catalog, same probes, same scores — just a sandboxed container instead of a local subprocess.

Skipped where Docker is absent (the dev box has none); runs on the VM / CI. Keep the expected
scores in lockstep with tests/test_pipeline.py.
"""
import pathlib
import shutil

import pytest

from hacklet_runner.catalog import load_catalog
from hacklet_runner.deploy import DockerDeployer
from hacklet_runner.pipeline import run

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog"
REFS = ROOT / "references"

pytestmark = pytest.mark.skipif(
    shutil.which("docker") is None, reason="Docker not available (run on the VM/CI)"
)


def _score(app: str) -> int:
    return run(DockerDeployer(str(REFS / app)), load_catalog(CATALOG)).slop_score


def test_docker_vulnerable_matches_subprocess():
    assert _score("vulnerable") == 190


def test_docker_hardened_is_clean():
    assert _score("hardened") == 0


def test_docker_minimal_is_clean():
    assert _score("minimal") == 0
