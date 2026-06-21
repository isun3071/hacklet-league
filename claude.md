# HackLet League Platform — Claude Code Conventions

*Entry point for any Claude Code session working on hackletleague.com. This document covers project conventions, tech stack, and architectural principles. For the competitive format itself, see format_spec.md. For league governance, see LEAGUE_OPERATIONS.md. For schema details, see DATA_MODEL.md. For service relationships, see ARCHITECTURE.md.*

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
- ✓ "HackLet League runs two formats" (the league)
- ✓ "HackLet Vibe is akin to..." (formal format name)
- ✓ "qualified for HackLet Vibe Sprint Regionals" (formal tournament)

## Tech Stack

- **Backend**: Django 5.x + Django REST Framework + Django Channels
- **Database**: PostgreSQL 16
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **Auth**: Django built-in auth + django-allauth (email, optional OAuth providers)
- **Permissions**: django-guardian for object-level (chapter-scoped) permissions
- **Realtime**: Django Channels for WebSocket connections
- **AI Proxy**: httpx-based proxy to OpenRouter (DeepSeek V4 Flash for season 1)
- **Deployment**: Docker Compose on Hetzner VPS
- **CI/CD**: GitHub Actions
- **Package Management**: uv (Python), pnpm (JavaScript)

Stack choices are deliberately boring. The format is novel; the implementation should not be. Django was chosen specifically to leverage existing developer expertise (SAPA-GP background), built-in admin interface for early operations, mature permissions framework, and security defaults appropriate for credentialing infrastructure.

## Architectural Principles

### Federated Platform from Day One

Chapters are first-class entities in the data model. Even at single-chapter MVP, the architecture treats chapters as parallel operational units rather than as a hardcoded concept. New chapters are data, not code changes.

### Server-Side Authority for All Game State

Timers, token budgets, fuzz budgets, scoring math, and all competitive state are computed and enforced server-side. Clients display state but cannot modify it. The frontend never holds authoritative game data. Any client-side enforcement of game rules is a security failure.

### Role × Scope Permissions

Permissions are scoped to chapter context. A user is not simply "a judge" — they are "a judge at Chapter X for Event Y." Use django-guardian for object-level permissions where chapter scoping matters. Standard role-based permissions for global concerns.

### Single Web Application with Role-Gated Routes

The platform is one Django backend + one Next.js frontend. There are not separate applications for different portals. Player, judge, organizer, and public views are routes within the same application, gated by authentication and role.

### Workstation Autonomy on Anti-Cheating

The platform does not manage chapter workstations. Chapters operate their own RMM, firewall, and infrastructure to league standards. The platform verifies chapter compliance through documentation review and audit, not through direct control. Platform code should not assume access to chapter workstation infrastructure.

### Centralized AI Substrate

The league supplies one OpenRouter API key used for all chapters and events. This key lives in encrypted environment variables / secret management, never exposed to frontend. All AI calls flow through the Django backend proxy. Chapters never see or supply API keys.

### Audit Everything

For credentialing integrity, all significant operations are logged. Chapter status changes, score modifications, verification decisions, role assignments — all auditable with user attribution and timestamps. Use Django's built-in logging plus dedicated audit tables for compliance-sensitive operations.

### Server-Side Validation, Always

Never trust client input. Validate all API inputs server-side. Frontend validation is for UX only, never for security or correctness. This applies to game rules, permissions, data constraints, and any business logic.

## Project Structure

Monorepo with backend and frontend as siblings:

```
hacklet-league/
├── backend/                    # Django project
│   ├── hacklet/                # Django project package
│   │   ├── settings/           # Split settings (base, dev, prod)
│   │   ├── urls.py
│   │   └── asgi.py             # Channels-aware
│   ├── chapters/               # Chapter management app
│   ├── events/                 # Event and round management
│   ├── users/                  # User accounts, profiles, memberships
│   ├── scoring/                # Scoring engine, rankings
│   ├── fuzz/                   # Fuzz catalog, fuzz runner integration
│   ├── ai_proxy/               # OpenRouter integration
│   ├── api/                    # DRF viewsets and serializers
│   ├── audit/                  # Audit logging
│   ├── tests/
│   ├── manage.py
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                   # Next.js project
│   ├── src/
│   │   ├── app/                # App router pages
│   │   │   ├── (public)/       # Public routes
│   │   │   ├── (auth)/         # Auth flows
│   │   │   ├── chapters/       # Chapter pages
│   │   │   ├── play/           # Player portal
│   │   │   ├── judge/          # Judge portal
│   │   │   └── admin/          # Organizer/superadmin
│   │   ├── components/
│   │   ├── lib/
│   │   └── styles/
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── .github/workflows/
├── claude.md                   # This document
├── format_spec.md              # The competitive format (tier-agnostic)
├── LEAGUE_OPERATIONS.md        # League governance + tier system overview
├── TIER_A_OPERATIONS.md        # Tier A operational template (credentialing-grade)
├── TIER_B_OPERATIONS.md        # Tier B operational template (middle tier)
├── TIER_C_OPERATIONS.md        # Tier C operational template (MVR / Extended / multi-round profiles)
├── DATA_MODEL.md               # Schema details
├── ARCHITECTURE.md             # Service relationships
└── README.md
```

Django apps are organized by domain concern. Each app owns its models, migrations, business logic, and tests. Cross-app dependencies should be minimal and explicit.

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
- **State**: server state via TanStack Query or SWR, client state via React Context or Zustand for complex cases
- **Naming**: PascalCase for components, camelCase for functions/variables, kebab-case for files

### Git Workflow

- Main branch is always deployable
- Feature branches off main, merged via PR
- PRs require passing CI
- Commit messages: imperative mood, lowercase subject, optional body
- Squash merge to keep main history clean

### Testing

- **Backend**: pytest, with django integration. Unit tests for business logic, integration tests for API endpoints, factory_boy for test data.
- **Frontend**: vitest for unit tests, playwright for end-to-end on critical flows.
- **Coverage**: not a percentage target. Test what matters: scoring math, permissions, state transitions, AI proxy budget enforcement.

## Common Pitfalls

These are mistakes Claude Code might make without warning. Watch for them.

### Never Client-Side Enforce Game Rules

Frontend may display token budget remaining, but the budget is enforced server-side. Any code that says "if budget exhausted, disable chat input" must have the server-side enforcement as primary; client-side is UX only. Same for timers, fuzz budgets, scoring, deployment validation.

### Never Expose OpenRouter Key to Frontend

The AI proxy is a Django endpoint. Frontend sends chat messages to `/api/ai/chat`, Django adds the API key and calls OpenRouter, returns response. The key never appears in frontend code, never in JavaScript, never in any client-accessible location.

### Always Scope Permissions to Chapter Context

A judge has permissions at specific chapters for specific events, not globally. When checking permissions, include the chapter context. django-guardian handles this naturally; use it. Don't fall back to global role checks for chapter-scoped operations.

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
- **DATA_MODEL.md** — Database schema. The entities, relationships, constraints. Required reading before writing models or queries.
- **ARCHITECTURE.md** — Service relationships, request flows, deployment topology.
- **README.md** — Getting started for developers.

## What This Document Is Not

This document is project conventions only. It does not:

- Describe the competitive format (that's format_spec.md)
- Define league governance (that's LEAGUE_OPERATIONS.md)
- Specify the database schema (that's DATA_MODEL.md)
- Detail service interactions (that's ARCHITECTURE.md)
- Document specific API endpoints (those are documented in code)
- Cover deployment procedures (those are in DEPLOYMENT.md when written)

Read the appropriate document for the concern you're addressing. This document is the entry point that points to the others.
