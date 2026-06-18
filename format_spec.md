# HackLet League — Format Specification

*Executive summary of the official rules. The complete rulebook addresses every edge case in detail; this document establishes the format's identity, mechanics, and core operating principles.*

---

## 1. What HackLet League Is

**In one sentence: hackathon, but minutes instead of hours, with a cheering audience.**

HackLet is an institution that runs competitive formats, not a single immutable format. Format names follow a three-axis structure: **HackLet {Format}: {Relationship} {Timer}**.

- **Format axis** — what the player does. **Vibe** (build an application from scratch under AI assistance) or **Unslop** (remediate a deliberately-broken application generated live during the round).
- **Relationship axis** — how the player works with AI. **Classical** (chat interface, copy/paste workflow, every line that lands is one the player put there) or **Agentic** (AI lives in the IDE with edit permissions, player accepts or rejects proposed changes).
- **Timer axis** — how long the round runs. **XP** (12 min), **Sprint** (24 min), **Scrum** (36 min), **Agile** (48 min), **Waterfall** (72-96 min). Token budgets scale with the timer.

The foundational format is **HackLet Vibe: Classical Sprint** — 24 minutes, chat-window AI relationship, build from scratch. It is the format described in detail by this document and the one the BU pilot operates. **HackLet Unslop: Classical Sprint** is documented as the canonical second format and is introduced once Vibe is operationally stable. Agentic variants and longer timer controls follow as the league matures. Future format introductions follow the same naming convention without renaming what came before.

HackLet Vibe: Classical Sprint is a competitive format for AI-assisted technical building under extreme time compression. Players have 24 minutes to construct, document, and defend a web application, working alone on a locked-down workstation with a single sanctioned AI substrate. Submissions are evaluated through automated adversarial testing, judge inspection, and live questioning. Multi-axis scoring produces categorical awards alongside an overall composite ranking.

The format borrows time-compression from bullet chess, multi-axis scoring from gymnastics and decathlon, regional feeder structure from CTWC, and tier organization from FMWC. What it adds is novel: systematic adversarial testing of AI-assisted submissions under tournament conditions. The 24-minute build duration deliberately parallels the 24-hour hackathon, positioning hacklet as a compressed-format descendant of hackathon culture rather than a replacement for it.

The name **Vibe** is deliberate. "Vibe coding" entered industry vocabulary in 2025 as a complaint — engineers directing AI rapidly without verification, producing slop at scale. HackLet reclaims the term. Vibe coding done by skilled engineers under proper conditions is real professional capability. HackLet Vibe champions demonstrate vibe coding *with* verification reflex, *with* defensive depth, *without* producing slop. The format name stakes territory in the industry's vocabulary dispute: vibe coding is a skill, and the league credentials those who practice it well.

A complete round cycle runs approximately 2 hours from opening to next-round-introduction, with the 24-minute build forming the competitive core. This structure makes multi-round day events practical for regional and championship competition while preserving broadcast quality through proper time allocation for evaluation, pitches, deliberation, and award reveals. Rounds are bounded at 8 players standard, with 6-12 as the acceptable operational range and 12 as the structural maximum. Events host one or more rounds; regional and championship events typically run multi-round days.

HackLet League is built for engineers who want to develop and demonstrate the cluster of skills AI-assisted defensive coding requires: prompting fluency, verification reflex, resource calibration, and defensive depth. It is not a beginner-friendly format. It assumes participants have working knowledge of web development and at least introductory familiarity with security concepts. Players who do not yet have those foundations are welcome to attend events as spectators and participate when their preparation matches the format's expectations.

## 2. Core Definitions

**Player**: An individual competitor registered in the appropriate tier.

**Round**: A complete competitive cycle including opening (5 min), 24-minute build phase, concurrent evaluation and pitch preparation (18 min), pitch and cross-examination phase (28 min for 8 players), concurrent deliberation and audience voting (18 min), award reveal and closing (~14 min), and zamboni period (25-30 min before the next round). The atomic unit of competition, running approximately 2-2.5 hours per cycle.

**Event**: A complete competitive gathering containing one or more rounds. Chapter events are typically single-round (approximately 2 hours total). Regional and championship events are multi-round days, typically 4-5 rounds with appropriate breaks (8-10 hour days).

**Submission**: The web application a player produces during a round, including its README documentation.

**Substrate**: The complete competitive environment — workstation, sanctioned AI model, package mirror, network configuration, and league infrastructure.

**Hacklet**: Both the event format and the output a player produces. "I'm competing in a hacklet" and "I built a hacklet" are both correct usages.

## 3. The Round

A round is the atomic unit of hacklet competition. From opening to next-round-introduction, a complete round cycle runs approximately 2 hours. The structure is designed to produce broadcast-quality competition while making efficient use of time through concurrent activities.

### 3.1 Round Opening (T+0:00 to T+5:00)

The round begins with five minutes of opening. The host welcomes the audience, frames the round (which tier, what's at stake, where this fits in the season), introduces contestants individually, and confirms readiness. Players are seated at their workstations but workstations remain locked. This is *transition time* — not idle, but oriented preparation. The opening creates production rhythm and lets the audience invest in the round before competition begins.

### 3.2 Build Phase (T+5:00 to T+29:00)

At T+5:00, the central system simultaneously unlocks all workstations and reveals the round prompt. Players have 24 minutes to construct a web application of their choice.

There are no required features. There are no mandated architectures. Players build what they choose to build. The scoring system, not the rules, shapes player decisions about what to build.

Players direct the AI substrate through the league competition website. They write code in the provided IDE. They invoke fuzz tests against their own work to gather intelligence about defensive coverage. They allocate their token budget and fuzz budget as they see fit.

At T+29:00, code freeze takes effect simultaneously across all workstations. The network cuts for code changes. All build activity ceases — no further coding, no agentic edits, no fuzz invocations against the workstation. AI responses mid-generation are truncated at the freeze point and any code changes from those partial responses roll back to the pre-prompt state. The submission is what existed at freeze; nothing later contributes to the code. The AI chat interface itself remains available for pitch preparation (see §3.3).

### 3.3 Concurrent Evaluation and Pitch Preparation (T+29:00 to T+47:00)

For 18 minutes after code freeze, *judges and players work in parallel*:

**Code submission and central fuzzing.** At freeze, each workstation copies its final code state to league infrastructure via SCP to a service-account path (`/opt/hacklet/submissions/$EVENT_ID/$USER/`). League infrastructure receives each submission, deploys it in an ephemeral container with an assigned port, and executes the full authoritative fuzz catalog — both public and hidden pools — against the deployed submission. This central testing is what counts for scoring; local fuzz during build was intelligence-gathering only. Post-competition, completed submissions are published to the public HackLet git org with player attribution as part of the credentialing artifact archive.

**Judges evaluate submissions.** Judges interact with each submission live in their portals while the fuzz runner completes its work. The panel includes specialized roles:

- One judge serves as **tester** — operating a portal that displays automated test applicability decisions, with override capability for cases where automated detection missed or misidentified features.
- One judge serves as **UX designer** — assessing user experience, interaction quality, visual hierarchy, and intuitive navigation. Brings professional design expertise to evaluation.
- Remaining judges conduct **general engineering evaluation** — assessing creative coherence, derived feature correctness, technical execution, and documentation quality.

With 18 minutes for 8 submissions across 4 judges, each judge has approximately 9 minutes per submission for substantive evaluation. The fuzz runner output gives them a quick technical baseline; clickaround surfaces what automation can't measure.

**Players prepare their pitches.** Code files become read-only at freeze (no further edits possible) but players retain access to their submitted code, README, and the AI chat interface for pitch preparation. Agentic edit capabilities are disabled at freeze; chat-only AI assistance remains available. Players who tokenmaxxed during the build phase have no AI assistance for prep — that strategic tradeoff is part of the format's resource calibration test. Players digest what they built, plan their pitch, anticipate likely cross-examination questions. This is recovery time from build intensity and strategic preparation for what comes next.

Both activities consume the same 18-minute window. Neither party waits on the other.

### 3.4 Pitch and Cross-Examination (T+47:00 to T+75:00 for 8 players)

Each player presents in sequence:

- **60 seconds** of pitch — what they built, key choices, what makes their submission distinctive
- **120 seconds** of cross-examination — judges ask questions in turn, each judge limited to one substantive question per player (four judges, four questions, roughly 30 seconds per question including the answer). Verbose answers cost remaining question slots.
- **30 seconds** of transition — next player gets situated, audience and judges briefly reset

At 3.5 minutes per player, this phase runs 28 minutes for the 8-player standard round size. The expanded 120-second cross-examination (up from 60 seconds in earlier format drafts) reflects that four judges produce substantively more questions than three, and that the Stakeholder Judge role (when introduced) operates differently from technical questioning and benefits from the additional time.

Same-archetype submissions (multiple players who built similar applications) pitch back-to-back to enable direct comparison and require explicit differentiation arguments.

### 3.5 Deliberation and Voting (T+75:00 to T+93:00)

After all pitches and cross-examinations conclude, judges enter explicit deliberation for 18 minutes:

- Compare what they witnessed during pitches against what they observed during clickaround
- Re-visit submissions for additional non-fuzz clickthrough now informed by player framing
- Read README content more carefully with player context
- Discuss scoring discrepancies between judges
- Finalize scores with proper consideration

During this same window, the audience votes for **People's Hacklet** through the league app. The audience has now seen all pitches and can make an informed choice rather than voting blindly during competition.

### 3.6 Award Reveal and Closing (T+93:00 to T+107:00)

Categorical awards are revealed in ascending order of prestige, culminating in the Best Overall (composite champion) reveal. Standard award sequence:

1. Most Efficient
2. Best UX/UI
3. Best Pitch
4. Most Novel
5. Most Resilient
6. People's Hacklet (audience favorite, revealed second-to-last for dramatic pacing)
7. Best Overall (composite champion)

Award reveal includes brief commentary on the winner's submission, allowing the audience to understand why each award was earned. Closing announcements wrap the round — thanks to judges and venue, recognition of all participants, preview of what comes next.

### 3.7 Zamboni Period (T+107:00 to T+135:00)

Between rounds, a 25-30 minute Zamboni Period runs operational transition:

- Per-player accounts are torn down and recreated: the outgoing player's ephemeral, non-sudo Unix account is deleted (`userdel -r`, wiping the home directory and session state) and a fresh one is provisioned from `/etc/skel` for the incoming player — seconds per workstation, system state untouched. Full image restoration is the *exceptional* operation (between events, on tamper detection, scheduled maintenance), not the per-round reset
- Outgoing players depart and incoming players are seated
- Judges file final scores from the completed round and refresh their tools
- Broadcast commentary covers recap and preview
- Audience takes needed breaks
- Production team resets any equipment

Approximately 5 minutes before the next round's opening (i.e., at T+130:00 of the current cycle), the next round's pre-introduction begins, bridging smoothly into the next round's opening. This produces a *continuous narrative flow* across multi-round events rather than discrete events with dead time between.

### 3.8 Round Sizing Notes

The 2-hour round cycle assumes 8 players — the standard target for broadcast quality and credentialing distribution. Round size varies within an acceptable operational range of 6-12 players:

- **8 players (standard)**: Full 2-hour round cycle. Best balance of broadcast tractability, judge evaluation depth (9 minutes per submission), categorical award distribution across varied competitors, and field variety for narrative threads. The format's foundational design point.
- **6-7 players (smaller events, pilot circumstances)**: ~105-115 minute round cycle (saves time in the pitch/cross-ex phase at 3.5 min per player). Appropriate for early chapter events, pilot rounds, or recruitment-constrained operations.
- **9-12 players (larger events with operational capacity)**: ~125-145 minute round cycle. Acceptable when needed but operates with reduced narrative depth per player.

The 8-player standard follows the FMWC precedent: their "888 Battle" (June 2021, 8 players) was the format that catalyzed Excel esports as a viable broadcast category and led to ESPN2 broadcast presence by 2022. FMWC's All-Star Battle 2022 on ESPN2 was also 8 players. Empirically, 8 is the broadcast-tractable cap for live single-event credentialing competition. 8 also leans into the cultural resonance of the number across the international competitive engineering audience HackLet operates within.

While the structural maximum remains 12 players per round, beyond 8 the per-player narrative depth degrades and judge evaluation time per submission tightens uncomfortably. Events with more than 8-12 players-worth of demand should add additional rounds rather than enlarge individual rounds.

### 3.9 Broadcast Architecture

Hacklet is designed as a watchable competitive format. Broadcast infrastructure is integral to the design, not an afterthought.

**Workstation screen capture.** Each player's workstation streams its display to league infrastructure during build and pitch phases. Broadcast directors select which workstation feed serves as the primary view at any moment, with picture-in-picture composites possible for showing multiple players simultaneously. Eight simultaneous feeds give directors abundant material to work with while staying tractable for director attention and audience cognitive load.

**Per-player stats overlays.** League-supplied stats overlays display in real-time alongside workstation views:

- Token budget remaining (shows how much AI access the player has left)
- Time remaining in the current phase
- Fuzz budget remaining (shows how many more probes the player can run)
- Accumulated fuzz score from player-triggered tests (the visible measure of build progress)

These metrics make engineering decisions legible to audiences. "Alex has 2000 tokens left, no room for a refactor" is real broadcast narrative produced directly from the metrics.

**Live player-fuzz leaderboard.** A sortable display of all players ranked by accumulated player-triggered fuzz score, updating in real-time as players invoke fuzz throughout the build. This generates running narrative arcs: who is ahead, who is climbing, who is falling behind, who is gambling on minimal testing.

**The suspense gap.** The player-triggered fuzz score is visible throughout build. The authoritative scoring including hidden test results is revealed only at code freeze. The gap between these — sometimes wider, sometimes narrower — generates the format's central dramatic tension. Did the player's high score reflect genuine architectural defense, or did the hidden tests reveal gaps the player never probed? Was the player's low score because they avoided testing, or because they had limited coverage? Every reveal is a story beat.

**Commentary infrastructure.** Commentators have access to all metrics for all players via a dedicated dashboard, enabling them to discuss any player meaningfully even when the primary broadcast feed is elsewhere. Commentary vocabulary develops naturally from the format's mechanics: "defended SQL clean," "hammered on uploads," "burning tokens fast," "saved fuzz budget for the closer."

**Production responsibility.** Chapters running broadcast-quality events (tier A) provide the production infrastructure: screen capture from workstations, audio/video of the venue, stream director coordination. The league provides the stats overlays and metrics feeds that production composites into the final broadcast. The league does not operate cameras or run production directly — chapters handle production within league standards.

## 4. Scoring

### 4.1 Component Structure

A player's performance is measured across three components:

- **Fuzz Score**: Sum of signed points across all applicable tests
- **Pitch Quality**: Judge evaluation on a 0-100 scale, averaged across the panel, incorporating judge clickaround findings
- **Cross-Examination Performance**: Judge evaluation on a 0-100 scale, averaged across the panel, scoring substance and conciseness

Each component is reported as a raw score and used in category awards. The Best Overall determination uses rank-based composition rather than weighted-sum.

### 4.2 Fuzz Scoring Philosophy

Fuzz scoring is signed at the test level. Each test specifies its own point values for each possible outcome:

| Outcome | Score |
| --- | --- |
| Defended | Positive value (varies by test) |
| Gracefully Handled (when applicable) | Smaller positive value |
| Not Applicable | Zero |
| Broken | Negative value (varies by test) |

Point values are calibrated using a five-axis methodology:

1. **Frequency**: How commonly this vulnerability appears in real applications
2. **Ease of Exploit**: How much attacker skill, time, and tooling is required to exploit successfully
3. **Severity**: Direct impact when exploitation succeeds, independent of application context
4. **Contextual Impact**: How the application's specific context amplifies or reduces severity
5. **Patching Difficulty**: How hard the correct defense is to implement

Scoring values derive systematically from the axes. Vulnerabilities with high frequency and low patching difficulty are scored asymmetrically — modest reward for defense (expected at competence baseline), large penalty for failure (represents negligence). Vulnerabilities with low frequency, hard exploitation, and high patching difficulty score the opposite — large reward for defense (demonstrates depth), modest penalty for failure (rare and difficult to anticipate).

A test produces the Gracefully Handled outcome only when the attack vector is non-adversarial in nature. Adversarial categories (SQL injection, authentication bypass, command injection) admit only Defended or Broken outcomes, because graceful handling does not prevent an iterating attacker from eventually succeeding. Non-adversarial categories (input validation, type coercion, resource limits) admit graceful handling because the inputs may come from confused users rather than active attackers.

**Variant Groups**: Some categories contain "variant groups" — sets of tests probing the same logical attack with different syntactic presentations (e.g., SQL injection across different comment syntaxes). These exist where a single correct architectural defense (such as parameterized queries) handles all variants automatically. Within variant groups, point values are calibrated such that partial defense (defending some variants but missing others) typically nets zero or negative. This reflects the security-engineering reality that incomplete defense of the same logical attack often creates false confidence and should not be rewarded as equivalent to architecturally correct defense.

**Result Reporting**: A raw fuzz score in isolation can be ambiguous — a near-zero score could mean catastrophic failure (nothing deployed), strategic minimalism (limited surface), or balanced engagement (broad surface with mixed outcomes). To disambiguate, each submission's result reports the raw fuzz score alongside contextual metadata:

- **Status**: Completed, DNF (Did Not Deploy), or Limited Engagement (fewer than the threshold of applicable tests)
- **Tests Applicable**: Count of tests that produced non-N/A outcomes
- **Tests Defended / Gracefully Handled / Broken**: Outcome counts
- **Attack Surface Coverage**: Categorical descriptor (Narrow / Moderate / Broad) derived from applicable count
- **Defense Rate**: Defended count divided by Applicable count, expressed as a percentage

This metadata accompanies the raw score in event results, persistent rankings, and broadcast displays. The composite scoring math uses raw fuzz score for ranking, but interpretation of results uses the full reporting bundle. A player whose persistent rankings show consistent broad coverage with high defense rate has demonstrably different signal than one with consistent narrow coverage at any defense rate.

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

The 5-second timeout threshold is deliberately set above tight production targets (real-world abandonment begins around 3 seconds) to remain reasonable for 24-minute builds that cannot fully optimize for performance. Tighter performance metrics (Core Web Vitals — LCP, INP, CLS) are deliberately excluded from universal QA: they measure performance optimization rather than engineering correctness, and would penalize all submissions uniformly without differentiating skill. Performance-specific testing may appear in future format variants or as a separate categorical award.

**Intent-Dependent QA Properties** — idempotency, specific concurrency behaviors, duplicate handling, persistence semantics — are deferred from the initial catalog. These depend on what the app is supposed to do (a checkout requires idempotency; a chat may not), and rigorous testing requires intent declarations and applicability decisions that add complexity disproportionate to the measurement value for 24-minute builds.

Future format iterations may add structured intent-dependent QA testing as the format matures and operational experience reveals where this measurement value is needed. The initial catalog focuses on universal properties that produce honest measurement of engineering quality for the format's actual scope: applications built in 24 minutes by individual engineers directing AI assistance.

The README remains load-bearing for cross-examination and pitch context. Players describe their app's intent for judge interpretation during clickaround, but the automated test catalog does not depend on intent classifications for its initial implementation.

### 4.3 Best Overall (Composite Ranking)

The Best Overall winner is determined through rank-based composition with differential tiebreaking:

1. Players are ranked independently on Fuzz Score and Communication Score (Communication = average of Pitch Quality and Cross-Examination Performance).
2. Each player's Rank Sum equals Fuzz Rank plus Communication Rank.
3. Lowest Rank Sum wins.
4. Ties on Rank Sum are broken by **smallest absolute differential** between Fuzz Rank and Communication Rank. This rewards balanced performance across components.
5. Ties on both Rank Sum and differential result in co-Champions. No additional tiebreakers are applied.

Standard competition ranking (1224 method) is used for component ranking, with ties shared and subsequent ranks skipping accordingly.

This produces the right kind of Best Overall winner: the most balanced player among those with the strongest combined performance, rather than the player who dominated a single component.

### 4.4 Categorical Awards

Categorical awards use raw scores on their respective metrics, independent of Best Overall ranking:

- **Most Resilient**: Highest raw Fuzz Score
- **Best UX/UI**: Highest UX dimension score averaged across the judge panel (with UX designer judge's expertise particularly informative)
- **Best Pitch**: Highest raw Pitch Quality Score
- **Most Novel**: Judge consensus on creative direction
- **Most Efficient**: Lowest token usage among players in the top half of Best Overall standings
- **People's Hacklet**: Audience vote (separate from judge evaluation entirely)

Players may win multiple categorical awards. A categorical winner need not also win Best Overall, and the Best Overall winner need not win any specific category.

## 5. Substrate

### 5.1 Workstation

All players in an event work on identically-configured workstations supplied by the league or the hosting chapter. Workstations run a standardized Linux distribution as a normal desktop environment — players have access to an IDE, browser, terminal, file manager, and standard development tools, used the way an engineer would use any workstation. The substrate's anti-cheating boundary is enforced at the network layer rather than through application lockdown.

**The development environment is local to the workstation.** The IDE, code editor, file manager, terminal, and local deployment all run natively on the workstation. The league competition website supplies only the chat interface to the AI substrate plus event coordination (timer, fuzz triggers, budget displays, submission state). Players write code in their local IDE, deploy locally for testing, and interact with the league platform only through a browser tab pointed at the chat interface. There is no hosted IDE, no remote code editor, no cloud development environment. The platform is event coordination infrastructure, not a development environment.

**Classical substrate — IDE: VSCodium** (telemetry-free), preinstalled with language support for common stacks (Python, JavaScript/TypeScript, Go, Rust, Ruby), standard formatters, and basic git tooling. Vim/Neovim are also installed for players who prefer them. All AI coding extensions (Copilot, Cline, Continue, Codeium, etc.) are disabled at the policy level and cannot be installed — external AI access is forbidden by the substrate model. In Classical, the IDE is for code editing only; AI access flows through the chat window in the league portal (a browser tab pointed at hackletleague.com). The player codes in the IDE and switches to the browser to direct the AI, moving snippets across by hand. That copy-paste step is friction by design: every adoption of AI output requires deliberate human action. (Other formats configure the substrate differently — the future Agentic format replaces the chat window with a locked, league-built extension. See LEAGUE_OPERATIONS.md.)

**Local fuzz capability for intelligence gathering and broadcast suspense.** Workstations include a locally-installed fuzz runner containing the public test pool. During build phase, players trigger this local runner via the league portal; the runner executes against their local deployment and returns intelligence about their defensive coverage in seconds. The local runner does *not* contain the hidden test pool — hidden tests live only on league central infrastructure. Local fuzz results are informational only; they do not contribute to scoring.

The primary purpose of player-triggered fuzz is **broadcast watchability**. The visible accumulation of player fuzz scores during build creates real-time narrative for audiences and commentators. The gap between visible player-triggered scores and the authoritative hidden-pool results at freeze generates the format's central dramatic tension: did the player's high score reflect genuine defense, or did the hidden tests reveal gaps the player never probed? Player fuzz is intelligence for the player; player fuzz score visibility is suspense for the audience.

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

The proxy exposes an **OpenAI-compatible chat completions endpoint** (`/api/v1/chat/completions`). This is deliberate: the OpenAI protocol is the de facto standard that chat clients, IDE extensions, and CLI tools all speak, so the substrate stays agnostic to client tooling — the Classical chat window today, an Agentic IDE extension later — without changing the API contract. Compatibility is surface-only: the league pins the season's model, enforces token and fuzz budgets and rate limits server-side, and audits every call. Clients cannot select the model, exceed budget, or bypass logging. Substrate equality holds regardless of which client a player uses.

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

- *Submission does not compile or fails to deploy at all*: Automatic zero on all fuzz tests. The submission may still proceed through pitch and cross-examination, where the player may discuss what they attempted.
- *Submission deploys but specific features error during testing*: Each broken feature scores per the relevant test catalog entry — a feature that exists but crashes when used is "Broken," not "Not Applicable." The player is penalized for shipping broken features in proportion to which features were affected.
- *Submission deploys and behaves consistently*: Standard fuzz scoring applies across all applicable test categories.

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

- **Chapter events**: Local events run by individual chapters, typically 6-8 players, monthly cadence. May be single-round (approximately 2 hours) or multi-round day events depending on chapter capacity.
- **Regional events**: Cross-chapter events with broader participation, quarterly cadence, typically multi-round day events (3-5 rounds across 8-10 hours) to justify travel for visiting players.
- **Championship events**: Season-culminating events with the strongest field, typically multi-day with multiple rounds per day.

Every individual round operates at **8 players as the standard**, with **6-12 as the acceptable range** and **12 as the structural maximum**. Beyond 8, per-player narrative depth degrades and judge evaluation time tightens. Beyond 12, broadcast quality breaks. Events with more than 8-12 players-worth of demand should add additional rounds rather than enlarge individual rounds.

**Round size targets**:

- *Standard (8 players)*: The format's foundational design point. Full 2-2.5 hour round cycle. Best broadcast quality, judge evaluation depth, and categorical award distribution. Validated by FMWC precedent (888 Battle, ESPN2 All-Star Battle).
- *Smaller (6-7 players)*: ~105-115 minute round cycle. Acceptable for early chapter events, pilot rounds, recruitment-constrained operations. Tighter per-player narrative.
- *Larger (9-12 players)*: ~125-145 minute round cycle. Acceptable when needed but operates with reduced narrative depth per player and tighter judge evaluation time.

**Standard 8-player round cycle (~2-2.5 hours)**:

- T+0:00 to T+5:00: Round opening (5 min)
- T+5:00 to T+29:00: Build phase (24 min)
- T+29:00 to T+47:00: Concurrent evaluation and pitch preparation (18 min)
- T+47:00 to T+75:00: Pitch and cross-examination (28 min, 3.5 min per player including 60s pitch + 120s cross-ex + 30s transition)
- T+75:00 to T+93:00: Concurrent deliberation and audience voting (18 min)
- T+93:00 to T+107:00: Award reveal and closing (14 min)
- T+107:00 to T+135:00: Zamboni period with next round pre-introduction beginning at T+130:00 (25-30 min)

Multi-round events host multiple rounds with different player groups across the day, using the same physical workstations. The Zamboni Period between rounds serves several functions:

- Per-player accounts are torn down and recreated: the outgoing player's ephemeral, non-sudo Unix account is deleted (`userdel -r`, wiping the home directory and session state) and a fresh one is provisioned from `/etc/skel` for the incoming player — seconds per workstation, system state untouched. Full image restoration is the *exceptional* operation (between events, on tamper detection, scheduled maintenance), not the per-round reset
- Outgoing players depart and incoming players are seated
- Judges file scores from the completed round and refresh their tools
- Broadcast commentary covers recap and preview, with next-round introduction beginning in the final 5 minutes
- Human participants take needed breaks
- Production team resets equipment as needed

Multi-round structure makes hacklet events economically viable for travel: a full day of competition with 4-5 rounds justifies driving or flying from distant chapters. It also produces substantial broadcast content, amortizes venue and production costs across many rounds, and creates continuous narrative flow between rounds rather than discrete events with dead time.

HackLet League is **ranked competition, not bracketed elimination**. All players in a round compete simultaneously and are ranked at completion. There is no head-to-head matchup structure, no advancement through rounds within an event, no losers' brackets. The format follows the precedent of individual measurable performance sports (track and field, swimming, cycling time trials, financial modeling competitions) rather than combat sports or single-elimination tournaments.

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

The Classical substrate's chat-window-and-copy-paste workflow is not an arbitrary choice — it matches the economically-dominant practice among the format's target population. Agentic IDE tooling (Cursor, Claude Code, Cline) requires either paid subscriptions or student-verification with friction that filters most undergraduate users; the chat-window workflow remains the only fully-free option for most CS students. Classical meets its audience where they already work. The Agentic format, when introduced, measures a more specialized skill that a smaller but growing subset of engineers practices.

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

The industry is grumbling about slop in 2026, and the grumble is documented. The Harness 2026 State of Engineering Excellence report finds 31% of a developer's day consumed by AI verification overhead. 81% of engineering leaders report increased code review burden since AI deployment. The Harvard Business Review estimates work-SLOP costs roughly $9 million per year per 10,000 employees. The MIT Media Lab finds 95% of organizations see no measurable return on AI investment. Engineering communities have organized vocabulary around the failure mode — "vibe coding," "tokenmaxxing," "slop register," "death loops" — and developed countermeasures (intent-driven verification, slop registers, AI Code Assurance). HackLet enters this moment with credentialing infrastructure that answers a specific market need: engineers who can operate effectively in AI-augmented environments without producing slop, and engineers who can remediate the slop others produce.

The two-format structure covers both halves of the anti-slop engineering profession. **HackLet Vibe** credentials producing code that isn't slop. **HackLet Unslop** credentials identifying and remediating slop in existing code. Together they map to the full surface of AI-augmented engineering work. The strategic articulation is simple: people grumble about slop, so HackLet makes anti-slop a sport, televises it, and credentials those who excel at it. The grumble is the market; the format is the product.

HackLet does not legislate AI usage style — any interface is fine (chat, agentic, command-line) so long as calls flow through the league's API and stay within budget. What matters is what survives the fuzz at code freeze, regardless of who or what produced it. The two principles (§10) are sufficient; the format evaluates nothing else.

The fuzz is what separates hacklets from slop.

---

*This document is the executive summary of the HackLet League rules. The complete rulebook contains formal specifications, edge case handling, appeals procedures, technical appendices, and case precedents accumulated through league operation. Players are responsible for familiarity with the full rulebook for the tier and season in which they compete.*
