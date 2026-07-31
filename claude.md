# HackLet League Platform — Claude Code Conventions

*Entry point for any Claude Code session working on hackletleague.com. This document covers project conventions, tech stack, and architectural principles. For the competitive format itself, see format_spec.md. For league governance, see LEAGUE_OPERATIONS.md. For schema details, see DATA_MODEL.md. For service relationships, see ARCHITECTURE.md.*

---

## Start here

**The docs describe more than the code implements, deliberately.** format_spec.md and the tier
operations documents specify the eventual format; the platform implements it in stages. A
document describing a mechanism is not evidence the mechanism exists.

Four things to know before you touch anything:

1. **Check the stage.** BUILD_ROADMAP.md's *Status & Deviations* block is the current truth.
   As of 2026-07-28: Stages 0-3 shipped, **Stage 4 (AI substrate) is active and unstarted**,
   Stage 5 (fuzz runner) is proceeding out of order as a standalone project in `fuzz-runner/`.
2. **Check the status marker.** Every section of every structural doc now carries one:
   **BUILT** (with a file:line citation), **DESIGNED**, **MIXED**, or **SUPERSEDED**. Timing
   blocks carry **ILLUSTRATIVE**. Absent a marker, assume nothing.
3. **Cite the code, not the doc.** Before claiming what the platform does, open the file and
   cite `path.py:line`. Design docs describe intent. This one did too, for a while: its
   structure tree listed six backend apps that never existed and a frontend `src/` directory
   that never existed.
4. **Two other sessions may be active.** `fuzz-runner/` and FUZZ_RUNNER_SPEC.md belong to the
   fuzzer session. `backend/` and `frontend/` are frequently held by the platform session.
   Check `git status` and recent commits before editing shared files.

Not-yet-decided questions are collected in DECISIONS_OWED.md. If a task needs one resolved,
ask rather than choosing — several of them look like small wording calls and are not.

---

## Project Identity

HackLet League is a competitive format for AI-assisted technical building. In one sentence: hackathon, but minutes instead of hours, with a cheering audience. Players spend 24 minutes building a web application using a sanctioned AI substrate, then defend their work through automated adversarial testing, judge inspection, and live cross-examination.

This repository implements hackletleague.com, the platform that coordinates league operations, manages chapters and users, runs the AI proxy, executes fuzz testing, and maintains rankings. The platform is event coordination and credentialing infrastructure, not a development environment. Players develop locally on chapter-operated workstations; the platform supplies the AI chat interface and event coordination.

## Brand vocabulary: `hacklet` vs `HackLet` (load-bearing)

Capitalization carries meaning — this is institutional vocabulary discipline. Apply it consistently across **all copy, all files, all surfaces** (current and future). Without the documented convention, the distinction drifts.

- **`hacklet`** (lowercase) — the **generic** noun: an app built quickly with AI assistance, OR a compressed hackathon-like event anyone can run. Use in slogans, generic descriptions, the dictionary entry, casual mentions, and example sentences.
- **`HackLet`** (CamelCase) — **HackLet League-sanctioned** events, formats, tournaments, or the league itself. Use for institutional references, formal event names, format names (HackLet Vibe, HackLet Unslop), and the organization-as-noun.

Correct usage:
- ✓ "the fuzz is what separates hacklets from slop" (generic principle)
- ✓ "Come attend a hacklet" (generic event)
- ✓ "build a hacklet in 24 minutes" (generic activity)
- ✓ "First HackLet coming soon" (formal league event)
- ✓ "HackLet League runs three formats" (the league)
- ✓ "HackLet Vibe is akin to..." (formal format name)
- ✓ "qualified for HackLet Vibe Sprint Regionals" (formal tournament)

## Tech Stack

**Installed and running** (verified against `backend/pyproject.toml` and
`frontend/package.json`):

- **Backend**: Django 5.x + Django REST Framework
- **Database**: PostgreSQL 16 in prod; SQLite locally (the dev box has no Docker/Postgres)
- **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind v4
- **Auth**: django-allauth **headless**, session-based, with Google OAuth via socialaccount
- **Permissions**: hand-rolled queryset scoping — see `backend/chapters/permissions.py`
- **Serving**: gunicorn (WSGI) behind Caddy, whitenoise for static
- **Email**: django-anymail with Resend
- **Deployment**: Docker Compose on a **home Proxmox VM** (Hetzner deferred until pilot dates lock)
- **CI/CD**: GitHub Actions — `backend`, `frontend`, then `deploy` on a self-hosted runner
- **Package Management**: uv (Python), pnpm (JavaScript)
- **Lint/test**: ruff, pytest + pytest-django + factory-boy, eslint

**Not installed — do not `import` these, they are planned, not present:**

- **Django Channels / WebSockets / Redis** — the round clock ships as **5-second polling**
  (`frontend/components/RoundLive.tsx:103`); `backend/hacklet/asgi.py` is plain Django ASGI.
  Real-time transport is unscheduled.
- **django-guardian** — never added. Object-level permissions are done by scoping querysets
  to the chapters a user manages. Follow the existing pattern; do not introduce guardian
  without a decision.
- **httpx** — not a dependency. The one outbound HTTP call in the codebase
  (`backend/newsletter/views.py`) uses `requests`, which arrives transitively rather than
  being declared. If you add an HTTP client, declare it.
- **OpenRouter / the AI proxy** — Stage 4, unstarted. No `ai_proxy` app, no endpoint, no key
  read anywhere. `OPENROUTER_API_KEY` appears in ARCHITECTURE.md's required-env list and is
  read by nothing.
- **mypy strict** — mypy is in dev deps but `pyproject.toml` has no `[tool.mypy]` section, so
  nothing enforces it. Treat the convention below as aspirational until configured.
- **prettier, vitest, playwright, TanStack Query, SWR, Zustand** — none are installed. The
  frontend has no test runner and no state library; server state is fetched in `lib/` helpers
  and held in component state.

Stack choices are deliberately boring. The format is novel; the implementation should not be. Django was chosen specifically to leverage existing developer expertise (SAPA-GP background), built-in admin interface for early operations, mature permissions framework, and security defaults appropriate for credentialing infrastructure.

## Architectural Principles

### Federated Platform from Day One

Chapters are first-class entities in the data model. Even at single-chapter MVP, the architecture treats chapters as parallel operational units rather than as a hardcoded concept. New chapters are data, not code changes.

### Server-Side Authority for All Game State

Timers, token budgets, fuzz budgets, scoring math, and all competitive state are computed and enforced server-side. Clients display state but cannot modify it. The frontend never holds authoritative game data. Any client-side enforcement of game rules is a security failure.

### Role × Scope Permissions

Permissions are scoped to chapter context. A user is not simply "a judge" — they are "a judge at Chapter X for Event Y."

**The shipped pattern is queryset scoping, not django-guardian** (which is not installed). See `backend/chapters/permissions.py` for `is_chapter_manager` and `managed_chapter_ids`, and `backend/rounds/views.py` for the standard shape: filter the queryset to what the user may touch, so an unauthorized lookup returns **404 rather than 403** and existence is never leaked. Follow that pattern. Introducing guardian is a decision, not a refactor.

### Single Web Application with Role-Gated Routes

The platform is one Django backend + one Next.js frontend. There are not separate applications for different portals. Player, judge, organizer, and public views are routes within the same application, gated by authentication and role.

### Workstation Autonomy on Anti-Cheating

The platform does not manage chapter workstations. Chapters operate their own RMM, firewall, and infrastructure to league standards. The platform verifies chapter compliance through documentation review and audit, not through direct control. Platform code should not assume access to chapter workstation infrastructure.

### Centralized AI Substrate

The league supplies one OpenRouter API key used for all chapters and events. This key lives in encrypted environment variables / secret management, never exposed to frontend. All AI calls flow through the Django backend proxy. Chapters never see or supply API keys.

### Audit Everything

For credentialing integrity, all significant operations are logged. Chapter status changes, score modifications, verification decisions, role assignments — all auditable with user attribution and timestamps. Use Django's built-in logging plus dedicated audit tables for compliance-sensitive operations.

**Status: aspirational.** No `AuditLog` model exists, and none of the operations above are recorded today, despite DATA_MODEL.md specifying the entity and ARCHITECTURE.md's security section describing the trail as if it runs. Treat this as the standard to build toward, not a description of current behaviour.

### Server-Side Validation, Always

Never trust client input. Validate all API inputs server-side. Frontend validation is for UX only, never for security or correctness. This applies to game rules, permissions, data constraints, and any business logic.

## Project Structure

Monorepo with backend and frontend as siblings. **This is the tree as it exists**, verified
2026-07-28. It is not the aspirational layout — an earlier version of this section listed six
backend apps that were never created (`scoring/`, `fuzz/`, `ai_proxy/`, `api/`, `audit/`,
`tests/`) and omitted three that exist, and put the frontend under a `src/` directory that has
never existed. If you are looking for a directory named below and it is missing, that is a bug
in this file, not in your checkout.

```
hacklet-league/
├── backend/                    # Django project
│   ├── hacklet/                # project package
│   │   ├── settings/           # split settings: base, dev, prod
│   │   ├── urls.py             # THE router — every route is registered here
│   │   ├── asgi.py             # plain Django ASGI (no Channels)
│   │   └── wsgi.py             # what gunicorn actually serves
│   ├── users/                  # custom email-based User (UUID pk, is_superadmin)
│   ├── chapters/               # Chapter, ChapterStaff, permissions.py, stats.py
│   ├── events/                 # Event, EventParticipant (players/judges/audience)
│   ├── rounds/                 # Round, Submission, Score
│   │   ├── services.py         #   phase profiles + server-authoritative clock
│   │   └── scoring.py          #   two-axis collapse + rank-sum composite
│   ├── rankings/               # Ranking + leaderboard aggregation (services.py)
│   ├── newsletter/             # Buttondown signup proxy (view only, no model)
│   ├── manage.py
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                   # Next.js project — NO src/ directory
│   ├── app/                    # App Router, routes are plain dirs (no route groups)
│   │   ├── page.tsx layout.tsx
│   │   ├── about/ contact/ scoring/ leaderboard/ profile/ dashboard/
│   │   ├── auth/               # login, signup, verify-email/[key]
│   │   ├── chapters/           # index, new, [slug], [slug]/edit, [slug]/staff
│   │   └── events/             # index, new, [chapter]/[event]/{-,edit,manage,rounds/[round]}
│   ├── components/             # RoundLive, JudgeConsole, RoundManager, RoundResults, ...
│   ├── lib/                    # api.ts (server), http.ts (browser), auth/events/rounds.ts
│   ├── package.json tsconfig.json eslint.config.mjs
│   └── Dockerfile
├── scripts/                    # deploy.sh, db-backup.sh, db-restore.sh
├── fuzz-runner/                # standalone grader — OWNED BY ANOTHER SESSION, do not edit
├── landing/                    # superseded static landing (Stage 0), kept but dead
├── docker-compose.yml  docker-compose.dev.yml  Caddyfile
└── .github/workflows/
```

Every Django app owns `models.py`, `serializers.py`, `views.py`, `admin.py`, `tests.py`, and
`migrations/`. There is **no central `api/` app** — DRF viewsets live in each app's `views.py`
and are registered on the one router in `hacklet/urls.py`. There is **no central `tests/`
directory** — tests are per-app `tests.py`. Cross-app dependencies should be minimal and
explicit.

**Not present, and named here so you do not go looking:** no `ai_proxy/` (Stage 4), no `fuzz/`
(Stage 5 — the runner is a separate project in `fuzz-runner/` and is not yet wired to the
platform), no `audit/` (no `AuditLog` model exists despite the principle below), no
`play/`, `judge/`, or `admin/` frontend portals.

There is no root `README.md`, though several documents link to one. `frontend/README.md`
exists and is the Next.js default.

## Code Conventions

### Python (Backend)

- **Formatter and linter**: ruff (replaces black, flake8, isort)
- **Type checking**: mypy with strict mode for new code
- **Style**: PEP 8, with ruff defaults
- **Docstrings**: Google style, required for public functions and classes
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants
- **Imports**: stdlib, third-party, local — separated by blank lines, alphabetized within groups
- **Async**: use Django's async ORM where it matters (websockets, AI proxy). Synchronous fine elsewhere.

### TypeScript (Frontend)

- **Formatter**: prettier with project defaults
- **Linter**: eslint with next.js and typescript configs
- **Style**: typescript strict mode, no `any` without justification
- **Components**: functional components with hooks, no class components
- **Naming**: PascalCase for components, camelCase for functions/variables, kebab-case for files

Two corrections to what this section used to claim. **Prettier is not installed** — eslint (`eslint-config-next`) is the only frontend tooling, and `pnpm lint` is the only check CI runs on the frontend besides `build`. And **no state library is installed**: not TanStack Query, not SWR, not Zustand. Server data is fetched through `lib/api.ts` (server components) or `lib/http.ts` (browser) and held in component state; polling lives in the component that needs it. Add a state library only if the need is real, and say so in the PR.

### Git Workflow

- Main branch is always deployable
- Feature branches off main, merged via PR
- PRs require passing CI
- Commit messages: imperative mood, lowercase subject, optional body
- Squash merge to keep main history clean

### Testing

- **Backend**: pytest + pytest-django + factory-boy. Unit tests for business logic, integration tests for API endpoints. Tests live in each app's `tests.py`. **Run them locally on SQLite via `uv` before every backend commit** — the dev box has no Docker or Postgres, and CI runs the same suite against Postgres.
- **Frontend**: **no test runner is installed.** vitest and playwright are aspirational; the only frontend CI check is `pnpm lint` plus the production build. Do not write frontend tests against a runner that is not there — add the runner first, in its own commit.
- **Coverage**: not a percentage target. Test what matters: scoring math, permissions, state transitions, and (when it exists) AI proxy budget enforcement.

## Common Pitfalls

These are mistakes Claude Code might make without warning. Watch for them.

### Never Client-Side Enforce Game Rules

Frontend may display token budget remaining, but the budget is enforced server-side. Any code that says "if budget exhausted, disable chat input" must have the server-side enforcement as primary; client-side is UX only. Same for timers, fuzz budgets, scoring, deployment validation.

### Never Expose OpenRouter Key to Frontend

**None of this exists yet — it is the Stage 4 design, stated here so it gets built correctly.** When the AI proxy lands, it is a Django endpoint: the frontend sends chat messages to `/api/ai/chat`, Django adds the API key and calls OpenRouter, and returns the response. The key never appears in frontend code, never in JavaScript, never in any client-accessible location. Today there is no `ai_proxy` app, no endpoint, and nothing reads `OPENROUTER_API_KEY`.

Two substrate rules to build against, both settled: the cutoff is **one server-side gate with two conditions** — budget exhausted, or **the pitch-preparation window has closed** — returning **403, not 429**, with a player-facing body, cutting in-flight streams rather than only refusing new requests. And the budget is **one pool per player per round**, shared across build and pitch prep.

The gate deliberately does **not** fire at build end. The substrate stays live through pitch preparation, because the submission is captured and deployed at the buzzer and the fuzzer grades the deployed copy — so post-freeze inference cannot reach the graded artifact. The freeze is enforced by where grading reads from, not by switching the model off. See format_spec.md §5.5.

### Always Scope Permissions to Chapter Context

A judge has permissions at specific chapters for specific events, not globally. When checking permissions, include the chapter context. Use the queryset-scoping helpers in `backend/chapters/permissions.py` (django-guardian is **not** installed — see Role × Scope Permissions above). Don't fall back to global role checks for chapter-scoped operations.

### Sessions, Not JWTs

We use session-based auth via django-allauth. Don't introduce JWT for any reason. Sessions are simpler, more secure, easier to invalidate, and sufficient for our use case.

### Use Django Admin for Staff Tooling

For superadmin operations (chapter approval, user management, fuzz catalog editing), use Django admin rather than building custom UI. This dramatically accelerates MVP and provides battle-tested CRUD operations. Custom UI for chapter admins and players is needed; custom UI for superadmins is mostly unnecessary.

### Treat Chapters as First-Class Always

Even when there's only one chapter, write all chapter-related logic as if there could be many. Don't hardcode chapter assumptions. Pass chapter context to all relevant operations.

### Migrations Are Forward-Only

Use Django migrations. Don't manually modify the database schema. Don't delete migrations after they've been applied. Squash migrations only when intentional and reviewed.

### Audit-Sensitive Operations Use Audit Tables

For operations that affect credentialing integrity (score changes, verification decisions, chapter tier changes), write to dedicated audit tables in addition to standard logging. These tables are append-only with user attribution.

## Document Map

- **format_spec.md** — What hacklet league is as a competitive format. Tier-agnostic format definition: two-axis taxonomy, scoring axes, substrate principles, two-principle thesis. Read this to understand what the platform is supporting.
- **LEAGUE_OPERATIONS.md** — How the league operates as a federated institution. Chapters, roles, tier system overview, freedom-integrity tradeoff, verification, governance.
- **TIER_A_OPERATIONS.md** — Tier A operational template. Credentialing-grade tier with full 135-min round profile, broadcast architecture, multi-day tournament template (snake-draft, alternates, two-leaderboard, tag credentialing), anti-cheating enforcement.
- **TIER_B_OPERATIONS.md** — Tier B operational template. Middle tier with league-hosted substrate + honor-system enforcement. 135-min round profile shared with Tier A but lighter operational burden.
- **TIER_C_OPERATIONS.md** — Tier C operational template. Training tier and Minimum Viable Round (MVR) floor. BYOD substrate, no enforced budgets, three operational profiles (the 60-min MVR with PITCH.md + LLM judging; Tier C Extended with live pitch/cross-ex + human judges; multi-round MVR-days). PITCH.md as canonical written communication artifact.
- **DATA_MODEL.md** — Database schema. The entities, relationships, constraints. Required reading before writing models or queries. Nine of its sixteen entities exist; each section says which.
- **ARCHITECTURE.md** — Service relationships, request flows, deployment topology. The most over-asserted document in the set; read its status markers, not just its prose.
- **BUILD_ROADMAP.md** — **Read this first to find out what stage we are in.** Stage gating, in-scope/out-of-scope per stage, and the Status & Deviations block that says what actually shipped. It is the reference for tense discipline; the other documents are being brought up to it.
- **CHANGELOG.md** — What changed and why, by stage. The decision record for anything that looks arbitrary.
- **IDEAS_FOR_LATER.md** — The parking lot. Per BUILD_ROADMAP Rule 2, out-of-scope ideas go here instead of getting built.
- **DOC_STATE.md** — Audit of every document's status (BUILT / DESIGNED / MEASURED / ASSUMED / SUPERSEDED) plus every known cross-document contradiction, `C-01`…`C-22`, each cited to file and line.
- **DECISIONS_OWED.md** — The 23 open calls that need Ian, with options and costs. **If a task requires resolving one of these, stop and ask rather than picking.**
- **FUZZ_RUNNER_SPEC.md** and **fuzz-runner/** — owned by a separate session. Do not edit either. The two copies of the spec have already drifted.
- **DEPLOY.md** — Deployment, backups, and the host migration runbook.
- **AGENTS.md** — Agent-facing notes.

There is no root `README.md`, though this file and others have linked to one.

## Naming and Copy Conventions

### Capitalization

The word "hacklet" / "HackLet" uses different capitalization for different meanings. The distinction is load-bearing institutional vocabulary discipline. Apply consistently across all current and future copy on the site, in documentation, and in public-facing communications.

**hacklet** (lowercase) = generic noun. An app built quickly with AI assistance, OR a compressed hackathon-like event anyone can run. Used in slogans, generic descriptions, dictionary entries, casual mentions, example sentences.

**HackLet** (CamelCase) = HackLet League-sanctioned events, formats, tournaments, or the league itself. Used for institutional references, formal event names, format names (HackLet Vibe, HackLet Unslop), and the organization-as-noun.

Correct usage examples:
- "the fuzz is what separates hacklets from slop" (generic principle)
- "Come attend a hacklet" (generic event)
- "build a hacklet in 24 minutes" (generic activity)
- "First HackLet coming soon" (formal league event)
- "HackLet League runs three formats" (the league)
- "HackLet Vibe is akin to a traditional hackathon" (formal format name)
- "qualified for HackLet Vibe Sprint Regionals" (formal tournament)

### Copy Voice (Public-Facing Materials)

Public-facing copy (landing page, sponsor materials, recruitment content, social posts, conference talks) should match founder voice rather than reading as marketing copy. Specifically:

**Avoid these patterns** that mark text as AI-generated and damage founder credibility:
- Em dashes when commas, periods, or parentheses would work
- "-grade" suffixes used for fake precision (exception: "credentialing-grade" is project canonical)
- "substantively" as compulsive hedge word
- "adversarial" / "robust" / "calibrated" / "comprehensive" / "thoughtful" / "nuanced" as default qualifiers
- Triple-clause rhythms ("not X, not Y, but Z" as a tic)
- "Worth being explicit about" / "Worth flagging" as transition hedges
- "It's worth noting that" / "That said," / "Moreover," / "Furthermore," as connective tissue
- "leverage" / "streamline" / "holistic" / "orchestrate" / "facilitate" / "utilize" / "comprises" / "encompasses" / "empower" as verb choices
- Bolded sentence fragments mid-paragraph signaling "look this is important"
- "At its core" / "In essence" / "Fundamentally" / "Essentially" as sentence openers

**Prefer instead**:
- Direct declarative sentences
- Conjunctions like "and" / "but" / "so" instead of em dashes
- Concrete nouns and verbs (use, run, help, write)
- Honest tone over marketing register

Canonical doc voice (format_spec, LEAGUE_OPERATIONS, tier ops) is more formal than public-facing copy and may use em dashes sparingly where they serve clarity. The avoid-list above applies most strictly to founder voice and external communications.

### Score vocabulary (Slop Score)

The fuzz catalog produces a **Slop Score**: deduction-only, range [0, +∞), **lower is better, 0 is perfect** (golf-style — you accumulate slop, you never earn points). Use "slop score" in all copy, UI labels, and docs for the measurement.

- The score is **Slop Score** — not "Resilience Score" or "Fuzz Score" (both retired names). But **"fuzz catalog" and "fuzz runner" keep the "fuzz" name**: fuzzing is the *method*, slop is what it *measures*.
- **"Most Resilient"** stays as the award title — it credentials the *quality* (aspirational), while the slop score is the *measurement* (descriptive). Golf names a "Champion," not a "Lowest Score Holder."
- **"resilient" / "resilience"** as an adjective or property ("build a resilient app," "resilience is what the catalog measures") is fine. Only the *score name* changed.
- Direction matters: lower slop is better. Never write "high slop score" as praise.

## What This Document Is Not

This document is project conventions only. It does not:

- Describe the competitive format (that's format_spec.md)
- Define league governance (that's LEAGUE_OPERATIONS.md)
- Specify the database schema (that's DATA_MODEL.md)
- Detail service interactions (that's ARCHITECTURE.md)
- Document specific API endpoints (those are documented in code — the router in `backend/hacklet/urls.py` is the index)
- Cover deployment procedures (those are in **DEPLOY.md**, which exists; this line previously pointed at a `DEPLOYMENT.md` that was never written)

Read the appropriate document for the concern you're addressing. This document is the entry point that points to the others.


## Style Guide

### Scope

This guide governs prose written for readers outside the project. Applications, pitches, outreach, landing and marketing copy, anything on the public site.

It does not govern technical writing inside this repo. Code comments, specs, roadmaps, the CHANGELOG and the documents listed above keep their existing conventions, which include em dashes and established domain terms such as deduction-only, intent-independent, best-of-N and the tier operations vocabulary. Those terms are load bearing and renaming them would cost more than the consistency is worth. Where this guide and a surrounding file disagree, the file wins.

The reason for the split is that the two audiences want different things. An outside reader is deciding whether to trust the work, so inflation reads as a warning sign. A reader inside the repo already trusts it and wants precision, so a fixed vocabulary earns its keep.

### Register

Peer, not student. Direct, specific, and confident without inflation. Professional but human. I would rather sound like a sharp practitioner talking to another practitioner than like a candidate performing enthusiasm.

### Hard bans (never use these)

Em dashes. Use a comma, a period, or restructure.
Semicolons in prose.
Hyphenated compounds unless the hyphen is established (co-organized and proper nouns are fine; full-stack, dual-axis, red-team, prompt-injection are not, write them open).
The words: genuinely, honestly, operational, structural, framing, delve, leverage (as a verb), spearheaded, passionate, results-driven, synergy, seamless.
Exclamation points, unless clearly intentional.
Filler openers: "I am writing to apply for," "As a highly motivated," "I am excited to."

### Preferences

Full sentences with real subjects. No dropped fragments as bullets when a sentence reads better.
Specificity over polish. Concrete true numbers and named tools beat smooth abstraction. "Scraped 70K records" not "worked with large datasets." "Guided 150+ students" not "supported learners."
Plain strong verbs: built, shipped, designed, ran, found, fixed, presented. Not: utilized, spearheaded, drove, championed.
Vary sentence length naturally. Do not produce three tricolons in a row or a wall of identical rhythm; that uniform cadence is itself an AI tell.


### AI slop patterns to avoid

Generic value claims with no evidence ("proven track record of delivering results").
Buzzword stacking ("dynamic, results-driven professional with a passion for innovation").
Over-hedged or over-smooth prose that could describe anyone.
Repeated sentence openers and mechanical parallelism.


### Honesty

Specificity is the differentiation, not decoration. Every concrete detail must be true and traceable. Never invent a metric, a skill, a title, or an outcome to make a sentence stronger. A true smaller claim always beats an impressive false one.
