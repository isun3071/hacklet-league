"""Run the catalog against a submission, a live URL, or a trusted reference app; print the report.

    # a real submission zip — unzip -> build Dockerfile -> sandboxed run -> fuzz (Docker host):
    uv run python -m hacklet_runner.cli --submission team.zip
    uv run python -m hacklet_runner.cli --submission team.zip --harden   # production sandbox

    # an already-running URL — dogfooding; no Docker (only test targets you own/are authorized to):
    uv run python -m hacklet_runner.cli --target https://hackletleague.com

    # a trusted reference app via subprocess, no Docker (dev/CI):
    uv run python -m hacklet_runner.cli --app references/vulnerable/app.py

Any submission that won't unzip, lacks a Dockerfile, won't build, or never answers $PORT emits
{"status": "DNF", ...} and exits 1 — never a runner crash.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
from dataclasses import asdict

from .catalog import load_catalog
from .deploy import DockerDeployer, RemoteDeployer, SubprocessDeployer
from .ingest import SubmissionError, extract_submission
from .pipeline import run

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Any deploy/build/health failure -> DNF (the worst outcome), not a crash.
_DEPLOY_FAILURES = (RuntimeError, TimeoutError, subprocess.SubprocessError, OSError)


def _emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def _report_payload(report) -> dict:
    return {"slop_score": report.slop_score, "outcomes": [asdict(o) for o in report.outcomes]}


def main() -> None:
    ap = argparse.ArgumentParser(description="HackLet fuzz runner")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--submission", help="path to a submission .zip (built + sandboxed via Docker)")
    src.add_argument("--target", help="fuzz an already-running URL — dogfooding; no Docker. Only "
                                      "test targets you own or are authorized to test.")
    src.add_argument("--app", help="path to a trusted reference app.py (subprocess deployer; dev/CI)")
    ap.add_argument("--catalog", default=str(_ROOT / "catalog"))
    ap.add_argument("--harden", action="store_true",
                    help="production sandbox: read-only rootfs + egress-blocked --network")
    ap.add_argument("--network", default="hacklet-fuzz-net",
                    help="docker network for --harden (create once: docker network create --internal <name>)")
    args = ap.parse_args()

    catalog = load_catalog(args.catalog)

    # Trusted reference app: subprocess, no Docker.
    if args.app:
        _emit(_report_payload(run(SubprocessDeployer(args.app), catalog)))
        return

    # Already-running URL: dogfooding, no Docker, no teardown of the target.
    if args.target:
        try:
            report = run(RemoteDeployer(args.target), catalog)
        except _DEPLOY_FAILURES as e:
            _emit({"status": "unreachable", "reason": str(e)[:500]})
            raise SystemExit(1)
        _emit(_report_payload(report))
        return

    # Untrusted submission: unzip -> build -> sandboxed run -> fuzz.
    try:
        sub = extract_submission(args.submission)
    except SubmissionError as e:
        _emit({"status": "DNF", "reason": str(e)})
        raise SystemExit(1)
    try:
        deployer = DockerDeployer(
            str(sub.context_dir),
            read_only=args.harden,
            network=args.network if args.harden else None,
        )
        report = run(deployer, catalog)
    except _DEPLOY_FAILURES as e:
        _emit({"status": "DNF", "reason": str(e)[:500]})
        raise SystemExit(1)
    finally:
        sub.cleanup()
    _emit(_report_payload(report))


if __name__ == "__main__":
    main()
