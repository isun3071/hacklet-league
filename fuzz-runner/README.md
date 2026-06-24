# HackLet fuzz runner (Stage 5 vertical slice)

Deploys a submission, probes it over HTTP, and emits a **slop score** (deduction-only, lower is
better). This is the smallest end-to-end proof of the pipeline; the catalog and sandbox grow from
here. Canonical design: [../FUZZ_RUNNER_SPEC.md](../FUZZ_RUNNER_SPEC.md).

## What the slice proves

`deploy → discover → applicability → execute → aggregate → report`, against two reference apps
with the same surface: a **vulnerable** one (accrues slop) and a **hardened** one (clean). Three
probes, one per bundle:

- `sec-sqli-001` — SQL injection via a boolean/auth-bypass **oracle** (security)
- `qa-errhyg-001` — leaked stack trace, a **declarative** matcher (qa)
- `perf-ttfb-001` — TTFB speed gate ≥ 3s (performance)

## Run it

```sh
uv run pytest -q                                          # the three-way calibration suite
uv run python -m hacklet_runner.cli --app references/vulnerable/app.py   # prints a slop report
uv run python -m hacklet_runner.cli --app references/hardened/app.py     # slop_score 0
```

## Hosting model

The pipeline depends only on a `Deployer` (`hacklet_runner/deploy.py`):

- **`SubprocessDeployer`** (dev/CI) launches a **trusted reference app** as a local subprocess on
  an injected `$PORT`. No Docker required. **Never** used for untrusted submissions.
- **`DockerDeployer`** (production) builds the submission's `Dockerfile` and runs it in the sandbox
  on the runner host where Docker exists: ephemeral, fixed CPU/RAM/PID quotas, `--cap-drop=ALL`,
  `--security-opt=no-new-privileges`, `$PORT` injected. Everything downstream of "container answers
  `$PORT`" is identical and stack-blind. The three-way calibration runs through it and scores
  identically — that equivalence is the test (`tests/test_docker_deploy.py`).

### Hardened sandbox (production)

For untrusted submissions, enable the hardening toggles:

```py
DockerDeployer(ctx, read_only=True, network="hacklet-fuzz-net", runtime="runsc")
```

Create the egress-blocked network once (`docker network create --internal hacklet-fuzz-net`) and
install gVisor for `runtime="runsc"`. `tests/test_docker_hardened.py` verifies that hardening
preserves the 98/0/0 calibration and that the `--internal` network actually blocks egress; it
manages its own throwaway network, so it needs no setup.

## Not yet in the slice (tracked in the spec)

Browser-driven discovery (Playwright) for SPAs + FCP/INP; the hidden pool; stochastic sampling
(median-of-N); container orchestration + throughput across many submissions; gVisor/Firecracker
runtime install on the runner host.

Already wired: the composition dampers (`aggregate.py` — variant-group-once +
diminishing-returns-within-category; per-bundle ordering lives in the penalty magnitudes) and the
vuln/hardened/minimal reference triad.
