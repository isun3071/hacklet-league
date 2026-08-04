# Judge Panel Reconciliation Patch

> **Status: APPLIED, then partly superseded at v1.0.0.** This patch locked a *four-rubric* Communication axis. The v1.0.0 freeze (2026-07-31) revised that to **two rubrics** — one shared technical rubric scored by three judges at 30/20/20, plus the stakeholder rubric at 30 (format_spec §4.1). The 30/20/20/30 *weighting* the patch locked is unchanged; only the rubric *count* did. Read the 'four rubrics' phrasing below as the historical decision, not the current rule.
>
> **Status: APPLIED — this patch's five edits have all landed.** Edit 1 and 2 are in format_spec
> §4.1 and §4.2; Edit 3 in TIER_A §9; Edit 4 in TIER_B §9; Edit 5 in the DATA_MODEL enum (**doc
> only** — the code still ships three `judge_specialization` values, not four). Edit 3's
> instruction *not* to overwrite cross-examination timing was correctly honoured; the clock is
> settled at 60s + 120s and the **mechanism is settled too** as of 2026-07-31 — the player's
> concision is scored, questions are not rationed (C-11 closed). The
> "Slopless Builder" name used below **was correct and the rest of the repo has caught up**
> (2026-07-31): the award is Slopless Builder everywhere, including the `slopless_builder`
> award key in code. C-17 is closed. Retained as the decision record; do not re-apply.

*Fixes the three-vs-four-judge contradiction. Right now the docs disagree with each other: format_spec §4 and IDEAS treat the stakeholder judge as a real role, but TIER_A §9's panel and the DATA_MODEL `judge_specialization` enum only list three (tester, ux_designer, general) with stakeholder as a "when the format absorbs it" maybe. This locks the four-judge structure decided in session: four permanent roles, four separate rubrics, weighted 30/20/20/30, all feeding the single 0-100 communication axis. Apply these edits to the canonical docs.*

---

## The decision being locked

Four permanent judge roles, each with its own rubric, each scoring 0-100, weighted into the single 0-100 **Communication axis**:

| Weight | Role | Owns (the axis it grades) |
|---|---|---|
| **30** | Tester | intent-*dependent* correctness (the fuzzer's blind spot: the fuzzer tests intent-*independent* universals; the tester tests "correct *for this app's intent*", e.g. at-most-once vs at-least-once) |
| **20** | UI/UX/HCI | the artifact's fitness for a human: legibility, error states a user can act on, workflow match, the works-to-*adopted* gap. Half-anchored in technical fact, half in human judgment (the bridge role) |
| **20** | General engineering | engineering judgment revealed by the choices: tradeoffs, scoping, which corners got cut, mostly recovered via cross-ex |
| **30** | Nontech stakeholder | translation/trust: can a skeptical non-engineer understand and trust it, without bullshit and without jargon-drowning. Per-format posture (CES attendee / anxious incumbent / the vague-brief author) |

**Why 30/20/20/30 and not 25/25/25/25:** tester and nontech carry the two most market-validated, hardest-to-fake axes (the AI-slop crisis; the rarely-co-occurring customer-facing skill). UI/UX/HCI and general are real but more artifact-legible, so they sit at 20. Base-10 numbers are also cleaner for judges to apply and audiences to read.

**Why the Communication axis stays separate from the Slop axis (do not fuse):** directionality (slop lower-is-better, comm higher-is-better), scale (slop unbounded `[0, +∞)`, comm ranged `[0, 100]`), epistemics (fuzzer is pure objectivity, cross-ex is where subjectivity is *allowed* to live), and the awards (Slopless Builder comes off the fuzzer, the comm award off the 100, Best Overall is the rank-sum of the two separate axes). Fusing them breaks all four. The four judges live entirely inside the Communication axis; the fuzzer's Slop Score is untouched by this patch.

---

## Edit 1 — format_spec §4.1 Component Structure

**Replace** the current three-component model (Slop Score / Pitch Quality / Cross-Examination Performance, where Communication = average of Pitch and Cross-Ex averaged across an unweighted panel) with:

> A player's performance is measured on **two independent axes**:
>
> - **Slop Score** — `[0, +∞)`, deduction-only, lower is better. Produced by the fuzz catalog (intent-independent universals). Unchanged by the judging structure below.
> - **Communication Score** — `[0, 100]`, higher is better. A **weighted composite of four judge-role rubrics**, each scoring the player's pitch + cross-examination on its own rubric:
>   - Tester **30%**
>   - UI/UX/HCI **20%**
>   - General engineering **20%**
>   - Nontech stakeholder **30%**
>
> The two axes are never summed into one number. Best Overall is the rank-based composition of the two axes (see §4.3).

**Note on the "pitch vs cross-ex" split:** the old model split communication into Pitch Quality + Cross-Examination Performance. Under the four-rubric model, each judge scores across *both* pitch and cross-ex on their rubric; pitch-vs-cross-ex can remain as an internal sub-structure of each rubric if desired, but the axis-level weighting is by judge role (30/20/20/30), not by pitch/cross-ex halves. Reconcile the sub-structure when the rubric internals are written.

---

## Edit 2 — format_spec §4.2 / §4.x (define the four judge roles + the intent line)

The intent-dependent-vs-independent boundary is already stated (the fuzzer owns intent-independent universals; the tester judge owns intent-dependent correctness). **Keep that.** Add the full four-role definition and make explicit that the tester judge *extends* the fuzzer (catches what it can't reach). Add UI/UX/HCI, general, and nontech stakeholder as **permanent** roles with the ownership shown in the table above. Remove any "when the format absorbs it" hedging for the stakeholder role.

> **SUPERSEDED 2026-07-31 — the override is gone.** This edit originally said the tester also *checks* the fuzzer by overriding intent-mismatched false positives. That was reversed: a human authority to void a finding makes the slop score a function of who judged it, breaking reproducibility, cross-panel comparability, intent-independence, and attribution-at-authoring-time. The tester may mark a finding **CONTESTED** instead, which changes no score and resolves into catalog changes going forward. See format_spec §4.2.

---

## Edit 3 — TIER_A_OPERATIONS.md §9 Live Judging Protocol

**Replace** the panel composition. Current text lists tester / UX designer / general as the panel and stakeholder as "(when format absorbs this role per IDEAS_FOR_LATER.md)". Change to:

> **Judge panel composition (four permanent roles):**
> - **Tester judge** — intent-dependent correctness; operates the portal showing automated-test applicability. No override (SUPERSEDED, see Edit 2); may mark a finding CONTESTED, which changes no score. Weight 30.
> - **UI/UX/HCI judge** — the artifact's human-fitness and adoption gap. Weight 20.
> - **General engineering judge** — engineering judgment revealed by the choices. Weight 20.
> - **Nontech stakeholder judge** — translation and trust to a non-verifier; per-format posture. Weight 30.
>
> Four judges, four rubrics, weighted 30/20/20/30 into the 0-100 Communication axis.

**Cross-examination structure — flag, do not silently overwrite.** §9 currently says 120-sec cross-ex, four judges, one substantive question each, ~30 sec per question, inside a 3.5-min-per-player / 28-min phase. In session we discussed a **1-min pitch + 2-min cross-ex** shape and scoring the *player's* concision/responsiveness (anti-filibuster) rather than rationing one question per judge. **RESOLVED 2026-07-31**: the clock is 60s + 120s (both candidate models agreed on it) and the mechanism is the concision rubric, not rationing. §9 and the phase block have been edited once, as instructed.

---

## Edit 4 — TIER_B_OPERATIONS.md §9

§9 originally said Tier B uses the same panel as Tier A but "may run 3 judges" with a compressed 90-sec cross-ex.

> **SUPERSEDED 2026-07-31.** This edit asked for the 3-judge reduction to be stated explicitly with re-normalized weights. Both are now retired: **all four roles are required at every human-judged tier**, and the 90-second window is gone (the cross-ex window is 120s and is not a function of panel size). Dropping a role deletes a dimension rather than rescaling one, and no re-weighting recovers it.

---

## Edit 5 — DATA_MODEL.md `judge_specialization` enum

Current:
```
judge_specialization : enum (tester, ux_designer, general), nullable (judge role only)
```
Change to:
```
judge_specialization : enum (tester, ux_designer, general, stakeholder), nullable (judge role only)
```
(Keep the value `ux_designer` to avoid a rename migration; its scope now covers UI/UX/HCI. Add `stakeholder` for the nontech role.)

**Scoring-math flag (not a clean one-line fix):** the `Score.score_type` enum and the aggregation logic model scoring as facet score-types (pitch_quality, cross_examination, creative_coherence, ux_quality, technical_execution, documentation) averaged into composites. Tonight's model is **weighted by judge role (30/20/20/30)**, which is a different decomposition. Adding the enum value does not by itself implement the role-weighting. The scoring-math change (weight each judge-role's contribution to the Communication composite) is a real code change beyond the schema enum, and should be scoped separately. Flagging so the enum add is not mistaken for a complete fix.

---

## Explicitly NOT changed by this patch (still open, do not hardcode)

- **Cross-ex timing** (120-sec/one-question-each vs 1+2-min/concision-scored) — unresolved; flagged in Edit 3.
- **Awards** — the three-prize cut (Slopless Builder / comm award / Best Overall) vs the tournament-level categoricals (Best UX/UI, Most Novel, Iron Player, Comeback) was discussed but not resolved: does the per-round cut also retire the tournament set, or only the per-round set? Docs still carry the fuller set. Leave until decided.
- **Comm award naming** — "Best Communicator" / "public speaker" flagged for rename (credit defense-under-pressure, not oratory); unsettled.
- **Rubric internals** — aggregation within each rubric, per-answer vs holistic, the anti-bullshit floor (mostly resolved-by-panel: the fuzzer + tester judge in shared panel block bullshitting a non-verifier, so no separate anti-bullshit clause needed on the nontech rubric). Write when the rubrics themselves are written.

---

## One-line summary of the fix

Make TIER_A §9, TIER_B §9, and the DATA_MODEL enum agree with format_spec §4 and IDEAS: **the nontech stakeholder judge is a permanent fourth role, not a maybe**, and the Communication axis is a **30/20/20/30 weighted composite of four separate judge-role rubrics**, sitting entirely separate from the fuzzer's Slop axis.
