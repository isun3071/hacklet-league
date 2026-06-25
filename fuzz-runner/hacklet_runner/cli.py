"""Deploy/target an app, probe it over HTTP, and report a slop score (lower is better).

Default output is a human-readable summary; --failed lists the probes that detected slop; --json
prints the full machine-readable report. See --help for all options.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import textwrap
from collections import Counter
from dataclasses import asdict

from . import browser
from .catalog import load_catalog
from .deploy import DockerDeployer, RemoteDeployer, SubprocessDeployer
from .ingest import SubmissionError, extract_submission
from .pipeline import run

_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Any deploy/build/health failure -> DNF (the worst outcome), not a crash.
_DEPLOY_FAILURES = (RuntimeError, TimeoutError, subprocess.SubprocessError, OSError)


# ---- output renderers (pure: build text, caller prints) -------------------------------------

def _report_payload(report) -> dict:
    return {"slop_score": report.slop_score, "outcomes": [asdict(o) for o in report.outcomes]}


def _summary_text(report, source: str) -> str:
    outs = report.outcomes
    slop = [o for o in outs if o.outcome == "slop_detected"]
    clean = sum(1 for o in outs if o.outcome == "clean")
    na = sum(1 for o in outs if o.outcome == "not_applicable")
    lines = [
        "",
        f"  {source}",
        "",
        f"  Slop score: {report.slop_score}        lower is better — 0 is clean",
        "",
        f"  {len(slop)} slop · {clean} clean · {na} n/a        ({len(outs)} probe runs)",
        "",
    ]
    if slop:
        by_cat = Counter(f"{o.bundle}/{o.category}" for o in slop)
        lines.append("  where the slop is:")
        for cat, n in sorted(by_cat.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"    {cat:<28} {n}")
        lines += ["", "  → --failed lists each one · --json for the full report"]
    else:
        lines.append("  clean — no slop detected.")
    lines.append("")
    return "\n".join(lines)


def _failed_text(report, source: str) -> str:
    slop = sorted(
        (o for o in report.outcomes if o.outcome == "slop_detected"),
        key=lambda o: (o.bundle, o.category, o.probe_id, o.target),
    )
    lines = ["", f"  {source} — {len(slop)} slop (score {report.slop_score})", ""]
    if not slop:
        return "\n".join(lines + ["  clean — no slop detected.", ""])
    lines.append(f"  {'PROBE':<16} {'CATEGORY':<20} {'PEN':>3}  TARGET")
    for o in slop:
        lines.append(f"  {o.probe_id:<16} {o.category:<20} {o.penalty:>3}  {o.target or '—'}")
    lines.append("")
    return "\n".join(lines)


def _print_report(report, source: str, args) -> None:
    if args.json:
        print(json.dumps(_report_payload(report), indent=2))
    elif args.failed:
        print(_failed_text(report, source))
    else:
        print(_summary_text(report, source))


def _fail(args, status: str, reason: str):
    if args.json:
        print(json.dumps({"status": status, "reason": reason}, indent=2))
    else:
        print(f"\n  {status}: {reason}\n")
    raise SystemExit(1)


# ---- entry point ----------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        prog="hacklet-runner",
        description="Deploy/target an app, probe it over HTTP, and report a slop score (lower is better).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            examples:
              %(prog)s --app references/vulnerable/app.py     # trusted ref, no Docker
              %(prog)s --submission team.zip --harden         # untrusted zip, sandboxed (Docker host)
              %(prog)s --target https://example.com --failed  # an already-running URL

            Only fuzz targets you own or are authorized to test.
            """
        ),
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--submission", metavar="ZIP", help="a submission .zip (built + sandboxed via Docker)")
    src.add_argument("--target", metavar="URL", help="an already-running URL (dogfooding; no Docker)")
    src.add_argument("--app", metavar="PATH", help="a trusted reference app.py (subprocess; dev/CI)")
    ap.add_argument("--catalog", metavar="DIR", default=str(_ROOT / "catalog"), help="probe catalog dir")
    ap.add_argument("--browser", action="store_true",
                    help="render pages with a headless browser (finds SPA/client-rendered forms)")
    ap.add_argument("--harden", action="store_true",
                    help="production sandbox for --submission: read-only rootfs + egress-blocked network")
    ap.add_argument("--network", metavar="NET", default="hacklet-fuzz-net",
                    help="docker network for --harden (create once: docker network create --internal NET)")
    out = ap.add_argument_group("output")
    out.add_argument("--json", action="store_true", help="print the full machine-readable JSON report")
    out.add_argument("--failed", action="store_true", help="list only the probes that detected slop")
    args = ap.parse_args()

    catalog = load_catalog(args.catalog)
    render = browser.render_html if args.browser else None
    source = args.app or args.target or args.submission

    # Trusted reference app: subprocess, no Docker.
    if args.app:
        _print_report(run(SubprocessDeployer(args.app), catalog, render=render), source, args)
        return

    # Already-running URL: dogfooding, no Docker, no teardown of the target.
    if args.target:
        try:
            report = run(RemoteDeployer(args.target), catalog, render=render)
        except _DEPLOY_FAILURES as e:
            _fail(args, "unreachable", str(e)[:500])
        _print_report(report, source, args)
        return

    # Untrusted submission: unzip -> build -> sandboxed run -> fuzz.
    try:
        sub = extract_submission(args.submission)
    except SubmissionError as e:
        _fail(args, "DNF", str(e))
    try:
        deployer = DockerDeployer(
            str(sub.context_dir),
            read_only=args.harden,
            network=args.network if args.harden else None,
        )
        report = run(deployer, catalog, render=render)
    except _DEPLOY_FAILURES as e:
        _fail(args, "DNF", str(e)[:500])
    finally:
        sub.cleanup()
    _print_report(report, source, args)


if __name__ == "__main__":
    main()
