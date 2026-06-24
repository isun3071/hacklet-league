# Tier A Operations

*Operational template for HackLet Tier A events. For tier philosophy and verification, see LEAGUE_OPERATIONS.md §4. For format mechanics and scoring, see format_spec.md. For Tier B and Tier C operational profiles, see TIER_B_OPERATIONS.md and TIER_C_OPERATIONS.md.*

---

## 1. Tier A Identity

Tier A is the **credentialing-grade tier** of HackLet operations. Tier A chapters have demonstrated infrastructure that makes faking results structurally hard, which is what makes their wins reliable credentials in the labor market. Tier A is also the **integrity-maximizing end** of the freedom-integrity tradeoff (LEAGUE_OPERATIONS.md §4): Tier A trades player workflow freedom for structural equality, anti-cheating enforcement, reproducible measurement, and market-meaningful credentials.

Tier A events contribute to **global league rankings**. Wins propagate through the federated platform as durable credentialing artifacts that employers can verify and interpret. The infrastructure investment required for Tier A operations is substantial; the credentialing payoff justifies the investment because Tier A credentials carry market signal that bounded credentials at lower tiers cannot match.

Tier A is where HackLet operates as a **distinct competitive institution** comparable to FIDE chess or FMWC financial modeling — independent of hackathon ecosystem framing, with its own credentialing claims, its own broadcast production, its own esports identity.

## 2. Infrastructure Requirements

Tier A chapters must demonstrate the following infrastructure to qualify for verification:

**Workstation control**:
- RMM-controlled workstations with verified standardized configuration
- Master image deployment for workstation consistency across players
- Hardware capacity to run the league-supplied VSCodium configuration, browser tab to portal, build tools, deployment infrastructure
- Per-player ephemeral Unix accounts created at round opening and removed via `userdel -r` at round end (Zamboni Period)

**Network isolation**:
- Network firewall with allowlist to league infrastructure only (no general internet, no external AI services)
- Outbound restricted to league portal endpoints, package mirror, and submission infrastructure
- DNS resolution restricted to league-managed endpoints
- No bypass paths (no shared wifi, no personal hotspots, no LAN-out)

**League-hosted AI substrate access** (see §3):
- Workstation browser tab locked to hackletleague.com chat-window interface
- Signed league-built VSCodium extension for agent interface (when deployed, Stage 12+ per BUILD_ROADMAP.md)
- All AI calls proxied through league infrastructure with audit logging
- Token budgets enforced server-side

**Submission capture**:
- League daemon on each workstation captures submissions via SCP at code freeze (T+29:00) to service-account path `/opt/hacklet/submissions/$EVENT_ID/$ROUND_ID/$USER/`
- Submissions automatic at freeze; no player action required
- Service-account credentials managed at the workstation infrastructure level, not exposed to player accounts

**Broadcast infrastructure** (see §6):
- Workstation streams to broadcast infrastructure with consent (visible to players via screen-share indicator)
- Multi-camera setup for venue
- Production-grade audio for commentary and pitch capture
- Scoreboard overlay infrastructure for live results display

**Judge corps**:
- Minimum 3 members per round, including at least one tester judge and one UX designer judge (see format_spec.md §3 for judge roles)
- Stakeholder judge role available when format design absorbs it (see IDEAS_FOR_LATER.md)
- Judge corps calibration through training events
- Judge availability for full round duration (135-min commitment per round)

**Venue and operational support**:
- Documented venue with appropriate physical setup (workstation seating, judge stations, audience accommodation, broadcast booth)
- Chapter admin team trained on league operations
- Pre-event setup checklist execution and verification

## 3. AI Substrate at Tier A

The league hosts AI substrate at Tier A through the unified-substrate model (see format_spec.md §5.3):

**Chat-window interface**: browser tab from each workstation to hackletleague.com chat window. The interface speaks the league's OpenAI-compatible chat completions endpoint (`/api/v1/chat/completions`). Players access this throughout the build phase and during pitch preparation (with reduced functionality at freeze — see §5).

**In-IDE agent interface** (when deployed, Stage 12+): league-built signed VSCodium extension locked to hackletleague.com. Provides chat sidebar plus accept/reject UI for agent-proposed file changes, modeled on Cline/Roo Code patterns. Talks to the same OpenAI-compatible endpoint with shared per-player token budget.

**Unified token budget**: chat-window and agent interface share the same per-player token budget for the round. Budget is enforced server-side at the proxy. A player using 5 chat windows + the agent has 1× budget split across however many interfaces they use, not 6× budget. The unification prevents tool-stacking advantage.

**Season-pinned model**: each season specifies a single AI model serving as substrate for all Tier A events that season. Season 1 substrate is **DeepSeek V4 Flash** accessed through OpenRouter, with no league-injected system prompt beyond standard production deployment. Substrate equality holds across all Tier A players because every player faces the same model with the same available parameters under the same enforced budget.

**Audit logging**: every AI call is logged at the proxy with player attribution, timestamp, token counts, and prompt content (for post-event review and dispute resolution). The audit trail is part of the credentialing integrity infrastructure — disputes about budget consumption or substrate behavior can be resolved through audit log review.

**Token budgets enforced**: per-player token budget per round (default 100k for Sprint timer, scales with timer per format_spec.md §1). Per-prompt cap of 25k tokens. Both enforced server-side at the proxy. Players who exhaust budget have no AI access remaining for the round; this is part of the resource calibration credentialing claim.

## 4. Round Timing — Tier A Standard Profile (135 Minutes)

The Tier A round profile is the format's full operational expression with production rhythm preserved:

```
T+0:00   → T+5:00    (5 min)  — Opening ceremony with broadcast intro
T+5:00   → T+29:00  (24 min)  — Build phase (Sprint timer)
T+29:00  → T+47:00  (18 min)  — Concurrent evaluation + pitch preparation
T+47:00  → T+75:00  (28 min)  — Pitch + cross-examination (8 players × 3.5 min)
T+75:00  → T+93:00  (18 min)  — Deliberation + audience voting
T+93:00  → T+107:00 (14 min)  — Award reveal + closing ceremony
T+107:00 → T+135:00 (28 min)  — Zamboni Period (workstation reset)
─────────────────────────────────────────────────
135 minutes per round
```

### Phase Details

**Opening ceremony (5 min)**: host welcomes audience, frames the round (which variant, which tier, what's at stake, where this fits in the season), introduces contestants individually, confirms readiness. Players seated at workstations but workstations remain locked. Production rhythm establishes audience engagement before competition begins.

**Build phase (24 min)**: at T+5:00 the central system simultaneously unlocks all workstations and reveals the round prompt. Players have 24 minutes to construct a web application of their choice. No required features, no mandated architectures. Players direct AI substrate through chat-window and (when available) agent interface. Local fuzz invocations are intelligence-gathering only; central catalog testing happens at freeze (see §7).

At T+29:00, code freeze takes effect simultaneously. The network cuts for code changes. All build activity ceases — no further coding, no agent edits via the in-IDE interface, no fuzz invocations against the workstation. AI responses mid-generation are truncated; partial code changes roll back to pre-prompt state. The submission is what existed at freeze.

**Concurrent evaluation + pitch preparation (18 min)**: judges and players work in parallel for 18 minutes:

*Code submission and central fuzzing*: at freeze each workstation copies its final code state to league infrastructure via SCP. League infrastructure deploys each submission in an ephemeral container with assigned port, executes the full authoritative fuzz catalog (both public and hidden pools). Central testing scores submissions; local fuzz during build was intelligence-gathering only.

*Judges evaluate submissions*: judges interact with each submission live in their portals while the fuzz runner completes work. The panel includes specialized roles (tester judge with override capability, UX designer with professional design expertise, general engineering judges). With 18 minutes for 8 submissions across 4 judges, each judge has ~9 minutes per submission for substantive evaluation. Fuzz runner output gives quick technical baseline; clickaround surfaces what automation can't measure.

*Players prepare pitches*: code files become read-only at freeze; players retain access to submitted code, README, and the chat-window AI interface for pitch preparation. Agent-interface edit capabilities are disabled at freeze; chat-window AI assistance remains for pitch planning and anticipating cross-examination. Players who tokenmaxxed during build have no AI assistance for prep. This is the strategic tradeoff. Players also author **PITCH.md** as part of pitch preparation, though at Tier A the live pitch + cross-ex is the primary credentialing dimension (see §8).

**Pitch + cross-examination (28 min for 8 players)**: each player presents in sequence:
- 60 seconds of pitch — what they built, key choices, what makes their submission distinctive
- 120 seconds of cross-examination — judges ask questions in turn, each judge limited to one substantive question per player (four judges, four questions, ~30 seconds per question including answer); verbose answers cost remaining slots
- 30 seconds of transition — next player gets situated, audience and judges briefly reset

At 3.5 minutes per player × 8 players = 28 minutes. Same-archetype submissions (multiple players who built similar applications) pitch back-to-back to enable direct comparison and require explicit differentiation arguments.

The live performance dimension of communication is the format's most distinctive credentialing element. Cross-examination tests defense under live questioning that LLM judges cannot replicate. This is why Tier A preserves live pitch + cross-ex while the Tier C MVR substitutes LLM-judged written evaluation (see TIER_C_OPERATIONS.md §8).

**Deliberation + audience voting (18 min)**: judges enter explicit deliberation. They compare what they witnessed during pitches against clickaround observations, re-visit submissions with player framing context, read README content more carefully, score across all dimensions, finalize categorical award nominees and Best Overall composite rankings.

Concurrent with judge deliberation, **audience votes** for People's Hacklet through the player portal on their own devices. Audience voting is open during the 18-min deliberation window; closes at T+93:00.

**Award reveal + closing ceremony (14 min)**: ceremonial reveal of categorical awards (Most Resilient, Best Communicator, People's Hacklet) followed by Best Overall reveal. Production rhythm supports audience reaction, brief player commentary, broadcast cuts. Award reveal is theatrical content that audience-design philosophy requires; the 14-min window allocates time for ceremony rather than just announcement.

**Zamboni Period (28 min)**: workstation reset for next round. League daemon executes `userdel -r` for each player's ephemeral account, removing all home directory content. Workstations rebooted to master image. Network state reset. Per-player accounts re-provisioned for next round. Audience break period; production cuts to commentary or pre-recorded content.

### Round Sizing

**8 players standard**. The 8-player limit serves multiple Tier A operational concerns:
- Workstation capacity (8 controlled workstations is tractable infrastructure investment)
- Audience visual coherence (8 streams on broadcast overlay manageable)
- Judge cognitive load (4 judges × 8 submissions = bounded eval workload)
- Pitch + cross-ex timing (28 min fits the format clock with 3.5 min per player)

6-12 is the acceptable operational range; 12 is the structural maximum. Tier A events typically run at exactly 8 because broadcast production assumes it.

## 5. Submission Mechanism

**SCP from workstation at code freeze**. At Tier A, each workstation runs a league daemon that copies the player's working directory via SCP to league infrastructure at `/opt/hacklet/submissions/$EVENT_ID/$ROUND_ID/$USER/` at T+29:00 simultaneously across all workstations.

The submission daemon runs as a **service account** with pre-configured SCP credentials targeting the central path. The player's ephemeral Unix account is just the source filesystem to copy *from*. The player's account doesn't accumulate git credentials, doesn't maintain long-lived repository state, and is deleted via `userdel -r` at Zamboni Period.

**Network configuration requirements**: chapter firewall must allow workstation outbound SCP to the league submission endpoint. This is part of the firewall allowlist (LEAGUE infrastructure only; submission endpoint is a league endpoint).

**No player action at freeze**. Players don't manually submit. Submission is automatic. Players who didn't get their working code into a deployable state by T+29:00 have whatever was in their working directory captured as their submission. The fuzz catalog evaluates what was submitted.

This differs from Tier C portal upload + grace period (see TIER_C_OPERATIONS.md §6) because Tier A's controlled workstations enable automatic capture; Tier C's BYOD substrate requires player-initiated upload with grace allowance for network latency.

## 6. Broadcast Architecture

Tier A is the **only tier with live broadcast production**. The broadcast infrastructure requires controlled workstations that can be screen-shared without compromising player privacy — a constraint that BYOD substrates (Tier C) preclude entirely and that Tier B's optional workstation hosting doesn't necessarily provide.

### Broadcast Components

**Multi-stream workstation capture**: each player's workstation streams to the broadcast infrastructure. Players consent to screen-share as part of Tier A participation (consent obtained at registration; visible screen-share indicators on workstations). Workstation streams display code editor, chat-window, and (when available) agent interface activity.

**Multi-camera venue coverage**: cameras capture player faces during build phase, judge panel during evaluation, pitch presentations, audience reactions during cross-examination, award reveal moments. Production switching between camera angles drives narrative rhythm.

**Commentator integration**: commentators provide live narration of build phase strategy, pitch performance analysis, cross-examination dynamics. Commentary requires technical background plus broadcast skill; commentator development is part of league maturation.

**Scoreboard overlay**: live results display during deliberation, dramatic categorical reveals during award ceremony, Best Overall reveal as broadcast climax. Scoreboard overlay infrastructure is part of broadcast production stack.

**Replay capability**: notable moments (clever defensive choices during build, sharp cross-examination exchanges, dramatic award reveals) capturable for highlight content and post-event coverage.

### Production Rhythm

The 135-min Tier A round timing is designed around broadcast narrative arcs:
- **Opening creates investment** (audience meets contestants, frames the round)
- **Build phase generates strategic tension** (parallel multi-stream coverage shows different approaches)
- **Eval phase is breathing room** (commentary fills the 18-min concurrent window, judges visible at work)
- **Pitch + cross-ex is the centerpiece** (28 min of structured live performance, each player gets focus time)
- **Deliberation is suspense** (audience voting visible, judges visibly deliberating, anticipation builds)
- **Award reveal is the climax** (categorical reveals build to Best Overall, audience reaction captured)

The 14-min award reveal window is **substantive broadcast theater** that lower tiers can't justify because lower tiers don't have broadcast production. At Tier A, the ceremony is load-bearing for audience engagement.

### Privacy and Consent

Players consent to broadcast as Tier A participation requirement. Broadcast content includes:
- Workstation screen captures during build phase
- Player faces during build, pitch, cross-examination, deliberation
- Audio of pitch presentations and cross-examination exchanges
- Audience reactions and commentary

Broadcast does **not** include:
- Personal devices (Tier A uses controlled workstations, not BYOD)
- Off-camera conversations between players
- Player faces during private moments (bathroom breaks, Zamboni period downtime)

Players who don't consent to broadcast can't participate in Tier A events. This is a substantive trade — the credentialing strength of Tier A depends on broadcast-grade transparency. Players seeking competitive engagement without broadcast can use Tier B/C events.

## 7. Fuzz Catalog Evaluation

The fuzz catalog operates at **full strength** at Tier A (and at every tier — the catalog is tier-agnostic per LEAGUE_OPERATIONS.md §4). The Tier A operational difference is that submission infrastructure enables more thorough catalog execution because submissions arrive in known-format from controlled workstations.

**Catalog scope**: both public and hidden pools execute against each Tier A submission. The hidden pool provides additional adversarial signal that players didn't have access to during build. Hidden pool composition evolves through catalog development discipline (see FUZZ_RUNNER_SPEC.md).

**Attack surface enumeration**: per IDEAS_FOR_LATER.md, the catalog includes endpoint enumeration phase (dirbuster/ffuf-pattern wordlist probing) discovering each submission's actual interaction surface. Probes target discovered endpoints, catching forgotten debug routes, exposed admin panels, missing auth boundaries, framework defaults left exposed.

**Catalog evolution**: post-event AI agent analysis runs against published Tier A submissions identifying novel vulnerability patterns. Findings curated by league catalog maintainers into new permanent catalog probes. Catalog matures through Tier A operational data feedback (see IDEAS_FOR_LATER.md on AI pentest agent for catalog development).

## 8. Scoring and Categorical Awards

Per format_spec.md §4, Tier A operates the full scoring framework:

**Available per-round awards** at Tier A:
- **Most Resilient**: lowest Slop Score
- **Best Communicator**: highest Communication Score (live pitch + cross-ex evaluation, human judges)
- **People's Hacklet**: highest audience vote
- **Best Overall**: composite rank with progressive tiebreakers (lowest rank sum → smallest differential → best Fuzz Rank → best Communication Rank → co-Champions)
- **Most Efficient**: lowest token usage among top half Best Overall standings (Tier A only — requires enforced token budget measurement)

**Communication Score** at Tier A captures **live performance** including pitch quality and cross-examination defense under live questioning. This is the format's most distinctive credentialing dimension. PITCH.md may be authored during pitch prep as preparation material; the live performance is what judges evaluate.

**Tournament-level categoricals** at multi-day Tier A tournaments include:
- Tournament Best Overall, Tournament Most Resilient, Tournament Best Communicator (cumulative across rounds)
- Best UX/UI (judge-aggregated across rounds)
- Most Novel (judge-aggregated across rounds, "consistently novel approach across tournament")
- Most Efficient (Tier A only, cumulative token discipline)
- Iron Player (maximum allowed rounds participated)
- Comeback Player (most improved early-to-late qualifying)

See §10 for multi-day tournament structure.

## 9. Live Judging Protocol

Tier A uses **human judge corps** with calibrated panel roles. LLM judging is not used at Tier A because the live performance dimension (pitch + cross-ex) requires human evaluators capable of real-time question generation, body-language reading, follow-up probing.

**Judge panel composition**:
- **Tester judge**: operates portal displaying automated test applicability decisions, with override capability for cases where automated detection missed or misidentified features
- **UX designer judge**: brings professional design expertise to UX/UI evaluation; assesses user experience, interaction quality, visual hierarchy, intuitive navigation
- **General engineering judges**: assess creative coherence, derived feature correctness, technical execution, documentation quality
- **Stakeholder judge** (when format absorbs this role per IDEAS_FOR_LATER.md): non-technical stakeholder perspective during cross-examination

**Judge calibration**: judge corps participates in pre-event calibration sessions reviewing exemplar submissions across scoring dimensions. Calibration produces shared evaluation standards reducing inter-judge variance. Calibration discipline is part of Tier A chapter operational maturity.

**Cross-examination structure**: each judge limited to one substantive question per player during the 120-sec cross-ex window. Four judges produce four questions. Players manage answer length strategically — verbose answers cost remaining question slots. Cross-examination tests defense under live pressure, which is the dimension human judging captures that LLM judging cannot.

## 10. Multi-Day Tournament Template

Tier A regional and championship events use multi-day tournament structure (per IDEAS_FOR_LATER.md "Multi-day Tier A tournament template"). The full template:

### Qualifying Days (Days 1-2)

12 rounds across 2 days × 2 concurrent pods. Schedule per day:

```
9:00-9:25   — Opening / recap ceremony
9:30-12:00  — Qualifier rounds 1+2 (concurrent in different pods)
12:00-13:00 — Lunch (includes Zamboni reset)
13:00-15:30 — Qualifier rounds 3+4 (concurrent)
15:30-18:00 — Qualifier rounds 5+6 (concurrent)
18:00+      — Networking, dinner, decompression
```

End of Day 2 (~19:00): qualifier announcement, snake-draft pod assignment for Day 3, alternates notification.

**Capacity arithmetic**: 12 rounds × 8 players ÷ 3 minimum participation = 32 theoretical capacity; 20-32 realistic operational capacity.

**Participation threshold**: N/4 with floor of 2. For 12 qualifying rounds, threshold = 3. Players who participate in fewer than 3 rounds are ineligible for qualifying ranking.

**Qualifying score**: average across participated rounds. Average is the right answer (not median, not trimmed mean) because it's simple to broadcast, rewards consistency, and the participation threshold protects against single-disaster-round catastrophe.

### Day 3 Championship Structure

Top 16 qualifiers advance to Day 3. Ranks 17-24 designated as alternates.

```
9:00-9:25   — Opening / finals ceremony
9:30-12:00  — Concurrent semifinal rounds (snake-draft pod composition)
12:00-13:00 — Lunch + top-8 announcement (top 4 from each pod advance)
13:30-16:00 — Finals round (single judge panel scores all 8 finalists)
16:00-16:30 — Score finalization
16:30-17:00 — Award ceremony + closing
```

### Snake Draft Pod Composition

Day 3 semifinals split 16 qualifiers into 2 pods of 8 via **snake draft on qualifying rank** (pod A picks rank 1, pod B picks 2, pod B picks 3, pod A picks 4, etc.). Snake draft produces exact total-seeding-strength balance across pods.

Snake draft is **universal across tournament tiers** because the player UX cost is absorbed by the platform: players see "Report to Pod A, Workstation 3, 9:30 AM" in their portal without needing to understand the algorithm. The platform handles assignment; players see the assignment.

### Within-Pod Top 4 Advancement

Each pod's top 4 advance to finals (8 total finalists from 16 semifinalists). Within-pod ranking only — judge calibration variance across pods doesn't affect advancement because comparison is within-pod. This **handles judge calibration variance structurally** without requiring sequential judging.

### Finals Round

Top 8 finalists compete in a single championship round with **single judge panel scoring all 8 finalists**. Single-panel finals preserves cross-finalist fairness; this is the credentialing climax of the tournament.

### Two-Leaderboard Model

The tournament maintains two parallel leaderboards:

**Qualifier leaderboard** (32 players): accumulates scores across all participated rounds (qualifying + semifinals + finals for advancers), averaged. Determines tournament-level categorical awards including Tournament Best Overall.

**Finals leaderboard** (8 players): scores the finals round only. Determines finals-specific awards including Finals Best Overall.

The two leaderboards can produce **different Best Overall winners**:
- Consistent across-tournament performer wins Tournament Best Overall (sustained excellence)
- Finals-peak performer wins Finals Best Overall (peak under championship pressure)
- Same player wins both when capability is unified across both dimensions
- Different winners produces richer credentialing signal (sustained vs peak capability distinguishable)

### Tag Credentialing Structure

Player profiles accumulate tournament credentials at multiple levels:
- **Champion** (1 player): Finals Best Overall winner
- **Finalist** (8 players): made finals
- **Day 3 Qualifier** (16 players total): made Day 3, didn't advance to finals if in remaining 8
- **Tournament Participant**: competed in qualifying, didn't advance

Plus categorical award tags stack independently. The information-richness lets employers interpret credentials specifically.

### Alternates Pool (Ranks 17-24)

Top 24 of starting field designated as either Qualifier (top 16) or Alternate (ranks 17-24). Alternates report to venue 8:30 AM Day 3, designated specific qualifier they'd replace. Activation cutoff 9:15 AM. Substitution in place without recomputing snake (minor pod-balance impact structurally acceptable for late-stage changes).

Non-activated alternates released with audience recognition and "Tournament Alternate" credential tag. Compensation: free venue access, food + beverages, "Tournament Alternate" tag for player profile.

### No-Show Policy

Four categories with proportionate consequences:

- **Excused absences** (documented emergency, illness, transportation crisis): no penalty, retains "Qualified, withdrew due to documented emergency" tag, eligible for future events. Documentation within 7 days post-event, chapter admin good-faith review, superadmin appeal path.
- **Communicated withdrawal** (notified by 8:00 AM Day 3, doesn't meet excused criteria): small persistent rating penalty, "Qualified, withdrew" tag, eligible for future events.
- **No-call no-show** (no appearance, no communication): substantial rating penalty, "Qualified but disqualified" public tag, one-event chapter cooldown (lifts after one event elapses). Repeat no-call no-shows: extended cooldown, chapter membership review.
- **Late arrival**: 10-minute grace from round start with reduced build time; after grace, treated as no-show for that round but eligible for later rounds.

Public visibility tiered — excused absences private, communicated withdrawals private with small mark, no-call no-shows publicly visible on tournament record, repeat patterns publicly aggregated.

### Platform Absorbs Operational Complexity

The platform handles snake-draft pod composition, workstation assignment within pods (randomized for fairness), judge panel composition by available corps, substitution logic, schedule notifications, and credential tag assignment. Chapter operators configure tournament parameters (rounds, pods, judge corps, variant); the platform produces operational artifacts. Recurring HackLet design philosophy: complexity the platform absorbs is complexity that doesn't burden participants.

### Judge Corps Planning

Multi-day tournament demands a corps of 6-8 senior judges with rotation across pods to manage cognitive fatigue. Concurrent semifinal pods need separate panels (4 judges each). Finals uses a single panel of 4, ideally fresh from the morning or composed from rested rotators.

## 11. Anti-Cheating Enforcement

Tier A integrity infrastructure makes cheating **structurally hard**:

**Workstation isolation**: firewall allowlist prevents external AI access. The only AI substrate available is the league-hosted endpoint. Players cannot use Cursor, GitHub Copilot, ChatGPT, or any external AI from workstations.

**Audit trail**: every AI call logged at the proxy. Post-event review can detect anomalous usage patterns. Disputes resolvable through audit log analysis.

**Ephemeral accounts**: per-player Unix accounts created at round start, removed at Zamboni Period via `userdel -r`. No long-term state accumulation; no opportunity to pre-stage code, configurations, or tooling.

**Workstation streaming**: workstation activity visible to broadcast infrastructure (player consent at registration). Manual review of recorded streams catches anomalies broadcast viewers might miss in real time.

**RMM-controlled configuration**: workstations standardized through master image deployment. No custom configurations, no personal tooling, no opportunity for player-specific advantages.

**Judge panel diversity**: multiple judges with different specializations reduce single-judge bias. Cross-examination requires defending engineering reasoning that pre-staged code can't address.

These layers compose. Defeating one isn't sufficient; cheating would require defeating multiple structural barriers. The compound infrastructure produces the credentialing integrity that makes Tier A credentials market-meaningful.

## 12. Credentialing Claims

Tier A wins carry **substantial market signal**:

- **Global league ranking contribution**: Tier A wins propagate through federated platform to global rankings
- **Substrate equality verified**: all players faced the same model with same available parameters under same enforced budget
- **All AI-complementary skill clusters tested**: verification reflex, defensive depth, AI direction, resource calibration, technical communication under pressure, deployment hygiene
- **Anti-cheating structurally enforced**: wins reliable signal to employers because the integrity infrastructure makes faking structurally hard
- **Multi-time multi-format wins become substantively rare credentials**: champions across multiple Tier A events or across multiple format variants demonstrate sustained credentialing-grade capability

**Credential interpretation for employers**:
- *Hiring for elite engineering capability*: Tier A wins demonstrate the strongest signal HackLet provides
- *Hiring for AI-augmented engineering capability under pressure*: Tier A wins specifically credential AI direction skill under time compression with verification reflex
- *Hiring for senior or specialized roles*: Tier A tournament wins (multi-day, multi-round, cumulative-grade) demonstrate sustained capability appropriate for senior consideration

## 13. Chapter Variant Portfolio

Tier A chapters' variant scope is determined by their verification application. Specialization is **common but not required**: chapters often concentrate Tier A verification on one variant or related variant family for operational efficiency. Chapters with substantial operational capacity may apply for verification across multiple variants over time.

The 1-event-1-format rule (per format_spec.md §7.1) means each event commits to one variant. Chapters host many events across varied formats over their lifetime. Cross-chapter coordination produces cross-format championships.

Initial Tier A chapters pick variants matching community demand (BU community probably wants Vibe Sprint based on cyber/AI club's existing comfort with chat-window AI workflows). Chapters expand verification as infrastructure and operational experience grow.

## 14. Strategic Timing

First Tier A chapter verification is **Year 3+ territory** in the league's strategic sequencing (see TIER_C_OPERATIONS.md §14). Tier A infrastructure investment is justified only after Tier C MVR operations have demonstrated sustained operational viability across multiple chapters over 1-3 years.

Tier A operations don't start at the same time as Tier C. The sequencing is deliberate: Tier C validates the format and builds the chapter ecosystem; Tier A scaling investment depends on that validation. Building Tier A first without Tier C validation would be premature optimization. The MVR's bounded credentialing claims free the league to use Tier C operations as R&D environment; mature credentialing-grade claims at Tier A justify substantial infrastructure investment because Tier C operations have de-risked the format.
