# HackLet League — Build Roadmap

*Staged build plan for hackletleague.com. Designed for scope discipline — each stage has explicit in-scope and out-of-scope items. Stages must be shipped sequentially; no stage begins until the previous one is complete and deployed.*

*This document is for both the human developer (Ian) and Claude Code. Both should reference this to determine what work is appropriate for the current stage. When in doubt about whether a feature belongs in the current stage, the answer is no.*

---

## The Scope Discipline Rules

These rules apply to every stage. Both human and AI assistants should enforce them.

**Rule 1: Ship the current stage before starting the next.** No half-built features bleeding into future stages. Each stage gets finished and deployed before the next begins. If the current stage isn't shippable, the next stage doesn't exist.

**Rule 2: Track scope creep externally.** When the urge to add features outside current stage scope appears, add them to `IDEAS_FOR_LATER.md`. Do not build them. The file is where good ideas wait their turn.

**Rule 3: Weekly progress check.** Every week, verify that something shipped. If nothing shipped, either constrain scope more tightly or actually code instead of planning.

**Rule 4: When in doubt, defer.** If unsure whether something is in scope, it isn't. Err toward simpler. Adding later is always possible; removing later is hard.

**Rule 5: Deploy frequently within stages.** Don't save up a month of work for one deploy. Ship small increments every 1-2 days within a stage. Small deploys mean small problems if things break.

**Rule 6: Imperfect is better than unshipped.** Rough styling that ships beats perfect styling that takes twice as long. Polish later. Ship now.

**Rule 7: The wishlist is not the spec.** format_spec.md describes the eventual format, not what's in stage N. The platform supports the full format eventually; the platform implements specific stages over time.

---

## Validation Runs Parallel to Building

The staged build below sequences *engineering* work. It does not imply that community-building, player recruitment, and format validation wait until the platform is done. These are concurrent tracks, not sequential phases.

From Stage 1 onward, parallel validation proceeds: talking to potential players, building an email list, mentioning hacklet in conversations, and — once Stage 3 infrastructure exists — running an informal concept demo (e.g., at a UPE meeting). The first real pilot is planned for fall 2026 after Stages 4–5, with the UPE BU chapter as the natural pilot community.

This is a deliberate sequencing choice — production rigor from day one, in the CTWC mold — rather than lean-startup MVP sequencing. The reasoning: arrive at the pilot with real infrastructure that demonstrates what hacklet actually is, rather than a weak proxy. The risk this trades against (building before validating demand) is mitigated by running validation activities in parallel rather than deferring them to the end. This sequencing decision is settled; revisit only if the parallel validation track surfaces evidence that the format itself doesn't hold.

---

## Status & Deviations (as of 2026-06-16)

- **Stage 1 in progress** — the platform (Django + DRF + Postgres + Next.js behind Caddy) runs on the home Proxmox VM and is **live on the public domain**, https://hackletleague.com, over HTTPS with production settings (DEBUG off, secure cookies, HSTS). It is **public (reachable) but not publicized** — no announcement or marketing; the domain simply resolves and serves while the platform is built and tested. (This supersedes the earlier "stealth / LAN-only until launch" plan — *public* and *publicized* are treated as separate steps.)
- **Hosting:** still the home VM; Hetzner remains the planned production host later (clean x86→x86 move via the portable Docker Compose repo).
- **Timeline:** the 4–6 week/stage estimates below assume ~10–15 h/week part-time *without* AI. With AI-assisted development at 30–40 h/week they compress to days — treat the week figures as loose upper bounds, not targets. Caveat: not everything compresses (Stage 5 fuzz-runner complexity, real-world testing, the one-week-stable gate, and all *non-code* operational work — venues, judges, hardware — run on their own clocks).

---

## Stage 0: Landing Page

**Goal: Claim the territory immediately with deployed presence at hackletleague.com.**

### In Scope

- One static landing page with the elevator pitch
- Brief about section explaining what HackLet League is
- Email signup using a third-party service (Buttondown or ConvertKit free tier — no backend required)
- Deployed via Cloudflare Pages or Vercel free tier
- DNS configured at Porkbun pointing to hosting
- Basic styling that looks clean and professional

### Out of Scope

- Any Django backend code
- Any database
- Any authentication
- Any styling framework that will be committed to long-term
- Any actual platform features
- Mobile app considerations
- Analytics integration (defer)
- SEO optimization beyond basic meta tags

### Success Criteria

Anyone can visit hackletleague.com and see a real landing page that explains what HackLet League is. The email signup form works. SSL is configured. The page loads quickly.

### Estimated Time

One focused afternoon (3-4 hours).

### Why This First

- Claims the domain territory immediately (no more dead-looking parked page)
- Teaches the deployment workflow with zero stakes
- Provides something to share when discussing the project
- Tests the developer/AI collaboration on a low-risk artifact

---

## Stage 1: Foundation

**Goal: Deployed platform with authentication and basic chapter creation.**

### In Scope

- Django project initialized with proper structure per claude.md
- PostgreSQL database with initial schema per DATA_MODEL.md (User, Chapter, ChapterMembership entities at minimum)
- User signup, login, logout, password reset via django-allauth
- Email verification flow
- User profile page with basic editing
- Chapter creation form (anyone authenticated can submit)
- Chapter approval interface via Django admin (superadmin approves)
- Chapter pages showing name, description, mode, tier (read-only for public)
- Public chapter directory listing all chapters
- Responsive landing page integrated with auth flow (replaces stage 0 static page)
- Next.js frontend for public site + auth pages
- Deployed to Hetzner VPS via Docker Compose
- CI/CD via GitHub Actions running tests on PR and deploying on merge to main
- Basic monitoring (uptime check at minimum)

### Out of Scope

- Events of any kind (Stage 2)
- Player or judge portals (Stage 3+)
- AI integration (Stage 4+)
- Fuzz runner (Stage 5+)
- Styling beyond clean and functional (use Tailwind defaults + shadcn/ui components)
- Custom admin UI for superadmin work (use Django admin)
- Mobile apps
- Chapter verification workflow beyond manual approval
- Chapter tier system enforcement (store the field, allow setting it, don't act on it yet)
- Federation features beyond chapter existence
- Real-time features (WebSockets, SSE) — not needed yet
- Object storage integration
- Email notifications beyond auth flows

### Success Criteria

- A new user can visit hackletleague.com, sign up, verify email, log in
- A logged-in user can apply for chapter creation through a form
- Superadmin (Ian) can review and approve the chapter in Django admin
- Approved chapter appears in the public chapter directory
- Chapter has its own page accessible by URL
- All of this works reliably in production

### Estimated Time

4-6 weeks of part-time work (10-15 hours/week).

### Why This Order

Foundation must exist before anything else. Auth, chapters, and users are the load-bearing entities that every subsequent stage depends on. Getting these right and well-tested is non-negotiable before building on top.

---

## Stage 2: Events Without Competition

**Goal: Platform supports creating and viewing events, but no actual rounds run yet.**

### In Scope

- Event entity per DATA_MODEL.md (without round mechanics yet)
- Event creation by chapter admins (UI in chapter admin area)
- Event scheduling: start time, end time, tier, player tier restriction
- Player and judge invitation flow (chapter admin invites users by email)
- Invitation acceptance flow (invitees see pending invitations on dashboard)
- Event public pages showing schedule and participants
- Judge assignment within events (which judges, what specialization role)
- Event status lifecycle: scheduled, registration open, registration closed, in progress (placeholder), completed
- Chapter member management UI (chapter admins can view members, change roles)
- ChapterMembership entity fully implemented with roles
- Basic role permissions enforced (chapter admins can only manage their chapter)

### Out of Scope

- Actual round execution
- Player workstation interaction
- AI integration
- Fuzz runner
- Scoring
- Live broadcast
- Real-time event updates (still no WebSockets needed)
- Email notifications beyond invitations
- Public event registration (chapter admin must explicitly invite players)
- Multi-round events (single round per event initially, multiple rounds is Stage 3)

### Success Criteria

- A chapter admin can create an event with full scheduling info
- The chapter admin can invite players and judges by email
- Invitees see and can accept invitations
- The event has a real public page showing participants and schedule
- Event status can transition through scheduled → registration open → registration closed
- "In progress" and "completed" statuses exist but don't yet involve real round execution

### Estimated Time

4-6 weeks of part-time work.

### Why This Order

Events are the next layer of structure built on chapters. Stage 2 establishes the *organizational structure* of events before tackling the harder problem of running actual rounds.

---

## Stage 3: Round Mechanics Without AI

**Goal: Rounds can run with timer and code submission, but no AI substrate yet.**

### In Scope

- Round entity per DATA_MODEL.md (multiple rounds per event now supported)
- Round state machine: scheduled, opening, build, evaluation, pitching, deliberation, awards, completed
- Server-authoritative timer infrastructure with WebSocket updates (now we need real-time)
- Player check-in flow for rounds they're enrolled in
- Code submission collection at code freeze (manual git push initially — chapter admin provides instructions)
- Submission entity per DATA_MODEL.md
- Basic judge interface for manual scoring (no fuzz integration yet — judges score everything by hand)
- Score entity per DATA_MODEL.md
- Basic score recording and composite calculation per scoring math in format_spec.md
- Ranking entity per DATA_MODEL.md (computed after rounds complete)
- Public round results pages
- Basic leaderboards (per-chapter, all-time)

### Out of Scope

- AI substrate integration
- Fuzz runner
- Automatic code freeze enforcement on workstations (manual for now)
- Workstation kiosk mode
- Broadcast infrastructure
- Audience voting (People's Hacklet) — deferred until broadcast features
- PlayerFuzzInvocation tracking (no fuzz to invoke yet)
- Verification application flow (still using manual chapter approval)

### Success Criteria

- A chapter can create an event with one round, schedule it, and run it
- Players can check in, the round opens, timer counts down through phases
- At code freeze, players manually submit code via git or zip upload
- Judges score submissions through web interface
- Scoring engine computes composite scores and announces winners
- Results appear on event page and contribute to rankings
- This is a *real but manual* hacklet round — no automation of code execution or fuzzing

### Estimated Time

4-6 weeks of part-time work.

### Why This Order

The format's central mechanic (round execution) needs to exist before AI integration adds value. Getting the round state machine, timer, and scoring math right with manual inputs lets us validate the format before adding the complexity of AI proxy and fuzz runner.

---

## Stage 4: AI Substrate

**Goal: Players can use AI chat during build phase, with token budget enforcement.**

### In Scope

- OpenRouter integration in Django (centralized API key, encrypted)
- AI chat interface in player portal (created in this stage)
- Player portal as new route in Next.js frontend
- Token counting per player per round (input + output, server-side)
- Token budget enforcement with hard cap, truncation, and rollback
- Streaming responses from OpenRouter to player via WebSocket
- Prompt history per player per round
- Comprehensive audit log of all AI interactions
- Updated round mechanics so build phase actually involves AI substrate
- Deepseek V4 Flash as the season 1 model (configurable via env var)
- Per-event monthly token limits with anomaly detection
- Emergency shutoff capability for runaway usage

### Out of Scope

- Fuzz runner (Stage 5)
- Local fuzz capability on workstations
- Broadcast features beyond basic
- Player workstation hardening
- Multi-model support beyond the single configured model
- Model rotation between seasons
- Cost tracking dashboards beyond basic monitoring
- Code submission automation (still manual at freeze)

### Success Criteria

- A real player can sit at any computer (workstation hardening comes later)
- They open hackletleague.com in browser, log in, navigate to active event
- They see the AI chat interface with their token budget displayed
- They chat with Deepseek through the platform during build phase
- Token budget enforced — they get cut off if they exceed it with proper truncation and rollback
- All interactions logged for audit
- They can build a real app in 24 minutes with AI assistance through the platform

### Estimated Time

4-6 weeks of part-time work.

### Why This Order

AI integration is core to what HackLet League is, but it depends on round mechanics existing first. Stage 4 makes hacklet events meaningfully real even though fuzz is still manual.

---

## Stage 5: Fuzz Runner

**Goal: Automated fuzz testing at code freeze with initial test catalog.**

*Strategic weight: the catalog this stage begins is HackLet's durable moat. A 24-minute format, solo play, even spectator framing can all be copied; a years-deep adversarial catalog calibrated for AI-assisted defensive coding — with a hidden pool that deepens each season — cannot be copied quickly. The catalog's quality is what decides whether HackLet results carry weight as a credential. This stage starts that asset; it never finishes it (the catalog deepens for the life of the league). The scope below is the technical starting set, not the moat itself.*

### In Scope

- Fuzz runner implementation per FUZZ_RUNNER_SPEC.md
- Initial fuzz catalog with approximately:
  - 30-50 universal QA tests (timeout, crash resistance, HTTP semantics, encoding, deployment hygiene)
  - 20-30 security tests (basic SQL injection, XSS, auth, file upload basics)
  - All in public pool initially (hidden pool grows over time)
- Central fuzz runner deployment in league infrastructure (ephemeral container per submission)
- Code submission automation at code freeze (git push triggers from workstation)
- FuzzResult and PlayerFuzzInvocation entities per DATA_MODEL.md
- Local fuzz runner deployable on workstations (Python service on local port)
- Tester judge override interface for fuzz applicability decisions
- Fuzz result integration with scoring engine
- Player portal updates to show fuzz triggers, budget, accumulated score
- Surface coverage metadata in result reporting
- Basic broadcast leaderboard endpoint (data only, broadcast production not yet built)

### Out of Scope

- Complete test catalog (catalog grows over seasons; this is the starting set)
- Hidden pool tests beyond a small starting set (mostly public initially)
- Broadcast video infrastructure (workstation streaming, overlays — Stage 6)
- Workstation hardening with RMM (Stage 7)
- Advanced production features
- Intent-dependent QA tests (deferred per format spec)
- LLM-assisted judge pre-analysis (deferred)
- Formal archetype declarations (deferred)

### Success Criteria

- A real hacklet round runs end-to-end with automated fuzzing
- Players triggered fuzz during build, saw real intelligence about their defenses
- At code freeze, code automatically pushes to league infrastructure
- Central fuzz runner deploys submissions and runs full catalog
- Tester judges review and override as needed
- Scoring engine produces composite results including authoritative fuzz scores
- Result reports include surface coverage metadata

### Estimated Time

8-12 weeks of part-time work. This is the most complex stage.

### Why This Stage Is Big

Fuzz runner is genuinely new infrastructure with several interconnected components: test format, runner engine, discovery system, applicability resolution, central and local deployment, judge override interface, scoring integration. Each is non-trivial. Combined they require substantial focused work.

---

## Stages 6+ (Deferred for Now)

These are real future work but should not be considered until Stage 5 ships and operates successfully.

### Stage 6: Broadcast Infrastructure
Workstation screen streaming, stats overlay APIs, commentator dashboard, live event production support.

### Stage 7: Workstation Hardening
RMM integration patterns, master image deployment, kiosk-style enforcement, firewall configuration tooling.

### Stage 8: Federation Features
Chapter-to-chapter coordination, regional event aggregation, cross-chapter rankings, league-wide qualifier flows.

### Stage 9: Verification System
Formal A/B/C tier verification process, documentation upload and review workflow, ongoing compliance monitoring.

### Stage 10: Governance
Dispute resolution interfaces, appeals processes, advisory board features, multi-team superadmin support.

### Stage 11: Unslop Format
The canonical second competitive format — **HackLet Unslop: Classical Sprint**. Reuses the entire Vibe: Classical Sprint substrate (workstation, AI substrate, SCP submission, fuzz catalog) and adds one new capability: a **slop-generation pipeline**. During the 5-minute round opening the league substrate generates a deliberately-broken web application from a seeded prompt and distributes the identical codebase to every workstation at T+5:00 — zero leakage risk, because the slop doesn't exist before the round. Players then find, diagnose, triage, fix, and verify the brokenness (security holes, QA failures, performance disasters, reliability gaps, hallucinated APIs, ugly UX) under AI assistance, and may add their own features and polish — "make it yours" is part of the credential. The same fuzz catalog scores Vibe and Unslop submissions identically at freeze, so it credentials a distinct skill cluster (reading unfamiliar code under pressure, triaging across dimensions of brokenness) on shared infrastructure. A meaningfully smaller build than the Agentic format — no new client, just the generation/distribution step plus a curated slop-prompt library — which is why it precedes Agentic. Introduced once Vibe operates successfully (targeting Season 2-3). Full sketch in IDEAS_FOR_LATER.md.

### Stage 12: Agentic Relationship
Introduces the **Agentic** relationship axis — AI living in the IDE with an accept/reject UI, as opposed to Classical's chat-window copy/paste. The foundational Agentic format is **HackLet Vibe: Agentic Agile** (the Agile timer; agents need more wall-clock than copy/paste, so the XP and Sprint timers are too tight). Requires a league-built, signed VSCodium extension locked to hackletleague.com — chat sidebar plus accept/reject UI for agent-proposed file changes, modeled on Cline/Roo Code. That extension is a substantial standalone project (TypeScript, ~4–6+ weeks for v1), which is why this trails Unslop. Adds the **agent-freeze rule** (at freeze the workspace reverts to the last accepted edit; pending proposals are dropped), a longer round cycle with budgets that scale to the timer, and a *Best Direction* award; it shares the fuzz catalog with every format (the runner is format-agnostic). Built only when the agentic-coding paradigm warrants it and Vibe is operating well. Full sketch in IDEAS_FOR_LATER.md.

---

## Total Realistic Timeline

If starting Stage 0 today:

- **Stage 0**: this week (1 afternoon)
- **Stage 1**: 4-6 weeks
- **Stage 2**: 4-6 weeks
- **Stage 3**: 4-6 weeks
- **Stage 4**: 4-6 weeks
- **Stage 5**: 8-12 weeks

**Total to first real hacklet event with full automation: 7-9 months** of part-time work.

This timeline assumes 10-15 hours per week of focused development with AI assistance. Full-time work would compress proportionally. Part-time work with significant other commitments would extend.

---

## What "Done" Looks Like Per Stage

For each stage to be considered "done" and the next stage to begin:

1. All in-scope items are implemented and deployed
2. Out-of-scope items have not been built (no scope creep)
3. The success criteria are met and verified by actual testing
4. Documentation updated where the implementation diverged from specs
5. Any discovered issues are either fixed or explicitly deferred with notes
6. The deployed system has been operating for at least one week without major incidents

If any of these conditions aren't met, the stage is not done. Do not advance to the next stage with unfinished work behind.

---

## Working With Claude Code Across Stages

When Claude Code is asked to work on hacklet, it should:

1. Verify what stage is currently active by checking BUILD_ROADMAP.md (this file)
2. Confirm whether the requested work fits within current stage scope
3. If the work is out of scope for current stage, suggest adding to IDEAS_FOR_LATER.md instead of building it
4. If the work is in scope, proceed with implementation following claude.md conventions
5. When work completes, update relevant documentation if implementation diverged from initial spec

Claude Code should respectfully push back when asked to do out-of-scope work. The discipline matters because it's the only thing preventing the project from becoming an endless design exercise.

---

*This document defines the build sequence. For what the format is, see format_spec.md. For league operations, see LEAGUE_OPERATIONS.md. For development conventions, see claude.md. For database schema, see DATA_MODEL.md. For service architecture, see ARCHITECTURE.md. For fuzz runner specifics, see FUZZ_RUNNER_SPEC.md.*
