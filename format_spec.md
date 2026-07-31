# HackLet League — Format Specification

*Executive summary of the official rules. The complete rulebook addresses every edge case in detail; this document establishes the format's identity, mechanics, and core operating principles.*

> **Reading the status markers.** Each section below carries a `Status:` line: **BUILT**
> (exists in code, cited to file and line), **DESIGNED** (specified, not implemented),
> **MIXED**, or **SUPERSEDED** (describes a decision that has been replaced). Timing blocks
> additionally carry **ILLUSTRATIVE**. Classifications were verified against source, not
> against other documents. The full audit — including every known cross-document
> contradiction — is in [DOC_STATE.md](DOC_STATE.md).

---

## 1. What HackLet League Is

> **Status: DESIGNED** — the format's identity. `Event.format` accepts all three values as of 2026-07-31, so the matrix is now recordable (DOC_STATE C-14 closed). Recordable is not the same as run: only **Vibe** has ever operated, and Unslop and Underspecified are introduced in that order as each predecessor stabilises.

**In one sentence: hackathon, but minutes instead of hours, with a cheering audience.**

HackLet is an institution that runs competitive formats, not a single immutable format. Format names follow a two-axis structure: **HackLet {Format} {Timer}**.

- **Format axis** — what the player does. **Vibe** (build an application from scratch under AI assistance), **Unslop** (remediate a deliberately-broken application generated server-side and distributed to all players at round opening), or **Underspecified** (build a solution to a deliberately vague, ill-formed client prompt, making and defending interpretive decisions under ambiguity).
- **Timer axis** — how long the build phase runs. **XP** (12 min), **Sprint** (24 min), **Scrum** (36 min), **Agile** (48 min), **Waterfall** (72-96 min). Token budgets scale with the timer.

3 formats × 5 timers = **15 sanctioned variants** in the operational matrix.

The foundational format is **HackLet Vibe Sprint** — 24-minute build phase from scratch. It is the format described in detail by this document and the one the BU pilot operates. **HackLet Unslop Sprint** is documented as the canonical second format and is introduced once Vibe is operationally stable. **HackLet Underspecified Sprint** is the canonical third, introduced after Unslop is stable. Longer and shorter timer controls follow as the league matures. Future format introductions follow the same naming convention without renaming what came before.

**The league does not legislate AI-interaction style.** Where the league hosts AI substrate (Tier B and Tier A), players are served *both* a chat-window interface and an in-IDE agent interface from the same league-controlled infrastructure with a *unified token budget* across all interfaces. Players choose whatever combination of chat-style brainstorming and agent-style execution fits their workflow. This matches how real engineering with AI actually happens: fluid switching between modes, with strategic discipline coming from how the player navigates the substrate rather than which mode the format forces them into. Where the league does not host AI substrate (Tier C, BYOD), players use whatever AI tools they choose. The "Relationship" axis that earlier drafts of the format spec used to distinguish Classical from Agentic has been retired in favor of the unified-substrate model, which is more honest to the format's "we don't legislate how you use AI" thesis (§10).

HackLet Vibe Sprint is a competitive format for AI-assisted technical building under extreme time compression. Players have 24 minutes to construct, document, and defend a web application, working alone on a locked-down workstation (Tier A/B) or their own laptop (Tier C) with sanctioned AI substrate access. Submissions are evaluated through automated adversarial testing, judge inspection, and live questioning. Multi-axis scoring produces categorical awards alongside an overall composite ranking.

The format borrows time-compression from bullet chess, multi-axis scoring from gymnastics and decathlon, regional feeder structure from CTWC, and tier organization from FMWC. What it adds is novel: systematic adversarial testing of AI-assisted submissions under tournament conditions. The 24-minute build duration deliberately parallels the 24-hour hackathon, positioning hacklet as a compressed-format descendant of hackathon culture rather than a replacement for it.

The name **Vibe** is deliberate. "Vibe coding" entered industry vocabulary in 2025 as a complaint — engineers directing AI rapidly without verification, producing slop at scale. HackLet reclaims the term. Vibe coding done by skilled engineers under proper conditions is real professional capability. HackLet Vibe champions demonstrate vibe coding *with* verification reflex, *with* defensive depth, *without* producing slop. The format name stakes territory in the industry's vocabulary dispute: vibe coding is a skill, and the league credentials those who practice it well.

A complete round cycle runs anywhere from ~60 minutes (the Tier C MVR) to ~135 minutes (the full Tier A broadcast profile), with the 24-minute build forming the competitive core. This structure makes multi-round day events practical for regional and championship competition while preserving broadcast quality through proper time allocation for evaluation, pitches, deliberation, and award reveals. Human-judged rounds are bounded at 8 players standard (6-12 range, 12 maximum); LLM-judged Tier C cohorts scale higher (§3.2). Events host one or more rounds; regional and championship events typically run multi-round days.

HackLet League is built for engineers who want to develop and demonstrate the cluster of skills AI-assisted defensive coding requires: prompting fluency, verification reflex, resource calibration, and defensive depth. It is not a beginner-friendly format. It assumes participants have working knowledge of web development and at least introductory familiarity with security concepts. Players who do not yet have those foundations are welcome to attend events as spectators and participate when their preparation matches the format's expectations.

## 2. Core Definitions

> **Status: DESIGNED** — Round, Event and Submission exist as platform entities; Substrate does not.

**Player**: An individual competitor registered in the appropriate tier.

**Round**: A complete competitive cycle — opening, build phase, evaluation, communication (written PITCH.md or live pitch + cross-examination), judging/deliberation, and award reveal, plus a zamboni reset where controlled workstations are used. The atomic unit of competition. The phase *sequence* is tier-agnostic (§3.1); phase *timing* varies by tier and profile — the full Tier A round runs ~135 min, the Tier C MVR ~60 min (see TIER_A_OPERATIONS.md and TIER_C_OPERATIONS.md).

**Event**: A complete competitive gathering containing one or more rounds. Chapter events are typically single-round (~1 hour for an MVR, up to ~2 hours for a full Tier A round). Regional and championship events are multi-round days, typically 4-5 rounds with appropriate breaks (8-10 hour days).

**Submission**: The web application a player produces during a round, including its README documentation.

**Substrate**: The complete competitive environment — workstation, sanctioned AI model, package mirror, network configuration, and league infrastructure.

**Hacklet**: Both the event format and the output a player produces. "I'm competing in a hacklet" and "I built a hacklet" are both correct usages.

## 3. The Round

A round is the atomic unit of hacklet competition. The round phase sequence is tier-agnostic — every tier operates the same underlying phases — but specific timing within each phase varies by tier per the operational template. See TIER_A_OPERATIONS.md, TIER_B_OPERATIONS.md, and TIER_C_OPERATIONS.md for tier-specific timing profiles.

> **ILLUSTRATIVE — every timing profile in these documents is a suggested itinerary, not a
> normative schedule.** Published timestamps (T+0, T+29, T+135, and the rest) establish
> *sequence and proportion*, not wall-clock law. Real events start late, overrun, and absorb
> delay. Phase *durations* are the design commitment; the absolute times are a worked example
> at a hypothetical on-time start.
>
> The operational consequence: **every enforced rule keys off round state, never off a
> timestamp.** The proxy gate asks whether the round is still in its build phase, not whether
> the clock reads T+29. The same holds for submission capture, the read-only flip, and budget
> enforcement. A round that opens nine minutes late must behave identically to one that opens
> on time. Wherever this document or an operations document says a rule takes effect "at
> T+29:00," read it as "at build end."

### 3.1 Round Phase Sequence

> **Status: MIXED** — the phase *clock* is BUILT (`backend/rounds/services.py:14-47`). SCP capture, the ephemeral container, the local fuzz runner and the proxy cutoff are all DESIGNED.

Every HackLet round operates the following phase sequence:

**Opening / Round Introduction**: host welcomes the room, frames the round (which variant, what's at stake, where this fits in the season), introduces players. Workstations or laptops remain locked or unprepared. This phase establishes orientation and (at Tier A) production rhythm.

**Build Phase**: the central system simultaneously unlocks all workstations and reveals the round prompt. Players have the variant's timer (24 minutes for Sprint, 12 for XP, 48 for Agile, etc.) to construct a web application. No required features, no mandated architectures. Players direct AI substrate however they choose within tier constraints. At freeze (build phase end), the network cuts for code changes, all build activity ceases — no further coding, no agent-interface edits, no fuzz invocations. The submission is captured and deployed at this instant, and grading reads the deployed copy from here on, so later edits reach nothing that is scored. The AI substrate stays available into pitch preparation on the same budget (§5.5).

**Evaluation Phase**: at freeze, submissions move to scoring infrastructure. Submission mechanism varies by tier — SCP from controlled workstations at Tier A/B, portal upload with grace period at Tier C (see tier docs for specifics). League infrastructure receives each submission, deploys in an ephemeral container, executes the full authoritative fuzz catalog (both public and hidden pools). Central testing scores submissions; any local fuzz invocations during build were intelligence-gathering only. Post-competition, submissions are published to the public HackLet git org with player attribution as part of the credentialing artifact archive.

**Pitch Preparation Phase**: code files become read-only at freeze. Players retain access to submitted code, README, and AI assistance for pitch preparation, drawing on the same token budget they built with (§5.5) — reading your own code is most of what preparing a pitch is, and the graded artifact is already captured, so the assistance cannot change it. Players digest what they built, plan their articulation, anticipate cross-examination questions. Players also author **PITCH.md** documenting defensive choices, design rationale, and strategic decisions — this artifact is the canonical written communication artifact in the Tier C MVR (LLM-judged) and serves as pitch prep material at Tier A/B and Tier C Extended (where live pitch is the primary credentialing dimension). See PITCH.md template per TIER_C_OPERATIONS.md §7.

**Pitch and Cross-Examination Phase**: human judges evaluate live performance at Tier A, Tier B, and Tier C Extended. Each player presents in sequence:
- Pitch — what they built, key choices, distinctiveness
- Cross-examination — judges ask questions in turn, each judge limited to one substantive question per player. Verbose answers cost remaining slots.
- Brief transition before next player

Specific timing per player (3.5 minutes at Tier A's standard 8-player rounds) and judge corps composition vary by tier. Same-archetype submissions (multiple players who built similar applications) pitch back-to-back to enable direct comparison.

In the Tier C MVR profile, live pitch + cross-examination is replaced with LLM-judged evaluation of PITCH.md + README + fuzz results (which also lets the MVR scale to large cohorts human judging couldn't). See TIER_C_OPERATIONS.md §8 for LLM judging architecture.

**Deliberation and Voting Phase**: judges enter explicit deliberation. All four sit together — the nontech stakeholder is in the room with the three technical judges — but the stakeholder scores on a **separate rubric**, because translation and trust to a non-verifier is a different measurement from technical defense, and running it through a technical lens loses the thing that role exists to catch. Judges compare what they witnessed during pitches against clickaround observations, re-visit submissions with player framing context, and score across their own rubrics.

**Deliberation produces scores, not winners.** Slopless Builder, the communication award, and Best Overall are all computed from the scores afterwards (§4.3, §4.4). No panel votes on an outcome. This matters behaviourally: a judge who believes they are deliberating toward a verdict argues differently from one who knows they are deliberating toward their own number. Concurrent with judge deliberation (when audience is present), audience votes for People's Hacklet through the player portal.

**Award Reveal and Closing Phase**: ceremonial reveal of categorical awards followed by Best Overall reveal. At Tier A with broadcast production, the 14-min window allocates time for theatrical ceremony with audience reaction and broadcast cuts. At Tier B and Tier C, compressed ceremony fits the operational profile (~7 min at Tier C MVR).

**Zamboni Period** (when controlled workstations are used): workstation reset for next round. League daemon executes `userdel -r` for each player's ephemeral account, removes home directory content. Workstations rebooted to master image. Network state reset. Per-player accounts re-provisioned for next round. Audience break period. Tier C events with BYOD substrate skip the Zamboni Period because there are no ephemeral accounts to reset.

### 3.2 Round Sizing

> **Status: DESIGNED** — no player cap is enforced anywhere; `Round.player_count` is a free integer. **Revised 2026-07-31**: the old "12 is the structural maximum" claim is retired, and DOC_STATE C-08 is resolved in favour of the broadcast reading.

**The unit that has a size limit is the panel, not the event.** A panel is four judges and the players they hear, and its ceiling comes from one place: pitch and cross-examination run in sequence, so the phase grows linearly with the number of players a single panel must sit through. **8 players per panel** is standard, **6-12** is the workable range, and beyond that the phase stops fitting a sensible clock.

**An event is not bounded by that.** Panels run **concurrently**, with players assigned across them, so a larger event gets *wider* rather than *longer*. Panel count is not capped by the format. What it costs is judges: four permanent roles per panel, so 24 players is three panels and twelve judges. That is the real constraint on event size, and it is an operations question for the chapter rather than a rule of the format.

Queue depth is the thing to watch. At a depth of 8, the last player in a panel's queue has waited through seven pitches — roughly 42 minutes of preparation against the first player's 18. That gap is a real and deliberate inequality, and it widens with depth, which is why panels get added rather than deepened.

**The 8-player cap is a broadcast constraint, and it binds only where there are cameras.** A **televised Tier A** round caps at **8 players**: eight streams composite onto an overlay, eight faces stay visible to the audience, and the award ceremony keeps its rhythm. That is a production limit, not a scoring one. An **untelevised Tier A** event has **no maximum** — it adds panels and judges to match its field. Tier B is the same. The **Tier C MVR** scales furthest, to 30-100+ players, because LLM judging runs in parallel and has no queue at all (TIER_C_OPERATIONS.md §5).

Nothing about grading changes with size. The catalog runs identically per submission no matter how many panels the event needs.

### 3.3 Broadcast Considerations

> **Status: DESIGNED** — no broadcast infrastructure exists (Stage 6).

Broadcast production is **Tier A only**. The broadcast infrastructure requires controlled workstations that can be screen-shared without compromising player privacy — a constraint that BYOD substrates (Tier C) preclude entirely and that Tier B's optional workstation hosting doesn't necessarily provide. See TIER_A_OPERATIONS.md §6 for broadcast architecture details (workstation screen capture, per-player stats overlays, live player-fuzz leaderboard, suspense gap dynamics, commentary infrastructure).

At Tier B and Tier C, the format runs without broadcast production. In-person audience is optional. Asynchronous content (written results, post-event recaps, social media coverage) remains viable at all tiers for remote audience interest without requiring live broadcast.

## 4. Scoring

### 4.1 Component Structure

> **Status: DESIGNED** — **the shipped code implements a different decomposition.** `backend/rounds/scoring.py:24-33` averages six judge-entered facets into two axes and never reads `judge_specialization`; the 30/20/20/30 role weighting is unimplemented. A third decomposition (40/30/30) lives in TIER_C §8. See DOC_STATE C-01 and the DATA_MODEL EventParticipant flag.

A player's performance is measured on **two independent axes**:

- **Slop Score**: the amount of slop the fuzz catalog detected in the submission — a **deduction-only** score in the range **[0, +∞)** where **lower is better and 0 is the aspirational maximum** (a clean submission). It is the sum of per-probe penalties for every probe that detected slop; passing a probe, or not having the surface a probe targets, contributes nothing. Golf-style: you accumulate slop the way a golfer accumulates strokes — zero is perfect, and there is no bound on how much slop a broken submission can carry. Produced by the fuzz catalog (intent-independent universals); unchanged by the judging structure below.
- **Communication Score**: judge evaluation of live performance on a **[0, 100]** scale where **higher is better** — a **weighted composite of four permanent judge-role rubrics**, each scoring the player's pitch + cross-examination on its own rubric:
  - Tester **30%** — intent-*dependent* correctness (the fuzzer's blind spot)
  - UI/UX/HCI **20%** — the artifact's fitness for a human (legibility, actionable error states, the works-to-adopted gap)
  - General engineering **20%** — engineering judgment revealed by the choices, mostly recovered via cross-ex
  - Nontech stakeholder **30%** — translation and trust to a skeptical non-engineer, without jargon-drowning

The two axes are **never summed into one number** — they differ in direction (slop lower-is-better, communication higher-is-better), scale (slop unbounded, communication ranged), and epistemics (the fuzzer is pure objectivity; cross-ex is where subjectivity is allowed to live). Each is reported as a raw score and used in categorical awards; Best Overall is the rank-based composition of the two axes (§4.3). The four judge rubrics live entirely inside the Communication axis; the Slop axis is untouched by the judging structure.

The old model split communication into separate Pitch Quality and Cross-Examination Performance components; under the four-rubric model each judge scores across *both* pitch and cross-ex on their own rubric, so pitch-vs-cross-ex is at most an internal sub-structure of a rubric — the axis-level weighting is by judge role (30/20/20/30). Rubric internals are written separately.

> **OPEN — four rubrics, or two?** The weighting above is settled at 30/20/20/30 by judge role,
> and it is settled that the **nontech stakeholder scores on a rubric of its own** (§3.1). What
> is *not* settled is whether the three technical judges each hold a separate rubric or share
> one. NONTECH_JUDGE_NOTES §1 argues they should share: they measure a single trait — can this
> person defend technical decisions under informed adversarial pressure — through three entry
> angles, and three separate rubrics would pretend to measure three traits while producing
> incoherent scores that mostly record which judge pressed hardest. Adopting that would collapse
> the axis to **70/30** and reopen the locked weighting, which is why it has not been adopted.
> Decide before rubric internals are written; the internals depend on it.

### 4.2 Slop Scoring Philosophy

> **Status: DESIGNED** — no fuzz runner is integrated with the platform. Note the DATA_MODEL FuzzTest/FuzzResult schema still carries the *pre-deduction* award-points model (DOC_STATE C-02, handed to the platform session).

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

The 5-second timeout threshold is deliberately set above tight production targets (real-world abandonment begins around 3 seconds) to remain reasonable for 24-minute builds that cannot fully optimize for performance. *(**ASSUMED** — the 3-second abandonment figure is industry folk knowledge with no source cited here, and the 5-second threshold is reasoned from it rather than calibrated against submissions. The gate values below inherit this.)*

Speed is also measured as **boolean abandonment-threshold gates** in the performance bundle, distinct from optimization targets: TTFB ≥ 3s, FCP ≥ 5s, and INP ≥ 5s each add the speed category's slop penalty, with no marginal credit for being faster (a player clears the gate, then spends remaining time elsewhere). These are gates, not slopes — they catch only the egregiously broken, so they do not "penalize all submissions uniformly." TTFB is server-side and applies to any HTTP response; FCP and INP are browser-measured and apply only to apps that serve a rendered HTML document (a pure API scores them N/A). Optimization-target scoring of Core Web Vitals (for example crediting LCP < 2.5s on a slope) remains excluded: it measures performance tuning rather than engineering correctness. See FUZZ_RUNNER_SPEC.md for the gate mechanics.

**Intent-Dependent QA Properties** — idempotency, specific concurrency behaviors, duplicate handling, persistence semantics — are deferred from the initial catalog. These depend on what the app is supposed to do (a checkout requires idempotency; a chat may not), and rigorous testing requires intent declarations and applicability decisions that add complexity disproportionate to the measurement value for 24-minute builds.

Future format iterations may add structured intent-dependent QA testing as the format matures and operational experience reveals where this measurement value is needed. The initial catalog focuses on universal properties that produce honest measurement of engineering quality for the format's actual scope: applications built in 24 minutes by individual engineers directing AI assistance.

The division is architectural, not merely sequencing. The fuzz catalog is the **intent-independent** axis — properties true regardless of what the app was meant to do (it crashed, it leaked a secret, it shipped no CSP), measured objectively and deterministically. **Intent-dependent** properties — logical correctness, business-rule fidelity, whether the build does what its brief actually asked — cannot be reduced to intent-free predicates and are the domain of a **human tester judge** who, knowing the round's intent, exercises and scores them. The two axes stay separate by design: folding subjective intent-judgment into the objective slop score would forfeit the determinism and defensibility that make the slop score worth having. Logical errors are the canonical intent-dependent case — hard to test universally precisely because they *are* intent-dependent — so they sit with the judge, not the runner. The tester judge *extends* the fuzzer, reaching the intent-dependent correctness it cannot. The tester is one of **four permanent judge roles** whose weighted rubrics compose the Communication axis (§4.1); the other three — UI/UX/HCI, general engineering, and nontech stakeholder — grade the human-facing and trust dimensions the fuzzer never touches.

**No judge can void a finding.** The tester judge has **no override** on the slop score. A human authority to strike a probe result would make the slop score a function of *who judged it*, and that breaks four properties the score is built on at once: **reproducibility** (the same submission must score the same twice, which is what lets a whole discovery profile be cached and replayed deterministically), **comparability** (a slop score from one panel in one city has to mean what a slop score from another panel in another city means), **intent-independence** (the authoring invariant that a probe's correct outcome does not depend on what the app was for — an override is exactly the intent judgment the invariant exists to keep out), and **attribution at authoring time** (a probe's penalty is decided when the probe is written and reviewed, not at the scoring table). If a probe produces intent-dependent false positives, the probe is badly authored, and the catalog is where that gets fixed.

What the tester judge has instead is the **contest**. They may mark a finding CONTESTED, which records the probe, the submission, the judge, the timestamp, and a reason. It changes no score. **The round result is final** — HackLet reveals live, so there is no window between scoring and the ceremony in which a result could be revised, and there is no retroactive amendment of a completed round. Contests are reviewed between events and resolve into catalog changes going *forward*: a contest that turns out to be right improves the probe for everyone who competes after it, which is the durable fix rather than the local one.

This is not a demotion of the role, because the tester was never the fuzzer's editor. **The fuzzer cannot read code.** It is a black-box HTTP grader: it sends requests to a running app and scores what comes back, and it has no idea what the source says, what the app was for, or whether a behaviour was deliberate. (The one exception proves the rule — a static scan of the submission for hardcoded secrets, which exists precisely because that class never reaches the wire. It pattern-matches files; it does not comprehend them.)

That is the gap the tester fills. They *can* read the code, so they can see intent-dependent correctness the fuzzer structurally cannot reach, and they can ask a question in cross-examination that the player cannot bluff past. The tester **extends** the fuzzer into territory it cannot enter; it was never the tester's job to correct it inside its own territory.

So the tester's influence on the result is real but it runs through their **own score**: weight 30 of the 100-point Communication axis (§4.1). It does not run through the slop axis, which is produced entirely by the catalog. Two axes, two sources, no crossing. The fuzzer tests the artifact; the humans test the reasoning.

#### Living with false positives and false negatives

The catalog will be wrong sometimes. Removing the override does not pretend otherwise; it moves where the error gets fixed. **The score stands as computed, and the correction lands in the catalog for everyone who competes after.** That is a deliberate trade of local accuracy for reproducibility and comparability, and it is only defensible on the terms below.

**The two error classes are not symmetric, and only one of them is visible at an event.**

A **false positive** is loud. It fires on a specific submission, the player knows their app does not do that, and the tester judge has the code access to confirm it. This is what the contest is for, and contest volume per probe is the signal: one contest is noise, the same probe contested across four events is a broken probe.

A **false negative** is silent. Nobody disputes a score that came out too well. There is no contest, no complaint, and no trace at an event. **Contests structurally cannot surface false negatives**, so a quality process built only on contests fixes precision while recall quietly rots. Recall has to be measured off-event, against reference applications with known-planted flaws — anything a deliberately vulnerable reference does not score is a miss, by construction — on a schedule that does not depend on any event having happened.

**Four rules keep the trade honest.**

1. **The unit of correction is the catalog version, not the round.** Contests accumulate, are reviewed between events, and land as a versioned catalog change. Credentials cite the version, so "ranked 4th of 47 on the Q3 2026 catalog" stays true after Q4 repairs a probe.

   > **OPEN — the review itself is unspecified.** "Reviewed between events" names no reviewer,
   > no schedule, and no resolution states. Nothing in the doc set defines a cadence for
   > reviewing the format or the catalog; the nearest neighbours are §9's 30-day change-notice
   > rule, LEAGUE_OPERATIONS §11's 14-day appeal window, and the quarterly catalog versioning
   > sketched in IDEAS_FOR_LATER. The candidates are per-season (matches substrate rotation,
   > slowest to fix a mid-season defect), quarterly (moves with the catalog, more governance
   > than a one-chapter league can absorb), or event-triggered (cheapest now, but provides no
   > forcing function, which is how the current drift accumulated). Also undecided: who holds
   > the authority — today that is the superadmin by default, since no catalog-maintainer role
   > exists. Nothing is blocked on this until events run.
2. **Never recompute a finished round.** A quarantined or repriced probe applies to the next version forward. Retroactive correction would make a score depend on when you look at it, which is precisely the property removing the override exists to protect.
3. **Penalty weight is bounded by oracle confidence.** A heuristic oracle may not carry a catastrophic penalty. The issued-key exposure probe is the model: an exact match against a string the league itself minted, zero false positives by construction, which is *why* it can sit at the top of the scale. A pattern-matching scan for secret-shaped strings measures the same class far less certainly and must be priced far lower. Score the probe's confidence first, then let it bound the penalty.
4. **Publish the measured error rate.** This is the price of finality. A league that tells players "the score stands even when it is wrong" owes them a number for how often that happens, and a description of how the number was obtained. Stated tolerance is a defensible position; silence is not.

**What the player is not left with is nothing.** A contested finding becomes cross-examination material: the player explains why the flagged behaviour was deliberate and correct, and doing that well earns on the Communication axis, which is exactly the axis where human judgment is allowed to operate. The aggregation dampers help too — a variant group fires once, and repeated instances within a category carry diminishing marginal penalty — so a false positive that clusters does not multiply into a ruined score.

The README remains load-bearing for cross-examination and pitch context. Players describe their app's intent for judge interpretation during clickaround, but the automated test catalog does not depend on intent classifications for its initial implementation.

### 4.3 Best Overall (Composite Ranking)

> **Status: BUILT** — `backend/rounds/scoring.py:95-112` implements the rank-sum and all four tiebreakers in this order. It currently ranks a judge-entered engineering stand-in rather than a machine slop score.

The Best Overall winner is determined through rank-based composition with progressive tiebreaking:

1. Players are ranked independently on Slop Score and Communication Score (Communication = the 30/20/20/30 weighted composite of the four judge-role rubrics, §4.1). Slop is ranked **ascending** (lowest slop is rank 1, since lower is better); Communication is ranked descending (highest is rank 1). Because composition is rank-based, the unbounded range and lower-is-better direction of the slop score need no normalization — only the ranking direction differs.
2. Each player's Rank Sum equals Slop Rank plus Communication Rank.
3. **Lowest Rank Sum wins.**
4. Ties on Rank Sum are broken by **smallest absolute differential** between Slop Rank and Communication Rank. This rewards balanced performance across components.
5. Ties on both Rank Sum and differential are broken by **best Slop Rank** (favors the engineering side if still tied).
6. Ties on Rank Sum, differential, and Slop Rank are broken by **best Communication Rank** (favors the communication side if still tied).
7. Ties on all four criteria result in co-Champions. No additional tiebreakers are applied.

Standard competition ranking (1224 method) is used for component ranking, with ties shared and subsequent ranks skipping accordingly.

This produces the right kind of Best Overall winner: the most balanced player among those with the strongest combined performance, rather than the player who dominated a single component. The progressive tiebreaker hierarchy resolves nearly all real-world ties before co-Champion is declared, while leaving co-Champion as the honest outcome when players are genuinely indistinguishable.

### 4.4 Categorical Awards

> **Status: MIXED** — Slopless Builder, Best Communicator and Best Overall are BUILT (`backend/rounds/scoring.py:132-137`). People's Hacklet is DESIGNED and deferred. Most Efficient is retired here but listed as live in TIER_A §8 and TIER_B §8 (DOC_STATE C-06).

Per-round categorical awards are kept deliberately small to preserve credentialing signal at 8-player round size. Per-round awards alongside Best Overall (§4.3):

- **Slopless Builder**: Lowest raw Slop Score.

  **Why this name, recorded once so it stops drifting.** "Slop" descends from *AI slop* and *workslop* — the BetterUp Labs and Stanford Social Media Lab work published in HBR in 2025 — defined as AI-generated output that masquerades as good work while lacking the substance to advance the task. That is an **absolute property, not a rate**: work either carries slop or it does not, which is exactly why the score is deduction-only and unbounded rather than a percentage. **"Slopless"** names the metric directly: raw slop, low, ideally zero.

  **"Builder" is carried by the other axis, not by this one.** The obvious objection to rewarding an absence is that a player could win by shipping almost nothing. They cannot, because a minimal app has nothing to defend under cross-examination and sinks on the Communication axis, and Best Overall is the rank-sum of both (§4.3). The name says what the metric measures and lets the composite handle the rest.

  *(This replaces "Slopless Builder," which was kept on an aspirational-title argument — that the award should credential the quality while the score described the measurement, on the analogy of golf naming a "Champion" rather than a "Lowest Score Holder." That rationale is superseded and should not be reintroduced.)*
- **Best Communicator**: Highest raw Communication Score (the weighted four-rubric composite per §4.1/§4.3). Replaces the earlier "Best Pitch" award, which scored pitch only — Best Communicator captures the full communication dimension including defense under cross-examination. *(Award name flagged for a possible rename — credit defense-under-pressure over oratory — but unsettled; left as-is here.)*
- **People's Hacklet**: Audience vote (separate from judge evaluation entirely)

**Awards are scoped to the event that produced them; leaderboards are scoped to the tier.** Every award above is decided against the field that actually competed in that event, and against nothing else. A player can take Slopless Builder at a chapter event with a slop score of 20 while the global board's leader sits at 0, and both facts are correct: the award says *best in that room*, the leaderboard says *best across the tier*. They are answering different questions and are not required to agree.

This follows from concurrent panels (§3.2) as much as from geography. Two panels at one event, or two events in two cities, are judged by different people, and the league is multi-city with disjoint judge corps by construction — so judge variance is a property of the institution, not something concurrent panels introduce. **There is no cross-panel score anchoring and no severity correction.** What makes a Communication score portable between panels is that the four rubrics are role-siloed and the same everywhere, not that panels are calibrated against each other. What makes a slop score portable is that no human can touch it (§4.2).

This produces **3 per-round categorical awards plus Best Overall** for each round, regardless of event tier or structure. Players may win multiple awards (e.g., a dominant performer might win Slopless Builder + Best Overall in the same round). A categorical winner need not also win Best Overall, and the Best Overall winner need not win any specific category.

**Awards explicitly retired at per-round level**:

- *Best UX/UI*: per-round UX evaluation is too contextual; the award is meaningful only when judges have observed multiple submissions across rounds (moves to tournament-level)
- *Most Novel*: per-round novelty is too prompt-dependent; the award is meaningful only as "consistently novel approach across the tournament" (moves to tournament-level)
- *Most Efficient*: requires enforced token measurement, only meaningful at Tier A with league-hosted AI substrate (drops at Tier C; available at Tier A tournament-level)

**Tournament-level expanded categorical awards** are deployed at multi-day Tier A tournaments where judges observe each player across multiple rounds, making subtle categorical distinctions meaningful through aggregated evidence. See IDEAS_FOR_LATER.md "Multi-day Tier A tournament template" for the expanded set (Best UX/UI, Most Novel, Most Efficient, Iron Player, Comeback Player) and their allocation across qualifier-leaderboard vs finals-leaderboard.

> **OPEN — does the per-round cut also retire the tournament set?** The three-award per-round
> cut above is settled. What was never resolved is whether it applies only per-round, leaving
> the tournament-level set intact as written here, or whether the anti-award-sprawl argument
> should retire that set too. Keeping both is the status quo and preserves the
> specialisation-recognition case that sponsor-facing material leans on; retiring the
> tournament set maximises signal density but discards the IDEAS tournament design wholesale.
>
> **This gates Most Efficient**, which is currently listed as retired per-round here and as a
> live per-round award in TIER_A §8 and TIER_B §8 — including at Tier B, where budgets are
> honour-system and the enforced measurement it requires does not exist. Its rationale is
> weakened either way: an efficiency award measures little against a budget the docs describe
> as a runaway-loop ceiling rather than a binding constraint (§5.5). Decidable now; nothing
> blocks it.

The design principle is anti-award-sprawl: too many per-round categoricals at 8-player events means almost every player wins something, which destroys the *non-winning* signal that makes awards meaningful. Per-round awards stay tight; tournament-level awards expand because the field and round count justify richer categorical distribution.

### 4.5 Tradeoffs and the Absence of a Permanent Meta

> **Status: DESIGNED** — design rationale, no implementation surface.

A competition is healthy only when no single strategy dominates regardless of context — a "solved" game collapses skill expression into rote execution of the one optimal play. HackLet's scoring is built to prevent that. The axes genuinely **conflict under the clock**: time pushes toward shipping fast, the fuzz catalog punishes shipping slop, and communication/judge scoring rewards ambition the fuzzer would penalize. No strategy maximizes all of them at once, so the optimal play is situational — it shifts by format, by prompt, and by the player's own strengths. Tradeoffs under pressure, not a dominant meta, are what the design selects for.

This matters more here than in an ordinary game, because it is **instrumental to the credential**. If a permanent meta existed, the format would measure who best learned the meta — rote preparation — rather than who has the disposition: situational judgment. The game-design property and the credentialing goal are the same requirement: situational skill must beat memorized strategy.

Objective, transparent scoring introduces one specific hazard — Goodhart's law: when a known measure becomes the target, players optimize to the measure rather than the underlying quality (a checklist meta). Three properties defuse it. First, the **hidden pool** (§3.1, §5.1): the public catalog is learnable, but the authoritative grade includes hidden probes, so the real scoring function cannot be memorized and gamed. Second, the **judge axis**: decomposition, communication, and decision-quality cannot be checklist-gamed. Third, **benign gaming**: for compliance-style checks (security headers, accessibility presence), optimizing to the metric *is* doing the right thing, so transparency there causes no harm.

The design must also guard against a degenerate strategy *within* a variant. In **Underspecified**, the fuzzer and judge can pull opposite ways — a trivially small, clean build aces resilience while ducking the ambiguity entirely. The judge weighting must reward bold-but-defensible interpretation over timid-but-clean minimalism, or the variant would select for risk-aversion, the opposite of the disposition it exists to surface. The general rule: wherever an axis admits a dominant low-effort strategy, another axis must price it out.

## 5. Substrate

### 5.1 Workstation

> **Status: DESIGNED** — no workstation infrastructure exists (Stage 7).

All players in an event work on identically-configured workstations supplied by the league or the hosting chapter. Workstations run a standardized Linux distribution as a normal desktop environment — players have access to an IDE, browser, terminal, file manager, and standard development tools, used the way an engineer would use any workstation. The substrate's anti-cheating boundary is enforced at the network layer rather than through application lockdown.

**The development environment is local to the workstation.** The IDE, code editor, file manager, terminal, and local deployment all run natively on the workstation. The league competition website supplies only the chat interface to the AI substrate plus event coordination (timer, fuzz triggers, budget displays, submission state). Players write code in their local IDE, deploy locally for testing, and interact with the league platform only through a browser tab pointed at the chat interface. There is no hosted IDE, no remote code editor, no cloud development environment. The platform is event coordination infrastructure, not a development environment.

**Workstation environment — IDE: VSCodium** (telemetry-free), preinstalled with language support for common stacks (Python, JavaScript/TypeScript, Go, Rust, Ruby), standard formatters, and basic git tooling. Vim/Neovim are also installed for players who prefer them. Third-party AI coding extensions (Copilot, Cursor, Cline, Continue, Codeium, etc.) are disabled at the policy level and cannot be installed — external AI access is forbidden by the substrate model because the league hosts and audits the sanctioned AI substrate. Players access the league's AI substrate through two parallel interfaces, both routed through the same proxy with a shared per-player token budget: (1) the **chat-window interface** in the league portal (a browser tab pointed at hackletleague.com) for chat-style brainstorming and copy/paste workflow; (2) the **league-built signed VSCodium extension** for in-IDE agent operations (chat sidebar plus accept/reject UI). The extension ships in Stage 12 (BUILD_ROADMAP); the chat-window-only substrate is the foundational configuration. Players use whatever combination of interfaces fits their workflow — the unified token budget prevents tool-stacking advantage and the format does not legislate which interface to use.

**Local fuzz capability for intelligence gathering and broadcast suspense.** Workstations include a locally-installed fuzz runner containing the public test pool. During build phase, players trigger this local runner via the league portal; the runner executes against their local deployment and returns intelligence about their defensive coverage in seconds. The local runner does *not* contain the hidden test pool — hidden tests live only on league central infrastructure. Local fuzz results are informational only; they do not contribute to scoring.

The primary purpose of player-triggered fuzz is **broadcast watchability**. A player's visible slop score falling as they fix issues during build creates real-time narrative for audiences and commentators. The gap between the visible public-pool slop and the authoritative hidden-pool slop at freeze generates the format's central dramatic tension: did the player's low public slop reflect genuine defense, or will the hidden tests surface slop the player never probed for? Player fuzz is intelligence for the player; the visible slop score is suspense for the audience.

Workstations are restricted to non-administrative user accounts. Players cannot modify system configuration, install global software, or access system directories. Within their home directory, they have full freedom to work as they would on any development machine.

USB ports are physically disabled or removed. No external storage, no Bluetooth, no Wi-Fi. Ethernet only. Virtual console access is disabled to prevent dropping out of the desktop session.

Workstations are centrally managed through the league's RMM platform. Configuration consistency is enforced through automated policy. Per-round reset is handled by per-player account lifecycle, not image restoration: an ephemeral, non-sudo Unix account is created from `/etc/skel` at round start and deleted with `userdel -r` at round end (after the player's session and processes are terminated), removing the home directory and all session state in seconds. System state persists between rounds untouched. Full image restoration is reserved for the exceptional cases — between events, on any tamper-detection signal, and scheduled maintenance. Because the system is no longer wiped every round, between-round tamper detection is load-bearing: any integrity signal forces an image restore before the workstation is reused. OS and application updates are pushed through controlled maintenance windows between events, not during competition.

The linux choice serves the league's operational needs — open-source tooling, zero licensing cost, mature deployment automation, hardware flexibility, and vendor independence. Players whose daily environment is Windows or macOS receive brief orientation before their first competition to familiarize with the desktop and development tools. The substrate choice is not designed to teach linux skills; it is designed to enable the league to operate transparently and affordably at scale.

On the 24-minute clock. The build duration is a deliberate steal from "the 24-hour hackathon" — only the unit of time changed. Pre-AI, 24 minutes of solo programming produced almost nothing of substance; that's why hackathons settled on 24-72 hours historically. With AI substrate, a skilled engineer produces in 24 minutes what an unassisted engineer needed 24 hours for. The unit shrinks; the competitive surface doesn't. The format isn't anachronistic for using a short clock — it's enabled by the substrate. HackLet is not adapting to AI; the format is constituted by AI. The clock also stands in for stakes. A real engagement applies *material* pressure — a customer relationship, money, a career consequence — that a competition cannot replicate; time pressure substitutes for part of it. It manufactures the adrenaline of consequence, and in tension with the fuzz catalog it recreates the actual professional bind: ship fast, but do not break the things that matter. The clock alone would reward only speed; the clock *against* the resilience bar rewards the judgment that speed-without-recklessness requires. The duration is also operationally deliberate — a 24-minute core fits inside a single club meeting and is broadcastable, where a 24-hour event is neither. Twenty-four minutes is enough to prove mettle, not to learn something new mid-round (§10).

### 5.2 Network Configuration

> **Status: DESIGNED**.

Workstations are firewall-restricted to a minimal allowlist:

- The league competition website (single endpoint)
- NTP for time synchronization

The league competition website internally routes to the sanctioned AI substrate, the package mirror, and the deployment infrastructure. Players reach these resources only through the competition website, never directly. No web search. No external documentation. No second AI tools. No copy-paste from outside sources.

Chapters may optionally deploy dedicated network appliances or VLANs for additional isolation. The league provides reference configurations.

### 5.3 AI Substrate

> **Status: DESIGNED** — there is no proxy. No `backend/ai_proxy/` app, no OpenRouter integration, no `/api/v1/chat/completions`. Stage 4 is active and unstarted.

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

> **Status: DESIGNED** — no mirror exists yet. The **language-tier framing was retired 2026-07-31**; what replaces it is below. This also closes DOC_STATE C-09 and D-06, which were a disagreement about which languages sat in which tier — a question that stops existing once the tiers do.

**Language support is a provisioning problem, not a grading one.** The catalog cannot tell what
a submission is written in and does not try. Every probe applies on observed HTTP surface alone
— whether an endpoint exists, whether it takes text input, whether there is a login form — and
the runner's discovery builds a stack-agnostic map by crawling the live app. A Flask app, a Go
service, and a hand-rolled C HTTP server are graded by the identical catalog, and no probe in it
branches on language or framework. The earlier Tier 1 / Tier 2 / Tier 3 ladder implied the
league's *measurement* got weaker down the list. It does not. Nothing about grading varies.

**What "supported" actually means, and it only means it at Tier A.** Tier A workstations are
firewalled to `hackletleague.com` and `*.hackletleague.com` (§5.2, §5.8), so a player cannot
reach npm, PyPI, crates.io, or anything else. A language is *supported* when the league has
preinstalled its toolchain on the workstation image and mirrors its packages. That is the whole
claim: **we are the mirror, because nothing else is reachable.** Support is a statement about
what the league has provisioned, not about what the catalog can see.

The mirror is operated by the league at `packages.hackletleague.com`, firewall-allowed alongside
the main domain. It updates between seasons, and the package set is published with season
documentation. A submission needing something outside the mirror fails to deploy and scores
accordingly — the ordinary consequence, not a special rule.

**At Tier B and Tier C this section does not apply.** Neither runs a locked workstation, so
players install what they like from the open internet and the mirror is irrelevant. The catalog
grades them the same way regardless, which is exactly the point.

The published language set for a season is therefore an operations decision, driven by what the
league can keep mirrored and imaged, and by what the target population actually writes. It is
not a ranking, and no language is second-class at grading time.
### 5.5 Resource Budgets

Each player receives per round:

- **10,000,000 tokens** total (input + output + chain-of-thought), **shared across the build
  phase and the pitch-preparation window** — a single pool, not two. Spend it all building and
  you prepare your pitch unassisted; that consequence is the point, not a side effect
- **50 fuzz budget points** for player-triggered self-testing during build — **ASSUMED**; same,
  and additionally untestable until a fuzz-trigger path exists

*(The per-timer ladder in IDEAS_FOR_LATER.md — 50k/100k/150k/200k/300-500k — was extrapolated
from the retired 100k figure and does not survive the rebase below. It needs re-deriving from
10M before it means anything.)*

**What the token budget is for.** The budget is **cost control first and an efficiency signal second**. It is a ceiling that stops a runaway loop from burning a chapter's month in one round, not a number calibrated to bind on a normal round and force triage. Earlier drafts leaned on the second function — resource calibration as a credentialed skill — as though the cap were tight enough to make every prompt a real allocation decision. It is not, and the format should not claim it is.

**The measurement that moved the number.** A live 24-minute Underspecified round consumed roughly **7.2 million tokens**, with approximately 85,000 resident in context at any moment. The gap is not overuse; it is the difference between *cumulative* consumption and *instantaneous* context — an agentic client re-sends its working context on every step, so the same 85,000 tokens are billed dozens of times over. Against that, the previous documented cap of 100,000 was not a constraint a player could work within; it was a number an agentic client would exceed before finishing its first task.

**Where 10M comes from, honestly.** It is a **ceiling set above the one observation**, not a figure derived from it. 7.2M is a single round, n=1, measured off-substrate on DeepSeek V4-Pro rather than season-one V4-Flash. 10M leaves headroom over that observation while still stopping a runaway loop, which is the job the budget actually has (above). It is not a claim about what a round costs, and it should be re-derived once rounds run on the season model. Treat it as **ASSUMED with a measured floor** rather than as calibrated.

**Run identification (outstanding).** The figures above are **MEASURED**, but the producing run is not identified — no date, no event, no operator, no log reference, and the platform stores nothing that would let it be reconstructed (`Submission.token_budget_used` exists but is never written). Until the run is named, this paragraph is a recollection with a number in it. Name the run or downgrade the figures.

**Two boundaries, two names.** These are distinct instants and the documents must not use one word for both. **Build end** is when build time is up — the freeze boundary, where the proxy cuts off, the submission is captured, and code files go read-only. **Round end** is when the round is over — awards complete, zamboni finished. On the illustrative Tier A itinerary these fall at T+29 and T+135 respectively, roughly a hundred minutes apart. "The round has ended" never means build end.

**Two open windows, one hard cut between them.** Substrate access is granted during the **build
phase** and again during the **pitch-preparation window**, and refused at every other time. The
boundary between them is a real interruption, not a seam: at build end the league disables the
player's key server-side, which kills any generation in flight. Access is restored when
preparation begins. A build-phase request issued at 23:59 therefore never delivers, which is the
whole point of cutting rather than draining — it must not be possible to receive usable code
after the buzzer.

**Why prep gets the substrate back.** Preparing a pitch well means reading your own code, and a
player should be able to do that with the assistance they built with. It is safe because of the
capture, not because of a rule: at build end the archive is uploaded and deployed server-side,
and the fuzzer grades **the deployed copy**, never the player's working directory. Anything the
model helps them change afterwards reaches nothing that is scored. The freeze is enforced by
*where grading reads from*, which needs no client cooperation at all.

**The gate has two conditions: the budget is exhausted, or the request falls outside an open window.** Both are enforced the same way a commercial provider cuts an account off at a usage limit — server-side, immediate, and requiring no cooperation from the client:

- The proxy refuses the request with **403, not 429**. A 429 signals retry-later, and agentic clients have backoff wired to it, so an agent would sit in a retry loop while the player watches a spinner. 403 is terminal and surfaces immediately.
- The response body is **player-facing text**, because it reaches the player through whatever client they are using. It states which condition fired: the budget is spent, or the substrate is closed right now. It must not say the round is over, which is a different and much later instant.
- **In-flight requests are cut, not allowed to finish** at every window close, including the one at build end.
- The player may continue working without AI assistance.

**Rate limiting replaces the per-prompt cap.** The former 25,000-token per-prompt ceiling is
retired: at a 10M budget it constrains nothing a player would notice, and it was already
non-functional for agentic clients, which carry more than that in resident context on a single
step. What the substrate enforces instead is an ordinary **throttle** — a rate limit on request
volume, the same shape any commercial API applies. It protects the proxy from a runaway loop
without pretending to be a strategic constraint on the player.

**Tier scope.** All of the above applies where the league hosts the substrate: **Tier A and
Tier B**. It does not apply at Tier C, which is BYOD — there is no league key to disable, no
budget to enforce, and no reason to serve league inference when neither is true (LEAGUE_OPERATIONS
§7). Tier C players keep their own tooling throughout, including during pitch preparation.

**The tradeoff this preserves.** Because the budget is one pool spanning build and preparation,
a player who spends everything building has nothing left to prepare with. That is the intended
consequence and an instance of the no-coddling principle: pacing across the whole round is part
of what is being measured, not a trap to be softened.

Human edits at freeze are a separate rule and remain tier-dependent: inspector-enforced at Tier A, honor system at Tier B (see the tier operations documents). Under the capture model above this rule protects the *player's own* working copy and the integrity story around it, not the graded artifact, which is already out of their hands.

Edited or regenerated prompts do not refund tokens. Each prompt submission costs against the budget regardless of subsequent edits.

Fuzz budget enforces strategic allocation of self-testing. Categories have varying costs reflecting test complexity. Players may invoke any subset of fuzz tests against their own work within budget, gathering intelligence about defensive coverage before the judge fuzz set runs at code freeze.

### 5.6 Submission Requirements

> **Status: MIXED** — the server-authoritative freeze is BUILT (`backend/rounds/views.py:228-229`). The deploy/README contract and every failure mode below it are DESIGNED.

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

> **Status: DESIGNED** — and contradicted by the shipped player-facing scoring page, which offers a league-provided database at `$DATABASE_URL` (DOC_STATE C-10; that page belongs to the platform session).

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

The 24-minute format makes serious external integration impractical even with AI assistance; the constraint reflects format reality, not arbitrary limitation. Players keep full freedom to write integration code, but the runner does not provide the environment for it to function, so such code fails its relevant probes. The policy relaxes as the league builds integration-testing infrastructure at higher tiers (Phase 3 — see IDEAS_FOR_LATER.md). **The one carve-out from the "third-party API keys unsupported" line above is runtime model inference, provided through the league's own proxy under §5.8 — precisely because the league controls that key rather than the player supplying an external one.**

**What is restricted, and what is not.** At Tier A the restriction on external credentials was never a written rule; it is **structural**, a consequence of the workstation firewall and RMM (§5.1, §5.2) leaving nothing external to reach. That structural restriction applies to **player-supplied credentials only**. It is not, and must not become, a prohibition on the AI-wrapper *category* of application. Wrappers are the dominant shape of contemporary software — Y Combinator's Fall 2025 batch was ~92% AI-incorporating, up from ~88% the batch before (**uncited**; verify before public use) — and a league whose entire premise is that AI is the substrate cannot coherently firewall out the most common thing built on it. The resolution is not to relax the environment but to supply the credential: league-issued proxy keys (§5.8) give the app a sanctioned inference endpoint while the league keeps control of the key, the model, the budget, and the audit trail. Player-supplied keys stay unreachable; league-issued keys are available on request.

### 5.8 App-Tier Substrate Access (League-Issued Proxy Keys)

> **Status: DESIGNED** — depends on a proxy that does not exist. Its 'settled decisions' cover grading but not the judge clickaround window; carried to the decisions list.

**The problem.** At Tier A the workstation is firewall-restricted to a single endpoint (§5), so a player's *app* has no reachable inference endpoint at runtime. That firewalls out the single largest category of contemporary app — the AI wrapper (~78% of AI startups shipped in 2024 reported as API wrappers; AI is >80% of the current YC intake — **both figures uncited**, no source named in-document, unlike the §11 industry figures which carry named reports and dates) — in a league whose whole premise (§10) is that AI is the substrate. §5.8 fixes this by exposing the league proxy (§5.3) to the player's app, not only to their coding interfaces, gated by a **league-issued key**.

**Why the proxy, not a local model.** The proxy already exists, the season model is already pinned (§5.3), and clients already cannot select it or bypass logging. Extending the *same* proxy to the app tier preserves substrate equality for free and adds no hardware dependency. A local model (Ollama on the box) would move inference speed onto the workstation and reintroduce the parity problem the pinned-proxy design already dissolves.

**The keys.** Per player, per event, scoped to that submission, revocable, with a token budget attached. The budget does double duty: it is the cost control the substrate already needs, and it makes runtime inference a resource the player spends *deliberately* rather than a free escape hatch. Taking a key is **opt-in**.

**The tradeoff (this is a §4.5 no-dominant-strategy mechanic).** Taking the key costs on three axes and buys on one:
- **Clock** — the correct wiring (key held server-side; the browser calls the player's own route; that route calls the proxy) is meaningfully slower to build than the wrong wiring (inline the key, `dangerouslyAllowBrowser`, done in ninety seconds).
- **Surface** — the app now carries a credential, a route, and a proxy call, so every probe touching those (secrets exposure, the app route's injection/SSRF/rate-limit surface) becomes applicable. More surface is more slop opportunity (Attack Surface Coverage, §4.2).
- **Budget** — inference is spent against the attached cap.
- **Bought: a higher communication ceiling.** The nontech-stakeholder (30%) and UI/UX (20%) rubrics (§4.1) are asking whether the artifact is *worth using*; an app with intelligence in it has a higher ceiling on that question than CRUD does.

So neither play dominates: take the key for a better pitch, a worse clock, and a wider slop surface; skip it for a cleaner slop rank, a faster build, and a weaker demo. The player must estimate, under the clock, whether they can ship the ambitious thing *correctly* in the time they have — a self-assessment under pressure, which is the closest a format gets to real engineering judgment.

**Self-regulation (why restraint stays competitive).** The mechanic is kept from collapsing into "always take the key" not by the budget but by the **catastrophic penalty for the wrong wiring**: an inlined league key is a secrets-exposure finding (the top-of-scale class, §4.2; secrets/crypto anchor the penalty scale), and that deduction erases the communication gain. The equilibrium is therefore "take the key *only if* you can wire it correctly under the clock." The tuning knob is the ratio of the communication-ceiling gain to the wrong-wiring penalty; the league calibrates it so both plays keep winning depending on execution. **Watch item once events run:** if every top finisher takes the key, the pull is too strong and the tradeoff has become mandatory — the calibration must be corrected so a well-executed clean build can out-rank a sloppy ambitious one.

**Why this is the thesis as a mechanic.** HackLet's claim (§10) is that AI collapsed the cost of *producing* and left the cost of *understanding* intact. The key decision is exactly that: the model makes an ambitious build possible in 24 minutes (collapsed production cost), but it does not make the player understand what shipping the key *means*, and that stays as expensive as it ever was. The format is not asking whether you can use AI; it is asking whether you can use it without hurting yourself.

**Settled decisions.**
- **The firewall sits above the container, not around it (2026-07-31).** The grading container is *not* network-isolated. It gets egress, and a firewall one layer up allows a league-controlled destination only. Everything else is blocked. This is what makes the mechanic work at all: the app can reach the proxy at runtime, and the allowlist keeps attribution airtight, because the league proxy remains the only inference endpoint any submission can reach. It also means "no internet access" is the wrong description of the sandbox and must not be restated; the correct one is "one allowed destination." (Egress restriction in FUZZ_RUNNER_SPEC's threat model should be read as *allowlisted*, not *absent*.)

  > **The allowlist itself is PROVISIONAL, not settled.** It currently reads
  > `hackletleague.com` and `*.hackletleague.com`. The wildcard is a placeholder because the
  > proxy has no address yet, and it **narrows to the proxy hostname the moment one exists.**
  >
  > Why it must not be inherited as final: `hackletleague.com` serves the platform API, the
  > judge portal, and the Django admin alongside the proxy. A wildcard therefore hands
  > untrusted contestant code a reachable target *inside league infrastructure*, and gives
  > every SSRF probe in the catalog a live pivot rather than a dead one — the runner would be
  > aiming submissions at the league's own surface. That is tolerable only while the proxy is
  > unbuilt and there is nothing narrower to point at. It must not survive the proxy landing.
- **Purely scored, not drainable.** An exposed key is scored (via the secrets finding), not made live-drainable by rivals — draining reintroduces PvP chaos and non-determinism, contradicting the design where the attacking half is handed to a *deterministic* catalog, not to opponents. The **budget cap is the containment**: an exposed key is technically drainable-until-revoked, but the blast radius is the player's own capped budget, and detection triggers immediate revocation.
- **The key stays valid through the grading window.** Revocation is at the buzzer *for the player's ability to spend*, but the issued key must remain valid for the central runner's grading pass — otherwise the app's inference route 500s during grading and the app is scored broken for the league's own revocation. Grading uses a **separate grading allowance** (the fuzzer's own probing must not drain the player's budget), and inference-backed routes are excluded from the amplifying load/DoS probes (FUZZ_RUNNER_SPEC).
- **Tier-A-scoped.** The mechanic depends on the firewall making the league proxy the *only* reachable inference endpoint, which is what makes attribution airtight. At Tier B/C there is no such firewall, players bring their own real keys, and secrets-checking is already live on real credentials — but the clean attribution and the controlled tradeoff are lost, so the Tier B/C version is **genuinely open** and not specified here.

**Open (deliberately undecided).** The app inference budget's size, and whether it is shared with or separate from the round token budget (§5.5); whether Tier B/C gets any league-key analogue; and **who pays for judge-driven inference** — a judge exercising a wrapper app during the clickaround window generates real cost that no allowance currently covers, distinct from the grading allowance above.

**New surface, new probes (roadmap).** Making AI-wrapper apps *exist* at Tier A opens vulnerability classes the catalog does not yet cover and which are dead-on-thesis for an AI-substrate league: **prompt injection** (user input reaching the model, able to override the system prompt or exfiltrate it — the flagship AI-app flaw), **cost-DoS on the inference route** (unbounded user-triggered model calls, which ties straight back to the budget), and **SSRF/abuse of the app's proxy route**. See FUZZ_RUNNER_SPEC for the concrete, immediately-buildable change: the exact-match issued-key exposure probe.

## 6. Tier Structure

HackLet League operates across three tiers calibrated to expected expertise:

> **Status: SUPERSEDED in its scoring language.** The three subsections below describe
> per-tier scoring asymmetry in the vocabulary of the retired award-points model —
> "positive-only scoring," "moderate asymmetric penalty," "full symmetric scoring." Under
> deduction-only slop (§4.2) there is no positive scoring to be *positive-only* about and no
> symmetric/asymmetric axis to vary: every probe either fires (penalty) or does not (zero),
> identically at every tier. What survives is the intended mechanic — **catalog scope widens
> with tier** — which is unaffected by the rename. Rewriting these three subsections in
> deduction-only terms is a real edit with a real decision inside it (does a collegiate player
> face a narrower catalog, or the same catalog with some penalties waived?) and is **not made
> here**.

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

> **Status: MIXED** — Event and Round entities are BUILT. The 1-event-1-format rule is not enforced in code, and the round-size targets are DESIGNED.

Events occur throughout the season at multiple scales:

- **Chapter events**: Local events run by individual chapters, typically 6-8 players, monthly cadence. May be single-round (~1 hour for an MVR, up to ~2 hours at the full Tier A profile) or multi-round day events depending on chapter capacity.
- **Regional events**: Cross-chapter events with broader participation, quarterly cadence, typically multi-round day events (3-5 rounds across 8-10 hours) to justify travel for visiting players.
- **Championship events**: Season-culminating events with the strongest field, typically multi-day with multiple rounds per day.

At **human-judged tiers (A/B)**, every **panel** operates at **8 players standard**, **6-12 acceptable** — beyond 8 per-player narrative depth degrades and judge time tightens. Events with more demand add **panels running concurrently**, not bigger panels, and pay for them in judges (four permanent roles each). The only hard event ceiling is **televised Tier A, capped at 8**, which is a camera constraint; untelevised Tier A and all of Tier B have none. **Large-cohort MVR rounds** run 30-100+ because LLM-judged written evaluation has no queue at all (see §3.2 and TIER_C_OPERATIONS.md §5).

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

> **Status: MIXED** — persistent/all-time rankings are BUILT (`backend/rankings/services.py:103-123`), chapter and global scope only. Season rankings are DESIGNED; no season entity exists.

Two parallel ranking systems operate:

- **Season Rankings**: Current-season performance, used for qualification flow into higher-tier events and for crowning season champions
- **Persistent Rankings**: All-time accumulated performance, providing long-term credentialing signal

Both rankings are publicly visible. Players accumulate rank points through event placement, weighted by event tier.

### 7.3 Qualification Flow

> **Status: DESIGNED**.

Top performers at chapter events qualify for regional events. Top performers at regional events qualify for the season championship. Specific qualification thresholds are published per season and per region.

## 8. Conduct

> **Status: DESIGNED** — no enforcement surface on the platform.

Players must respect other competitors, judges, league staff, and the integrity of the substrate. Specifically:

- No harassment of other players or judges
- No attempts to influence judges outside the structured evaluation process
- No attempts to access external resources during a round through any means
- No collusion between players or coordination across submissions
- Truthful representation of identity, eligibility, and submission claims
- Respect for judges' in-event scoring decisions, with appeals through formal post-event process

Violations are addressed through the penalty structure detailed in the full rulebook, ranging from warnings through point deductions through round forfeit through event ban through season ban through permanent league ban, calibrated to severity.

## 9. Format Evolution

> **Status: DESIGNED** — policy.

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

> **Status: DESIGNED** — positioning.

The format rests on two principles:

1. **Substrate equality** — every player has the same tools, model, and resources.
2. **Submission resilience** — the fuzz catalog is the authority on how well the work holds up.

The format does not legislate *how* a player uses AI. Chat, agentic integration, command-line, tool chains — any interface is fine, provided every call flows through the league's API and stays within budget (§5.3). It cares only that the substrate is equal and that submissions are measured by objective adversarial testing. Resilience is what the fuzz catalog measures; communication (pitch and cross-examination) is scored separately and combined for Best Overall (§4). Slop loses to fuzz regardless of who or what produced it.

The chat-window interface matches the economically-dominant AI-coding practice among the format's target population. Third-party agentic IDE tooling (Cursor, Claude Code, Cline) requires either paid subscriptions or student-verification with friction that filters most undergraduate users; the chat-window workflow remains the only fully-free option for most CS students, which is why the chat window is the foundational substrate interface and the in-IDE agent interface ships later (Stage 12). *(The supporting "~70-85% of CS undergrads primarily use chat" figure in IDEAS_FOR_LATER.md is **ASSUMED** — no survey or source is named. The pricing claims beneath it are checkable; the usage share is not.)* When the agent interface lands, both interfaces are available to every Tier A/B player simultaneously with a unified token budget, so the format remains accessible to chat-first players while accommodating agent-fluent players without forcing either group into the other's mode.

In practice, succeeding under those principles exercises a specific cluster of AI-complementary capabilities:

- **Engineering judgment**: knowing what needs defensive attention without being told
- **AI direction**: effectively prompting an AI substrate to produce robust work
- **Verification reflex**: catching AI errors, hallucinations, and weaknesses before they ship
- **Resource calibration**: allocating limited tokens and fuzz budget strategically. *(Listed as an exercised capability, not a credentialed one — §5.5 withdraws the claim that the budget is tight enough to force genuine triage, pending on-substrate data.)*
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

> **Status: DESIGNED**, with **cited external figures**. The Harness / HBR / MIT NANDA statistics are sourced and dated and carry a fact-check caveat in IDEAS_FOR_LATER.md; they are not league measurements and are left as-is.

HackLet League exists to provide structured competitive infrastructure for a community that already cares about AI-assisted technical building. The format treats players as engineering adults responsible for their own decisions. It evaluates submissions through narrow precise measurement rather than broad subjective assessment. It publishes its methodology in full, including its limitations.

The structural precedent is the **Financial Modeling World Cup**. Founded in 2020 by Andrew Grigolyunovich (Latvia) after ModelOff was discontinued, FMWC took competitive financial modeling — a niche, measurable skill — to mainstream attention (its All-Star Battle aired on ESPN2 in 2022) through recurring tiered competition and persistent rankings, built into a durable institution by one founder. HackLet applies the same playbook to AI-assisted defensive coding, a domain with a deeper participant pool and more cultural pull. The precedent matters because it answers the first question every chapter operator, sponsor, and player asks — *is this real?* — with a pattern that has already worked once. HackLet borrows the template, not a claim of equivalent reach.

Credentialing is the aspiration, not the pitch. The League's job is to run the format well: equal substrate, honest measurement, methodology published in full. Done consistently, the credential emerges as a side effect — persistent rankings accumulate career-spanning evidence, and employers may over time reference HackLet standings as signal for AI-assisted engineering and defensive-coding roles. That value depends entirely on whether the measurements are trustworthy, which is why rigor comes first and the credential follows.

The League is honest about what AI actually delivers: a meaningful but modest productivity multiplier, useful when directed well, sloppy when directed poorly. The format demonstrates this empirically in every event. Submissions that pass the fuzz gauntlet are evidence of what skilled AI-assisted work can produce. Submissions that fail are evidence of what unskilled AI-assisted work cannot.

The industry is grumbling about slop in 2026, and the grumble is documented. The Harness 2026 State of Engineering Excellence report finds roughly 31% of a developer's day consumed by invisible work — reviewing AI-generated code, fixing its bugs, and context-switching between tools — and 81% of engineering leaders report increased code-review burden since adopting AI tools. The Harvard Business Review (2025) estimates "workslop" costs roughly $9 million per year per 10,000 employees. MIT's Project NANDA finds 95% of organizations see no measurable return on AI investment. Engineering communities have organized vocabulary around the failure mode — "vibe coding," "tokenmaxxing," "slop" — and vendors are shipping countermeasures (AI code-review and intent-verification tooling). HackLet enters this moment with credentialing infrastructure that answers a specific market need: engineers who can operate effectively in AI-augmented environments without producing slop, and engineers who can remediate the slop others produce.

The format structure covers the surface of anti-slop engineering work. **HackLet Vibe** credentials producing code that isn't slop (greenfield). **HackLet Unslop** credentials identifying and remediating slop in existing code (brownfield — the messy existing systems most real work actually inhabits). **HackLet Underspecified** credentials turning a vague, ill-formed brief into a defensible solution under ambiguity; because its 24-minute deliverable is a *tested foundation a client can understand* rather than a finished product, it maps to the first hours of a real engagement — a working spike that demonstrates a direction and de-risks the build. Across the three, the engineering halves (greenfield + brownfield) and the framing half (ambiguity decomposition) are covered. The strategic articulation is simple: people grumble about slop, so HackLet makes anti-slop a sport, televises it, and credentials those who excel at it. The grumble is the market; the format is the product.

What the three formats jointly surface is the disposition of a **Forward Deployed Engineer** — the role (popularized by Palantir, now among the fastest-growing hires at OpenAI, Anthropic, and Google) whose core is not algorithmic depth but scrappy, ownership-driven execution that ships defensible work fast under ambiguity. The mapping is exact where it counts: the trait FDE interviews prize most — moving fast *without* compromising the things that matter (security, eval gates, rollback) — is precisely what a low slop score under a 24-minute clock objectively demonstrates, a claim those interviews otherwise assess through fakeable behavioral stories. HackLet does not certify FDEs; it credentials **potential** FDEs. It evidences the innate builder disposition — the half hardest to assess and hardest to teach — and is honest that it does not test the rest of the role: sustained customer relationships, multi-week delivery, live stakeholder management. That makes it an **entry-level pathway** — an evidence-based on-ramp to a hot, experience-gated role for people who have the disposition but not yet the résumé, at a moment when AI has both gutted entry-level hiring and made the old signals (polished demos, self-reported projects) unverifiable. The narrow, honest claim — *this person has demonstrated the disposition* — is the one the credential can actually stand behind.

HackLet does not legislate AI usage style — any interface is fine (chat, agentic, command-line) so long as calls flow through the league's API and stay within budget. What matters is what survives the fuzz at code freeze, regardless of who or what produced it. The two principles (§10) are sufficient; the format evaluates nothing else.

The fuzz is what separates hacklets from slop.

---

*This document is the executive summary of the HackLet League rules. The complete rulebook contains formal specifications, edge case handling, appeals procedures, technical appendices, and case precedents accumulated through league operation. Players are responsible for familiarity with the full rulebook for the tier and season in which they compete.*
