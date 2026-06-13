# HackLet League — Fuzz Runner Specification

*Architecture and conventions for the fuzz runner that executes the test catalog against submissions. Covers test format, runner phases, execution model, and catalog organization. Distinct from format_spec.md (what tests measure) and DATA_MODEL.md (how results are stored).*

---

## Overview

The fuzz runner is responsible for executing standardized tests against player submissions. It runs in two modes:

- **Local runner**: lightweight version on chapter workstations, runs public pool tests against local deployments during build phase. Results are informational.
- **Central runner**: full version on league infrastructure, runs both pools (public and hidden) against deployed submissions at code freeze. Results are authoritative.

Both modes share the same test format and execution semantics. They differ in what catalog content they have access to and where results are persisted.

## Test Definition Format

Each test is defined as a YAML file with a standardized schema. The schema is validated via Pydantic models in the runner codebase.

### Schema

```yaml
id: <unique-identifier>           # e.g., sec-sqli-001
bundle: <security | qa>
category: <category-name>          # human-readable category
subcategory: <subcategory>         # optional, for variant grouping
difficulty_tier: <1 | 2 | 3 | 4 | 5>
pool: <public | hidden>
intent_dependence: <universal | intent_sensitive>
attack_type: <adversarial | non_adversarial>
description: <text description of what the test does>
points_defended: <positive integer>
points_gracefully_handled: <positive integer or null>  # only if non-adversarial
points_broken: <negative integer>
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

assertion:
  defended_if:
    - <assertion_condition>
  gracefully_handled_if:           # only if non-adversarial
    - <assertion_condition>
  broken_if:
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

Assertions are expressed as structured conditions, with common patterns:

**Response status conditions:**
- `response_status_in: [<list_of_codes>]`
- `response_status_equals: <code>`
- `response_status_500_with_db_error`

**Response content conditions:**
- `response_does_not_contain: <pattern>`
- `response_contains_unauthorized_records`
- `response_contains_credentials`
- `response_does_not_leak_db_error`
- `response_does_not_leak_stack_trace`

**Timing conditions:**
- `response_received_within: <duration>`
- `response_received_after: <duration>`

**Behavioral conditions:**
- `upload_rejected: true`
- `upload_succeeds_and_executes: true`
- `auth_bypassed: true`
- `feature_existed_before_attack: true`

**Complex conditions** that require code can reference named predicates:

```yaml
assertion:
  defended_if:
    - predicate: csrf_token_validated
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
7. Produce a submission profile structure

The discovery phase runs for a fixed time budget (e.g., 30 seconds) or until exhaustion, whichever comes first.

### Phase 2: Applicability Resolution

For each test in the catalog:

1. Check whether all `applicability.requires` conditions are met against the submission profile
2. If yes, mark the test as applicable
3. If intent-sensitive, additionally flag for tester judge review (central runner only)
4. Universal tests run automatically; intent-sensitive tests run with placeholder pending judge resolution

The result is a list of applicable tests and their initial automated applicability status.

### Phase 3: Execution

Applicable tests execute in parallel up to a concurrency limit (default: 20 concurrent tests per submission):

1. For each test, construct the HTTP request(s) per the probe specification
2. Send requests with configured timeout
3. Collect responses
4. Evaluate assertion conditions against responses
5. Determine outcome: defended / gracefully_handled / not_applicable / broken
6. Record outcome, response data, and timing

Some tests may require sequential execution (e.g., session-dependent tests). The test definition can declare `requires_sequential: true` to opt out of parallel execution.

### Phase 4: Result Aggregation

After all tests complete:

1. Tally outcomes per test
2. Compute total fuzz score from per-test point values
3. Compute attack surface coverage (narrow / moderate / broad) from applicable count
4. Compute defense rate (defended / applicable)
5. Generate per-category summaries

### Phase 5: Reporting

Results are persisted via different paths depending on runner mode:

**Local runner** (during build):
- Records to PlayerFuzzInvocation table
- Streams results to player portal for real-time display
- Updates broadcast leaderboard if event is being broadcast

**Central runner** (at code freeze):
- Records to FuzzResult table (authoritative)
- Notifies tester judge portal for override review
- Triggers scoring engine when all judges complete reviews

## Execution Architecture

### Local Runner

Runs as a Python service on each workstation, started by RMM at event startup.

- Listens on local port (e.g., `127.0.0.1:8888`) for trigger requests from league portal browser tab
- Has access to public pool test catalog (deployed via RMM with workstation image)
- Hits player's local deployment at known port (e.g., `127.0.0.1:3000`)
- Reports results back to league via outbound HTTPS

The local runner does not contain hidden pool tests. Hidden pool YAML files are never present on workstations.

### Central Runner

Runs as a containerized service on league infrastructure.

- Receives submission code via git push at code freeze
- Deploys submission to ephemeral Docker container
- Container exposes submission's port to runner
- Runner executes full catalog (both pools) against deployed container
- After completion, container is destroyed
- Results persisted to FuzzResult table

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
    "form_routes": ["/login", "/signup", "/contact"]
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
2. Author runs local validation: schema validation + sample-run against reference submissions
3. Author opens PR against the catalog repository
4. PR review verifies: test schema valid, scoring calibrated appropriately, predicate logic sound
5. PR merged to main triggers catalog version bump
6. Chapter platforms pull updated catalog at next sync

Reference submissions (curated examples that test should and shouldn't catch) are part of the catalog repository for validation.

## Scoring Integration

After runner completes, scoring integration follows:

1. Runner writes FuzzResult records per test outcome
2. Scoring engine reads FuzzResult records for a submission
3. Sums points per test outcome
4. Applies variant-group scoring rules where applicable
5. Computes final fuzz score for submission
6. Generates result metadata (status, attack surface coverage, defense rate)
7. Submission is ready for composite ranking

The scoring engine is separate from the runner — runner produces structured outcomes, scoring engine interprets them into final scores.

---

*This document specifies the runner architecture. For what tests measure and the scoring philosophy behind them, see format_spec.md. For how results are persisted, see DATA_MODEL.md. For overall service relationships, see ARCHITECTURE.md.*
