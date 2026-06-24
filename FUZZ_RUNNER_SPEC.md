# HackLet League — Fuzz Runner Specification

*Architecture and conventions for the fuzz runner that executes the test catalog against submissions. Covers test format, runner phases, execution model, and catalog organization. Distinct from format_spec.md (what tests measure) and DATA_MODEL.md (how results are stored).*

---

## Overview

The fuzz runner is responsible for executing standardized tests against player submissions. It runs in two modes:

- **Local runner**: lightweight version on chapter workstations, runs public pool tests against local deployments during build phase. Results are informational.
- **Central runner**: full version on league infrastructure, runs both pools (public and hidden) against deployed submissions at code freeze. Results are authoritative.

Both modes share the same test format and execution semantics. They differ in what catalog content they have access to and where results are persisted.

## v1 Catalog Design (Universal-Only)

### Universal-only principle

The catalog is **language-, framework-, and protocol-agnostic**. Every submission is tested by the same black-box HTTP probing of its deployed app; the catalog contains **no framework-specific tests**. A Python/Flask app, a Go service, and a hand-rolled C HTTP server are all evaluated by the identical catalog.

"Tested the same way" means **same catalog, applicability-resolved per discovered surface** — not literally the same test set for every app. A submission that exposes a file-upload endpoint receives the upload probes; one that does not, cannot (there is nothing to test). That asymmetry is correct and is what **Attack Surface Coverage** (format_spec §4.2, narrow/moderate/broad) measures: exposing more surface means more applicable tests, which is itself signal.

The tradeoff (loss of framework-specific precision) is largely recovered through **universal symptom probes**: a misconfiguration that is framework-specific in cause is usually framework-agnostic in symptom. `DEBUG=True` surfaces as stack traces in responses (caught by universal error-hygiene); an exposed admin/actuator surfaces via a universal sensitive-path probe that GETs a list of known-dangerous paths (`/.env`, `/.git`, `/actuator`, `/admin`, `/debug`, `/swagger`) regardless of stack.

### The intent-independence litmus (authoring invariant)

A test may exist **only if its correct outcome is the same regardless of what the app is supposed to do**. The authoring litmus:

> Is there a legitimate app for which the "failing" behavior is actually correct?

- **No** (wrong for every legitimate intent) → universal → include.
- **Yes** (some real app legitimately wants it) → intent-dependent → exclude.

| Property | Legit app wanting the "fail"? | Verdict |
| --- | --- | --- |
| SQL injection succeeds | none | universal |
| Stack trace leaked in error response | none | universal |
| `GET` mutates state | none (HTTP mandates safe `GET` for all apps) | universal |
| `POST /pay` dedupes a double-submit | yes (an append-only event log wants both writes) | intent-dependent → excluded |
| at-most-once delivery | yes (messaging legitimately wants at-least-once) | intent-dependent → excluded |

Because every test in the catalog is universal by construction, the schema carries **no intent flag**. Intent-dependent engineering quality is not unmeasured: it is credentialed on the **communication axis** (PITCH.md + cross-examination + judge clickaround), where a human carries the intent the runner refuses to guess. The slop score stays intent-free and fully automated; there is no per-test judge override of slop outcomes.

### Bundles

v1 ships three bundles. The six-axis Slop model (IDEAS_FOR_LATER) adds Race Conditions and Behavioral Consistency as later bundles without changing the runner.

- **security** — OWASP-aligned: injection (SQL/NoSQL/command/template), XSS, auth bypass, broken access control / IDOR, CSRF, SSRF, security headers, sensitive-path exposure.
- **qa** — universal QA per format_spec §4.2: crash resistance, error hygiene, HTTP semantics, encoding round-trip, deployment hygiene.
- **performance** — speed checkpoints (below) plus load/spike handling and DoS resistance (oversized bodies/URLs/headers, decompression bombs, unbounded pagination, slow-loris). Load and DoS are measured inside the container's **fixed resource envelope** (identical CPU/RAM/PID quotas for every submission), so comparison is fair: it measures how the app holds up within the standard box, not scaling to arbitrary hardware. DoS probes are bounded so the runner cannot become its own amplifier.

### Speed checkpoints

Speed is scored as **boolean gates at user-abandonment thresholds**, not optimization targets:

| Metric | Adds slop at | Where measured |
| --- | --- | --- |
| TTFB | ≥ 3s | server-side timing (any HTTP response) |
| FCP | ≥ 5s | headless browser; HTML-rendering apps only |
| INP | ≥ 5s | headless browser (Total-Blocking-Time proxy / scripted interaction); HTML apps only |

Clearing all gates adds no slop; each gate that trips adds the speed category's slop, with **no marginal credit for being faster** (Goodhart-resistant: players optimize to the gate, then redirect remaining time elsewhere). FCP and INP apply only to apps that serve a rendered HTML document; a pure JSON API scores them **N/A** (structural, from discovery). FCP/INP require the headless-browser harness, which renders untrusted submission pages and is therefore sandboxed like the rest of the runner (isolated context, no host FS, egress-restricted).

**Reconciliation with format_spec §4.2.** §4.2 previously excluded Core Web Vitals as optimization metrics that "penalize all submissions uniformly without differentiating skill." Abandonment-threshold *gates* are a different instrument: they do not penalize uniformly, they catch only the egregiously broken. The gates above supersede that blanket exclusion; optimization-target scoring (e.g., crediting LCP < 2.5s on a slope) stays out of scope.

### Outcome semantics: deduction-only (slop)

Scoring is **deduction-only** (format_spec §4.2). A probe never adds credit, only slop. Each probe resolves to one of:

| Outcome | Slop |
| --- | --- |
| **slop_detected** (the probe fired) | + penalty |
| **clean** (applicable surface present, probe did not fire) | 0 |
| **not_applicable** (no such surface) | 0 |

`clean` and `not_applicable` both contribute 0 — they are tracked separately only for the reporting bundle (Attack Surface Coverage, Clean Rate). The submission's **slop score** is the sum of every fired probe's penalty.

This collapses the earlier provable/failure-only scoring split. A clean result is 0 whether the defense was *observed* (an XSS payload returned escaped) or simply *never fired* (parameterized SQL, or no SQL at all), so **the runner no longer has to tell "defended" from "absent"** — the unsolvable case dissolves. Every probe needs only a **slop oracle**: the conditions under which slop is present. They match → penalty; otherwise → 0. We never prove the inverse.

`evidence_model` survives only as a **detection hint**, never a scoring driver:

- `provable` — the slop oracle reads observable output (the payload's fate is in the response: XSS escaping, a leaked stack trace, another user's record returned).
- `oracle` — the sink is hidden (SQLi, command injection, SSTI), so the slop oracle uses a differential / timing / error signal.

Both score identically (penalty if slop detected, else 0). The distinction only tells the runner *how* to look.

### Detecting slop (the oracle)

Never a single payload against a single response — a matched set that fires only when the slop is real. SQLi:

- **Boolean differential** — `' OR '1'='1' --` vs `' AND '1'='2' --` diverge in the attacker's favor → slop.
- **Error oracle** — a lone `'` yields a 500 with SQL error text → slop.
- **Time oracle** — a `pg_sleep(5)`-style payload delays the response ~5s → slop.

If none fire → clean (0). Egress is locked, so oracles are **in-band only** (differential / timing / error / observed output); out-of-band callbacks are unavailable (see threat model), which bounds detection of fully-blind injections and OOB-only SSRF.

### Aggregation: plain summation

The slop score is the sum of every fired probe's penalty across its applicable targets. There is **no worst_case/additive distinction to maintain** — with no positive credit to protect, "partial defense" simply means each missed target adds its slop. Catastrophic categories (SQLi, auth bypass) carry **large per-probe penalties** so a single failure dominates the score; that calibration does the work the old worst_case mode used to, without a separate aggregation rule.

### N/A and reporting honesty

A category never claims "defended." It reports slop found (with penalty) or **no slop found**. `not_applicable` (surface absent, structural from the discovery profile + `applicability.requires`) and `clean` (surface present, no slop) both score 0 but are tracked separately. **Clean Rate** = clean / (clean + slop_detected) over applicable probes; **Attack Surface Coverage** derives from the applicable count.

Authoring consequence: every test has a single `slop_if` (the oracle conditions). There is no `defended_if` — absence of slop is simply 0, never positive credit.

## Runner as a Sandboxed, Deployable Service

The runner is a **standalone deployable component, separate from the hackletleague.com platform process**. It executes untrusted contestant code, so it must not share a trust domain with the platform's database, secrets, or session store. It is deployed isolated (separate host/VM, restricted egress). This separation also makes **dogfooding (LEAGUE_OPERATIONS §12) first-class**: the runner points at any deployed HTTP target, so the league's own production code is just another target.

### Platform ↔ runner contract

1. The platform stores the submission zip at code freeze (portal upload, TIER_C_OPERATIONS §6).
2. The platform enqueues a run: `{submission_id, artifact_ref, catalog_version}`.
3. The runner pulls the artifact, deploys it to an ephemeral container, and runs the five phases.
4. The runner returns a structured **slop report** (per-probe outcomes + penalties + metadata).
5. The platform persists `FuzzResult` rows; the scoring engine (separate, see Scoring Integration) folds the result into the composite.

The platform **never executes submission code in-process**.

### Threat model (sandbox for hostile code)

Submissions are untrusted code generated by players directing AI. The runner is a sandbox first, a test executor second.

- **Container isolation** — unprivileged user, no sudo, read-only base image where feasible, ephemeral, destroyed after each run.
- **Resource exhaustion** — CPU / RAM / disk / PID quotas and a wall-clock lifecycle bound on every container; load and DoS probes are bounded so the runner is never an amplifier.
- **Network egress** — submission containers have no outbound network except the runner's probe channel. This prevents data exfiltration, lateral movement, and using a submission as an egress proxy.
- **Hidden-pool boundary** — hidden-pool test definitions exist **only on the central runner**. They are never deployed to workstations, never included in any client- or player-facing payload, and never echoed in player-visible results. The local (workstation) runner contains the public pool only.
- **Headless-browser harness** — because it renders untrusted submission pages, it runs in the same sandbox posture: isolated browser context, no host filesystem access, egress-restricted.

## Test Definition Format

Each test is defined as a YAML file with a standardized schema. The schema is validated via Pydantic models in the runner codebase.

### Schema

```yaml
id: <unique-identifier>           # e.g., sec-sqli-001
bundle: <security | qa | performance>
category: <category-name>          # human-readable category
subcategory: <subcategory>         # optional, for variant grouping
difficulty_tier: <1 | 2 | 3 | 4 | 5>
pool: <public | hidden>
attack_type: <adversarial | non_adversarial>        # informational
evidence_model: <provable | oracle>                  # DETECTION hint only, not scoring: provable = slop
                                                    #   visible in the response; oracle = differential/
                                                    #   timing/error signal for a hidden sink
description: <text description of what the test does>
penalty: <positive integer>                          # slop added when slop_if fires; 0 otherwise
variant_group_id: <UUID or null>  # if part of a syntactic variant group

applicability:
  requires:
    - <applicability_condition_1>
    - <applicability_condition_2>

probe:
  method: <HTTP method>
  target: <target_selector>
  payload_template: <structured payload>
  per_target_timeout_seconds: <integer, default 30>
  variants:                       # additional payloads to test
    - <variant_1>

slop_if:                           # slop detected (penalty applied) when ALL conditions match; else 0
  - <assertion_condition>
  - <assertion_condition>
```

### Applicability Conditions

Common applicability conditions reference properties of the submission profile:

- `submission_deploys_successfully`
- `at_least_one_http_endpoint_exists`
- `any_endpoint_accepts_text_input`
- `submission_has_file_upload_endpoint`
- `submission_has_auth_endpoints`
- `submission_has_form_endpoints`
- `submission_has_api_endpoints`
- `submission_has_post_endpoints_creating_records`
- `submission_stores_persistent_data`
- `submission_serves_html_document`   # gates FCP/INP speed checks; false for pure JSON APIs

The discovery phase produces a submission profile listing which conditions are true for that submission.

### Target Selectors

Targets identify which endpoints in the submission a probe should hit:

- `homepage` — root URL
- `all_discovered_routes` — every URL the discovery phase found
- `discovered_form_endpoints` — every form-accepting endpoint
- `discovered_api_endpoints` — every API endpoint
- `file_upload_endpoints` — endpoints accepting file uploads
- `auth_endpoints` — login, signup, password reset endpoints
- `<specific_path>` — explicit URL pattern

### Assertion Conditions

A probe's `slop_if` lists structured conditions describing **when slop is present** (all must match for the probe to fire and add its penalty). Common patterns:

**Response status conditions:**
- `response_status_in: [<list_of_codes>]`
- `response_status_equals: <code>`
- `response_status_500_with_db_error` — a 500 leaking a DB error is itself slop

**Response content conditions** (slop = the bad thing is present):
- `response_contains: <pattern>`
- `response_contains_unauthorized_records`
- `response_contains_credentials`
- `response_leaks_db_error`
- `response_leaks_stack_trace`

**Timing conditions:**
- `response_received_after: <duration>` — e.g. a time-based injection oracle firing

**Speed-gate conditions** (performance bundle; browser-measured ones apply only when `submission_serves_html_document`) — slop when the threshold is breached:
- `ttfb_at_least: <duration>`   # server-side; slop at >= 3s
- `fcp_at_least: <duration>`    # headless browser; slop at >= 5s
- `inp_at_least: <duration>`    # headless browser (TBT proxy / scripted interaction); slop at >= 5s

**Behavioral conditions** (slop = the attack succeeded):
- `upload_succeeds_and_executes: true`
- `auth_bypassed: true`
- `boolean_differential_diverges: true` — injection oracle: the TRUE/FALSE payloads differ in the attacker's favor

**Complex conditions** that require code reference named predicates that return true **when slop is present**:

```yaml
slop_if:
  - predicate: csrf_unprotected
```

These named predicates live in the `predicates/` directory and are reviewed alongside test additions.

## Runner Phases

The runner executes in five distinct phases per submission.

### Phase 1: Discovery

The runner explores the submission to build its profile:

1. Start at the homepage (configurable per submission, typically `http://submission:PORT/`)
2. Crawl reachable URLs via HTML link extraction
3. Identify form endpoints by parsing `<form>` elements
4. Identify API endpoints by checking common patterns (`/api/*`, GraphQL, OpenAPI specs if present)
5. Identify authentication boundaries by examining 401/403 responses
6. Identify file upload capabilities by checking form encoding types and file inputs
7. Determine whether the app serves a rendered HTML document (`Content-Type: text/html` with a parseable DOM) versus a pure API — this gates the FCP/INP speed checks
8. Establish per-endpoint baselines (benign-input response signatures: status, length, timing) so adversarial oracles have a reference to diff against
9. Produce a submission profile structure

The discovery phase runs for a fixed time budget (e.g., 30 seconds) or until exhaustion, whichever comes first.

### Phase 2: Applicability Resolution

For each test in the catalog:

1. Check whether all `applicability.requires` conditions are met against the submission profile
2. If yes, mark the test as applicable; if not, the test resolves to `not_applicable` (structural N/A) and is skipped

Applicability is **fully automated** — the catalog is universal-only, so there are no intent-sensitive tests and no judge-resolution step. (Behavioral N/A, where an applicable test's vector turns out not to reach a live sink, is resolved during execution by the test's oracle, not here.) The result is the list of applicable tests.

### Phase 3: Execution

Applicable tests execute in parallel up to a concurrency limit (default: 20 concurrent tests per submission):

1. For each test, construct the HTTP request(s) per the probe specification
2. Send requests with configured timeout
3. Collect responses
4. Evaluate assertion conditions against responses
5. Determine outcome: slop_detected / clean / not_applicable
6. Record outcome, response data, and timing

Some tests may require sequential execution (e.g., session-dependent tests). The test definition can declare `requires_sequential: true` to opt out of parallel execution.

### Phase 4: Result Aggregation

After all tests complete:

1. Tally outcomes per test
2. Compute the slop score by summing fired probes' penalties
3. Compute attack surface coverage (narrow / moderate / broad) from applicable count
4. Compute clean rate (clean / applicable)
5. Generate per-category summaries

### Phase 5: Reporting

Results are persisted via different paths depending on runner mode:

**Local runner** (during build):
- Records to PlayerFuzzInvocation table
- Streams results to player portal for real-time display
- Updates broadcast leaderboard if event is being broadcast

**Central runner** (at code freeze):
- Records to FuzzResult table (authoritative)
- Triggers the scoring engine when the run completes — under universal-only the slop score is fully automated, with no per-probe override
- Tester judges may spot-check for false positives out of band, but that does not gate scoring; judges' scored role is the communication axis (clickaround, pitch, cross-examination)

## Execution Architecture

### Local Runner

Runs as a Python service on each workstation, started by RMM at event startup.

- Listens on local port (e.g., `127.0.0.1:8888`) for trigger requests from league portal browser tab
- Has access to public pool test catalog (deployed via RMM with workstation image)
- Hits player's local deployment at known port (e.g., `127.0.0.1:3000`)
- Reports results back to league via outbound HTTPS

The local runner does not contain hidden pool tests. Hidden pool YAML files are never present on workstations.

### Central Runner

Runs as a standalone, containerized service on league infrastructure, separate from the platform process (see "Runner as a Sandboxed, Deployable Service").

- Pulls the submission **zip** the platform stored at code freeze (portal upload, TIER_C_OPERATIONS §6) — there is no git in the submission path
- Deploys the submission to an ephemeral Docker container under the sandbox posture (unprivileged, quota-bound, egress-restricted)
- Container exposes the submission's port to the runner only
- Runner executes the full catalog (both pools) against the deployed container
- After completion, the container is destroyed
- Returns the slop report to the platform, which persists FuzzResult rows

The central runner runs in a queue model — 12 submissions arrive at freeze, workers process them in parallel up to infrastructure capacity. Target: complete all submissions within the 12-minute evaluation window.

## Catalog Organization

The test catalog is a versioned repository (`fuzz-catalog`) with this structure:

```
fuzz-catalog/
├── security/
│   ├── sql-injection/
│   │   ├── sqli-001-boolean.yaml
│   │   ├── sqli-002-union.yaml
│   │   └── ...
│   ├── xss/
│   ├── file-upload/
│   ├── auth/
│   ├── csrf/
│   └── ...
├── qa/
│   ├── crash-resistance/
│   │   ├── crash-001-empty-input.yaml
│   │   ├── crash-002-oversized-input.yaml
│   │   └── ...
│   ├── error-hygiene/
│   ├── http-semantics/
│   ├── timeout/
│   ├── encoding/
│   └── ...
├── performance/
│   ├── speed-checkpoints/        # TTFB / FCP / INP boolean gates
│   ├── load-spike/
│   ├── dos-resistance/
│   └── ...
├── predicates/
│   ├── http_response.py
│   ├── timing.py
│   ├── content.py
│   ├── csrf.py
│   └── ...
├── schemas/
│   └── test_schema.json
├── CATALOG_VERSION
└── README.md
```

Catalog versioning follows semver:
- **Major version**: structural changes to test format
- **Minor version**: new tests added, new categories introduced
- **Patch version**: bug fixes to existing tests, scoring recalibrations

Catalog releases are tagged in git. Chapters can pin to specific versions or auto-update on minor releases.

## Submission Profile Schema

The discovery phase produces a JSON document describing what the runner found:

```json
{
  "deploys_successfully": true,
  "endpoints": [
    {
      "path": "/",
      "methods": ["GET"],
      "auth_required": false,
      "form_accepting": false
    },
    {
      "path": "/login",
      "methods": ["GET", "POST"],
      "auth_required": false,
      "form_accepting": true,
      "form_fields": ["email", "password"]
    },
    {
      "path": "/upload",
      "methods": ["POST"],
      "auth_required": true,
      "file_upload": true,
      "accepted_types": ["*/*"]
    }
  ],
  "capabilities": {
    "auth_endpoints": ["/login", "/signup"],
    "file_upload": ["/upload"],
    "api_routes": ["/api/users", "/api/items"],
    "form_routes": ["/login", "/signup", "/contact"],
    "serves_html_document": true
  },
  "discovery_completed": true,
  "discovery_duration_seconds": 24
}
```

This profile is the input to applicability resolution. Tests query the profile to determine if they apply.

## Predicate Functions

Named predicates live as Python functions in `predicates/`:

```python
# predicates/csrf.py
async def csrf_token_validated(probe_response, submission_profile):
    """Verify the response indicates CSRF protection."""
    # Implementation here
    return True or False
```

Predicates receive the probe response and submission profile as inputs. They return a boolean indicating whether the predicate matched. Predicates can be referenced by name from test definitions.

Adding new predicates requires PR review since they affect test interpretations across multiple tests.

## Test Authoring Workflow

New tests are added to the catalog through this process:

1. Author creates new YAML file in appropriate category directory
2. Author runs local validation: schema validation + three-way reference calibration (below)
3. Author opens PR against the catalog repository
4. PR review verifies: passes the **intent-independence litmus** (a test that fails it does not get a file), schema valid, scoring calibrated appropriately, predicate logic sound, oracle reliably distinguishes broken from N/A
5. PR merged to main triggers catalog version bump
6. Chapter platforms pull updated catalog at next sync

**Three-way reference calibration.** Reference submissions are curated apps in the catalog repository. Before a test merges, it must resolve correctly against all three: **slop_detected** on a known-vulnerable app, **clean** on a known-good app that has the real live surface, and **not_applicable** on an app that lacks the surface. A test whose oracle fires on the good app (false positive) or misses the vulnerable one (false negative) is not ready — that separation is the proof the oracle works.

## Scoring Integration

After runner completes, scoring integration follows:

1. Runner writes FuzzResult records per probe outcome (slop_detected / clean / not_applicable)
2. Scoring engine reads FuzzResult records for a submission
3. Sums the penalties of every probe that detected slop
4. Applies variant-group rules where applicable (each missed variant adds its slop)
5. Computes the final slop score for the submission
6. Generates result metadata (status, attack surface coverage, clean rate)
7. Submission is ready for composite ranking

The scoring engine is separate from the runner — runner produces structured outcomes, scoring engine interprets them into final scores.

---

*This document specifies the runner architecture. For what tests measure and the scoring philosophy behind them, see format_spec.md. For how results are persisted, see DATA_MODEL.md. For overall service relationships, see ARCHITECTURE.md.*
