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

## Status & Deviations (as of 2026-06-19)

- **Stage 1 complete** — Django + DRF + Postgres + Next.js foundation, Google SSO landed, chapter model in place. Platform runs at https://hackletleague.com over HTTPS with production settings (DEBUG off, secure cookies, HSTS). It is **public (reachable) but not publicized** — no announcement or marketing; the domain resolves and serves while the platform is built and tested. (This supersedes the earlier "stealth / LAN-only until launch" plan — *public* and *publicized* are treated as separate steps.) **Stage 2 begins.**
- **Hosting:** the home Proxmox VM continues hosting through Tier C pilot preparation. Hetzner production host is provisioned when the first Tier C pilot is scheduled — the clean x86→x86 move via portable Docker Compose repo is well-understood and doesn't need to happen before it's actually needed. Hosting move timing is "when pilot dates lock," not "when next stage starts."
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
- **Player portal submission upload endpoint** (zip upload with Dockerfile + README + code, size/structure validation)
- **Server-side deployment service** (container build, ephemeral container per submission, subdomain provisioning via Caddy reverse proxy under `submissions.hackletleague.com/{event}/{round}/{player}/`)
- **Untrusted-code container security** (unprivileged user, no sudo, network egress restricted to fuzz runner only, CPU/RAM/disk quotas, time-bounded lifecycle)
- Central fuzz runner deployment in league infrastructure
- Fuzz runner targets deployed submission subdomains (reusable input mechanism — see Stage 7 note)
- FuzzResult and PlayerFuzzInvocation entities per DATA_MODEL.md
- Tester judge override interface for fuzz applicability decisions
- Fuzz result integration with scoring engine
- Player portal updates to show fuzz triggers, budget, accumulated score, deployment success/failure feedback
- Surface coverage metadata in result reporting
- Basic broadcast leaderboard endpoint (data only, broadcast production not yet built)

### Out of Scope

- Complete test catalog (catalog grows over seasons; this is the starting set)
- Hidden pool tests beyond a small starting set (mostly public initially)
- Broadcast video infrastructure (workstation streaming, overlays — Stage 6)
- Workstation hardening with RMM (Stage 7)
- SCP-from-workstation submission capture (Stage 7 input mechanism for Tier A; Stage 5 ships portal-upload input mechanism for Tier C)
- Local fuzz runner deployable on workstations (Tier A "stress test during build" feature, deferred to Stage 7)
- Advanced production features
- Intent-dependent QA tests (deferred per format spec)
- LLM-assisted judge pre-analysis (deferred)
- Formal archetype declarations (deferred)

### Success Criteria

- A real hacklet round runs end-to-end with automated fuzzing
- Players triggered fuzz during build, saw real intelligence about their defenses
- At code freeze, code automatically pushes to league infrastructure
- Central fuzz runner deploys submissions and runs full catalog
- Tester judges may spot-check for false positives (slop scoring is automated; no per-probe override)
- Scoring engine produces composite results including authoritative slop scores
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
RMM integration patterns, master image deployment, kiosk-style enforcement, firewall configuration tooling, **SCP-from-workstation submission capture at code freeze** (writes to the same `/opt/hacklet/submissions/$EVENT/$ROUND/$PLAYER/` directory the Stage 5 portal upload writes to — the deployment pipeline downstream is reused without modification), local fuzz runner on workstations for "stress test during build" capability. The submission processing pipeline (unpack → container build → ephemeral deployment → subdomain routing → fuzz evaluation → scoring) ships in Stage 5 and is reused in Stage 7 unchanged; what Stage 7 adds is the workstation-side input mechanism and the workstation control infrastructure that makes Tier A's structural anti-cheating real.

### Stage 8: Federation Features
Chapter-to-chapter coordination, regional event aggregation, cross-chapter rankings, league-wide qualifier flows.

### Stage 9: Verification System
Formal A/B/C tier verification process, documentation upload and review workflow, ongoing compliance monitoring.

### Stage 10: Governance
Dispute resolution interfaces, appeals processes, advisory board features, multi-team superadmin support.

### Stage 11: Unslop Format
The canonical second competitive format — **HackLet Unslop Sprint**. Reuses the entire Vibe Sprint substrate (workstation, AI substrate, submission/deployment pipeline, fuzz catalog) and adds one new capability: a **slop-generation pipeline**. The league substrate generates a deliberately-broken web application from a seeded prompt server-side; for Tier A/B events the workstation receives the codebase at T+5:00 of round opening (zero leakage risk because generation is server-controlled); for Tier C events the same broken app is distributed as a downloadable zip via the player portal at T+5:00 (also zero leakage). Players then find, diagnose, triage, fix, and verify the brokenness (security holes, QA failures, performance disasters, reliability gaps, hallucinated APIs, ugly UX) under AI assistance, and may add their own features and polish — "make it yours" is part of the credential. The same fuzz catalog scores Vibe and Unslop submissions identically at freeze, so it credentials a distinct skill cluster (reading unfamiliar code under pressure, triaging across dimensions of brokenness) on shared infrastructure. A meaningfully smaller build than the agent interface (Stage 12) — no new client, just the generation/distribution step plus a curated slop-prompt library — which is why it precedes Stage 12. Introduced once Vibe operates successfully (targeting Season 2-3). Full sketch in IDEAS_FOR_LATER.md.

### Stage 12: Agent Interface (Substrate Expansion)
Adds an **in-IDE agent interface** to the league substrate as a parallel client alongside the chat-window interface from Stage 4. A league-built, signed VSCodium extension locked to hackletleague.com — chat sidebar plus accept/reject UI for agent-proposed file changes, modeled on Cline/Roo Code patterns. The extension talks to the same OpenAI-compatible chat completions endpoint that the chat window uses (format_spec §5.3); the season-pinned model, per-player token budget, and audit logging are shared. The unified-substrate model means there is no separate "Agentic format" — players at Tier A and Tier B receive both interfaces and use whichever combination fits their workflow, with a unified token budget that prevents tool-stacking advantage. Adds the **agent freeze rule** (at freeze the workspace reverts to the last accepted edit; pending proposals dropped). Substantial standalone TypeScript project, ~4-6+ weeks for v1. Built once Stage 4 chat-only substrate operates well; the agent interface is *substrate expansion*, not a new format. Sketch in IDEAS_FOR_LATER.md "Agent interface for unified league substrate."

---

## Stage-Tier Readiness Mapping

The tier system (LEAGUE_OPERATIONS.md §4) and the staged build couple naturally — different tiers require different infrastructure depth, so different stages unlock different tier-readiness. This mapping is what determines the earliest point at which real events can run, which matters for resisting build-build-build syndrome.

**The one-line summary**: **Stage 5 is when we can run our first event (Tier C). Stage 7 is when we can run our first Tier A event.** Everything else slots into this structure — Tier C is the entry point that ships first, Tier A is the credentialing destination that requires the full infrastructure stack.

### Pre-Stage 3: Format Mechanics Validation Only

Before round mechanics ship, the format can be validated through scrappy 4-person dry-runs using manual timing, manual judging, and manual fuzz catalog. This is *not* an event in the credentialing sense — no leaderboards, no rankings, no records. It's *format validation* with human play surfacing observations the spec can't anticipate. Worth doing as soon as the design is stable enough to run; doesn't require any platform infrastructure.

### After Stage 5: Tier C Events Viable (Earliest Real Events)

Tier C events become viable after the fuzz runner ships. Tier C requires:
- Stage 1 (foundation), 2 (events), 3 (round mechanics) for platform event support
- Stage 5 (fuzz runner) for automated catalog evaluation at code freeze

Tier C **does not require** Stage 4 (AI substrate) because Tier C is BYOD-substrate — players bring their own AI. The Stage 4 league-hosted OpenRouter integration is for Tier B+ operations where the league hosts AI substrate. For Tier C launch, Stage 4 can be deferred or built in parallel with Stage 5 rather than sequentially.

Tier C **does not require** Stage 6 (broadcast), Stage 7 (workstation hardening), Stage 8 (federation), Stage 9 (verification system), or Stage 10 (governance). Tier C operates with audience-in-room rather than broadcast, BYOD rather than RMM-controlled workstations, chapter-local rather than federation-coordinated, and light superadmin review rather than formal verification.

The Stage 5 scope can be calibrated for Tier C launch — a minimal universal arsenal catalog of 30-50 tests is sufficient to make Tier C events meaningful. The catalog deepens from there as more events run.

**Practical implication**: the first real HackLet event at BU can happen after Stage 5 ships with minimal Stage 4. Earliest realistic timing depends on whether Stage 4 is deferred (faster) or built in parallel (more substrate options).

### After Stage 7: Tier A Events Viable (Credentialing-Grade)

Tier A events require the full infrastructure stack:
- Stages 1-3 for platform event support
- Stage 4 for league-hosted AI substrate with enforced token budgets
- Stage 5 for automated fuzz runner with deep catalog
- Stage 6 for broadcast infrastructure
- Stage 7 for workstation hardening (RMM, master images, firewall configuration)

Without Stage 7, the "structural anti-cheating" property that makes Tier A credentials reliable (see LEAGUE_OPERATIONS.md §4 and IDEAS_FOR_LATER.md "credential reliability argument") doesn't exist. Tier A operations can't honestly claim credentialing-grade integrity without infrastructure-enforced substrate control.

### After Stage 8: Multi-Chapter Coordination Viable

Cross-chapter rankings, regional events, qualifier flows, and the federation operational model require Stage 8 to function. Pre-Stage 8 the platform can support multiple chapters as data, but cross-chapter event coordination is manual.

### After Stage 9: Formal Tier A Verification Process

The verification application workflow, documentation review, and ongoing compliance monitoring are Stage 9 work. Before Stage 9, Tier A status (if conferred) is informal — superadmin says "yes" without a structured verification artifact. Acceptable for the first 1-2 Tier A chapters; needs Stage 9 before broader Tier A expansion.

### Stage 11/12: Additional Format Variants

### Stage 11/12: Format and Substrate Expansions

Unslop (Stage 11) adds the second format axis (build-from-scratch becomes the Vibe family; remediate-broken becomes the Unslop family). The agent interface (Stage 12) adds a parallel client to the league-hosted AI substrate. Neither unlocks new tier capabilities — they expand the format ecosystem and substrate capability within the existing tier structure.

---

## Total Realistic Timeline

Starting from current state (Stage 1 shipped 2026-06):

- **Stage 0**: ✓ shipped 2026-06
- **Stage 1**: ✓ shipped 2026-06 (Google SSO + foundation)
- **Stage 2**: 4-6 weeks part-time, 1-2 weeks summer velocity
- **Stage 3**: 4-6 weeks part-time, 1.5-2.5 weeks summer velocity
- **Stage 4**: 4-6 weeks (deferrable for Tier C launch — defer to Tier B horizon)
- **Stage 5**: 8-12 weeks part-time, 4-6 weeks summer velocity (genuine engineering complexity; the hardest single stage; don't rush the catalog quality)

**Total to first Tier C event (BU pilot, BYOD substrate)**:
- Part-time pace (10-15h/week): roughly 6-8 months from current state if Stage 4 is deferred, 7-9 months if Stage 4 ships sequentially.
- **Summer velocity (30-40h/week through July-August 2026)**: Stage 5 shipping by end of summer 2026 is genuinely realistic with deferred Stage 4. That puts scrappy dry-run early October 2026 and first BU Tier C pilot late October / November 2026.

Either way, the first real HackLet event happens after Stage 5, not after Stage 7. **Scrappy dry-runs for format validation can happen even earlier — anytime after Stage 3 round mechanics work.**

**Total to first Tier A event (credentialing-grade)**: Stages 1-7 sequential. The Stage 7 work is *substantially lighter* than originally implied because Stage 5 builds the submission processing pipeline (unpack → containerize → deploy → fuzz → score) that Stage 7 reuses unchanged — Stage 7 adds workstation-side SCP capture as an input mechanism, plus the workstation control infrastructure (RMM, master image, firewall). Roughly 8-12 months from Stage 5 ship to Stage 7 ship at part-time pace; faster with sustained focus.

**What doesn't compress with velocity**:
- The one-week-stable gate between stages (calendar time, not engineering time)
- Real-world testing of the fuzz runner (requires humans submitting code)
- Operational prep (venue, judges, sponsor outreach when relevant)
- Hetzner migration window (tied to pilot scheduling, not stage shipping)

Part-time pace assumes ~10-15h/week without AI; with AI-assisted development at 30-40h/week, stages compress substantially. Summer velocity scenario assumes sustained 30-40h/week with CC as collaborator through July-August 2026.

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
