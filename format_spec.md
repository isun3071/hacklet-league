# HackLet League — Format Specification

*Executive summary of the official rules. The complete rulebook addresses every edge case in detail; this document establishes the format's identity, mechanics, and core operating principles.*

---

## 1. What HackLet League Is

**In one sentence: hackathon, but minutes instead of hours, with a cheering audience.**

HackLet is an institution that runs competitive formats, not a single immutable format. Format names follow a two-axis structure: **HackLet {Format} {Timer}**.

- **Format axis** — what the player does. **Vibe** (build an application from scratch under AI assistance) or **Unslop** (remediate a deliberately-broken application generated server-side and distributed to all players at round opening).
- **Timer axis** — how long the build phase runs. **XP** (12 min), **Sprint** (24 min), **Scrum** (36 min), **Agile** (48 min), **Waterfall** (72-96 min). Token budgets scale with the timer.

2 formats × 5 timers = **10 sanctioned variants** in the operational matrix.

The foundational format is **HackLet Vibe Sprint** — 24-minute build phase from scratch. It is the format described in detail by this document and the one the BU pilot operates. **HackLet Unslop Sprint** is documented as the canonical second format and is introduced once Vibe is operationally stable. Longer and shorter timer controls follow as the league matures. Future format introductions follow the same naming convention without renaming what came before.

**The league does not legislate AI-interaction style.** Where the league hosts AI substrate (Tier B and Tier A), players are served *both* a chat-window interface and an in-IDE agent interface from the same league-controlled infrastructure with a *unified token budget* across all interfaces. Players choose whatever combination of chat-style brainstorming and agent-style execution fits their workflow. This matches how real engineering with AI actually happens: fluid switching between modes, with strategic discipline coming from how the player navigates the substrate rather than which mode the format forces them into. Where the league does not host AI substrate (Tier C, BYOD), players use whatever AI tools they choose. The "Relationship" axis that earlier drafts of the format spec used to distinguish Classical from Agentic has been retired in favor of the unified-substrate model, which is more honest to the format's "we don't legislate how you use AI" thesis (§10).

HackLet Vibe Sprint is a competitive format for AI-assisted technical building under extreme time compression. Players have 24 minutes to construct, document, and defend a web application, working alone on a locked-down workstation (Tier A/B) or their own laptop (Tier C) with sanctioned AI substrate access. Submissions are evaluated through automated adversarial testing, judge inspection, and live questioning. Multi-axis scoring produces categorical awards alongside an overall composite ranking.

The format borrows time-compression from bullet chess, multi-axis scoring from gymnastics and decathlon, regional feeder structure from CTWC, and tier organization from FMWC. What it adds is novel: systematic adversarial testing of AI-assisted submissions under tournament conditions. The 24-minute build duration deliberately parallels the 24-hour hackathon, positioning hacklet as a compressed-format descendant of hackathon culture rather than a replacement for it.

The name **Vibe** is deliberate. "Vibe coding" entered industry vocabulary in 2025 as a complaint — engineers directing AI rapidly without verification, producing slop at scale. HackLet reclaims the term. Vibe coding done by skilled engineers under proper conditions is real professional capability. HackLet Vibe champions demonstrate vibe coding *with* verification reflex, *with* defensive depth, *without* producing slop. The format name stakes territory in the industry's vocabulary dispute: vibe coding is a skill, and the league credentials those who practice it well.

A complete round cycle runs anywhere from ~60 minutes (the Tier C MVR) to ~135 minutes (the full Tier A broadcast profile), with the 24-minute build forming the competitive core. This structure makes multi-round day events practical for regional and championship competition while preserving broadcast quality through proper time allocation for evaluation, pitches, deliberation, and award reveals. Human-judged rounds are bounded at 8 players standard (6-12 range, 12 maximum); LLM-judged Tier C cohorts scale higher (§3.2). Events host one or more rounds; regional and championship events typically run multi-round days.

HackLet League is built for engineers who want to develop and demonstrate the cluster of skills AI-assisted defensive coding requires: prompting fluency, verification reflex, resource calibration, and defensive depth. It is not a beginner-friendly format. It assumes participants have working knowledge of web development and at least introductory familiarity with security concepts. Players who do not yet have those foundations are welcome to attend events as spectators and participate when their preparation matches the format's expectations.

## 2. Core Definitions

**Player**: An individual competitor registered in the appropriate tier.

**Round**: A complete competitive cycle — opening, build phase, evaluation, communication (written PITCH.md or live pitch + cross-examination), judging/deliberation, and award reveal, plus a zamboni reset where controlled workstations are used. The atomic unit of competition. The phase *sequence* is tier-agnostic (§3.1); phase *timing* varies by tier and profile — the full Tier A round runs ~135 min, the Tier C MVR ~60 min (see TIER_A_OPERATIONS.md and TIER_C_OPERATIONS.md).

**Event**: A complete competitive gathering containing one or more rounds. Chapter events are typically single-round (~1 hour for an MVR, up to ~2 hours for a full Tier A round). Regional and championship events are multi-round days, typically 4-5 rounds with appropriate breaks (8-10 hour days).

**Submission**: The web application a player produces during a round, including its README documentation.

**Substrate**: The complete competitive environment — workstation, sanctioned AI model, package mirror, network configuration, and league infrastructure.

**Hacklet**: Both the event format and the output a player produces. "I'm competing in a hacklet" and "I built a hacklet" are both correct usages.

## 3. The Round

A round is the atomic unit of hacklet competition. The round phase sequence is tier-agnostic — every tier operates the same underlying phases — but specific timing within each phase varies by tier per the operational template. See TIER_A_OPERATIONS.md, TIER_B_OPERATIONS.md, and TIER_C_OPERATIONS.md for tier-specific timing profiles.

### 3.1 Round Phase Sequence

Every HackLet round operates the following phase sequence:

**Opening / Round Introduction**: host welcomes the room, frames the round (which variant, what's at stake, where this fits in the season), introduces players. Workstations or laptops remain locked or unprepared. This phase establishes orientation and (at Tier A) production rhythm.

**Build Phase**: the central system simultaneously unlocks all workstations and reveals the round prompt. Players have the variant's timer (24 minutes for Sprint, 12 for XP, 48 for Agile, etc.) to construct a web application. No required features, no mandated architectures. Players direct AI substrate however they choose within tier constraints. At freeze (build phase end), the network cuts for code changes, all build activity ceases — no further coding, no agent-interface edits, no fuzz invocations. AI responses mid-generation are truncated; partial code changes roll back to pre-prompt state.

**Evaluation Phase**: at freeze, submissions move to scoring infrastructure. Submission mechanism varies by tier — SCP from controlled workstations at Tier A/B, portal upload with grace period at Tier C (see tier docs for specifics). League infrastructure receives each submission, deploys in an ephemeral container, executes the full authoritative fuzz catalog (both public and hidden pools). Central testing scores submissions; any local fuzz invocations during build were intelligence-gathering only. Post-competition, submissions are published to the public HackLet git org with player attribution as part of the credentialing artifact archive.

**Pitch Preparation Phase**: code files become read-only at freeze. Players retain access to submitted code, README, and (per tier specifics) AI assistance for pitch preparation. Players digest what they built, plan their articulation, anticipate cross-examination questions. Players also author **PITCH.md** documenting defensive choices, design rationale, and strategic decisions — this artifact is the canonical written communication artifact in the Tier C MVR (LLM-judged) and serves as pitch prep material at Tier A/B and Tier C Extended (where live pitch is the primary credentialing dimension). See PITCH.md template per TIER_C_OPERATIONS.md §7.

**Pitch and Cross-Examination Phase**: human judges evaluate live performance at Tier A, Tier B, and Tier C Extended. Each player presents in sequence:
- Pitch — what they built, key choices, distinctiveness
- Cross-examination — judges ask questions in turn, each judge limited to one substantive question per player. Verbose answers cost remaining slots.
- Brief transition before next player

Specific timing per player (3.5 minutes at Tier A's standard 8-player rounds) and judge corps composition vary by tier. Same-archetype submissions (multiple players who built similar applications) pitch back-to-back to enable direct comparison.

In the Tier C MVR profile, live pitch + cross-examination is replaced with LLM-judged evaluation of PITCH.md + README + fuzz results (which also lets the MVR scale to large cohorts human judging couldn't). See TIER_C_OPERATIONS.md §8 for LLM judging architecture.

**Deliberation and Voting Phase**: judges enter explicit deliberation. They compare what they witnessed during pitches against clickaround observations, re-visit submissions with player framing context, score across all dimensions, finalize categorical award nominees and Best Overall composite rankings. Concurrent with judge deliberation (when audience is present), audience votes for People's Hacklet through the player portal.

**Award Reveal and Closing Phase**: ceremonial reveal of categorical awards followed by Best Overall reveal. At Tier A with broadcast production, the 14-min window allocates time for theatrical ceremony with audience reaction and broadcast cuts. At Tier B and Tier C, compressed ceremony fits the operational profile (~7 min at Tier C MVR).

**Zamboni Period** (when controlled workstations are used): workstation reset for next round. League daemon executes `userdel -r` for each player's ephemeral account, removes home directory content. Workstations rebooted to master image. Network state reset. Per-player accounts re-provisioned for next round. Audience break period. Tier C events with BYOD substrate skip the Zamboni Period because there are no ephemeral accounts to reset.

### 3.2 Round Sizing

Standard round size is **8 players** across all tiers. This is the format's foundational unit — the size most operational templates are designed around, the size that fits broadcast overlays at Tier A, the size that balances judge cognitive load with competitive variety.

**6-12 players** is the acceptable operational range; **12 is the structural maximum** because pitch + cross-examination timing breaks beyond 12 players (28 min for 8 players at 3.5 min each scales to 42 min for 12 players, pushing the format clock substantially).

**At large-cohort scale**, the Tier C MVR relaxes the 8-player limit because LLM judging scales to dozens of submissions in parallel — large-cohort MVR rounds run 30-100+ players (see TIER_C_OPERATIONS.md §5). Tier A and Tier B preserve the 8-12 player range because they use human judging that doesn't scale beyond that range.

The 8-player limit at Tier A specifically is tied to broadcast and audience purposes — 8 streams on broadcast overlay manageable, 8 player faces visible to audience, dramatic ceremony works at this scale. Lower tiers without broadcast have more flexibility on round size within operational constraints.

### 3.3 Broadcast Considerations

Broadcast production is **Tier A only**. The broadcast infrastructure requires controlled workstations that can be screen-shared without compromising player privacy — a constraint that BYOD substrates (Tier C) preclude entirely and that Tier B's optional workstation hosting doesn't necessarily provide. See TIER_A_OPERATIONS.md §6 for broadcast architecture details (workstation screen capture, per-player stats overlays, live player-fuzz leaderboard, suspense gap dynamics, commentary infrastructure).

At Tier B and Tier C, the format runs without broadcast production. In-person audience is optional. Asynchronous content (written results, post-event recaps, social media coverage) remains viable at all tiers for remote audience interest without requiring live broadcast.

## 4. Scoring

### 4.1 Component Structure

A player's performance is measured across three components:

- **Slop Score**: the amount of slop the fuzz catalog detected in the submission — a **deduction-only** score in the range **[0, +∞)** where **lower is better and 0 is the aspirational maximum** (a clean submission). It is the sum of per-probe penalties for every probe that detected slop; passing a probe, or not having the surface a probe targets, contributes nothing. Golf-style: you accumulate slop the way a golfer accumulates strokes — zero is perfect, and there is no bound on how much slop a broken submission can carry.
- **Pitch Quality**: Judge evaluation on a 0-100 scale, averaged across the panel, incorporating judge clickaround findings
- **Cross-Examination Performance**: Judge evaluation on a 0-100 scale, averaged across the panel, scoring substance and conciseness

Each component is reported as a raw score and used in category awards. The Best Overall determination uses rank-based composition rather than weighted-sum.

### 4.2 Slop Scoring Philosophy

Slop scoring is **deduction-only**. Each probe has one job: detect whether a specific kind of slop is present. A probe that detects slop adds its penalty to the slop score; a probe that detects nothing — whether because the submission defended correctly or because the targeted surface does not exist — adds **zero**. There is no positive reward for passing. Resilience is table stakes, not bonus territory: you are not credited for *not* having SQL injection, you are penalized for having it.

| Probe outcome | Slop contribution |
| --- | --- |
| Slop detected (the failure fired) | + penalty (varies by probe) |
| Clean (defended, or no such surface) | 0 |

This resolves the attacker/defender asymmetry honestly. A submission that defends seven of eight SQL endpoints is fully compromisable through the eighth: the seven clean endpoints add nothing, the one failure adds its full penalty, and the gap between "mostly defended" and "fully defended" is exactly the cost of that one failure — which matches the real-world outcome (you are breached). It also resolves the parameterized-SQL invisibility problem structurally: correctly parameterized SQL is behaviorally identical to "no SQL at all" from a probe's perspective, and deduction-only scoring treats both as zero, which is substantively correct — neither is vulnerable.

Penalty magnitudes are calibrated on a three-axis methodology:

1. **Frequency** — how common the surface/vulnerability class is in real applications. Higher → larger penalty: defending a common class is baseline competence.
2. **Worst-case severity** — the damage if the failure fires, read as *expected* damage (how bad × how reachable). Worse → larger penalty. Under universal-only the catalog assumes the worst context, so this single axis absorbs exploitability and contextual impact.
3. **Fix difficulty** — how hard the correct defense is to implement in a 24-minute build. Harder → **smaller** penalty. A competent engineer under real constraints (under-funded security/QA, velocity pressure, a forward-deployed engineer answering to contradictory stakeholders, tight timelines) rationally triages and defers rare, hard, lower-severity risks. The format credentials that judgment, not ivory-tower perfection.

Shape: `penalty = BASE × frequency × severity × discount(fix_difficulty)`, each axis scored 1–5. The fix-difficulty discount is **bounded, never an override** — it shaves at most ~40%, and tightens at the top severity tier (a catastrophe keeps the large majority of its penalty no matter how subtle the fix; you cannot "accept" account takeover). It rarely binds, because the worst *common* vulns are also the *easiest* to patch: SQL injection and auth bypass score easy-fix, take no discount, and land at maximum penalty, exactly as they should. The discount only bites where real triage happens — rare, genuinely-hard, moderate-severity issues like subtle race conditions. Worked points: SQLi (common · catastrophic · easy-fix) → max; a missing security header (common · low · trivial-fix) → small; a subtle race condition (rare · moderate · hard-fix) → low. (Magnitudes are placeholders pending calibration against reference submissions — flagged for follow-up design.)

Because scoring is deduction-only, the old distinction between categories where a defense is *observable* (XSS, access control) and categories where it is *not* (SQL injection, command injection) no longer affects scoring at all — both simply report slop-or-clean, penalty if detected and zero otherwise. Whether a probe can see a defense or only a failure is now purely a **detection** concern (the per-probe `evidence_model` in FUZZ_RUNNER_SPEC.md), not a scoring one. Non-adversarial QA probes work the same way: a graceful, correct response adds zero; a crash or a leak adds the penalty.

**Variant Groups**: Some categories contain "variant groups" — sets of probes testing the same logical attack on the same surface with different syntactic presentations (e.g., SQL injection across comment syntaxes), where a single correct architectural defense (parameterized queries) handles all of them. The variants are **detection robustness, not penalty multipliers**: a variant group contributes its penalty **once** if any variant fires. This still treats partial defense as full failure — blocking some syntaxes but missing one means the group fires and the full penalty applies — without over-counting one logical flaw by however many syntaxes happen to land.

**Aggregation across the catalog.** A submission's slop score sums penalties across categories, with two dampers that keep the total honest. *Within a category*, repeated instances of the same flaw across different endpoints have **diminishing marginal penalty** — the tenth endpoint missing a security header adds far less than the second, because once a class of mistake is established, breadth is noted rather than multiplied linearly. *Across bundles*, penalties are scaled so **security ≫ qa > performance**: a breach dominates a quality bug dominates a slow endpoint. Together these make the slop ranking reflect *worst class of problem, plus breadth across distinct classes*, instead of letting many trivial repeats outweigh one catastrophic flaw.

**Result Reporting**: A slop score in isolation can be ambiguous — a low score could mean a clean submission with broad surface (excellent) or a trivial one with almost no surface to test (Limited Engagement). To disambiguate, each submission's result reports the slop score alongside contextual metadata:

- **Status**: Completed, DNF (Did Not Deploy), or Limited Engagement (fewer than the threshold of applicable probes)
- **Probes Applicable**: Count of probes whose target surface was present
- **Slop Detected**: Count of probes that fired, with a per-category breakdown
- **Attack Surface Coverage**: Categorical descriptor (Narrow / Moderate / Broad) derived from applicable count
- **Clean Rate**: probes passed divided by probes applicable, as a percentage (the proportion of the tested surface that carried no slop)

This metadata accompanies the slop score in event results, persistent rankings, and broadcast displays. The composite scoring math uses the raw slop score for ranking, but interpretation of results uses the full reporting bundle. A player whose persistent rankings show broad coverage with low slop has demonstrably different signal than one with consistently narrow coverage. Because lower slop is better, a **DNF** (did not deploy) or **Limited Engagement** submission is ranked below every completed submission regardless of its trivially-low raw slop: not deploying is the worst outcome, never a clean zero.

**Test Bundles**: Tests in the catalog are split into two bundles reflecting their different correctness models:

- **Security tests**: Universally correct regardless of application intent. SQL injection should always be defended; XSS should always be prevented; auth should never be bypassable. The security bundle is comprehensive and covers the OWASP-aligned attack surface.
- **QA tests**: Focused on universally-correct quality properties that apply to 95-98% of applications. The QA bundle deliberately avoids intent-dependent edge cases at this stage of the format's maturity.

**Universal QA Properties** are quality behaviors that apply regardless of what the app is supposed to do:

- Crash resistance under unexpected input (empty, whitespace-only, oversized, null bytes, special characters, unicode, numeric overflow, malformed JSON, missing fields, wrong content-types)
- Error response hygiene (no stack traces, database errors, file paths, environment variables, or credentials leaked in user-facing responses)
- Basic resource cleanup (no obvious memory or file handle leaks in observable time)
- HTTP protocol semantics (404 for not-found, 401 for unauthenticated, 403 for unauthorized, 405 for wrong method, 400 for malformed, proper Content-Type headers)
- Charset handling (UTF-8, basic unicode, emoji, CJK, RTL text — round-trip correctly without crashes)
- Size limit handling (oversized request bodies, URLs, headers rejected rather than crashing)
- Timeout behavior (no endpoint takes longer than 5 seconds to respond — matches user abandonment threshold)
- Basic deployment hygiene (no secrets in static assets or HTML source, no debug mode in production, no exposed admin endpoints)
- HTTP-spec-mandated idempotency (GET requests are idempotent per HTTP spec, regardless of app intent)

These properties no legitimate application intent violates. They are testable universally without intent considerations.

The 5-second timeout threshold is deliberately set above tight production targets (real-world abandonment begins around 3 seconds) to remain reasonable for 24-minute builds that cannot fully optimize for performance.

Speed is also measured as **boolean abandonment-threshold gates** in the performance bundle, distinct from optimization targets: TTFB ≥ 3s, FCP ≥ 5s, and INP ≥ 5s each add the speed category's slop penalty, with no marginal credit for being faster (a player clears the gate, then spends remaining time elsewhere). These are gates, not slopes — they catch only the egregiously broken, so they do not "penalize all submissions uniformly." TTFB is server-side and applies to any HTTP response; FCP and INP are browser-measured and apply only to apps that serve a rendered HTML document (a pure API scores them N/A). Optimization-target scoring of Core Web Vitals (for example crediting LCP < 2.5s on a slope) remains excluded: it measures performance tuning rather than engineering correctness. See FUZZ_RUNNER_SPEC.md for the gate mechanics.

**Intent-Dependent QA Properties** — idempotency, specific concurrency behaviors, duplicate handling, persistence semantics — are deferred from the initial catalog. These depend on what the app is supposed to do (a checkout requires idempotency; a chat may not), and rigorous testing requires intent declarations and applicability decisions that add complexity disproportionate to the measurement value for 24-minute builds.

Future format iterations may add structured intent-dependent QA testing as the format matures and operational experience reveals where this measurement value is needed. The initial catalog focuses on universal properties that produce honest measurement of engineering quality for the format's actual scope: applications built in 24 minutes by individual engineers directing AI assistance.

The README remains load-bearing for cross-examination and pitch context. Players describe their app's intent for judge interpretation during clickaround, but the automated test catalog does not depend on intent classifications for its initial implementation.

### 4.3 Best Overall (Composite Ranking)

The Best Overall winner is determined through rank-based composition with progressive tiebreaking:

1. Players are ranked independently on Slop Score and Communication Score (Communication = average of Pitch Quality and Cross-Examination Performance). Slop is ranked **ascending** (lowest slop is rank 1, since lower is better); Communication is ranked descending (highest is rank 1). Because composition is rank-based, the unbounded range and lower-is-better direction of the slop score need no normalization — only the ranking direction differs.
2. Each player's Rank Sum equals Slop Rank plus Communication Rank.
3. **Lowest Rank Sum wins.**
4. Ties on Rank Sum are broken by **smallest absolute differential** between Slop Rank and Communication Rank. This rewards balanced performance across components.
5. Ties on both Rank Sum and differential are broken by **best Slop Rank** (favors the engineering side if still tied).
6. Ties on Rank Sum, differential, and Slop Rank are broken by **best Communication Rank** (favors the communication side if still tied).
7. Ties on all four criteria result in co-Champions. No additional tiebreakers are applied.

Standard competition ranking (1224 method) is used for component ranking, with ties shared and subsequent ranks skipping accordingly.

This produces the right kind of Best Overall winner: the most balanced player among those with the strongest combined performance, rather than the player who dominated a single component. The progressive tiebreaker hierarchy resolves nearly all real-world ties before co-Champion is declared, while leaving co-Champion as the honest outcome when players are genuinely indistinguishable.

### 4.4 Categorical Awards

Per-round categorical awards are kept deliberately small to preserve credentialing signal at 8-player round size. Per-round awards alongside Best Overall (§4.3):

- **Most Resilient**: Lowest raw Slop Score. The award title stays aspirational (it credentials the *quality* of resilience demonstrated) while the underlying measurement is descriptive (slop score 0 is what earned it) — the same way golf names a "Champion," not a "Lowest Score Holder."
- **Best Communicator**: Highest raw Communication Score (combined Pitch Quality + Cross-Examination Performance per §4.3). Replaces the earlier "Best Pitch" award, which scored pitch only — Best Communicator captures the full communication dimension including defense under cross-examination.
- **People's Hacklet**: Audience vote (separate from judge evaluation entirely)

This produces **3 per-round categorical awards plus Best Overall** for each round, regardless of event tier or structure. Players may win multiple awards (e.g., a dominant performer might win Most Resilient + Best Overall in the same round). A categorical winner need not also win Best Overall, and the Best Overall winner need not win any specific category.

**Awards explicitly retired at per-round level**:

- *Best UX/UI*: per-round UX evaluation is too contextual; the award is meaningful only when judges have observed multiple submissions across rounds (moves to tournament-level)
- *Most Novel*: per-round novelty is too prompt-dependent; the award is meaningful only as "consistently novel approach across the tournament" (moves to tournament-level)
- *Most Efficient*: requires enforced token measurement, only meaningful at Tier A with league-hosted AI substrate (drops at Tier C; available at Tier A tournament-level)

**Tournament-level expanded categorical awards** are deployed at multi-day Tier A tournaments where judges observe each player across multiple rounds, making subtle categorical distinctions meaningful through aggregated evidence. See IDEAS_FOR_LATER.md "Multi-day Tier A tournament template" for the expanded set (Best UX/UI, Most Novel, Most Efficient, Iron Player, Comeback Player) and their allocation across qualifier-leaderboard vs finals-leaderboard.

The design principle is anti-award-sprawl: too many per-round categoricals at 8-player events means almost every player wins something, which destroys the *non-winning* signal that makes awards meaningful. Per-round awards stay tight; tournament-level awards expand because the field and round count justify richer categorical distribution.

## 5. Substrate

### 5.1 Workstation

All players in an event work on identically-configured workstations supplied by the league or the hosting chapter. Workstations run a standardized Linux distribution as a normal desktop environment — players have access to an IDE, browser, terminal, file manager, and standard development tools, used the way an engineer would use any workstation. The substrate's anti-cheating boundary is enforced at the network layer rather than through application lockdown.

**The development environment is local to the workstation.** The IDE, code editor, file manager, terminal, and local deployment all run natively on the workstation. The league competition website supplies only the chat interface to the AI substrate plus event coordination (timer, fuzz triggers, budget displays, submission state). Players write code in their local IDE, deploy locally for testing, and interact with the league platform only through a browser tab pointed at the chat interface. There is no hosted IDE, no remote code editor, no cloud development environment. The platform is event coordination infrastructure, not a development environment.

**Workstation environment — IDE: VSCodium** (telemetry-free), preinstalled with language support for common stacks (Python, JavaScript/TypeScript, Go, Rust, Ruby), standard formatters, and basic git tooling. Vim/Neovim are also installed for players who prefer them. Third-party AI coding extensions (Copilot, Cursor, Cline, Continue, Codeium, etc.) are disabled at the policy level and cannot be installed — external AI access is forbidden by the substrate model because the league hosts and audits the sanctioned AI substrate. Players access the league's AI substrate through two parallel interfaces, both routed through the same proxy with a shared per-player token budget: (1) the **chat-window interface** in the league portal (a browser tab pointed at hackletleague.com) for chat-style brainstorming and copy/paste workflow; (2) the **league-built signed VSCodium extension** for in-IDE agent operations (chat sidebar plus accept/reject UI). The extension ships in Stage 12 (BUILD_ROADMAP); the chat-window-only substrate is the foundational configuration. Players use whatever combination of interfaces fits their workflow — the unified token budget prevents tool-stacking advantage and the format does not legislate which interface to use.

**Local fuzz capability for intelligence gathering and broadcast suspense.** Workstations include a locally-installed fuzz runner containing the public test pool. During build phase, players trigger this local runner via the league portal; the runner executes against their local deployment and returns intelligence about their defensive coverage in seconds. The local runner does *not* contain the hidden test pool — hidden tests live only on league central infrastructure. Local fuzz results are informational only; they do not contribute to scoring.

The primary purpose of player-triggered fuzz is **broadcast watchability**. A player's visible slop score falling as they fix issues during build creates real-time narrative for audiences and commentators. The gap between the visible public-pool slop and the authoritative hidden-pool slop at freeze generates the format's central dramatic tension: did the player's low public slop reflect genuine defense, or will the hidden tests surface slop the player never probed for? Player fuzz is intelligence for the player; the visible slop score is suspense for the audience.

Workstations are restricted to non-administrative user accounts. Players cannot modify system configuration, install global software, or access system directories. Within their home directory, they have full freedom to work as they would on any development machine.

USB ports are physically disabled or removed. No external storage, no Bluetooth, no Wi-Fi. Ethernet only. Virtual console access is disabled to prevent dropping out of the desktop session.

Workstations are centrally managed through the league's RMM platform. Configuration consistency is enforced through automated policy. Per-round reset is handled by per-player account lifecycle, not image restoration: an ephemeral, non-sudo Unix account is created from `/etc/skel` at round start and deleted with `userdel -r` at round end (after the player's session and processes are terminated), removing the home directory and all session state in seconds. System state persists between rounds untouched. Full image restoration is reserved for the exceptional cases — between events, on any tamper-detection signal, and scheduled maintenance. Because the system is no longer wiped every round, between-round tamper detection is load-bearing: any integrity signal forces an image restore before the workstation is reused. OS and application updates are pushed through controlled maintenance windows between events, not during competition.

The linux choice serves the league's operational needs — open-source tooling, zero licensing cost, mature deployment automation, hardware flexibility, and vendor independence. Players whose daily environment is Windows or macOS receive brief orientation before their first competition to familiarize with the desktop and development tools. The substrate choice is not designed to teach linux skills; it is designed to enable the league to operate transparently and affordably at scale.

On the 24-minute clock. The build duration is a deliberate steal from "the 24-hour hackathon" — only the unit of time changed. Pre-AI, 24 minutes of solo programming produced almost nothing of substance; that's why hackathons settled on 24-72 hours historically. With AI substrate, a skilled engineer produces in 24 minutes what an unassisted engineer needed 24 hours for. The unit shrinks; the competitive surface doesn't. The format isn't anachronistic for using a short clock — it's enabled by the substrate. HackLet is not adapting to AI; the format is constituted by AI.

### 5.2 Network Configuration

Workstations are firewall-restricted to a minimal allowlist:

- The league competition website (single endpoint)
- NTP for time synchronization

The league competition website internally routes to the sanctioned AI substrate, the package mirror, and the deployment infrastructure. Players reach these resources only through the competition website, never directly. No web search. No external documentation. No second AI tools. No copy-paste from outside sources.

Chapters may optionally deploy dedicated network appliances or VLANs for additional isolation. The league provides reference configurations.

### 5.3 AI Substrate

Each season specifies a single AI model that serves as the substrate for all events that season. The model is announced at least 30 days before the season begins. Players have access to practice with the announced model in advance.

Season 1 substrate: **DeepSeek V4 Flash**, accessed through OpenRouter, with no league-injected system prompt beyond the model's standard production deployment. The model behaves as it would in any other standard deployment. No league-specific tuning, persona, or behavioral modification.

The league hosts the competition website that proxies all AI calls. This provides:

- Consistent player interface across model rotations
- Server-side enforcement of token budgets, fuzz budgets, and rate limits
- Complete audit trail of all interactions
- Single firewall endpoint for workstations
- Centralized cost management

**Unified substrate model (Tier A and Tier B)**: where the league hosts AI substrate, players are served *both* a chat-window interface (browser tab to the league portal) *and* a league-built signed VSCodium extension with an in-IDE agent (chat sidebar plus accept/reject UI for agent-proposed file changes). Both interfaces talk to the same proxy, the same season-pinned model, and the same per-player token budget. Players may open multiple chat windows, work with the agent, or combine both freely. The unified budget means there is no tool-stacking advantage: a player using 5 chat windows plus the agent does not have 6× tokens; they have 1× budget split across however many interfaces they use.

This matches how real engineering with AI actually happens. Engineers brainstorm in chat, have agents execute, switch fluidly. The format does not force players into one interaction mode because doing so would credential the mode rather than the skill. Strategic discipline comes from how players navigate the unified substrate (when to use chat-style thinking, when to delegate to the agent, when to spend tokens on which mode), not from which mode the format pre-selects for them.

**BYOD substrate (Tier C)**: Tier C does not host AI substrate. Players bring their own laptops and use whatever AI tooling they prefer (chat clients, IDE agents, mix and match). Web search and multiple AIs are allowed because BYOD makes restriction theater. Token budgets do not apply because the league is not paying for the AI and cannot enforce the budget. See LEAGUE_OPERATIONS.md §4 for the full Tier C operational profile.

The proxy exposes an **OpenAI-compatible chat completions endpoint** (`/api/v1/chat/completions`). The OpenAI protocol is the de facto standard that chat clients and IDE extensions speak, so the substrate stays compatible with the league's chat window, the league's VSCodium extension, and future client tooling without changing the API contract. Compatibility is surface-only: the league pins the season's model, enforces token and fuzz budgets and rate limits server-side, and audits every call. Clients cannot select the model, exceed budget, or bypass logging. Substrate equality holds across all interfaces because they all share the same model, budget, and policy enforcement.

Mid-tier model choice is deliberate. Frontier models would mask the verification skill that distinguishes thoughtful AI direction from lazy AI direction. Mid-tier models hallucinate at rates that exercise verification skill meaningfully. Players who instinctively prompt for resilience and verify model output succeed; players who do not, fail.

## 5.4 Substrate Languages and Package Mirror

The substrate supports a tiered set of languages calibrated to the
target population — junior software engineers. The Union-Of-Resumes
heuristic governs inclusion: a language is in the substrate if it
appears commonly on junior SWE resumes in the league's target market.

**Tier 1 — Full substrate parity**:
Python, JavaScript, TypeScript, Go
Mirrored starter kits cover web frameworks, ORMs, validation,
testing, and common utilities. Quality of substrate is equal across
these languages.

**Tier 2 — Maintained substrate parity**:
Java, C#, Rust, Ruby
Mirrored starter kits cover web frameworks and core utilities.
Substrate is maintained but with smaller catalogs than Tier 1.

**Tier 3 — Compiler-only**:
C, C++
Toolchain available. No mirrored framework ecosystem. Players using
Tier 3 languages bring their own infrastructure within the round time.

The mirror is operated by the league at packages.hackletleague.com,
firewall-allowed alongside the main domain. Mirror updates between
seasons; package availability is published with season documentation.
Submissions requiring packages outside the mirror will fail to deploy
and score accordingly.
### 5.5 Resource Budgets

Each player receives per round:

- **100,000 tokens** total (input + output + chain-of-thought)
- **50 fuzz budget points** for player-triggered self-testing during build

Token budget is a hard cap enforced server-side. Once reached:

- The current model response is truncated at the cap point
- Any code changes from the truncated response are rolled back
- The player may continue working in the IDE without AI assistance

Edited or regenerated prompts do not refund tokens. Each prompt submission costs against the budget regardless of subsequent edits.

Fuzz budget enforces strategic allocation of self-testing. Categories have varying costs reflecting test complexity. Players may invoke any subset of fuzz tests against their own work within budget, gathering intelligence about defensive coverage before the judge fuzz set runs at code freeze.

### 5.6 Submission Requirements

A valid submission must:

- Deploy successfully to the designated localhost port
- Respond to HTTP requests at that port
- Include a `README.md` file describing the build
- Be authored entirely during the 24-minute build phase via the sanctioned substrate

The README may be written by the AI. Players who use the AI to draft documentation are responsible for verifying its accuracy. README claims that misrepresent the submission's actual behavior become points of cross-examination scrutiny. Submissions without a README receive a significant flat penalty rather than disqualification.

**Failure modes are scored distinctly:**

- *Submission does not compile or fails to deploy at all*: Marked **DNF** (did not deploy) — the worst outcome, ranked below every submission that runs (not a clean zero, under lower-is-better slop; see §4.2). The submission may still proceed through pitch and cross-examination, where the player may discuss what they attempted.
- *Submission deploys but specific features error during testing*: Each broken feature scores per the relevant test catalog entry — a feature that exists but crashes when used is "Broken," not "Not Applicable." The player is penalized for shipping broken features in proportion to which features were affected.
- *Submission deploys and behaves consistently*: Standard fuzz scoring applies across all applicable test categories.

### 5.7 Application Self-Containment

Submissions must run as **self-contained applications**. The fuzz runner provides no external service credentials, API keys, or third-party network egress. Code that requires secrets to function fails at runtime, and the runner scores the resulting failures as slop — it does not detect or reject such code; the consequence is natural at the fuzz layer.

**Permitted persistence:**

- SQLite files committed to the submission repository
- Client-side browser storage (localStorage, sessionStorage, IndexedDB)
- In-memory state within the application process

**Not supported at current operational maturity:**

- External databases (Supabase, MongoDB Atlas, cloud-hosted Postgres, etc.)
- Third-party API integrations requiring keys (Stripe, OpenAI, Auth0, etc.)
- External auth providers
- Cloud storage services

The 24-minute format makes serious external integration impractical even with AI assistance; the constraint reflects format reality, not arbitrary limitation. Players keep full freedom to write integration code, but the runner does not provide the environment for it to function, so such code fails its relevant probes. The policy relaxes as the league builds integration-testing infrastructure at higher tiers (Phase 3 — see IDEAS_FOR_LATER.md).

## 6. Tier Structure

HackLet League operates across three tiers calibrated to expected expertise:

### 6.1 Collegiate Tier

For currently-enrolled undergraduate students. Standard fuzz set covers categories appropriate to undergraduate CS education (SQL injection, basic XSS, input validation, CRUD lifecycle, fundamental authentication). Advanced categories appear as opt-in bonus opportunities with positive-only scoring — collegiate players are not penalized for attempting categories beyond their expected baseline knowledge.

### 6.2 Under-25 Tier

For competitors aged 25 and under, including recent graduates and graduate students. Expanded standard fuzz set incorporating intermediate categories (unicode handling, basic race conditions, session management). Advanced categories scored with moderate asymmetric penalty for failure.

### 6.3 Open Tier

For any competitor regardless of age or status. Complete professional fuzz gauntlet including sophisticated categories (double-byte normalization, complex concurrency patterns, timing attacks, advanced authorization). Full symmetric scoring across the catalog. Represents the highest competitive level the format offers.

Tier eligibility is verified during registration. Misrepresentation of tier eligibility is grounds for disqualification and possible season ban.

Players may compete in tiers above their expected eligibility (a collegiate player may register for Open) but the higher tier's full scoring applies. Players may not compete in tiers below their eligibility.

## 7. Season Structure

### 7.1 Events

Events occur throughout the season at multiple scales:

- **Chapter events**: Local events run by individual chapters, typically 6-8 players, monthly cadence. May be single-round (~1 hour for an MVR, up to ~2 hours at the full Tier A profile) or multi-round day events depending on chapter capacity.
- **Regional events**: Cross-chapter events with broader participation, quarterly cadence, typically multi-round day events (3-5 rounds across 8-10 hours) to justify travel for visiting players.
- **Championship events**: Season-culminating events with the strongest field, typically multi-day with multiple rounds per day.

At **human-judged tiers (A/B)**, every round operates at **8 players standard**, **6-12 acceptable**, **12 structural maximum** — beyond 8 per-player narrative depth degrades and judge time tightens; beyond 12 broadcast quality and human-judging throughput break. Events with more demand add rounds rather than enlarge them. **Large-cohort MVR rounds relax this cap to 30-100+**, because LLM-judged written evaluation scales where human judging can't (see §3.2 and TIER_C_OPERATIONS.md §5).

**Round size targets** (the human-judged Tier A/B profile; the full phase-by-phase breakdown lives in TIER_A_OPERATIONS.md §3, and the Tier C MVR / large-cohort profiles in TIER_C_OPERATIONS.md §4–5):

- *Standard (8 players)*: the format's foundational design point — best broadcast quality, judge evaluation depth, and categorical award distribution. Validated by FMWC precedent (888 Battle, ESPN2 All-Star Battle). Full Tier A cycle ~135 min.
- *Smaller (6-7 players)*: ~105-115 min Tier A cycle. Acceptable for early chapter events, pilot rounds, recruitment-constrained operations.
- *Larger (9-12 players)*: ~125-145 min Tier A cycle. Acceptable when needed, with reduced per-player narrative depth and tighter judge time.

The round *phase sequence* is defined tier-agnostically in §3.1; each tier's phase *timing* lives in its operations file (the full Tier A round runs T+0→T+135; the Tier C MVR runs T+0→T+60).

Multi-round events host multiple rounds with different player groups across the day, using the same physical workstations. The Zamboni Period between rounds serves several functions:

- Per-player accounts are torn down and recreated: the outgoing player's ephemeral, non-sudo Unix account is deleted (`userdel -r`, wiping the home directory and session state) and a fresh one is provisioned from `/etc/skel` for the incoming player — seconds per workstation, system state untouched. Full image restoration is the *exceptional* operation (between events, on tamper detection, scheduled maintenance), not the per-round reset
- Outgoing players depart and incoming players are seated
- Judges file scores from the completed round and refresh their tools
- Broadcast commentary covers recap and preview, with next-round introduction beginning in the final 5 minutes
- Human participants take needed breaks
- Production team resets equipment as needed

Multi-round structure makes hacklet events economically viable for travel: a full day of competition with 4-5 rounds justifies driving or flying from distant chapters. It also produces substantial broadcast content, amortizes venue and production costs across many rounds, and creates continuous narrative flow between rounds rather than discrete events with dead time.

**One event, one format.** Each event commits to a single format variant (Format × Timer combination from the sanctioned matrix in §1). Rounds within an event may vary prompts and starting conditions but use the same format throughout — its substrate, timing, scoring scale, and judge calibration assumptions. This applies to single-round events, multi-round day events, and multi-day tournaments alike. The rule preserves scoring coherence (averaging across rounds requires comparable units), credential clarity (employers can interpret what a specific format variant credentials), and operational consistency (chapter operators don't reconfigure substrates mid-event). Cross-format championships are a deliberate exception with their own scoring rules (see IDEAS_FOR_LATER.md "Format-lane structure").

**Cardinality across the institution**: each *event* runs exactly one *format* (1-to-1); each *chapter* hosts many *events* over time (1-to-many); each *chapter* runs many *formats* across its event history (many-to-many on chapter↔format, mediated through events). Chapter portfolio variety is encouraged; event format consistency is required.

HackLet League is **ranked competition, not bracketed elimination, within each round**. All players in a round compete simultaneously and are ranked at completion. There is no head-to-head matchup structure inside a round, no losers' brackets, no in-round advancement. The format follows the precedent of individual measurable performance sports (track and field, swimming, cycling time trials, financial modeling competitions) rather than combat sports or single-elimination tournaments.

Across rounds in a multi-day tournament, cumulative-score advancement is used to separate qualifying-stage performers from finals participants (see IDEAS_FOR_LATER.md "Multi-day Tier A tournament template"). This matches FIDE Swiss-system, Olympic qualification structures, and golf-cut conventions — individual-competition formats use cumulative-score thresholds rather than head-to-head pairings to manage field size across multi-stage events.

League growth happens through event frequency and geographic spread rather than larger individual rounds. Many smaller events feeding into accumulated rankings is structurally similar to chess tournaments, golf tours, and FIDE rating-based competitive systems.

### 7.2 Rankings

Two parallel ranking systems operate:

- **Season Rankings**: Current-season performance, used for qualification flow into higher-tier events and for crowning season champions
- **Persistent Rankings**: All-time accumulated performance, providing long-term credentialing signal

Both rankings are publicly visible. Players accumulate rank points through event placement, weighted by event tier.

### 7.3 Qualification Flow

Top performers at chapter events qualify for regional events. Top performers at regional events qualify for the season championship. Specific qualification thresholds are published per season and per region.

## 8. Conduct

Players must respect other competitors, judges, league staff, and the integrity of the substrate. Specifically:

- No harassment of other players or judges
- No attempts to influence judges outside the structured evaluation process
- No attempts to access external resources during a round through any means
- No collusion between players or coordination across submissions
- Truthful representation of identity, eligibility, and submission claims
- Respect for judges' in-event scoring decisions, with appeals through formal post-event process

Violations are addressed through the penalty structure detailed in the full rulebook, ranging from warnings through point deductions through round forfeit through event ban through season ban through permanent league ban, calibrated to severity.

## 9. Format Evolution

The league reserves the right to evolve the format between seasons, including:

- Rotating the AI substrate
- Updating the package mirror
- Refining the fuzz set
- Adjusting scoring parameters
- Adding new categories or tests
- Modifying rules based on observed gaps

Changes are announced at least 30 days before they take effect. Players who specialize narrowly to a specific season's parameters accept that future evolution may invalidate that specialization. The league's commitment is to evolve thoughtfully and transparently, not to maintain perfect stasis.

The format's core mechanics — 24-minute build, single-player solo competition, sanctioned substrate, multi-axis scoring with rank-based composition — are considered foundational and not subject to between-season modification.

## 10. What the Format Measures

The format rests on two principles:

1. **Substrate equality** — every player has the same tools, model, and resources.
2. **Submission resilience** — the fuzz catalog is the authority on how well the work holds up.

The format does not legislate *how* a player uses AI. Chat, agentic integration, command-line, tool chains — any interface is fine, provided every call flows through the league's API and stays within budget (§5.3). It cares only that the substrate is equal and that submissions are measured by objective adversarial testing. Resilience is what the fuzz catalog measures; communication (pitch and cross-examination) is scored separately and combined for Best Overall (§4). Slop loses to fuzz regardless of who or what produced it.

The chat-window interface matches the economically-dominant AI-coding practice among the format's target population. Third-party agentic IDE tooling (Cursor, Claude Code, Cline) requires either paid subscriptions or student-verification with friction that filters most undergraduate users; the chat-window workflow remains the only fully-free option for most CS students, which is why the chat window is the foundational substrate interface and the in-IDE agent interface ships later (Stage 12). When the agent interface lands, both interfaces are available to every Tier A/B player simultaneously with a unified token budget, so the format remains accessible to chat-first players while accommodating agent-fluent players without forcing either group into the other's mode.

In practice, succeeding under those principles exercises a specific cluster of AI-complementary capabilities:

- **Engineering judgment**: knowing what needs defensive attention without being told
- **AI direction**: effectively prompting an AI substrate to produce robust work
- **Verification reflex**: catching AI errors, hallucinations, and weaknesses before they ship
- **Resource calibration**: allocating limited tokens and fuzz budget strategically
- **Technical communication**: explaining decisions clearly under time pressure
- **Defense under questioning**: responding substantively to judge cross-examination

These are what humans contribute when AI does the typing. They do not become easier as AI models improve, because the bottleneck is human judgment about how to direct AI rather than AI capability itself.

The format does not measure:

- Learning ability (24 minutes is too brief for meaningful in-event learning)
- Team collaboration (the format is solo by design)
- Long-term project management (the time window precludes it)
- Specific framework expertise (substrate-agnostic by design)
- Pre-event practice access (the format equalizes substrate during competition only)

The published methodology is comprehensive about what the format claims to measure and explicit about what it does not.

## 11. The League's Position

HackLet League exists to provide structured competitive infrastructure for a community that already cares about AI-assisted technical building. The format treats players as engineering adults responsible for their own decisions. It evaluates submissions through narrow precise measurement rather than broad subjective assessment. It publishes its methodology in full, including its limitations.

The structural precedent is the **Financial Modeling World Cup**. Founded in 2020 by Andrew Grigolyunovich (Latvia) after ModelOff was discontinued, FMWC took competitive financial modeling — a niche, measurable skill — to mainstream attention (its All-Star Battle aired on ESPN2 in 2022) through recurring tiered competition and persistent rankings, built into a durable institution by one founder. HackLet applies the same playbook to AI-assisted defensive coding, a domain with a deeper participant pool and more cultural pull. The precedent matters because it answers the first question every chapter operator, sponsor, and player asks — *is this real?* — with a pattern that has already worked once. HackLet borrows the template, not a claim of equivalent reach.

Credentialing is the aspiration, not the pitch. The League's job is to run the format well: equal substrate, honest measurement, methodology published in full. Done consistently, the credential emerges as a side effect — persistent rankings accumulate career-spanning evidence, and employers may over time reference HackLet standings as signal for AI-assisted engineering and defensive-coding roles. That value depends entirely on whether the measurements are trustworthy, which is why rigor comes first and the credential follows.

The League is honest about what AI actually delivers: a meaningful but modest productivity multiplier, useful when directed well, sloppy when directed poorly. The format demonstrates this empirically in every event. Submissions that pass the fuzz gauntlet are evidence of what skilled AI-assisted work can produce. Submissions that fail are evidence of what unskilled AI-assisted work cannot.

The industry is grumbling about slop in 2026, and the grumble is documented. The Harness 2026 State of Engineering Excellence report finds roughly 31% of a developer's day consumed by invisible work — reviewing AI-generated code, fixing its bugs, and context-switching between tools — and 81% of engineering leaders report increased code-review burden since adopting AI tools. The Harvard Business Review (2025) estimates "workslop" costs roughly $9 million per year per 10,000 employees. MIT's Project NANDA finds 95% of organizations see no measurable return on AI investment. Engineering communities have organized vocabulary around the failure mode — "vibe coding," "tokenmaxxing," "slop" — and vendors are shipping countermeasures (AI code-review and intent-verification tooling). HackLet enters this moment with credentialing infrastructure that answers a specific market need: engineers who can operate effectively in AI-augmented environments without producing slop, and engineers who can remediate the slop others produce.

The two-format structure covers both halves of the anti-slop engineering profession. **HackLet Vibe** credentials producing code that isn't slop. **HackLet Unslop** credentials identifying and remediating slop in existing code. Together they map to the full surface of AI-augmented engineering work. The strategic articulation is simple: people grumble about slop, so HackLet makes anti-slop a sport, televises it, and credentials those who excel at it. The grumble is the market; the format is the product.

HackLet does not legislate AI usage style — any interface is fine (chat, agentic, command-line) so long as calls flow through the league's API and stay within budget. What matters is what survives the fuzz at code freeze, regardless of who or what produced it. The two principles (§10) are sufficient; the format evaluates nothing else.

The fuzz is what separates hacklets from slop.

---

*This document is the executive summary of the HackLet League rules. The complete rulebook contains formal specifications, edge case handling, appeals procedures, technical appendices, and case precedents accumulated through league operation. Players are responsible for familiarity with the full rulebook for the tier and season in which they compete.*
