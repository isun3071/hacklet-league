# DOC_STATE — Documentation Audit (HISTORICAL SNAPSHOT)

> ## ⚠ This is a historical artifact, not a live audit.
>
> Produced 2026-07-28 and **not re-run since**. The rulebook was frozen at **v1.0.0 on
> 2026-08-03** (see format_spec.md and CHANGELOG.md), and many rows below are stale — every
> contradiction `C-01…C-22` that was resolvable has been resolved, and the four `OPEN` decisions
> the audit flagged are now decided. **Do not use the tables below as current state.** For what
> is true now: read the inline `Status:` markers in each doc, and the CHANGELOG for decisions.
> This file is retained only as the record of the reconciliation that produced v1.0.0.

*Produced 2026-07-28. Read-only audit. No document other than this one was modified.*

> ## ⚠ Nine contradictions have been closed since this audit ran
>
> This file is a **snapshot of 2026-07-28** and has not been re-audited. Its status columns and
> `C-nn` entries below still describe the repository as it was then. Closed since:
>
> **C-02** (fuzz schema rewritten deduction-only, 07-30) · **C-04** and **C-05** (token budget
> reframed, then rebased to 10M with the per-prompt cap retired) · **C-07** (the substrate gate:
> two windows with a cut at build end) · **C-09** (language tiers retired, so the §5.4-vs-IDEAS
> disagreement dissolves) · **C-10** (no league-provided database; the scoring page corrected) ·
> **C-12** (Tier C Extended retired) · **C-14** (`Event.format` accepts `underspecified`) ·
> **C-20** (the 3-minute upload grace is implemented).
>
> Also changed: `judge_specialization` now ships all four values, so the "BUILT with a known gap"
> row for EventParticipant is stale — but the scoring-math divergence that row points at
> (**C-01** / D-11) is **still real**, and is now waiting on the fuzzer being wired rather than
> on a decision.
>
> The **7.2M-token measurement is withdrawn** (2026-07-31). It could never be identified —
> no date, event, operator or log — so it is treated as never having happened rather than
> cited as evidence. The 10M budget stands as an **ASSUMED** figure sized to survive
> agentic context re-sending. Rows below that mark it MEASURED are stale.
>
> Also closed: **C-17** (the award is **Slopless Builder**, in docs and in the `slopless_builder`
> award key).
>
> DECISIONS_OWED.md, which this file referred to for the open list, was **deleted on
> 2026-07-31**: its resolutions had landed in format_spec, and its still-open items are now
> marked `OPEN —` in the sections that own them. Search for that string. [CHANGELOG.md](CHANGELOG.md)
> carries the reasoning. Where either disagrees with the snapshot below, they win.

**Purpose.** The docs are written in present indicative throughout, so a reader cannot tell
shipped from designed from superseded. This file assigns a status to every section of every
doc in scope, lists every cross-document contradiction found, and identifies which of them
need a decision rather than an edit.

---

## Method and repo state

Every BUILT claim below was checked against source, not against another document. Where a
doc asserts a mechanism, the audit names the file and line that implements it, or records
that nothing does.

Repo state at audit time:

- Branch `main`, working tree **clean**, nothing modified in the last hour.
- Most recent commits: `4b1e471` … `7b140cf` at 2026-07-28 11:07 (four docs commits),
  `ce57998` at 10:32.
- Docs last touched 2026-07-28: `format_spec.md`, `TIER_A_OPERATIONS.md`,
  `ARCHITECTURE.md`, `BUILD_ROADMAP.md`, `IDEAS_FOR_LATER.md`, `LEAGUE_OPERATIONS.md`,
  `CHANGELOG.md`. Docs last touched 2026-07-06: `TIER_B_OPERATIONS.md`, `DATA_MODEL.md`,
  `NONTECH_JUDGE_NOTES.md`, `JUDGE_PANEL_RECONCILIATION_PATCH.md`. Last touched
  2026-06-23: `TIER_C_OPERATIONS.md`, `PITCH.md`.
- **Nothing is currently blocked for Phase 2 on the uncommitted/recently-modified rule.**
  Re-check immediately before editing; the platform session owns `format_spec.md` and the
  tier docs and is active in them.

### Status vocabulary

| Status | Means |
|---|---|
| **BUILT** | Exists in code. Cited to `path:line`. |
| **DESIGNED** | Specified, no implementation. |
| **MEASURED** | A number from an identified real run. |
| **ASSUMED** | A number estimated, carried from conversation, or with no traceable source. |
| **SUPERSEDED** | Describes a decision that has been replaced. |

Sections often mix. Where they do, the dominant status is given first and the exception is named.

---

## Ground truth: what actually exists

This is the baseline every BUILT classification below is measured against.

**Django models that exist — 9 of the 16 entities DATA_MODEL.md describes:**
`User` (`backend/users/models.py:42`), `Chapter` + `ChapterStaff`
(`backend/chapters/models.py:8,62`), `Event` + `EventParticipant`
(`backend/events/models.py:8,88`), `Round` + `Submission` + `Score`
(`backend/rounds/models.py:8,75,129`), `Ranking` (`backend/rankings/models.py:7`).

**Entities that do not exist in any form:** `VerificationApplication`, `FuzzTest`,
`FuzzResult`, `PlayerFuzzInvocation`, `AuditLog`, `AudienceVote`, `WorkstationSession`.
(`WorkstationSession` is the only one DATA_MODEL.md marks as deferred.)

**Infrastructure that does not exist:**

- No `backend/ai_proxy/` app. No OpenRouter integration anywhere. No `/api/ai/chat`,
  no `/api/v1/chat/completions`, no `/api/fuzz/trigger` — the full route table is
  `backend/hacklet/urls.py:37-51`.
- No token budget enforcement. `Submission.token_budget_used`
  (`backend/rounds/models.py:108`) and `fuzz_budget_used` (`:109`) are unwritten integer
  fields; nothing increments them.
- No Channels, no Redis, no Celery, no WebSockets. `backend/hacklet/asgi.py:6` is plain
  Django ASGI and says so. The frontend **polls every 5 seconds**
  (`frontend/components/RoundLive.tsx:103`).
- No container deploy pipeline, no SCP capture, no fuzz integration in the platform.
  `Submission.deployed_url` (`backend/rounds/models.py:106`) is a URL the player types in
  (`backend/rounds/views.py:245`). `SUBMITTED_DEPLOYED` / `SUBMITTED_FAILED`
  (`:83-84`) are declared and never set by any code path.

**What is genuinely built and works:**

- Server-authoritative phase clock. `backend/rounds/services.py:14-47` defines three
  profiles; `current_phase()` (`:78-100`) derives the live phase from stored absolute UTC
  boundaries and never consults client time.
- Server-authoritative code freeze. `backend/rounds/views.py:228-229` rejects uploads past
  `build_end_at` on the server's own clock.
- Portal zip upload — **for every tier, with no tier gating**
  (`backend/rounds/views.py:212-253`), stored privately
  (`backend/rounds/models.py:68-72`, `backend/hacklet/settings/base.py:149-153`).
- Scoring: six judge-entered facets averaged into two axes, rank-summed with progressive
  tiebreakers (`backend/rounds/scoring.py:24-33, 87-112`); three awards emitted (`:132-137`).
- Rankings: chapter + global (Tier A chapters only), `all_time` period only, idempotent
  recompute on round complete/cancel (`backend/rankings/services.py:103-123`).

---

## Per-document classification

### format_spec.md

| § | Subject | Status | Note |
|---|---|---|---|
| 1 | Format identity, 3×5 matrix | DESIGNED | Code has 2 formats, not 3 — see **C-14** |
| 2 | Core definitions | DESIGNED | Round/Event/Submission exist as entities; Substrate does not |
| 3.1 | Phase sequence | **Mixed** | Clock BUILT (`services.py:14-47`); SCP, ephemeral container, local fuzz runner, proxy cutoff all DESIGNED |
| 3.2 | Round sizing (8 std, 6–12, 12 max) | DESIGNED | No cap enforced anywhere; `Round.player_count` is a free integer (`models.py:51`) |
| 3.3 | Broadcast | DESIGNED | |
| 4.1 | Two axes; four judge roles 30/20/20/30 | **DESIGNED** | Code implements a *different decomposition* — see **C-01** |
| 4.2 | Deduction-only slop philosophy | DESIGNED | **C-02 RESOLVED 2026-07-30** — DATA_MODEL's fuzz schema now matches |
| 4.3 | Best Overall rank-sum | **BUILT** | `scoring.py:95-112`, exact tiebreaker order matches. Runs over the stand-in axis, not slop |
| 4.4 | Categorical awards | **Mixed** | 3 of 4 BUILT (`scoring.py:132-137`); People's Hacklet DESIGNED. Most Efficient retired per-round here but live in tier docs — **C-06** |
| 4.5 | Tradeoffs / no permanent meta | DESIGNED | Design rationale |
| 5.1 | Workstation, VSCodium, local fuzz | DESIGNED | |
| 5.2 | Network configuration | DESIGNED | |
| 5.3 | AI substrate, OpenAI-compatible proxy | DESIGNED | No proxy exists |
| 5.4 | Substrate languages | DESIGNED | Contradicts IDEAS — see **C-09** |
| 5.5 | Resource budgets | **Mixed** | 100k tokens / 50 fuzz points **ASSUMED**; 7.2M-token round **MEASURED** (n=1, off-substrate, self-labeled); buzzer gate DESIGNED |
| 5.6 | Submission requirements | **Mixed** | README/deploy contract DESIGNED; freeze enforcement BUILT |
| 5.7 | Self-containment | DESIGNED | Contradicted by the shipped `/scoring` page — see **C-10** |
| 5.8 | League-issued proxy keys | DESIGNED | Its "settled decisions" bear directly on the Phase 3 key question |
| 6 | Tier structure (collegiate/U25/open) | DESIGNED | `Event.player_tier_restriction` exists (`events/models.py:67`); no scoring differs by it. §6.1's "positive-only scoring" is also **SUPERSEDED** by §4.2 deduction-only — **C-03** |
| 7.1 | Events, round size targets, 1-event-1-format | **Mixed** | Event/Round entities BUILT; 1-event-1-format not enforced; size targets DESIGNED |
| 7.2 | Two ranking systems | **Mixed** | Persistent/all-time BUILT; season DESIGNED (`services.py:14-16`) |
| 7.3 | Qualification flow | DESIGNED | |
| 8 | Conduct | DESIGNED | |
| 9 | Format evolution | DESIGNED | |
| 10 | What the format measures | DESIGNED | |
| 11 | League's position | DESIGNED + **cited external figures** (Harness, HBR, MIT NANDA — sourced, dated, fact-check note in IDEAS:127) |

### TIER_A_OPERATIONS.md

| § | Subject | Status | Note |
|---|---|---|---|
| 1 | Tier A identity | DESIGNED | |
| 2 | Infrastructure requirements | DESIGNED | `:38` SCP capture — **not built** |
| 3 | AI substrate at Tier A | DESIGNED | `:73` per-prompt 25k cap + "resource calibration credentialing claim" — **SUPERSEDED** by format_spec §5.5 and LEAGUE_OPS §4. See **C-04**, **C-05** |
| 4 | 135-min timing block (`:80-88`) | **BUILT** | Exactly matches `services.py:15-25`. The only tier timing block that verifies clean |
| 4 | Phase details | **Mixed** | `:101` SCP + container DESIGNED. `:103` **arithmetic error** — Phase 2(b). `:105` AI retained during prep contradicts `:97` — **C-07** |
| 4 | Round sizing | DESIGNED | Rationale conflicts with format_spec §3.2 — **C-08** |
| 5 | Submission mechanism (SCP) | **DESIGNED** | `:136,138,140,142` all present-tense. Reality: portal zip for all tiers (`views.py:212`) |
| 6 | Broadcast architecture | DESIGNED | |
| 7 | Fuzz catalog evaluation | DESIGNED | |
| 8 | Scoring and awards | **Mixed** | `:207` says "best **Fuzz** Rank" where format_spec §4.3 says Slop Rank — stale term. `:208` Most Efficient as a per-round award — **C-06** |
| 9 | Live judging protocol | DESIGNED | Panel definition matches the locked patch. Cross-ex timing is the **unresolved** item — **C-11** |
| 10 | Multi-day tournament template | DESIGNED | Duplicates IDEAS:45-69 nearly verbatim |
| 11 | Anti-cheating enforcement | DESIGNED | |
| 12 | Credentialing claims | DESIGNED | |
| 13 | Chapter variant portfolio | DESIGNED | |
| 14 | Strategic timing | DESIGNED | |

### TIER_B_OPERATIONS.md

| § | Subject | Status | Note |
|---|---|---|---|
| 1–3 | Identity, infrastructure, substrate | DESIGNED | |
| 4 | 135-min timing block | DESIGNED | No `tier_b` value exists in `Round.TimingProfile` (`rounds/models.py:19-22`); a Tier B round must be scheduled as `tier_a`. Undocumented |
| 5 | Submission mechanism | **DESIGNED** | `:108` SCP identical to Tier A — not built |
| 6 | Audience and broadcast | DESIGNED | |
| 7 | Fuzz catalog evaluation | DESIGNED | |
| 8 | Scoring and awards | DESIGNED | `:139` Most Efficient available at Tier B — **C-06**, and doubly odd since Tier B budgets are honor-system |
| 9 | Live judging protocol | DESIGNED | Four roles landed. `:147` 3-judge fallback → 90s cross-ex vs Tier A's 120s — **C-11** |
| 10–12 | Credentialing, verification, position | DESIGNED | |

### TIER_C_OPERATIONS.md

| § | Subject | Status | Note |
|---|---|---|---|
| 1–3 | Identity, profiles, substrate | DESIGNED | `:21` Tier C Extended "~135-180 min" contradicts the shipped profile — **C-12** |
| 4 | MVR 60-min timing block (`:40-46`) | **BUILT** | Matches `services.py:27-34` exactly |
| 5 | Large-cohort ~74-min block | **DESIGNED** | No such profile exists in `TimingProfile` |
| 6 | Submission mechanism | **Mixed** | Portal upload BUILT (`views.py:212-253`); 3-min grace **not implemented** (freeze is hard at `build_end_at`, `views.py:228`); `:103` "automatic zero" contradicts DNF semantics — **C-13** |
| 7 | PITCH.md artifact | DESIGNED | No PITCH.md field on `Submission` |
| 8 | LLM judging architecture | DESIGNED | `:192` 40/30/30 weighting is a **third** communication decomposition — **C-01** |
| 9 | Scoring and awards | DESIGNED | Correctly defers to format_spec §4 |
| 10–14 | Audience, MLH, credentialing, R&D, sequencing | DESIGNED | `:210` LLM cost $5-15/round, $60-180/chapter/year — **ASSUMED** (model-priced estimate, no run) |

### DATA_MODEL.md

| § | Subject | Status | Note |
|---|---|---|---|
| Overview / Entity list | 16 entities | **Mixed** | 9 BUILT, 7 not. Only `WorkstationSession` is marked deferred |
| User, Chapter, ChapterStaff | | **BUILT** | |
| VerificationApplication | | DESIGNED | |
| Event | | **BUILT** | `:130` format enum `(vibe, unslop)` — only 2, vs format_spec's 3. **C-14** |
| Round | | **BUILT** | `:157` timing_profile enum matches code exactly. `:158` status enum omits `pitching`, `deliberation`, `cancelled` which the code has (`rounds/models.py:24-34`) — minor drift |
| Submission | | **BUILT** | Accurate, including the "never extracted until Stage 5" note |
| WorkstationSession | | DESIGNED | Self-labeled Stage 7 — the one honestly-tensed entity |
| FuzzTest | `penalty : int (>= 0)` | DESIGNED | **C-02 fixed 2026-07-30.** Award-points fields removed. `bundle` (2 values vs the runner's 3) and `intent_dependence` left open, noted in place |
| FuzzResult | `outcome` 3-value, `penalty_contributed : int (>= 0)` | DESIGNED | **C-02 fixed 2026-07-30.** `override_by_judge` / `override_reason` deliberately retained — **D-18** |
| PlayerFuzzInvocation | `slop_added : int (>= 0)` | DESIGNED | **C-02 fixed 2026-07-30.** `score_delta` → `slop_added`, running score renamed and documented as ascending-sort |
| EventParticipant | | **BUILT with a known gap** | `:294` enum includes `stakeholder`; the code has only tester/ux_designer/general (`events/models.py:99-102`). The **⚠ flag at `:315`** correctly states the scoring-math divergence — this is the single most honest passage in the doc set |
| Score | | **BUILT** | `:327` facet enum matches `rounds/models.py:134-140` exactly |
| Ranking | | **BUILT** | Enums match `rankings/models.py:12-20`; `:359` accurately describes shipped Stage 3 behavior |
| AuditLog, AudienceVote | | DESIGNED | |
| Indexes / constraints / cascades | | **Mixed** | Constraints BUILT; several listed indexes reference non-existent tables |

### ARCHITECTURE.md

The most uniformly over-asserted document in the set. Written entirely in present tense for
a system that is roughly one-third built.

| § | Subject | Status | Note |
|---|---|---|---|
| Services | "runs four primary services" | **DESIGNED** | Redis/Channels absent (`asgi.py:6`, `backend/pyproject.toml` deps). Three services run, not four |
| Authentication flow | | **BUILT** | allauth headless, session cookies, no JWT — accurate |
| Public page flow | SSR | **BUILT** | |
| Player AI chat flow | | **DESIGNED** | No endpoint exists. `:60` and `:96` contradict each other — **C-07** |
| Fuzz trigger flow | | DESIGNED | |
| Code submission + authoritative fuzz | | **DESIGNED** | `:86`, `:94` SCP present-tense |
| Scoring flow | | **Mixed** | Judge scoring BUILT; `/api/scoring/submit` is wrong (real route is `/api/scores/`, `urls.py:34`); "after all judges complete" is not how `compute_round_results` works — it computes on demand from whatever scores exist (`scoring.py:57-72`) |
| Event lifecycle state machine | | **BUILT** (timings) | Matches `services.py`. "Django scheduled task" transitions do **not** exist — phase is derived on read |
| Workstation session lifecycle | | DESIGNED | Self-labels as Stage 7 |
| OpenRouter integration | "centralized in `backend/ai_proxy/`" | **DESIGNED** | Directory does not exist |
| Broadcast infrastructure | | DESIGNED | |
| Deployment topology | | **Mixed** | Caddy + Docker Compose + Postgres BUILT; Redis and daphne DESIGNED; "Hetzner VPS" is stale — BUILD_ROADMAP:45 says home Proxmox VM |
| Environment configuration | | **Mixed** | `OPENROUTER_API_KEY` listed as **Required** — nothing reads it |
| Scaling / Security architecture | | **Mixed** | TLS, session cookies, CSRF, ORM, DRF serializers BUILT. `AuditLog` and **django-guardian** (`:289`) do not exist |
| Future considerations | | DESIGNED | Correctly tensed |

### LEAGUE_OPERATIONS.md

| § | Subject | Status | Note |
|---|---|---|---|
| 1–3 | Federation, responsibilities, chapter modes | **Mixed** | `Chapter.mode` BUILT (`chapters/models.py:22`); behavior per mode not implemented |
| 4 | Tiers and verification | DESIGNED | `Chapter.tier` + `verification_status` BUILT; verification workflow is Django-admin manual |
| 4 | **Token Budget's Two Functions** (`:129-137`) | DESIGNED, **current** | This is the *updated* framing (cost control first). It landed here and in format_spec §5.5 but **not** in TIER_A §3 — **C-04**. Note `:97` in the same doc still asserts the old framing — intra-document |
| 5 | Role hierarchy | **Mixed** | Superadmin/owner/organizer/judge/player BUILT via `ChapterStaff.roles` + `EventParticipant.role`. Six-level cascade partly enforced (`chapters/permissions.py`) |
| 6 | User account model | **BUILT** | |
| 7 | Centralized AI substrate | DESIGNED | `:255` "100,000 per round, server-enforced" — **ASSUMED**, and "server-enforced" is false today |
| 8 | Permissionless chapter creation | **BUILT** | |
| 9–10 | Platform as foundation, governance | DESIGNED | |
| 11 | Sanctions | DESIGNED | |
| 12 | Dogfooding the catalog | DESIGNED | |

### NONTECH_JUDGE_NOTES.md

Self-labels at `:3` as *"Working notes, not canonical yet."* That label is accurate and
should be kept — but the notes contain **positions the league has since decided against**,
and nothing in the file says so.

| § | Subject | Status |
|---|---|---|
| 1 | "Three technical judges share ONE rubric" | **SUPERSEDED** — format_spec §4.1 and the patch lock four separate rubrics. **C-15** |
| 2 | Tester judge covers intent-dependent correctness | DESIGNED, **current** |
| 3, 4A, 4B, 4, 5 | Per-format stakeholder postures, CES/incumbent/brief-author models | DESIGNED (working) |
| 6, 7 | Pre-commit and freeze; on-stage intro | DESIGNED (working) |
| 8 | Cross-ex concision / anti-filibuster | DESIGNED — **the live alternative** to Tier A's one-question-per-judge rationing. **C-11** |
| 9 | Slop-score reveal withheld through cross-ex | DESIGNED — contradicts TIER_A:103. **C-16** |
| 10 | Open questions incl. aggregation | **SUPERSEDED in part** — "aggregation not decided" was decided as 30/20/20/30 |

### JUDGE_PANEL_RECONCILIATION_PATCH.md

A patch-instruction document. Its edits have been applied; the file has not been retired.

| Edit | Target | Status |
|---|---|---|
| Edit 1 | format_spec §4.1 | **APPLIED** (format_spec:100-108) |
| Edit 2 | format_spec §4.2 four roles | **APPLIED** (format_spec:172) |
| Edit 3 | TIER_A §9 panel | **APPLIED** (TIER_A:226-232) |
| Edit 3 note | Cross-ex timing — *"do NOT overwrite"* | **CORRECTLY NOT APPLIED** — still open, **C-11** |
| Edit 4 | TIER_B §9 | **APPLIED** (TIER_B:145-147) |
| Edit 5 | DATA_MODEL enum | **APPLIED in doc** (DATA_MODEL:294), **NOT in code** (`events/models.py:99-102`) |
| `:87-92` | Explicitly-open list | Still open: cross-ex timing, awards structure, comm-award naming, rubric internals |
| `:20`, `:90` | Award called **"Slopless Builder"** | **Naming drift** — every other doc says "Most Resilient". **C-17** |

### PITCH.md

Player/audience-facing pitch copy. Last touched 2026-06-23; predates the four substrate
decisions of 2026-07-28 entirely. Everything here is **DESIGNED** presented as fact, which
is defensible in marketing copy but should be marked in-repo.

| Pitch | Status | Note |
|---|---|---|
| 1 — Tier A spectator | DESIGNED | `:8` live token-budget and slop-score overlays; `:11` four judges (current) |
| 2 — Tier A participant | DESIGNED | `:25` "100,000 tokens… hard cap, server enforced" — **ASSUMED** + not built. `:27` SCP + ephemeral container — not built |
| 3 — Tier C / BU pilot | DESIGNED | `:40` MVR timing matches the built profile. `:42` container deploy — not built. `:44` LLM judging — not built |

> **The 28.2% accessibility and "68% of defect weight in chores" figures are not in
> PITCH.md, and not anywhere else in this repository.** See "Corrections to the briefing"
> below.

### BUILD_ROADMAP.md

The best-tensed document in the set. Its Status & Deviations block was corrected today
(`ce57998`) and verifies accurate against code.

| § | Subject | Status |
|---|---|---|
| Scope discipline rules | | Policy — current |
| Status & Deviations (`:39-46`) | | **BUILT/accurate.** Stages 0–3 shipped ✓; "Stage 4 active, no substrate code exists yet — no `ai_proxy` app" ✓ verified |
| Stage 0, 1 | | **BUILT** |
| Stage 2 | | **BUILT** — except `:162` "ChapterMembership entity" is a **stale name** (renamed `ChapterStaff`, migration `0004`) |
| Stage 3 | | **BUILT with two undocumented deviations**: `:206` "WebSocket updates (now we need real-time)" — shipped as 5s polling; `:207`/`:231` "manual git push" / "via git or zip upload" — **SUPERSEDED**, git was removed (DATA_MODEL:195) |
| Stage 4 | | DESIGNED — `:257` correctly carries the new 403 gate |
| Stage 5 | | DESIGNED — `:316` "Tester judge override interface" vs `:341` "no per-probe override" **contradict each other inside one stage**. **C-18** |
| Stages 6–12 | | DESIGNED, correctly future-tensed |
| Stage-Tier Readiness Mapping | | DESIGNED — internally consistent |
| Timeline | | **ASSUMED** — all week/velocity figures are estimates; `:46` says so explicitly |

### CHANGELOG.md

Historical record; present tense is appropriate. Entries verify against git history.
`:8-16` (Stage 4 substrate decisions) is the authoritative statement of the 2026-07-28
changes and correctly labels the 7.2M measurement as n=1 and off-substrate. `:29` correctly
records that no platform migration accompanied the deduction-only rename — matching
`scoring.py:9-13`. **No corrections needed.**

### IDEAS_FOR_LATER.md

Parking lot. Entries carry their own deferral markers, which is the right convention. Two
issues:

- `:89-99` **Season 1 substrate selection contradicts format_spec §5.4** — **C-09**.
- `:25` correctly records the nontech judge as LOCKED and cites the patch — this entry is
  **current**, not deferred, and sits in a file whose header says everything in it is
  waiting its turn. Minor mis-filing.
- External market figures (`:127`, `:129`) are **cited and dated** with an explicit
  fact-check caveat. Leave as-is.

---

## Corrections to the briefing's starting points

Three of the six supplied starting points need adjustment before Phase 2 acts on them.

**1. BUILD_ROADMAP is not stale on SCP.** The briefing lists BUILD_ROADMAP.md:328, 363,
450 as asserting SCP as current. They do the opposite:

- `:328` places SCP under Stage 5 **Out of Scope** — "Stage 7 input mechanism for Tier A;
  Stage 5 ships portal-upload input mechanism for Tier C."
- `:363` is the Stage 7 description, under a heading reading "Deferred for Now."
- `:450` reads "Stage 7 **adds** workstation-side SCP capture."

All three are correctly future-tensed. **Do not mark these.** The genuinely stale SCP
assertions are TIER_A:38, 101, 136, 138, 140, 142; TIER_B:108; ARCHITECTURE:86, 94 — plus
two the briefing did not have: **PITCH.md:27** and **`frontend/app/scoring/page.tsx:15-16`**
(*"Tier A captures straight from your workstation"*), the latter shipped to players today.

**2. The 28.2% / 68% figures do not exist in this repository.** Grepped for `28.2`, `68%`,
"defect weight", "chores", and every percentage token across all thirteen docs plus
`log.txt`. Zero hits. There is nothing to mark ASSUMED, because the claim was never written
down here. What *does* exist is in the fuzzer repo, is **MEASURED**, and is traceable:

> `fuzz-runner/hacklet_runner/probes.py:3776-3794` — **v11 corpus, 1,531 scored apps.** At
> the old 30/18/10/4 a11y tiers: accessibility **34.0%** of total corpus penalty,
> security-headers **24.4%**, web-vitals **10.4%**; a11y fired on **73.6%** of apps. After
> re-pricing to 20/12/7/3: accessibility **25.5%**, median hit 19, max 44.

Your "accessibility 25.5%, security-headers 27.5%" is right and I can confirm the second
number arithmetically: 24.4% was headers' share of the *pre-repricing* total; once a11y
drops, the denominator shrinks and headers rise to 27.5%. **The comment at probes.py:3794
gets this wrong** — it compares post-repricing a11y (25.5%) against pre-repricing headers
(24.4%) and concludes a11y is still larger. It isn't; headers is. That file belongs to the
fuzzer session — **flagging, not touching.**

**3. §5.8 has already half-decided the key question.** format_spec.md:394-395 carries a
"Settled decisions" bullet reading *"The key stays valid through the grading window…
Grading uses a separate grading allowance."* That is close to, but not identical with, your
third option, and it sits in direct tension with §5.5:322 (access ends when "the round has
ended") and TIER_A:97 ("refuses all requests for the round from the buzzer forward"). The
Phase 3 framing still holds — the *judge clickaround window* is nowhere covered by either
rule — but the decision record is not blank.

---

## Cross-document contradictions

Every side cited to file and line. IDs are stable; Phase 3 references them.

**C-01 — Communication axis has three incompatible definitions.**
`format_spec.md:100-108` — weighted composite of four judge-role rubrics, 30/20/20/30.
`backend/rounds/scoring.py:24-33, 78-84` + `frontend/lib/rounds.ts:174-181` — unweighted
mean of six facet score-types collapsed into two axes; `judge_specialization` is never read.
`TIER_C_OPERATIONS.md:192` — 40% technical own-merit / 30% nontechnical / 30% comparative.
`DATA_MODEL.md:315` already flags the first-vs-second divergence correctly and warns against
silently rewriting either. The third (Tier C) is unflagged anywhere.

**C-02 — Fuzz scoring model: deduction-only vs positive/negative points. — RESOLVED 2026-07-30.**
`format_spec.md:112-118` — "There is no positive reward for passing"; clean contributes 0.
DATA_MODEL's three fuzz entities carried the retired award-points model:
`FuzzTest.points_defended` (positive) / `points_gracefully_handled` / `points_broken`
(negative); `FuzzResult.outcome` as a four-value enum with `points_contributed` "can be
positive, zero, or negative"; `PlayerFuzzInvocation.score_delta` signed. CHANGELOG:24 recorded
the deduction-only change as cascaded to DATA_MODEL; it had not been.

**Fixed as prose, before it became a migration.** `FuzzTest` now carries a single
`penalty : int (>= 0)`; `FuzzResult` carries `penalty_contributed : int (>= 0)` and the three
deduction-only outcomes (`slop_detected` / `clean` / `not_applicable`, the last two scoring
zero but counted apart so Clean Rate and Attack Surface Coverage still work);
`PlayerFuzzInvocation.score_delta` became `slop_added : int (>= 0)`. No model exists for any of
the three (`backend/rounds/models.py` has `Round`, `Submission`, `Score` only), so this cost
nothing today — it would have cost a migration once Stage 5 built from the schema.

**Deliberately left standing**, each noted in place rather than silently changed:
`FuzzResult.override_by_judge` / `override_reason` (**D-18**), `FuzzTest.bundle` listing two
values where the runner ships three, and `intent_dependence` / `applicability_notes`, which
presuppose per-test intent classification the runner spec says the schema should not carry.

**C-03 — Tier scoring asymmetry survives deduction-only.**
`format_spec.md:408` — collegiate advanced categories are "opt-in bonus opportunities with
**positive-only scoring**"; `:412` "moderate asymmetric penalty"; `:416` "full symmetric
scoring."
`format_spec.md:112` — deduction-only; there is no positive scoring to be "positive-only"
about, and no symmetric/asymmetric axis to vary. §6 is pre-rename language.

**C-04 — Token budget's purpose.**
`format_spec.md:316` — "cost control first and an efficiency signal second… Earlier drafts
leaned on… resource calibration as a credentialed skill… It is not, and the format should
not claim it is." `LEAGUE_OPERATIONS.md:129-137` — same, current.
`TIER_A_OPERATIONS.md:73` — "this is part of the **resource calibration credentialing
claim**." `LEAGUE_OPERATIONS.md:97` — "Resource calibration as a measurable skill requires
enforceable token usage measurement (Tier A)" (intra-document).
`format_spec.md:520` — lists "Resource calibration" among the capabilities the format
exercises.
Decision made, propagation incomplete. **Phase 2(c) candidate.**

**C-05 — The 25k per-prompt cap.**
`TIER_A_OPERATIONS.md:73` — "Per-prompt cap of 25k tokens. Both enforced server-side at the
proxy." Stated flat, no caveat.
`format_spec.md:318` — "the 25,000 per-prompt cap is **non-functional for agentic use**,
because a single agentic step already carries more than that in resident context."
`format_spec.md:320` explicitly declines to change the number. TIER_A:73 is the only place
the cap is actually *stated as a rule*, and it carries none of that.

**C-06 — Most Efficient: retired per-round, or live at three tiers?**
`format_spec.md:206` — explicitly under "Awards explicitly retired at per-round level";
"available at Tier A **tournament-level**."
`TIER_A_OPERATIONS.md:208` — listed under "**Available per-round awards** at Tier A."
`TIER_B_OPERATIONS.md:139` — listed under "Available per-round awards," with an
honor-system caveat — at a tier where format_spec says the measurement requirement isn't met.
`TIER_C_OPERATIONS.md:222` — correctly excludes it.

**C-07 — Is AI available during the evaluation/pitch-prep window?**
NO: `format_spec.md:322` — "Substrate access ends at a single server-side gate with two
conditions: the budget is exhausted, or **the round has ended**"; `:326` in-flight cut.
`TIER_A_OPERATIONS.md:97` — "The league proxy refuses all requests for the round **from the
buzzer forward**." `ARCHITECTURE.md:60` — 403 when "the round has ended."
YES: `format_spec.md:60` — "Players retain access to submitted code, README, and (per tier
specifics) **AI assistance** for pitch preparation."
`TIER_A_OPERATIONS.md:105` — "the chat-window AI interface **remains** for pitch preparation…
Players who tokenmaxxed during build have no AI assistance for prep. This is the strategic
tradeoff." `ARCHITECTURE.md:54` — validates "round is in build **OR evaluation** phase (chat
retained during prep)". `ARCHITECTURE.md:96` — "The AI chat interface remains available
during pitch preparation."
Both TIER_A and ARCHITECTURE contradict **themselves**, ~8 and ~36 lines apart respectively.
The root ambiguity is whether "the round has ended" in §5.5 means the buzzer (T+29) or the
round (T+135). **This is a decision, not an edit — see Phase 3.**

**C-08 — Is the 8-player cap a format constraint or a broadcast constraint?**
Format: `format_spec.md:79` — "Standard round size is 8 players **across all tiers**. This
is the format's foundational unit." `format_spec.md:432` — 8 standard at human-judged tiers.
Broadcast: `format_spec.md:85` — "The 8-player limit **at Tier A specifically** is tied to
broadcast and audience purposes… Lower tiers without broadcast have more flexibility."
`TIER_A_OPERATIONS.md:126-131` — four reasons, of which two are broadcast/audience.
`TIER_B_OPERATIONS.md:102` — 8-12, "Tier B's flexibility on broadcast… allows chapters to
scale to 12."
Both readings live in format_spec §3.2, six lines apart. Nothing in code enforces any cap.

**C-09 — Substrate language tiers (§5.4 vs IDEAS).**
`format_spec.md:288-297` — Tier 1: Python, JavaScript, TypeScript, Go. Tier 2: Java, C#,
**Rust, Ruby**.
`IDEAS_FOR_LATER.md:93` — Tier 1: Python, JavaScript, TypeScript, **Java**, Go, **PHP**,
**C#**. `IDEAS_FOR_LATER.md:99` — "*Excluded:* **Rust** (below threshold for junior web
roles…), **Ruby** (declining)."
Java and C# move tier; PHP exists in one document only; Rust and Ruby are simultaneously
maintained-parity and excluded. `IDEAS:101` marks itself as landing in §5.4 post-pilot, so
this is a pending-application drift rather than a pure conflict — but §5.4 is written as
current policy. Compounding: `frontend/app/scoring/page.tsx:175` advertises **Rust** to
players as a supported stack.

**C-10 — Self-containment vs the provided database.**
`format_spec.md:356-368` — permitted persistence is SQLite committed to the submission,
browser storage, in-process memory; "**Not supported:** External databases… cloud-hosted
Postgres."
`frontend/app/scoring/page.tsx:155-156` — "if you need a database, connect to the one **we
provide** at `$DATABASE_URL`. that is the whole contract."
Also `page.tsx:26` — the container has "**no internet access**", which forecloses §5.8's
league-issued inference key at grading time. Both shipped to players in `c869054` today.
**Frontend is the platform session's — reporting only.**

**C-11 — Cross-examination structure.**
`JUDGE_PANEL_RECONCILIATION_PATCH.md:61, 89` — explicitly unresolved; instructs *"Do NOT
overwrite the timing in this patch."*
Model A (one question per judge, rationed): `format_spec.md:64`;
`TIER_A_OPERATIONS.md:109, 236`; `PITCH.md:28`.
Model B (score the player's concision, don't ration): `NONTECH_JUDGE_NOTES.md:173-175`.
**Precision note:** the *clock* is not actually in dispute — both models are 60s pitch +
120s cross-ex. What is unresolved is the **anti-filibuster mechanism**: ration the judges'
questions, or score the player's responsiveness. Separately, `TIER_B_OPERATIONS.md:147`
introduces a **90-second** cross-ex for 3-judge panels, which no other document mentions.

**C-12 — Tier C Extended duration.**
`TIER_C_OPERATIONS.md:21` — "**~135-180 minutes**."
`backend/rounds/services.py:35-46` — `tier_c_extended` ends at `awards_end` = **T+107**,
with the comment "Mirrors Tier A's phase shape minus the Zamboni." Tier A minus the 28-min
Zamboni is 107, not 135-180. The doc and the shipped clock disagree by 28-73 minutes.

**C-13 — DNF: worst outcome, or automatic zero?**
`format_spec.md:143` — "a **DNF**… is ranked below every completed submission regardless of
its trivially-low raw slop: not deploying is the worst outcome, **never a clean zero**."
`format_spec.md:348` — same.
`TIER_C_OPERATIONS.md:103` — "Submissions that don't deploy successfully receive
**automatic zero on fuzz tests**." Under lower-is-better slop, zero is the *best possible
score*. This is the sign-flip rename not fully cascaded.

**C-14 — How many formats are sanctioned?**
`format_spec.md:13, 16` — three format axes (Vibe, Unslop, **Underspecified**); "3 formats ×
5 timers = **15** sanctioned variants." Repeated at `:548`, `IDEAS:33, 43`.
`DATA_MODEL.md:130` — `format : enum (vibe, unslop)`.
`backend/events/models.py:18-20` — `VIBE`, `UNSLOP`. **Underspecified cannot be recorded.**
Notable because §5.5's one real measurement was taken on an *Underspecified* round.

**C-15 — Three technical rubrics, or one shared?**
`format_spec.md:100-105` + `JUDGE_PANEL_RECONCILIATION_PATCH.md:9-18` — four separate
rubrics, weighted 30/20/20/30.
`NONTECH_JUDGE_NOTES.md:11` — "**The three technical judges share ONE rubric.**… Giving them
three separate rubrics would pretend they measure three different traits."
`NONTECH_JUDGE_NOTES.md:187` — aggregation "Not decided," leaning toward
technical-average-plus-nontech.
The file is labelled working-notes, but carries no marker that the panel question was
subsequently locked against it.

**C-16 — When do judges see the slop score?**
`NONTECH_JUDGE_NOTES.md:181` — withhold through pitch and cross-ex, because "the
highest-value signal… only exists if they defend blind"; reveal as a cross-ex beat.
`TIER_A_OPERATIONS.md:103` — during the 18-min evaluation window, "Fuzz runner output gives
quick technical baseline" — i.e. judges hold the slop score before the pitch phase begins at
T+47. `ARCHITECTURE.md:91` — "Results visible to judges in their portal for clickaround
context."
Not in the supplied list; it is a real sequencing conflict.

**C-17 — Award naming: "Most Resilient" vs "Slopless Builder."**
`format_spec.md:196`, `TIER_A:204`, `TIER_B:135`, `TIER_C:217`, `scoring.py:134`
(`most_resilient`) — "Most Resilient," preserved deliberately per `CHANGELOG.md:27`.
`JUDGE_PANEL_RECONCILIATION_PATCH.md:20, 90` — "Slopless Builder."
Interacts with the Slopless Builder denominator question carried forward to Phase 3.

**C-18 — Tester judge override: interface, or none? (intra-document + cross)**
`BUILD_ROADMAP.md:316` (Stage 5 In Scope) — "Tester judge **override interface** for fuzz
applicability decisions."
`BUILD_ROADMAP.md:341` (Stage 5 Success Criteria) — "Tester judges may spot-check for false
positives (slop scoring is automated; **no per-probe override**)."
`format_spec.md:172` — the tester judge "*checks* it (**overriding** an intent-mismatched
false positive)."
`DATA_MODEL.md:255-256` — `FuzzResult.override_by_judge`, `override_reason`.
Three-to-one in favour of override existing; the Success Criteria line is the outlier.

**C-19 — People's Hacklet availability.**
`format_spec.md:198` — one of three standard per-round categorical awards.
`BUILD_ROADMAP.md:223` — "Audience voting (People's Hacklet) — **deferred until broadcast
features**" (Stage 6+). `backend/rounds/scoring.py:133` — same, in code comment.
`TIER_B_OPERATIONS.md:118` and `TIER_C_OPERATIONS.md:219` — available, contingent on
audience presence — at tiers that by definition **have no broadcast**
(`TIER_B:116`, `TIER_C:226`).
The deferral is gated on the wrong dependency: the award needs an *audience*, not a
*broadcast*.

**C-20 — Grace period for Tier C submission.**
`TIER_C_OPERATIONS.md:94-95` — 3-minute grace, T+29 → T+32; failure to submit by T+32 is
disqualification. `TIER_B_OPERATIONS.md:110` — same. `PITCH.md:42` and
`frontend/app/scoring/page.tsx:15` promise it to players.
`backend/rounds/views.py:228-229` — the server rejects **anything past `build_end_at`**, no
grace, no tier branch. The shipped freeze is stricter than every document and both
player-facing surfaces promise.

**C-21 — Submission mechanism, generally.**
`TIER_A:38, 101, 136-142`, `TIER_B:108`, `ARCHITECTURE:86, 94`, `PITCH:27`,
`frontend/app/scoring/page.tsx:15-16` — SCP from workstation, present tense.
`backend/rounds/views.py:212-253` — one portal upload path, no tier gating, for everyone.
BUILD_ROADMAP:328/363/450 gets this right and is the model to propagate from.

**C-22 — Real-time transport.**
`ARCHITECTURE.md:11, 14, 58, 107, 140`, `BUILD_ROADMAP.md:206`,
`DATA_MODEL.md:172` ("via Django signals") — WebSockets/Channels/Redis, present tense.
`backend/hacklet/asgi.py:6` — "Channels (WebSockets) arrives in Stage 3" (Stage 3 shipped
without it). `frontend/components/RoundLive.tsx:101-103` — 5-second polling.
Round status transitions are **derived on read** (`services.py:78-100`), not signal-driven.

---

## Numbers inventory (for Phase 2d)

| Figure | Where | Status | Source |
|---|---|---|---|
| 7.2M tokens / ~85k resident | format_spec:318, CHANGELOG:16 | **MEASURED** | One live 24-min Underspecified round. n=1, off-substrate, DeepSeek V4-**Pro**. Self-labelled at :320. Round not otherwise identified — no date, no event ID |
| 100,000 tokens/round | format_spec:313, TIER_A:73, LEAGUE_OPS:255, PITCH:25 | **ASSUMED** | No derivation recorded anywhere |
| 25,000 per-prompt cap | TIER_A:73 | **ASSUMED** + known non-functional | format_spec:318 |
| 50 fuzz budget points | format_spec:314 | **ASSUMED** | No derivation |
| Timer→budget ladder (50k/100k/150k/200k/300-500k) | IDEAS:33 | **ASSUMED** | Linear extrapolation from the 100k assumption |
| a11y 34.0% → 25.5%; headers 24.4% → 27.5%; web-vitals 10.4%; a11y fires on 73.6% | **fuzz-runner only** | **MEASURED** | v11 corpus, 1,531 scored apps — `fuzz-runner/hacklet_runner/probes.py:3776-3794`. **Not present in any league doc.** The 27.5% figure is correct but is *not written down* — probes.py:3794 misstates it as 24.4% |
| "about 75% of the catalog is public / 25% hidden" | `frontend/app/scoring/page.tsx:166-167` | **ASSUMED** | Shipped to players today. BUILD_ROADMAP:309 says the opposite starting split ("All in public pool initially") |
| LLM judging $5-15/round, $60-180/chapter/yr | TIER_C:210 | **ASSUMED** | Model-priced estimate, no run |
| Fusion latency 15-45s; 90 concurrent requests | TIER_C:183 | **ASSUMED** | Cites "OpenRouter docs", no version/date |
| 5s timeout, TTFB 3s / FCP 5s / INP 5s gates | format_spec:164-166 | **ASSUMED** (rationale given) | Abandonment-threshold reasoning, no run |
| Security ceiling 40 / a11y critical 20 | fuzz-runner only | **MEASURED/derived** | probes.py:3782-3786 |
| Stage timelines (4-6 wk, 8-12 wk, etc.) | BUILD_ROADMAP:139-458 | **ASSUMED** | Self-labelled at :46 |
| Tournament capacity 32 / 20-32 realistic | TIER_A:257, IDEAS:47 | **ASSUMED** (arithmetic) | 12 × 8 ÷ 3; the arithmetic checks out |
| **~9 min per judge per submission** | TIER_A:103 | **WRONG** | 18 min ÷ 8 submissions = **2.25 min**. Phase 2(b) |
| 31% / 81% / $9M / 95% (industry) | format_spec:546, IDEAS:127 | **Cited external** | Harness 2026, HBR Sept 2025, MIT NANDA. Dated, with a fact-check caveat at IDEAS:127. Leave |
| ~78% wrappers / ~92% YC / ~88% prior | format_spec:371, 375 | **Cited external** | No source named in-doc — weakest of the external citations |
| ~70-85% of CS undergrads use chat-window | IDEAS:125, format_spec:513 | **ASSUMED** | No source |

---

## Phase 2 readiness

**Clear to edit** (no uncommitted changes, none modified within the hour; re-verify at
edit time): all thirteen docs.

**Do not edit:** `FUZZ_RUNNER_SPEC.md` and everything under `fuzz-runner/` (fuzzer
session). `backend/`, `frontend/` (platform session). Four findings above touch
platform-session files — C-10, C-20, and the SCP/Rust items in C-21/C-09, all in
`frontend/app/scoring/page.tsx`, shipped in `c869054` today. **Reported, not edited.**

**Phase 2(b), the one arithmetic fix:** TIER_A_OPERATIONS.md:103. Four permanent
specialized roles means every judge scores every player, so each judge covers 8 submissions
in 18 minutes — **~2.25 minutes each**, not ~9. (The ~9 figure is 18 × 4 ÷ 8, which is the
number you get by treating the four judges as *dividing* the field, i.e. two submissions
each — which the permanent-role structure forbids.) The 18-minute phase duration is BUILT
and verified at `services.py:19`; it does not move.

**Phase 2(c) propagation candidates** — decisions already made, applied unevenly:
C-04 (token budget purpose → TIER_A:73, LEAGUE_OPS:97, format_spec:520);
C-02 (deduction-only → DATA_MODEL FuzzTest/FuzzResult/PlayerFuzzInvocation) — **done 2026-07-30**;
C-13 (DNF ≠ zero → TIER_C:103);
C-03 (deduction-only → format_spec §6 tier scoring language);
C-21/C-22 (tense-marking only — the underlying decisions are not in dispute);
BUILD_ROADMAP:162 ChapterMembership → ChapterStaff; BUILD_ROADMAP:207/231 git → zip.

**Not Phase 2** — these need a call and are carried to Phase 3: C-01, C-06, C-07, C-08,
C-09, C-11, C-12, C-14, C-15, C-16, C-17, C-18, C-19, C-20.

---

## Phase 2 — applied 2026-07-28

Mechanical only. No contradiction was resolved by choosing a side.

- **Terminology.** *Build end* (build time is up) and *round end* (round is over) are now
  distinct terms, defined canonically in format_spec §5.5. The gate condition and the 403
  response body were corrected in format_spec, ARCHITECTURE, BUILD_ROADMAP and CHANGELOG.
- **C-07 reconciled to one question.** The two self-contradictions (TIER_A, ARCHITECTURE) were
  vocabulary plus one real policy question. The vocabulary is fixed; the policy question is
  stated once as an OPEN note in format_spec §5.5, and all six affected passages are marked
  CONTESTED and point at it. Not decided.
- **ILLUSTRATIVE.** Applied to all eight timing blocks across TIER_A (3), TIER_B (1), TIER_C
  (2), ARCHITECTURE (1), with the canonical definition in format_spec §3.
- **Arithmetic.** TIER_A §4: ~9 min → **~2.25 min** per submission per judge. Phase duration
  unchanged.
- **Status markers.** 112 section markers across the seven structural docs; whole-document
  status notes on the six others; a reading legend on each.
- **Propagation.** Token-budget reframe → TIER_A §3, LEAGUE_OPS §4, format_spec §10. DNF ≠ zero
  → TIER_C §6. Deduction-only → format_spec §6 (marked SUPERSEDED, not rewritten — the rewrite
  contains a decision). Stale names/paths → BUILD_ROADMAP Stages 1–3.
- **Citations.** Untraceable figures marked ASSUMED in place: 100k tokens, 50 fuzz points, the
  timer→budget ladder, LLM judging cost and latency, the 5s/3s speed thresholds, the wrapper
  and YC percentages, the CS-undergrad chat share. The 7.2M measurement is marked MEASURED with
  an outstanding run identification. **No v11 corpus value was written into any doc.**
- **C-11.** Clock marked SETTLED (60s + 120s); mechanism marked OPEN with both candidates
  stated. TIER_B's 90-second window marked UNCORROBORATED.

**Deliberately not touched:** C-20 (the grace period — code vs four documents, still a call);
`frontend/`, `backend/`, `fuzz-runner/`, `FUZZ_RUNNER_SPEC.md`.

**Closed after this audit (2026-07-30, platform session):** **C-02** — DATA_MODEL's three fuzz
entities rewritten in deduction-only terms while they were still prose. See the C-02 entry
above for what was left standing and why.
