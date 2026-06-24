# Tier C Operations

*Operational template for HackLet Tier C events. For tier philosophy and verification, see LEAGUE_OPERATIONS.md §4. For format mechanics and scoring, see format_spec.md. For Tier A and Tier B operational profiles, see TIER_A_OPERATIONS.md and TIER_B_OPERATIONS.md.*

---

## 1. Tier C Identity

Tier C is HackLet's **training tier** and the **Minimum Viable Round (MVR)** floor of the league. It is the smallest operational configuration that genuinely delivers HackLet competitive infrastructure: substrate equality within tier constraints, deterministic fuzz catalog evaluation, PITCH.md communication artifact, multi-axis scoring. Below Tier C is not HackLet at all; at Tier C, the format runs at its accessibility floor with bounded credentialing claims.

Tier C is also the **truest expression of the format's "we don't legislate AI usage" thesis**. Players use whatever AI tooling fits their workflow. The league does not host AI substrate, does not enforce token budgets, does not constrain client choice. The credentialing claims at Tier C are correspondingly bounded — chapter-local rankings only, no global contribution — but the credential itself is real engagement signal at the chapter level.

The freedom-integrity tradeoff (LEAGUE_OPERATIONS.md §4) sits at the freedom-maximizing end at Tier C. Players who want freedom-style competition use Tier C. Players who want credentialing-grade equality use Tier A.

## 2. Three Operational Profiles

Tier C operates under three distinct profiles serving different chapter goals. All three share core HackLet DNA — BYOD substrate, deterministic fuzz catalog, time compression, AI-native design — and differ only in cohort scale, judging method, and ceremony, never in format fundamentals.

**MVR (60 minutes)** — the floor and the default. **PITCH.md + LLM-judged** written evaluation (§7, §8), any cohort from **8 to 100+**, club-meeting compatible. The Minimum Viable Round is the smallest configuration that genuinely delivers HackLet, and the profile most chapters run most weeks. Timing in §4; large-cohort scaling (to ~74 min for 30-100+ in a single round) in §5.

**Tier C Extended (~135-180 minutes)** — **live pitch + cross-examination with human judges**, 8-12 players, weekend-afternoon timeframe. Equivalent operational rhythm to Tier B's live communication credentialing, but on BYOD substrate, so the credentialing claims stay Tier-C-bounded. For chapters with the judge capacity and player commitment to run the format's live-performance + cross-ex-defense dimension at chapter-local scope. (Phase shape mirrors the Tier A 135-min profile — see TIER_A_OPERATIONS.md §3 — minus broadcast production.)

**Multi-round MVR-day** — multiple MVR rounds back-to-back as a half-day or full-day event (typically 2-4 rounds over 2-4 hours), serving participant volume by rotating cohorts through independent rounds rather than enlarging any single round. Detail in §4.

Chapters choose the profile that matches their community capacity, and many run more than one: weekly MVRs for engaged competitors, an occasional Tier C Extended for the live-pitch experience, multi-round MVR-days for larger turnout.

## 3. Substrate

**BYOD substrate**. Players bring their own laptops. The league does not host AI substrate at Tier C. Players use whatever AI tooling they prefer (chat clients, IDE agents, mix and match). Web search and multiple AIs are allowed because BYOD makes restriction theater. No enforced token budgets because the league is not paying for inference and cannot enforce the budget.

**Substrate equality at Tier C** is not a substantive claim. Players with $200/mo premium AI subscriptions have systematic substrate advantages over players with free-tier-only AI access. The credential at Tier C does not claim substrate equality; it claims demonstrated capability under self-selected substrate. Honest credential scoping.

**No firewall, no workstation control, no audit trail**. Tier C operates on honor for everything that would require infrastructure to enforce. This is acceptable because Tier C credentials don't claim what the infrastructure can't enforce.

## 4. Round Timing — MVR Profile (60 Minutes)

The MVR round profile fits a one-hour club meeting:

```
T+0:00  → T+5:00   (5 min)  — Opening / round introduction
T+5:00  → T+29:00 (24 min)  — Build phase
T+29:00 → T+47:00 (18 min)  — Pitch writing (PITCH.md) + concurrent server-side fuzzing
T+47:00 → T+52:00  (5 min)  — LLM judging (parallel multi-dimension execution)
T+52:00 → T+60:00  (8 min)  — Awards + closing
─────────────────────────────────────────────────
60 minutes total
```

The MVR profile substantively compresses ceremony and judging windows compared to the Tier A 135-min profile but preserves the format's core: build phase under time compression, fuzz catalog evaluation, communication credentialing via PITCH.md, multi-axis scoring with categorical awards.

The MVR profile enables **weekly chapter operations** at university clubs. New chapters can start running events without complex logistics; established chapters develop player capability through repeated participation across the academic year.

### MVR Phase Details

**Opening (5 min)**: host welcomes the room, frames the round (which variant, what's at stake), introduces players. Lighter ceremony than Tier A — no broadcast, no production rhythm requirements, just orientation.

**Build phase (24 min)**: identical to all HackLet Sprint variants. Players construct a web application of their choice. No required features, no mandated architectures. Players direct their BYOD AI substrate however they choose. Server-side preparation begins for fuzzing infrastructure during build.

**Pitch writing + concurrent fuzzing (18 min)**: at code freeze (T+29), players submit via portal upload with grace period (see §6). Server-side fuzzing begins immediately on submitted code. Concurrently, players write **PITCH.md** articulating their defensive choices, design rationale, what they hardened, what they didn't get to and why. PITCH.md is the canonical communication artifact at Tier C (see §7). Players may use AI assistance for PITCH.md writing — the substrate-agnostic AI direction skill the format credentials applies to articulation as well as code production.

**LLM judging (5 min)**: at T+47, all PITCH.md + README + fuzz results bundle goes to the LLM judging pipeline. Multiple parallel Fusion calls execute concurrently (see §8). 5-min wall-clock window accommodates parallel execution.

**Awards + closing (8 min)**: compressed ceremony. Categorical award reveals, Best Overall reveal, brief closing remarks. No 14-min broadcast theater. Light social transition before round ends.

### Multi-round MVR-day Events

Chapters can run multiple MVR rounds back-to-back as a multi-round day event (typically 2-4 rounds across 2-4 hours). Each round operates independently with its own opening, build, judging, awards. Multi-round events let chapters serve larger participant pools by rotating through multiple rounds rather than scaling cohort size per round.

Multi-round MVR-day events remain within Tier C credentialing scope. Champions of multi-round days earn chapter-local recognition; no global ranking contribution.

## 5. Round Timing — MVR at Large-Cohort Scale

The MVR is not a separate "large" profile — it is the same PITCH.md + LLM-judged mechanism run for a bigger single-round cohort (30-100+ players). The timing extends modestly to absorb larger-venue logistics and a bigger judging pool:

```
T+0:00  → T+10:00 (10 min) — Opening / round introduction (larger venue logistics)
T+10:00 → T+34:00 (24 min) — Build phase (identical to MVR)
T+34:00 → T+54:00 (20 min) — Pitch writing + concurrent fuzzing (slightly extended for cohort scale)
T+54:00 → T+64:00 (10 min) — LLM judging (parallel multi-dimension across large cohort)
T+64:00 → T+74:00 (10 min) — Awards + closing
─────────────────────────────────────────────────
~74 minutes per round
```

Large-cohort MVR rounds can run standalone or 2-4 back-to-back as a multi-round MVR-day (§4). Round size scales with infrastructure capacity (venue, wifi, judge LLM throughput). Recommended starting scale: 30-60 players per round, expandable as chapter infrastructure matures.

The 10-min LLM judging window at this scale accommodates larger-cohort comparative judging (see §8) plus per-submission own-merit evaluation. Cost and latency scale with submission count but remain operationally tractable at typical large-cohort scale.

## 6. Submission Mechanism

**Portal upload with grace period**. At Tier C, the league does not have league-controlled workstations to SCP submissions from. Players upload submissions through the league portal (hackletleague.com) from their BYOD laptops:

- At T+29 (end of build phase), the portal upload window opens
- Players have a **3-minute grace period** (T+29 → T+32) to push their final code state through the portal
- Failure to submit by T+32 results in disqualification (no PITCH.md evaluation, no fuzz evaluation, no scoring)
- The grace period accommodates upload latency for BYOD network conditions while preserving build phase integrity

**Submission contents**:
- Source code archive (zip file of working directory)
- README.md (player-authored project documentation)
- Dockerfile or similar deployment configuration for niche languages

**Niche language handling**: players using languages outside the league-supported runtime pool (see format_spec.md §5.4) must provide a Dockerfile or README with run instructions. Submissions that don't deploy successfully receive automatic zero on fuzz tests. The deployment contract responsibility shifts to the player at Tier C because the league can't pre-configure their BYOD environment.

**Server-side deployment and fuzzing**: identical to Tier A/B pipeline. Submitted code deploys to ephemeral container with assigned port. Fuzz catalog (both public and hidden pools) executes against the deployed submission. Results flow into scoring pipeline (see §9).

## 7. PITCH.md — Written Communication Artifact

PITCH.md is the canonical communication artifact at Tier C. It substitutes for the live pitch + cross-examination dimension of Tier A scoring. Players write PITCH.md during the pitch-writing + fuzzing window (T+29 → T+47).

### PITCH.md Required Sections

The PITCH.md template (provided as starter file in submission scaffold):

```markdown
# Pitch — [Player Name / Submission ID]

## What I built
[1-3 sentences describing the application]

## Key defensive choices
[Articulate specific defensive decisions: authentication, input validation,
error handling, attack surface management, etc. Each choice with rationale.]

## What I prioritized
[Engineering judgment: where you spent effort and why]

## What I didn't get to
[Honest acknowledgment of unfinished work or known gaps]

## Expected fuzz catalog response
[Self-assessment: where you think you'll score well and where you might struggle]

## AI direction strategy
[How you used AI assistance during build — chat patterns, agent usage,
verification reflexes, where you delegated and where you drove manually]
```

The template structure guides players toward articulation depth without requiring them to invent structure under time pressure. The sections collectively credential the specific communication skills the format claims to measure: engineering reasoning, defensive thinking, strategic AI direction, honest self-assessment.

### LLM-Assisted PITCH.md Authorship

Players may use AI assistance for PITCH.md writing. This is **substantively consistent** with the format's AI-augmented thesis — the substrate is AI-augmented across all phases, not just code production. The credential measures AI direction skill across build + articulation + (at Tier A) live performance. AI-assisted PITCH.md authorship credentials the player's ability to direct AI toward technical articulation quality, not pure human writing capability.

The LLM judging pipeline still distinguishes capability through patterns the substrate can detect:
- **Hallucinated defensive claims**: PITCH.md claiming "I implemented CSRF protection" when the code lacks CSRF — caught by judges reading PITCH.md + code together
- **Boilerplate disguised as reasoning**: generic AI output without submission-specific context — scored lower than specific reasoning
- **Missing reasoning depth**: lists of what was built without explaining why — scored lower than substantive rationale
- **Inconsistency with fuzz catalog results**: PITCH.md claims strong defensive coverage when the slop score is high — judges identify the mismatch

AI assistance doesn't automatically produce strong PITCH.md. Players must direct AI toward specificity, depth, accuracy, and consistency with their actual submission. That direction is the credentialed skill.

## 8. LLM Judging Architecture

The MVR profile evaluates submissions through **LLM-judged written evaluation** rather than human-judged live performance. The architecture uses OpenRouter Fusion (or equivalent multi-model deliberation pipeline) to evaluate PITCH.md + README + fuzz results across multiple dimensions in parallel.

### Pipeline Architecture

At T+47 (end of pitch writing + fuzzing), all submissions bundle for parallel LLM evaluation. **Three Fusion calls execute concurrently per round**, each with a different scoring purpose:

**Call A — Technical own-merit evaluation**
- Panel of 3-5 LLMs reads each submission's PITCH.md + README + fuzz results
- Each panel member evaluates independently with the **technical sysprompt**
- Judge model synthesizes panel outputs into per-submission technical communication score
- Captures: engineering articulation depth, defensive reasoning quality, technical accuracy, framework knowledge precision

**Call B — Nontechnical own-merit evaluation**
- Same architecture, different sysprompt
- Panel evaluates with the **nontechnical stakeholder sysprompt**
- Judge synthesizes per-submission nontechnical communication score
- Captures: stakeholder translation, clarity for non-engineers, business-impact framing, jargon management

**Call C — Comparative evaluation**
- Panel reads all PITCH.md submissions side-by-side in a single context window
- Judge produces relative rankings + cross-submission analysis (consensus, contradictions, coverage gaps, unique insights, blind spots)
- Eliminates scoring drift that own-merit evaluation can produce when LLM standards shift across sequential evaluations
- Captures: relative articulation quality, outlier detection, comparative reasoning depth

All three calls **start dry** (no carried context from prior calls). This guarantees evaluation integrity: technical evaluation isn't influenced by nontechnical conclusions; comparative judging doesn't carry forward own-merit biases. Each Fusion call has its own variance envelope rather than compounding across stages.

### Parallel Execution Window

The 5-min judging window (10-min at large-cohort MVR) accommodates parallel execution. Fusion call latency is ~15-45 seconds for typical 4-model pools per OpenRouter docs; multiple calls executing concurrently complete in roughly the same wall-clock time as a single call (slowest call determines total elapsed). At 30 submissions × 3 parallel Fusion calls = 90 concurrent API requests — well within OpenRouter throughput.

### Communication Score Aggregation

The final Communication score per submission combines:
- Technical own-merit score (Call A)
- Nontechnical own-merit score (Call B)
- Comparative ranking signal (Call C)

Default weighting: 40% technical own-merit + 30% nontechnical own-merit + 30% comparative ranking. Chapters may configure weighting per event based on credentialing emphasis (e.g., chapter prioritizing technical credentialing might weight 60/20/20; chapter prioritizing cross-functional communication might weight 30/40/30).

### Panel Diversity Mitigates Self-Recognition Bias

The multi-LLM panel architecture **substantively dilutes** any single-LLM self-recognition bias. If a player uses Claude for PITCH.md writing, the GPT/Gemini/Llama panel members have no shared substrate to recognize. The judge synthesizing across diverse panel outputs sees consensus from substantively independent evaluators. Single-LLM judging would have self-recognition concerns; Fusion's panel diversity handles this without requiring additional safeguards.

### Sysprompts as Canonical Format Artifacts

The technical and nontechnical sysprompts (plus the comparative judging sysprompt) become **load-bearing format artifacts** analogous to the fuzz catalog. The league maintains:
- Technical sysprompt (versioned, evolved through observed evaluation quality)
- Nontechnical sysprompt (versioned, separately evolved)
- Comparative judging sysprompt (versioned)
- Judge synthesis sysprompt (versioned)

Sysprompt evolution discipline includes versioning, public publication of major versions, community review of sysprompt changes. Early large-cohort MVR events produce judging outputs that inform sysprompt refinement; after 10-20 events the sysprompts converge on reliable evaluation patterns. Chapters using early-version sysprompts should be honest with players that the evaluation methodology is still calibrating.

### Operational Cost

LLM judging is real recurring cost. At large-cohort MVR (30 submissions × 3 Fusion calls × ~10K tokens average), each round costs roughly $5-15 depending on model selection (Budget vs Quality Fusion presets). For chapters running monthly large-cohort MVR events, annual league-supplied LLM cost runs $60-180 per chapter. Sustainable but worth budgeting for. League covers this cost because large-cohort MVR events validate the format and build the chapter ecosystem; the cost is investment in league maturation.

## 9. Scoring and Categorical Awards

The full award set and scoring math are defined once in **format_spec.md §4**; this section only notes which awards Tier C offers and how the Communication Score is produced per profile.

Tier C offers the **per-round award set** (format_spec §4):
- **Most Resilient** — lowest Slop Score (the deterministic catalog applies identically at every tier).
- **Best Communicator** — highest Communication Score. The score is **LLM-judged** in the MVR profile (PITCH.md, §8) and **human-judged** in the Tier C Extended profile (live pitch + cross-examination); the award honors the same skill dimension either way.
- **People's Hacklet** — audience-contingent: applies when a chapter hosts an in-person audience, skipped for audience-free events.
- **Best Overall** — composite ranking per format_spec §4.3.

**Tournament-level awards** (Best UX/UI, Most Novel, Most Efficient, Iron Player, Comeback Player) are **Tier A multi-day** territory and are not offered at Tier C — they depend on enforced token budgets and/or multi-round tournament structure that Tier C doesn't operate. See format_spec §4.

## 10. Audience and Broadcast

**No broadcast at Tier C**. BYOD substrate precludes screen sharing for privacy reasons (personal devices contain personal context — notifications, browser history, signed-in services, work content — that cannot be broadcast without violating player and third-party privacy). Broadcast production is **Tier A only** (see TIER_A_OPERATIONS.md).

**In-person audience optional at Tier C**. Chapters may invite audience when local capacity supports it (university clubs with engaged communities, chapter members not competing this round, friends and family of competitors). Audience is welcome but not required.

**Asynchronous content remains viable**. Post-event recap content (written results announcements, brief highlight summaries, social media coverage) can serve remote audience interest at Tier C without requiring live broadcast infrastructure.

The format's audience-design philosophy (per format_spec.md §10) applies where broadcast infrastructure makes spectacle meaningful (Tier A). At Tier C, the format runs primarily for **competitive and community-building purposes** rather than spectacle purposes.

## 11. MLH Palatability Framing

large-cohort MVR events are structurally compatible with the MLH (Major League Hacking) operational template — hackathon-style scale, BYOD substrate, accessibility-focused community building. large-cohort MVR can be framed for CS student communities as "compressed AI hackathon with adversarial scoring" or "micro-hackathon with fuzz-catalog credentialing."

The MLH brand carries substantial recognition in CS student communities. After demonstrated operational maturity (probably Year 2-3 of league operations), MLH partnership for large-cohort MVR events becomes viable strategy: MLH sanctioning legitimizes large-cohort MVR events to the broader CS student community; HackLet provides the format innovation that distinguishes the events from traditional hackathons.

**large-cohort MVR can pursue MLH backing; Tier A operates independently**. The same league has different institutional positioning at different operational tiers — MLH-adjacent at the accessibility tier, distinct competitive credentialing institution at the credentialing tier. Honest tier scoping rather than format-identity bifurcation: both tiers share HackLet DNA (fuzz catalog, AI-native design, time compression) while differing in operational scope and credentialing weight.

Pursuing MLH partnership is Year 2-3 strategic territory. Current focus (Year 0-1) is demonstrating MVR viability at the BU chapter through repeated operations.

## 12. Credentialing Claims

Tier C credentials carry **bounded but real** market signal:

**Substantive credentialing claims**:
- Demonstrated AI-augmented engineering capability against deterministic fuzz catalog
- Demonstrated communication capability under time compression — written PITCH.md (LLM-judged) in the MVR profile, live pitch + cross-examination (human-judged) in the Tier C Extended profile
- Demonstrated engagement with competitive engineering community at chapter level

**Claims explicitly NOT supported at Tier C**:
- Substrate equality (BYOD precludes it)
- Resource calibration credentialing (no enforced budgets)
- Global league ranking contribution (no cross-chapter ranking due to substrate variance)
- Live performance under pressure *in the MVR default* (it's written/LLM-judged) — credentialed only when a chapter runs the Tier C Extended profile

**Credential interpretation for employers**:
- *Hiring for engagement signal*: Tier C participation demonstrates competitive engineering engagement, peer-network involvement, technical community membership
- *Hiring for AI-augmented engineering capability*: Tier C wins demonstrate the capability against deterministic adversarial testing within chapter-scope
- *Hiring for credentialing-grade signal*: Tier C is not the appropriate credential; Tier A events provide that level

Honest credential calibration matters. Tier C doesn't oversell what it credentials. Employers who understand the tier system interpret Tier C credentials with appropriate weight; the credential's meaning strengthens through market consistency, not through credential inflation.

## 13. The MVR as League R&D Infrastructure

Tier C MVR events are substantively the league's research and development infrastructure. Each event generates operational data that informs league-level artifact evolution:

- **Submitted code patterns** reveal common engineering choices, defensive patterns, slop signatures — feeds fuzz catalog evolution
- **PITCH.md artifacts** reveal articulation patterns, communication failure modes, AI-assisted writing characteristics — feeds sysprompt calibration
- **LLM judging outputs** reveal evaluation quality, scoring drift, sysprompt edge cases — informs sysprompt refinement
- **Round timing data** reveals where the format clock breaks under stress, which phases compress acceptably, which compromise quality
- **Audience engagement observations** (where audience present) reveal what's spectator-legible and what isn't

After 30+ MVR events across a chapter's first year of operations, the league has substantial operational data. The fuzz catalog matures, the judging sysprompts converge, the format clock validates. Tier A operations starting later (Year 3+) inherit mature infrastructure rather than building from scratch.

The MVR's bounded credentialing claims free the league to use Tier C operations as R&D environment. Mature credentialing-grade claims at Tier A justify substantial infrastructure investment **because** Tier C operations have de-risked the format. Building Tier A first without MVR validation would be premature optimization; building MVR first validates the format before Tier A investment commits.

## 14. Strategic Sequencing

Tier C operations are the league's near-term focus (Year 0-2) before Tier A infrastructure investment is justified:

**Year 0-1**: BU chapter operates MVR events. Demonstrates operational viability, player engagement, chapter sustainability. Refines sysprompts, fuzz catalog, format clock through repeated execution.

**Year 1-2**: MVR expansion to additional chapters. Demonstrates format transferability across communities. Chapter ecosystem grows. Large-cohort MVR operations emerge at chapters with capacity.

**Year 2-3**: MLH partnership conversation becomes viable for large-cohort MVR operations. large-cohort MVR events at MLH-palatable scale grow chapter ecosystems further. First Tier A chapter verification application (probably BU) begins.

**Year 3+**: First Tier A chapter verification completes. Workstation infrastructure deployment. Credentialing-grade events begin. Esports production emerges. Full league pipeline operates from MVR through credentialing tier.

This sequencing reflects the substantive constraint that Tier A investment requires Tier C validation. Tier A won't come unless Tier C proves itself; the proof comes through sustained operational viability across multiple chapters over 1-3 years of MVR operations.
