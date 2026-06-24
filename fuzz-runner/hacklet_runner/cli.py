"""Run the catalog against one reference app via the subprocess deployer; print the slop report.

    uv run python -m hacklet_runner.cli --app references/vulnerable/app.py
"""
from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import asdict

from .catalog import load_catalog
from .deploy import SubprocessDeployer
from .pipeline import run

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser(description="HackLet fuzz runner (vertical slice)")
    ap.add_argument("--app", required=True, help="path to a reference app.py (subprocess deployer)")
    ap.add_argument("--catalog", default=str(_ROOT / "catalog"))
    args = ap.parse_args()

    report = run(SubprocessDeployer(args.app), load_catalog(args.catalog))
    print(
        json.dumps(
            {"slop_score": report.slop_score, "outcomes": [asdict(o) for o in report.outcomes]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
