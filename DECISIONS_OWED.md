# Decisions Owed

*Phase 3 of the 2026-07-28 documentation reconciliation. Every contradiction that needs a call
from Ian, with options and costs. Evidence cited to file and line; `C-nn` refers to the
contradiction list in [DOC_STATE.md](DOC_STATE.md).*

> ## ⚠ Read this first — eight of these were decided on 2026-07-31
>
> The entries below are **as written on 2026-07-28** and were accurate then. They have not been
> rewritten. Where this file and the list here disagree, **this list wins**, and
> [CHANGELOG.md](CHANGELOG.md) carries the reasoning.
>
> | ID | Status | Outcome |
> |---|---|---|
> | **D-01** | **DECIDED** | The container is not isolated. It gets egress, firewalled one layer up to `hackletleague.com` and `*.hackletleague.com` only. *Still open:* who pays for judge-driven inference during clickaround. |
> | **D-02** | **DECIDED** | Budget is **10M**, one pool across build and pitch prep. The 25k per-prompt cap is **retired**, replaced by a rate-limit throttle. |
> | **D-06** | **DISSOLVED** | The language-tier ladder is retired, so "which tier is Rust in" stops being a question. Support means *provisioned at Tier A*, not gradeable. Rust stays. |
> | **D-09** | **DECIDED** | Two substrate windows (build, pitch prep) with a real cut at build end that kills in-flight generation. Tier A/B only. |
> | **D-15** | **DECIDED** | Tier C Extended is **retired** — durations undecided, so the profile is withdrawn rather than guessed. |
> | **D-16** | **DECIDED** | `Event.format` accepts `underspecified`. Migrated. |
> | **D-21** | **DECIDED** | The league does **not** provision a database. SQLite committed to the submission, in-memory, or browser storage. The scoring page no longer claims otherwise. |
> | **C-20** | **DECIDED + BUILT** | The 3-minute upload grace is implemented, not just promised. |
> | **D-11** | **PARTLY** | `judge_specialization` now has all four values. The 30/20/20/30 weighting is **still not implemented**, and is now waiting on the fuzzer being wired rather than on a decision. |
> | **D-13** | **DECIDED** | The size limit is the **panel's**, not the event's. 8 per panel (6-12 workable); events add concurrent panels and judges. Televised Tier A caps at 8 as a camera constraint; untelevised Tier A and Tier B have no maximum. |
> | **D-18** | **DECIDED** | **No override.** The tester marks a finding CONTESTED, which changes no score and resolves into catalog changes going forward. The round result is final. |
>
> Also settled alongside these: awards are scoped to the event and leaderboards to the tier, with **no cross-panel anchoring** (bears on **D-04**); and the nontech stakeholder deliberates **in the same room on a separate rubric** (bears on **D-17**, though whether the three technical judges share one rubric is still open).
>
> **Everything else in this file is still open.**

---

## D-01 — The league key and the evaluation window (**new**)

**The problem.** §5.8 issues a player's app a league proxy key so AI-wrapper submissions can
exist at Tier A. The key's whole justification is a *higher communication ceiling*: the
nontech-stakeholder (30%) and UI/UX (20%) rubrics ask whether the artifact is worth using, and
an app with intelligence in it has a higher ceiling on that question than CRUD does
(format_spec.md:414-418).

But nobody evaluates the app while it is alive. Judges click around during the evaluation
window, which begins at build end. The fuzzer probes the container after freeze. If the key is
revoked at the buzzer, the app's inference route is dead for **the entire period anyone looks
at it** — so the ceiling the key was bought for never materializes, and the player has paid the
clock cost, the slop-surface cost, and the budget cost for nothing.

**What the docs already say — partially.** format_spec.md:432 records a settled decision: *"The
key stays valid through the grading window… Grading uses a separate grading allowance."* That
covers the **central runner's grading pass**. It does not mention the judge clickaround window
at all, which is the longer of the two and the one that feeds the rubrics the key exists to
serve. Two further passages collide with it: [TIER_A_OPERATIONS.md:118](TIER_A_OPERATIONS.md#L118)
cuts the proxy "from the buzzer forward", and the shipped player-facing scoring page promises
the container has **"no internet access"** (`frontend/app/scoring/page.tsx:26`), which if
implemented literally forecloses §5.8 entirely.

**The three shapes, and what each costs:**

| Shape | Cost |
|---|---|
| **A — key stays live through grading** | Egress is open on a container running untrusted player code *precisely while* hidden-pool probes fire — the one window where an exfiltration channel matters most. Collides with FUZZ_RUNNER_SPEC's egress restrictions and with the "no internet access" promise already shipped to players. Also leaves open who pays: without a separate allowance, the fuzzer's own probing drains the player's budget, and a probe that hammers an inference route bills the player for being tested. |
| **B — key dies at the buzzer** | AI-wrapper submissions are ungradeable. The inference route 500s, and the app is scored broken *for the league's own revocation* — the exact failure §5.8:432 was written to prevent. In effect this re-bans the wrapper category, which [CHANGELOG.md:18](CHANGELOG.md#L18) explicitly warns against: *"If a future edit re-broadens this… it has silently re-banned the wrapper category and undone §5.8."* Cheapest to build, highest thesis cost. |
| **C — separate grading-time credential, issued to the container** | Cleanest separation: player budget untouched, egress scoped to exactly one endpoint, credential lifetime bounded to the evaluation window. Costs a credential lifecycle that does not exist today (issue → scope → expire → revoke) on top of a proxy that also does not exist, and it weakens attribution — the league can no longer say "this inference was the player's spend," which is part of what makes Tier A's audit trail airtight. |

**The sub-decision every shape needs regardless:** does *judge-driven* inference during
clickaround get metered, and against whose allowance? A judge exercising a wrapper app for
several minutes generates real inference cost that no current document accounts for. Shape B
makes this moot by making the feature dead; A and C both need an answer.

---

## Carried forward — still open, still yours

### D-02 — Token budget value

100,000 tokens/round and the 25k per-prompt cap stand unchanged and are now marked **ASSUMED**
in place ([format_spec.md §5.5](format_spec.md#L344)). The one measurement — ~7.2M consumed,
~85k resident — is n=1, off-substrate, on V4-Pro rather than season-one V4-Flash.

- **Hold at 100k/25k**: costs nothing today (nothing enforces them) but ships a per-prompt cap
  the docs *themselves* now say is non-functional for agentic use. Any agentic client hits it
  on step one.
- **Raise to something derived from the 7.2M observation**: sets a number from n=1 on the wrong
  model — precisely what format_spec.md:352 declines to do.
- **Split the cap**: separate cumulative budget from per-prompt ceiling, or drop the per-prompt
  cap entirely and keep only the cumulative ceiling. Costs a re-derivation of what the
  per-prompt cap was protecting against.
- **Blocked on**: Stage 4 existing at all, plus one on-substrate round.

### D-03 — `best_communicator` rename

Flagged unsettled in [format_spec.md:226](format_spec.md#L226) and
JUDGE_PANEL_RECONCILIATION_PATCH.md:91 — credit defence-under-pressure over oratory.

- **Keep "Best Communicator"**: free; the name is already in shipped code
  (`backend/rounds/scoring.py:135`), the frontend, and three tier docs.
- **Rename**: costs a code change (award key), a migration of any stored results, and edits in
  five docs. Cheapest to do *now*, while no event has ever produced the award. Gets
  monotonically more expensive after the first real round.

### D-04 — Slopless Builder denominator

**Caveat: this has almost no footprint in this repository.** "Slopless Builder" appears only in
JUDGE_PANEL_RECONCILIATION_PATCH.md:20 and :90, where it names the award everything else calls
"Most Resilient" (that naming conflict is D-14 below). The denominator question — *slopless
relative to what measured surface?* — depends on fuzz-runner measurements I must not edit.

What exists here that bears on it: [format_spec.md §4.2](format_spec.md#L167) already defines a
denominator — **Clean Rate = probes passed ÷ probes applicable** — alongside Probes Applicable
and Attack Surface Coverage (Narrow/Moderate/Broad). If the credential needs a denominator,
that is the in-repo candidate and it is already specified.

- **Denominator = probes applicable** (the existing Clean Rate): free, already written, but
  "applicable" is decided by the runner's discovery, so a shallow discovery pass flatters the
  app by shrinking the denominator.
- **Denominator = full catalog**: stable across submissions and comparable across rounds, but
  punishes narrow-surface apps for probes that could never have applied.
- **No denominator — publish raw slop plus coverage metadata**: what §4.2 currently does.
  Honest, but gives the outward-facing credential no single legible number, which is the thing
  a durability credential most needs.

### D-05 — Awards structure

Unresolved in JUDGE_PANEL_RECONCILIATION_PATCH.md:90: does the three-prize per-round cut also
retire the tournament-level set, or only the per-round set? Docs still carry the fuller set
(TIER_A §8 and §10, IDEAS_FOR_LATER.md:57 lists ~13 tournament credential positions).

- **Per-round tight, tournament expansive** (status quo in the docs): preserves the
  anti-award-sprawl argument in format_spec.md:239 while giving multi-day events rich
  categorical distribution. Costs the coherence problem in D-12 below — Most Efficient is
  currently listed in both places.
- **Retire tournament categoricals too**: maximum signal density, but discards the
  IDEAS_FOR_LATER tournament design wholesale and removes the specialisation-recognition
  argument that sponsor-facing material leans on.
- **Blocked on**: nothing. Decidable now, and it gates D-12.

### D-06 — §5.4 vs IDEAS substrate drift (Rust and Ruby) (C-09)

[format_spec.md §5.4](format_spec.md#L302) puts **Rust and Ruby in Tier 2** (maintained
substrate parity, mirrored web frameworks). [IDEAS_FOR_LATER.md:99](IDEAS_FOR_LATER.md#L99)
**excludes both** — Rust "below threshold for junior web roles, framework ecosystem still
maturing", Ruby "declining". The same entry moves Java and C# *up* to Tier 1 and adds PHP,
which §5.4 does not mention at all.

- **§5.4 wins**: Rust and Ruby stay Tier 2. Costs mirror maintenance for two ecosystems the
  Union-Of-Resumes analysis says are below threshold — real recurring work for languages few
  target players use.
- **IDEAS wins**: Rust and Ruby drop to Tier 3 (compiler-only) or out. Costs a player-facing
  reversal — the shipped scoring page advertises **Rust** by name as a supported stack
  (`frontend/app/scoring/page.tsx:175`) — and loses the diversity-signalling argument.
- **Note**: IDEAS_FOR_LATER.md:101 marks itself as landing in §5.4 *post-pilot*, so this may be
  a sequencing artifact rather than a genuine disagreement. But §5.4 currently reads as live
  policy, and PHP exists in exactly one of the two lists.

### D-07 — Contest review cadence

**No footprint in any document.** Nothing in the thirteen docs describes a cadence for
reviewing the format itself. The nearest neighbours: format_spec §9 (format evolution, "changes
announced at least 30 days before they take effect"), LEAGUE_OPERATIONS.md:352 (appeals filed
within 14 days, decided within 30), and IDEAS_FOR_LATER.md:83 (quarterly *catalog* versioning).

- **Per-season**: matches the substrate rotation and the 30-day announcement rule; slowest to
  correct a format defect found mid-season.
- **Quarterly**: matches the proposed catalog cadence, so format and catalog move together;
  costs more governance overhead than a one-chapter league can absorb.
- **Event-triggered**: review when operational data says something broke. Cheapest now, but
  provides no scheduled forcing function, which is how the current doc drift accumulated.
- **Blocked on**: nothing, but has no value until events run.

### D-08 — Player sequestration during the pitch phase

**No footprint in any document.** Players pitch in sequence (8 × 3.5 min), and nothing says
whether players 2-8 watch players 1-7. Same-archetype submissions are deliberately scheduled
back-to-back "to enable direct comparison" ([TIER_A_OPERATIONS.md:131](TIER_A_OPERATIONS.md#L131)),
which sharpens the problem: the second player of a pair hears the first's pitch *and* the
judges' questions before answering.

- **Sequester**: fair — every player faces cross-examination cold. Costs a holding room, a
  staff member to run it, and it removes players from the audience of their own event, which
  cuts against the broadcast and community design.
- **Open room**: free, better atmosphere, but later pitch slots are structurally advantaged,
  and the advantage is largest exactly where the format deliberately concentrates comparison.
- **Randomise order and publish that it is random**: does not remove the advantage, only
  distributes it across rounds. Cheap, partial.
- **Note**: interacts with D-17 — if the slop score is withheld until cross-ex, an unsequestered
  player can hear it revealed in someone else's cross-ex beat.

---

## Surfaced by the audit — also yours

### D-09 — Does the substrate gate admit a pitch-preparation carve-out? (C-07)

Produced by the Phase 2 terminology fix and stated in full at
[format_spec.md §5.5](format_spec.md#L396). The gate cuts access at **build end**; six passages
grant chat-window AI during pitch preparation, which runs after build end.

- **Gate is absolute** — no AI after build end. Simple, matches the buzzer-enforcement
  decision as written, one rule to implement. Retires the "players who tokenmaxxed during build
  have no AI assistance for prep" tradeoff, which is a real designed mechanic and an instance of
  the no-coddling principle.
- **Third clause** — inference allowed for prep, no file writes. Preserves the tradeoff, but the
  gate stops being "one gate, two conditions" and becomes a phase-dependent policy; needs a rule
  for what the agent interface may do (Stage 12), and needs the budget to survive past build end.
- **Blocked on**: nothing. This is a pure design call and it gates Stage 4 implementation.

### D-10 — Cross-examination anti-filibuster mechanism (C-11)

Clock is **settled** (60s pitch + 120s cross-ex — both candidate models use it, now marked as
such at [TIER_A_OPERATIONS.md §9](TIER_A_OPERATIONS.md#L253)). Mechanism is open.

- **Ration the judges' questions** (TIER_A §9 as written): one substantive question each; a
  verbose answer consumes a later judge's slot. Makes the player liable for the panel's clock
  management, and a judge who runs long silences a colleague.
- **Score the player's concision** (NONTECH_JUDGE_NOTES.md §8): no rationing; the rubric scores
  whether the player answered and yielded the floor. Self-correcting — a rational player answers
  tight, so the panel gets more questions in — but adds a judgment call ("padding vs thorough")
  to every rubric.
- **Attached, needs its own answer**: [TIER_B_OPERATIONS.md:158](TIER_B_OPERATIONS.md#L158)
  introduces a **90-second** cross-ex for 3-judge panels that appears nowhere else in the doc
  set and is reflected in no phase block. It shortens the round by 30s per player — four minutes
  across eight players. Either a real Tier B accommodation that never propagated, or an artifact
  of deriving 3 × 30s from the rationing model that may not survive this decision.

### D-11 — Which decomposition is the Communication axis? (C-01)

Three live definitions: 30/20/20/30 by judge role ([format_spec §4.1](format_spec.md#L124));
six facets averaged into two axes (shipped — `backend/rounds/scoring.py:24-33`, which never
reads `judge_specialization`); 40/30/30 across LLM calls
([TIER_C_OPERATIONS.md §8](TIER_C_OPERATIONS.md#L214)).

- **Role weighting is canonical, code follows**: matches the locked panel decision. Costs a real
  scoring-logic change plus a `judge_specialization` enum migration (code ships three values, not
  four), and DATA_MODEL.md:315 already warns against doing this silently.
- **Facet decomposition is canonical, spec follows**: costs nothing to build — it already runs
  and has produced results — but discards the four-rubric decision the reconciliation patch was
  written to land.
- **Both, scoped by profile**: role weighting at human-judged tiers, 40/30/30 at the LLM-judged
  MVR. Honest to the two evaluation modes; costs cross-tier comparability of the Communication
  score, which the ranking math currently assumes.

### D-12 — Most Efficient: retired or live? (C-06)

format_spec.md:235 retires it per-round and confines it to Tier A tournament level. TIER_A §8
and TIER_B §8 both list it as an available per-round award — at Tier B, where budgets are
honor-system and the measurement format_spec requires does not exist.

- **Honour the retirement**: delete from two tier docs. Free; loses a categorical track that
  IDEAS_FOR_LATER.md:39 maps to "resource-constrained engineering" hiring.
- **Reinstate per-round at Tier A only**: costs enforced token measurement (D-02, Stage 4) and
  contradicts format_spec's own anti-award-sprawl argument at 8-player fields.
- **Depends on** D-05, and its rationale is undercut by D-02 — an award for efficiency against a
  cap the docs say does not bind measures very little.

### D-13 — Is the 8-player cap a format or a broadcast constraint? (C-08)

Both claims sit in format_spec §3.2, six lines apart: :88 "across all tiers… the format's
foundational unit"; :94 "at Tier A specifically… tied to broadcast and audience purposes. Lower
tiers without broadcast have more flexibility."

- **Format constraint**: 8 everywhere, 6-12 range, 12 max. Simple and uniform; forecloses the
  large-cohort MVR of 30-100+, which is the entire Tier C scaling story and the MLH pitch.
- **Broadcast constraint**: cap binds at Tier A only; lower tiers size to judging capacity.
  Coherent with LLM-judged scaling; costs the "foundational unit" claim and the comparability
  argument that lets a Tier C result mean anything next to a Tier A one.
- Nothing in code enforces any cap today, so this is free to decide and cheap to implement
  either way.

### D-14 — Award naming: "Most Resilient" vs "Slopless Builder" (C-17)

Every doc and the shipped code say `most_resilient`; JUDGE_PANEL_RECONCILIATION_PATCH.md:20 and
:90 say "Slopless Builder". Same cost structure as D-03, and probably one decision with it —
deciding award nomenclature twice is how the drift happened. Interacts with D-04, since the
denominator question is about what "slopless" asserts.

### D-15 — Tier C Extended duration (C-12)

[TIER_C_OPERATIONS.md:23](TIER_C_OPERATIONS.md#L23) says ~135-180 min; the shipped
`tier_c_extended` profile ends at **T+107** (`backend/rounds/services.py:35-46`, "Tier A's phase
shape minus the Zamboni" — which is exactly 107).

- **Doc is right, code is wrong**: the profile needs 28-73 more minutes somewhere, and the doc
  does not say which phase absorbs them.
- **Code is right, doc is wrong**: change the doc to ~107 min. Free; makes Tier C Extended
  meaningfully shorter than the "equivalent operational rhythm to Tier B" it claims.
- Smallest decision here, and the only one where shipped behaviour and prose differ by a
  measurable quantity.

### D-16 — Can the third format be recorded at all? (C-14)

format_spec §1 sanctions 3 formats × 5 timers = 15 variants. `Event.format` ships `(vibe,
unslop)` — **Underspecified cannot be recorded**. Notable because §5.5's one real measurement
came from an Underspecified round, and NONTECH_JUDGE_NOTES devotes its longest section to it.

- **Add the enum value**: one migration, trivial. Makes the doc true.
- **Drop Underspecified to 10 sanctioned variants**: costs the three-format credentialing
  argument that format_spec §11 and IDEAS_FOR_LATER.md:75 both build on.
- Platform-session change either way; flagged here because it is a format decision, not a code one.

### D-17 — Three technical rubrics or one? (C-15), and when the slop score is revealed (C-16)

Two related calls, both from NONTECH_JUDGE_NOTES:

- **Rubrics.** format_spec §4.1 and the locked patch specify four separate rubrics.
  NONTECH_JUDGE_NOTES.md:11 argues the three technical judges should share **one** rubric,
  because they measure one trait through three windows and separate rubrics produce incoherent
  scoring. Cost of four: the incoherence that entry predicts. Cost of one: the 30/20/20/30
  weighting collapses into 70/30 and the locked decision is reopened.
- **Slop reveal.** NONTECH_JUDGE_NOTES.md:181 wants it withheld through pitch and cross-ex, so
  players defend blind — the highest-value signal being whether they can find their own
  weakness without the machine telling them. TIER_A §4 hands judges fuzz output during the
  evaluation window, *before* pitches. Cost of withholding: judges lose the technical baseline
  the clickaround window was designed around, which is severe under D-22. Cost of not
  withholding: the self-knowledge signal is unrecoverable — a player can parrot the machine.

### D-18 — Does the tester judge get a per-probe override? (C-18)

BUILD_ROADMAP Stage 5 In Scope says yes ("override interface for fuzz applicability
decisions"); Stage 5 Success Criteria says no ("slop scoring is automated; no per-probe
override"); format_spec §4.2 says yes ("overriding an intent-mismatched false positive");
DATA_MODEL FuzzResult carries `override_by_judge` and `override_reason`.

- **Override exists**: preserves the tester's stated role as the fuzzer's check. Costs the
  determinism claim — a human can move the objective axis, which is the property the two-axis
  separation exists to protect.
- **No override, spot-check only**: keeps the slop axis machine-pure. Costs the false-positive
  remedy, leaving a player penalised for behaviour that is correct for their app.

### D-19 — What gates People's Hacklet? (C-19)

BUILD_ROADMAP.md:230 and `backend/rounds/scoring.py:133` defer it *until broadcast features*.
TIER_B §6 and TIER_C §9 offer it contingent on *audience presence*, at tiers that have no
broadcast by definition.

- **Gate on audience**: the award needs people in a room, not cameras. Makes it available at
  Tier B/C now and is what those docs already assume. Costs nothing but an `AudienceVote` model.
- **Gate on broadcast**: keeps the current deferral, and removes the award from the two tiers
  most likely to run first.
- The dependency looks simply mis-specified; still yours to confirm.

### D-20 — Rewriting §6 tier scoring in deduction-only terms (C-03)

format_spec §6.1-6.3 describe per-tier scoring as "positive-only", "moderate asymmetric
penalty", "full symmetric scoring" — vocabulary from the retired award-points model. Marked
SUPERSEDED in Phase 2 rather than rewritten, because the rewrite contains a decision:

- **Narrower catalog at lower tiers**: a collegiate player faces fewer probes. Simple; makes
  cross-tier slop scores incomparable, since the denominator differs.
- **Same catalog, some penalties waived**: comparable surface, tier-adjusted penalties. Keeps
  scores commensurable; costs a per-tier penalty table.
- **Same catalog, same penalties, tier is context only**: simplest and most honest to
  deduction-only; removes the collegiate protection §6.1 exists to provide.

### D-21 — Self-containment vs the provided database (C-10)

format_spec §5.7 permits SQLite committed to the submission and forbids external databases. The
shipped scoring page tells players *"if you need a database, connect to the one we provide at
`$DATABASE_URL`"* (`frontend/app/scoring/page.tsx:155-156`) — shipped in `c869054`.

- **Page is right**: the league provisions a database per container. Materially easier for
  players; costs a provisioning path per submission and quietly widens §5.7.
- **§5.7 is right**: SQLite only, and the page is wrong on a page whose stated purpose is
  "no surprises on competition day."
- Same page also promises "no internet access" (D-01) and a 3-minute grace period that does not
  exist (below). Whichever way these go, that page needs one pass.

### D-22 — Is 2.25 minutes per submission enough? (consequence of the arithmetic fix)

The Phase 2 correction is arithmetic and not in dispute. Its consequence is: with four
permanent roles each scoring every player, a judge gets **~2.25 minutes** per submission, and
[TIER_A_OPERATIONS.md:122](TIER_A_OPERATIONS.md#L122) asks that window to carry "substantive
evaluation" plus fuzz-output review plus clickaround.

- **Accept 2.25 min**: no change. The evaluation window becomes triage, and the phrase
  "substantive evaluation" is doing work the clock does not support.
- **Lengthen the evaluation phase**: the 135-min profile grows, and it is the one timing block
  that currently matches shipped code exactly.
- **Judges split the field**: restores ~9 min, but abandons the permanent-specialised-role
  structure — each submission then gets one judge's lens, not four.
- **Reduce field size**: 2.25 → 4.5 min at four players; cuts against the 8-player standard (D-13).
- Interacts with D-17: withholding the slop score removes the technical baseline that makes a
  2.25-minute pass survivable at all.

### D-23 — Identify the 7.2M-token run

Marked outstanding at [format_spec.md §5.5](format_spec.md#L374). The figure is real but the
producing run has no date, event, operator, or log reference, and the platform stores nothing
that could reconstruct it (`Submission.token_budget_used` exists and is never written).

- **Name it**: costs a few minutes of recall while it is still recent.
- **Downgrade to ASSUMED**: honest, and loses the only empirical bound the substrate section has.
- Gets harder every week; the recall window is the constraint.

---

## Handed to the platform session — not decisions, defects

Both are code, reported here for handover completeness. Neither was fixed.

**C-02 — DATA_MODEL still carries the pre-slop award-points schema.** `FuzzTest.points_defended
: int (positive value)`, `points_gracefully_handled`, `points_broken : int (negative value)`;
`FuzzResult.points_contributed` "can be positive, zero, or negative" with a four-value `outcome`
enum; `PlayerFuzzInvocation.score_delta` signed. format_spec §4.2 is deduction-only: a passing
probe contributes exactly zero and there is no positive award.
[CHANGELOG.md:35](CHANGELOG.md#L35) claims this cascaded to DATA_MODEL. It did not. Same shape
as `scoring.py` holding the facet decomposition — the decision reached the prose and not the
schema. Sections are marked SUPERSEDED; the schema is untouched.

**C-20 — The 3-minute grace period does not exist.** TIER_C §6, TIER_B §5, PITCH.md:42 and
`frontend/app/scoring/page.tsx:15` all promise T+29 → T+32 with disqualification at T+32.
`backend/rounds/views.py:228-229` rejects everything past `build_end_at` with no tier branch and
no grace. The shipped freeze is **stricter than every document and both player-facing surfaces
promise**. Either the code grows a grace window or four documents stop promising one.

---

## Hold — do not write these numbers into any document

**Corpus statistics need re-derivation before use.** The figures carried in conversation —
accessibility **28.2%**, **68%** of defect weight in chores, and the winner-vs-non-winner null
at **t=1.5229, p=0.1283, d≈0.11, n=111 vs 514** — were computed on a **625-app** run. v11 is
**1,531 scored apps**. The null in particular has materially more power at 1,531 and may not
survive.

Confirmed in Phase 1: none of these figures appear anywhere in this repository, so nothing
needed correcting. Phase 2 wrote **no** v11 value into any document, and deliberately did not
substitute v11 numbers into prose written about the earlier corpus — the surrounding sentences
would not survive the swap.

Also outstanding, and **not mine to fix**: `fuzz-runner/hacklet_runner/probes.py:3794` states
a11y "remains the second-largest category (25.5% against headers' 24.4%)". That compares
post-repricing a11y against *pre*-repricing headers. Headers rises to ~27.5% once a11y drops, so
headers is the larger of the two and the sentence's conclusion is inverted. The fuzzer session
owns that file.
