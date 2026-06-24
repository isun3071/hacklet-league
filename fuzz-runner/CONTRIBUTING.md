# Authoring probes

How to add, change, and remove fuzz probes. The runner is a **fixed engine**; **probes are data**
(`catalog/**/*.yaml`, loaded by `load_catalog()` at run time). Reusing existing detection needs no
code change — only a *new* detection primitive touches Python. Canonical design lives in
[../FUZZ_RUNNER_SPEC.md](../FUZZ_RUNNER_SPEC.md); this is the practical recipe.

## The probe schema

```yaml
id: sec-sqli-001            # unique
bundle: security            # security | qa | performance
category: sql-injection     # diminishing returns apply within a category
variant_group_id: <id>      # optional; probes sharing one fire ONCE (same logical flaw)
pool: public                # public | hidden
evidence_model: provable    # provable (slop visible in response) | oracle (differential)
penalty: 40                 # slop added when it fires (deduction-only; always positive)
applicability:
  requires: [any_endpoint_accepts_text_input]   # capabilities from discovery; empty = always
probe:
  # EITHER declarative:
  method: POST
  target: /search
  query: { q: "<payload>" }   # optional query params
  data:  { age: abc }         # optional form body
  # OR an oracle:
  predicate: sqli_auth_bypass
  payload: "' OR '1'='1' -- "
slop_if:                      # declarative only; ALL must match -> slop (omit for predicate probes)
  - response_contains: "<payload>"
```

## Add a probe

### 1. Declarative, reusing a matcher — one file, no code
Drop a YAML in `catalog/<bundle>/`. Example: a second error-hygiene probe on `/profile`, reusing
`response_leaks_stack_trace`:

```yaml
# catalog/qa/qa-errhyg-002.yaml
id: qa-errhyg-002
bundle: qa
category: error-hygiene
penalty: 8
applicability: { requires: [at_least_one_http_endpoint_exists] }
probe: { method: POST, target: /profile, data: { age: abc } }
slop_if: [ response_leaks_stack_trace ]
```

Matchers available today (`hacklet_runner/probes.py` → `MATCHERS`):

| Matcher | Slop when |
| --- | --- |
| `response_leaks_stack_trace` | the response body contains a traceback signature |
| `response_contains: <str>` | the response body contains `<str>` (e.g. an unescaped XSS marker) |
| `response_missing_header: <name>` | the response lacks header `<name>` |
| `response_server_error` | status is 500 / 502 / 503 / 504 (a crash, not 501/405) |
| `ttfb_at_least: <seconds>` | time-to-first-byte ≥ `<seconds>` |

### 2. A variant of an existing group — one file, same `variant_group_id`
A new SQLi syntax: copy a `sec-sqli-*.yaml`, change the `payload`, keep
`variant_group_id: sqli-auth-bypass`. It reuses the oracle and folds into the same fires-once
group automatically (the group counts one penalty no matter how many syntaxes fire).

### 3. A new detection primitive — +1 function, then the YAML
- **New matcher** → add to `MATCHERS`. Signature `(resp, arg=None) -> bool`, returning `True`
  when slop is present.
- **New oracle** → add to `PREDICATES`. Signature `(ctx, probe) -> bool`; use `ctx.client`
  (httpx), `ctx.profile` (discovered surface), and `probe.probe` for params like `payload`.

Predicates available today (`PREDICATES`): `sqli_auth_bypass`.

## Change a probe
- **Tuning** (penalty, payload, threshold, applicability, pool) → edit the YAML field, re-calibrate.
  e.g. tighten the speed gate `ttfb_at_least: 3.0 → 2.5`, or re-weight SQLi `penalty: 40 → 50`.
- **Detection logic** → edit the matcher/predicate in `probes.py` (affects every probe that uses
  it, so review accordingly).
- **Pool flip** (public ↔ hidden) → change `pool:` and move the file between this public catalog
  and the private `fuzz-catalog` repo.

## Remove a probe
Delete the YAML file — the runner stops loading it. Update/remove its assertion in `tests/`. For an
event-grade catalog, *deprecate in the changelog* rather than silently delete, so past results stay
interpretable.

## The calibration gate (non-negotiable)
Every add/change must keep `uv run pytest` green. A probe must read **slop on
`references/vulnerable`, clean on `references/hardened`, and N/A or clean on `references/minimal`**.
If your probe targets a surface the reference apps lack, add it — broken in `vulnerable`, defended
in `hardened`. So "add a probe" is usually three coupled edits:

1. the probe YAML,
2. the reference surface (if new),
3. the test assertion.

That coupling is the point: a probe that can't separate defended from broken from absent does not
merge.

## Over time
Versioning (semver + quarterly cadence), PR review, and public-vs-hidden governance are in
[../FUZZ_RUNNER_SPEC.md](../FUZZ_RUNNER_SPEC.md) (Catalog Organization, Test Authoring Workflow,
Pool composition). Hidden probes are authored the same way but live in the **private `fuzz-catalog`
repo**, never this public one.
