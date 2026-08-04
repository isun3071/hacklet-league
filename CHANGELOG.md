# Changelog

> **Status: historical record — present tense is correct here.** Entries describe what was
> decided or shipped at the time of writing and were verified against git history during the
> 2026-07-28 documentation audit. One terminology correction has been applied (build end, not
> round end). Where an entry claims a decision "cascaded" to a given file, that claim is not
> self-verifying: the deduction-only entry below claims a cascade to DATA_MODEL.md that did not
> reach the schema. See [DOC_STATE.md](DOC_STATE.md).

Notable changes to HackLet League, organized by build stage (see [BUILD_ROADMAP.md](BUILD_ROADMAP.md)).
This is a human-readable summary; the authoritative record is the git history.

---

## The tier ladder now grades on judging rigour (2026-08-03)

**Tier B is redefined. It is what was called Tier C Extended: live pitch and cross-examination with human judges, on BYOD substrate.**

The old Tier B — "league-hosted substrate with honour-system budgets" — did not describe an integrity step, and TIER_B:75 said so out loud: *"no firewall prevents continued AI calls beyond budget — the proxy still serves the calls."* That was wrong on its own terms. **The firewall never enforced the budget; the server gate does**, and a per-player budget is enforceable anywhere the league hosts. What a missing firewall actually costs is *exclusivity* — nothing stops a player alt-tabbing to their own subscription — and exclusivity is the whole of the parity claim. So the old Tier B occupied the worst cell available: Tier A's costs for Tier C's integrity.

**Each rung now buys exactly one thing:**

| Tier | What it is | What the rung adds |
|---|---|---|
| **C** | PITCH.md, LLM-judged, one hour, scales to 100+ | the accessible floor |
| **B** | live pitch + cross-examination, human judges, BYOD | **live human cross-examination** |
| **A** | the above plus controlled workstations and enforced substrate | **parity you can actually claim** |

C→B is bought with *people rather than hardware* — a four-role judge corps and an afternoon, no infrastructure a Tier C chapter lacks. That matters because cross-examination is the format's most distinctive credentialing dimension and it was previously reachable only through RMM, a firewall, broadcast and an on-site inspector, which is Year 3+ territory.

**Who pays for the AI is no longer on the ladder.** League-hosted substrate is an **opt-in available at any tier**: the league meters and pays, the budget is genuinely enforced, and the event records it. It becomes an *integrity claim* only at Tier A, where the firewall makes it exclusive. Supplying a model and guaranteeing everyone used it are different things, and only the second is worth a credential. **Most Efficient is consequently Tier A only** — it needs total usage, and below Tier A a player can spend outside the proxy.

**It also dissolves a problem the tier-C leaderboard would have created.** With Extended inside Tier C, a Tier C board would have mixed LLM-judged and human-judged Communication scores — two instruments on one axis, deciding rank-sum. Now each tier has exactly one judging instrument, so each board is internally coherent.

**Exact phase durations are retired as commitments.** Only the **24-minute build clock** (server-enforced, and the format's defining constraint) and the **per-player pitch slot** (60s + 120s, a fairness constraint) are hard. Everything around them — opening, evaluation, deliberation, awards, Zamboni — is a planning estimate. This dissolves the "107 versus 135-180" disagreement that prompted retiring Extended in the first place: those were two planning estimates being compared as though they were specifications, and neither was a claim. Tier B's shape is Tier A's minus the Zamboni, because BYOD has no workstations to reset.

**Code:** `Round.TimingProfile` gains `tier_b` (migration `0004`); `tier_c_extended` remains resolvable in `services.PHASE_PROFILES` as a legacy alias so any existing row still renders, but is not selectable. Frontend types, labels and the round-manager list follow. This also closes the gap DOC_STATE flagged where no `tier_b` value existed and a Tier B round had to be scheduled as `tier_a`.

---

## The RSAC precedent, written down (2026-08-03)

Cross-examination was modelled on the **Shark Tank-style Q&A of the RSAC Innovation Sandbox**, and that fact lived only in conversation. Recorded in format_spec §3.1, with the boundary rather than just the resemblance, because the boundary is what will get misremembered.

**Verified:** ten finalists in sequence on one stage to a single panel, a **three-minute pitch** each, a Q&A round, **five judges**, deliberating to one winner. **The Q&A duration is not published.** An earlier claim in this session that it runs 180 seconds could not be substantiated and has been retracted; it never reached a file, and the doc now warns against citing any number for it.

**What transfers:** the panel works the window freely rather than in rationed turns, and ten finalists to one panel backs the 8-per-panel sizing.

**What HackLet adds, and why the two are not interchangeable: rubrics.** RSAC publishes none and produces no per-judge scores — it is a *selection process* that picks a winner on one night and never needs the number again. HackLet is a *measurement instrument*: the Communication axis has to mean the same thing in another city next season, which is what makes it composable with slop and what lets it feed a leaderboard.

**Where HackLet is deliberately stricter:** RSAC does not sequester and is not questioned for it; HackLet does, because same-archetype submissions pitch back-to-back.

**Where HackLet is deliberately tighter:** a 60-second pitch against RSAC's 180. The justification is real rather than stylistic — a HackLet judge has already used the submission during the evaluation window, so the pitch is argument rather than exposition.

---

## Rulebook v1.0.0 — the format is frozen (2026-08-03)

The documentation set is versioned as a rulebook, and **v1.0.0** is the first frozen version: a coherent, decided set of rules with **no open format questions**. Future rule changes ship as new versions, announced 30 days ahead (§9), and credentials cite the version they were earned under.

The four questions that were still `OPEN —` in the spec are resolved:

- **Communication axis is two rubrics, not four (§4.1).** One shared **technical** rubric scored by the tester, UI/UX/HCI and general judges from three angles (combining 30/20/20), plus the **stakeholder** rubric at 30. The 30/20/20/30 weighting is unchanged — "two rubrics" means two scoring instruments, not two weights. They measure one trait through three windows and one genuinely-different trait; three separate technical rubrics would have recorded which judge pressed hardest. This adopts NONTECH_JUDGE_NOTES §1, which was written as a losing position and turned out to be the right one.
- **A season is an academic year (§7.0).** Fall through spring, named by starting year (Season 2026 = fall 2026–spring 2027). Fits the university population, puts the championship before finals, keeps a student's results in one season. `Ranking.season_year` holds the starting year.
- **Three global leaderboards, one per tier (§7.2).** **Verified** (Tier A), **Open** (Tier B), **Developmental** (Tier C) — named by what a placement means, never compared across. Each tier has exactly one judging instrument, so each board is coherent; the slop axis stays comparable everywhere.
- **Tournament-level awards deferred to a future version (§4.4).** v1 defines the four per-round awards only (Slopless Builder, Best Communicator, People's Hacklet at televised Tier A, Best Overall). The tournament set waits in IDEAS for the multi-day Tier A events that give it meaning.

Two smaller items resolved with the same freeze: **contest review is event-triggered, superadmin authority** (§4.2), and **qualification is on season standing, best-N-of-M, feeding the capacity-constrained tiers** (§7.3). Sequestration is now provisioned in the Tier A/B venue requirements.

**What v1.0.0 does not claim: that the platform implements it.** The scoring engine still runs the Stage-3 six-facet stand-in; the AI proxy, the fuzz-runner wiring, and the per-tier boards are DESIGNED, not built. That is expected — a rulebook is the rules, and the platform tracks it by stage (BUILD_ROADMAP). The rules are frozen and internally consistent; the code catches up behind them.

---

## Four orphaned open items, resolved (2026-08-03)

Deleting DECISIONS_OWED against a five-item precondition dropped several genuinely-open questions that were not on that list. Found by auditing the deleted file against its homes, and resolved rather than restored.

**Players are sequestered.** They wait in a dedicated room and do not watch the pitches before their own. The exposure was pattern rather than content — a player defends their own build, so there is no answer key to overhear — but same-archetype submissions pitch back-to-back by design, so the second of a pair would otherwise hear the first's pitch *and* the panel's questions immediately before answering. It also keeps the slop-reveal-as-cross-ex-beat option viable, which an open room would leak. Costs a room, a staffer, and players missing their own event's audience.

**Cross-examination is not rationed; the player's concision is scored** (NONTECH_JUDGE_NOTES §8). The panel works the 120-second window; the player's rubric scores whether they answered what was asked and yielded the floor. This replaces one-substantive-question-per-judge, under which a long answer silently cost a colleague their turn and the player carried liability for the panel's clock management. Self-correcting: a player facing that rubric answers tight, so the panel gets *more* questions in. Note this lands one rubric line — the rest of rubric internals stay open.

**Tier B's 90-second cross-ex window is deleted.** It existed only as 3 judges × 30 seconds, derived from the rationing model, appeared nowhere else in the doc set, and was reflected in no phase block. The window is 120 seconds at every human-judged tier and is not a function of panel size.

**People's Hacklet is televised Tier A only.** It is a broadcast element, so it needs Tier A *and* cameras. Since a televised round caps at 8 players, it never reaches the larger untelevised Tier A fields. Removed from Tier B §4/§6/§8 and Tier C §9, which had offered it contingent on audience presence. This resolves the standing contradiction with BUILD_ROADMAP and `scoring.py:133`, both of which already deferred it to broadcast. Worth noting the cost: the tiers most likely to run first, and most likely to have a room full of people, no longer have an audience award.

**Also applied, from an earlier ruling that the docs had not caught up to: all four judge roles are required.** The drop-to-3 allowance at Tier A §2 and Tier B §9 is retired, along with the "minimum 3 members" corps requirement. The reasoning worth keeping: dropping a role does not rescale the axis, it *deletes a dimension*. A round with no nontech stakeholder has measured nothing about translation to a non-verifier, and no re-weighting recovers that.

---

## Slopless Builder, a provisional allowlist, and one fewer source of truth (2026-08-03)

**The award is Slopless Builder.** The metric had landed (lowest raw Slop Score); the name had not, and it had grown a rationale for staying — that the title should be aspirational while the score stayed descriptive, on the analogy of golf naming a Champion rather than a Lowest Score Holder. **That rationale is superseded and should not be reintroduced.** Recorded once, in format_spec §4.4, so it stops drifting: "slop" descends from *AI slop* and *workslop* (BetterUp Labs + Stanford Social Media Lab, HBR 2025), meaning AI-generated output that masquerades as good work while lacking the substance to advance the task. That is an absolute property rather than a rate, which is why the score is deduction-only and unbounded, and why **"Slopless"** names the metric exactly. **"Builder" is carried by the Communication axis, not the metric** — a minimal app has nothing to defend under cross-examination and sinks on the rank-sum, so the name does not need to smuggle in a substance requirement the composite already enforces. Renamed in eight documents and in code: the award key is now `slopless_builder`.

**The container allowlist is PROVISIONAL, not settled.** §5.8 records `hackletleague.com` plus the wildcard as a placeholder that **narrows to the proxy hostname once a proxy exists**, with the reason written down so it is not inherited as final: that host also serves the platform API, the judge portal and the Django admin, so a wildcard hands untrusted contestant code a reachable target inside league infrastructure and turns every SSRF probe in the catalog into a live pivot aimed at us. Tolerable only while there is nothing narrower to point at.

**DECISIONS_OWED.md is deleted.** Its resolutions live in format_spec and here, and its body still described the pre-resolution world — D-01 as three open shapes, D-02 at 100k with the 25k cap, D-04 arguing over a denominator that no longer exists. A second source of truth for decisions is exactly how the drift started. Its five genuinely-open items were first marked **`OPEN —` in the section that owns them**, which is the convention going forward: a decision and its context stay together. Three of the five had no home anywhere and were newly written — the rubric count (§4.1), contest review cadence (§4.2), and whether the per-round award cut retires the tournament set (§4.4, which also gates Most Efficient).

---

## The judge panel: no override, panels not events, local awards (2026-08-03)

Four decisions that had been sitting decided-but-unapplied.

**The tester judge's fuzzer override is removed (D-18).** A human authority to void a finding would make the slop score a function of *who judged it*, and that breaks four things at once: **reproducibility** (the same submission must score the same twice, which is what lets a discovery profile be cached and replayed), **cross-panel comparability** (a score from one city has to mean what a score from another city means), **intent-independence** (the authoring invariant that a probe's correct outcome does not depend on what the app was for — an override is precisely the intent judgment the invariant exists to exclude), and **attribution at authoring time** (a penalty is decided when the probe is written and reviewed, not at the scoring table). If a probe produces intent-dependent false positives, the probe is badly authored and the catalog is where that gets fixed.

Replaced by the **contest**: the tester may mark a finding CONTESTED, recording probe, submission, judge, timestamp and reason. It changes no score. **The round result is final** — HackLet reveals live, so there is no gap between scoring and ceremony in which a result could move, and no completed round is ever amended. Contests are reviewed between events and resolve into catalog changes going *forward*, which fixes the probe for everyone who competes after rather than one submission retroactively. The role is not diminished: the tester's weight is 30 on the **Communication** axis, never on slop, and code access is the instrument that lets them ask a question the player cannot bluff. The fuzzer tests the artifact; the humans test the reasoning. `FuzzResult`'s `override_by_judge` / `override_reason` become `contested_by` / `contested_reason` / `contested_at`.

**And a policy for being wrong, which the override removal made necessary.** §4.2 now carries an explicit false-positive / false-negative section. The core asymmetry: an FP is loud (it fires on a specific app, the player knows, the tester can confirm) and the contest channel catches it, while an **FN is silent** — nobody disputes a score that came out too well, so contests structurally cannot surface one. Recall has to be measured off-event against deliberately vulnerable reference apps, on a schedule independent of whether any event ran. Four rules keep the trade honest: the unit of correction is the **catalog version, not the round**; **never recompute a finished round**, because that makes a score depend on when you look at it; **penalty weight is bounded by oracle confidence**, so a heuristic oracle may not carry a catastrophic penalty; and the **measured error rate gets published**, because a league that says "the score stands even when it is wrong" owes players a number for how often. A contested finding is not nothing to the player either — it becomes cross-examination material, and defending it well earns on the Communication axis.

**The size limit belongs to the panel, not the event (D-13).** "12 is the structural maximum" is retired. A panel is four judges and the players they hear in sequence, and 8 (6-12 workable) is its ceiling because pitch and cross-ex grow linearly with queue length. Events scale **wider** instead: concurrent panels, players distributed across them, no format cap on panel count. The cost is judges — 24 players is three panels and twelve judges — which is a chapter operations problem, not a rule. Queue depth stays worth watching: at depth 8 the last player has ~42 minutes of prep against the first player's 18, so add panels rather than deepen them.

**The 8-player cap is a camera constraint and binds only where there are cameras.** Televised Tier A caps at 8: eight streams on the overlay, eight faces to the audience, ceremony rhythm intact. **Untelevised Tier A has no maximum**, and neither does Tier B. Grading is identical regardless of how many panels an event needed.

**Awards are scoped to the event, leaderboards to the tier (D-04 adjacent).** An award is decided against the field that actually competed and nothing else. Winning Slopless Builder at a chapter event with a slop score of 20 while the global board's leader sits at 0 is not a contradiction — the award says *best in that room*, the board says *best across the tier*. Consequently there is **no cross-panel anchoring and no severity correction**: the league is multi-city with disjoint judge corps by construction, so judge variance is a property of the institution rather than something concurrent panels introduce. Communication scores travel between panels because the four rubrics are role-siloed and identical everywhere; slop scores travel because no human can touch them.

**The nontech stakeholder deliberates in the same room, on a separate rubric.** All four judges sit together; the stakeholder scores translation and trust on its own rubric rather than through a technical lens, which is what keeps that role measuring the thing it exists to measure. Also recorded, because it changes how judges behave: **deliberation produces scores, not winners.** Every award is computed from the scores afterwards by `compute_round_results`. A judge who thinks they are deliberating toward a verdict argues differently from one who knows they are deliberating toward their own number.

---

## Six blocked decisions resolved (2026-08-03)

Answers to six of the calls in DECISIONS_OWED, and what each changed.

**Two substrate windows with a hard cut between them (D-09).** The substrate is open during the build phase, cut at build end, and reopened for pitch preparation. The cut is real: the league disables the player's key server-side, which kills any generation in flight, so a request issued at 23:59 never delivers. That is the point of cutting rather than draining — usable code must not arrive after the buzzer. Access then resumes for prep.

Prep gets it back because preparing a pitch means reading your own code, and that is safe for a reason independent of any rule: at build end the archive is captured and deployed, and the fuzzer grades **the deployed copy**, never the working directory. Post-freeze assistance reaches nothing that is scored, so the freeze is enforced by *where grading reads from* rather than by withholding a tool the player legitimately needs. The **budget is one pool** across both windows, so spending it all building means preparing unassisted — the tradeoff survives, now resting on a mechanism instead of on a switch. Applies at **Tier A and Tier B only**; Tier C is BYOD, where there is no league key to disable and no budget to enforce. Cascaded through format_spec §3.1 and §5.5, TIER_A §3 and §4, ARCHITECTURE, BUILD_ROADMAP, and claude.md, clearing every `contested` marker the audit had placed on those passages.

**The token budget is 10,000,000, not 100,000, and the per-prompt cap is gone (D-02).** The budget is **ASSUMED**, not calibrated — nothing has been measured on the season model. It is raised for a structural reason: agentic clients re-send their working context every step, so cumulative consumption runs orders of magnitude above what is resident in context, and a cap sized against instantaneous context is exceeded before an agent finishes its first task. 10M sits well above that failure mode while still stopping a runaway loop, which is the job the budget actually has. The per-timer ladder in IDEAS_FOR_LATER was extrapolated from the retired 100k and needs re-deriving. The **25,000-token per-prompt cap is retired** — meaningless against 10M, and already non-functional for agentic clients, which carry more than that in resident context on a single step. An ordinary **rate-limit throttle** takes its place: it protects the proxy from a runaway loop without pretending to be a strategic constraint on the player.

**The container gets egress, allowlisted to one destination (D-01).** The sandbox is not network-isolated. It has internet access, and a firewall **above** the container permits `hackletleague.com` and `*.hackletleague.com` only. That is what lets a player's app call the proxy at runtime, and the allowlist is what keeps attribution airtight, since the league proxy stays the only reachable inference endpoint. "No internet access" was the wrong description and is corrected on the player-facing scoring page. Still open: who pays for judge-driven inference during clickaround.

**The three-minute upload grace is real now (C-20).** It was promised by four documents and implemented by none — the code rejected everything one second past build end. `backend/rounds/views.py` now accepts uploads until `build_end_at + 3 minutes`, the round payload exposes `submission_deadline`, and the player UI gates its upload form on that deadline rather than on the phase (the phase flips to `evaluation` at the buzzer, which would have hidden the form during the very window the grace exists for). Two tests cover the boundary. The buzzer still ends the *build*; the grace only protects the upload.

**The language-tier ladder is retired, which dissolves D-06 rather than answering it.** §5.4 sorted languages into Tier 1 / 2 / 3, implying the league's measurement got weaker down the list. It does not: the catalog cannot tell what a submission is written in. Verified against the runner — every applicability condition is observed HTTP surface (`at_least_one_http_endpoint_exists`, `any_endpoint_accepts_text_input`, `has_auth_entrypoint`, `browser`, `served_over_https`, `any_form_has_password`), discovery builds a deliberately stack-agnostic map, and the only framework names anywhere in the code are comments explaining why a *generic* mechanism works across them (CSRF hidden-input parsing for "Gitea, Django, Rails, ..."; OpenAPI discovery for "FastAPI, connexion, Spring, NestJS, Express+swagger").

So "supported" never meant "gradeable." It means **provisioned**, and only at Tier A, where workstations are firewalled to `*.hackletleague.com` and therefore cannot reach npm or PyPI: a language is supported when the league has imaged its toolchain and mirrors its packages. **We are the mirror because nothing else is reachable.** At Tier B and Tier C, where no workstation is locked, the section does not apply at all. Rust stays supported; so does everything else the league chooses to image. The Rust-versus-Ruby disagreement (DOC_STATE C-09) stops existing along with the tiers, and the surviving question is an operations one: what can the league keep mirrored and imaged for a season.

**Tier C Extended is retired (D-15).** Its durations were never decided, and the doc's "~135-180 minutes" disagreed with a shipped profile that ended at T+107. Rather than invent a number to reconcile them, the profile is withdrawn from the selectable choices so no new round can pick it. The phase profile stays in `services.PHASE_PROFILES` so any round already carrying the value still resolves, and the design stays in TIER_C_OPERATIONS for when the durations are settled.

**Two schema gaps closed.** `Event.format` accepts `underspecified`, so the third sanctioned format can finally be recorded — notable because the one token measurement above came from an Underspecified round. `EventParticipant.judge_specialization` accepts `stakeholder`, completing three technical roles plus one nontechnical. **Neither implements the 30/20/20/30 role weighting**: `rounds/scoring.py` still averages six facet score-types and never reads `judge_specialization`. That remains D-11, and it is still blocked on what feeds the second axis before the fuzzer is wired.

---

## Deduction-only reaches the fuzz schema at last (2026-07-30, DOC_STATE C-02)

DATA_MODEL's three fuzz entities were still written in the award-points model retired a month earlier. Now they are not.

- **`FuzzTest`** — `points_defended` / `points_gracefully_handled` / `points_broken` collapse into one `penalty : int (>= 0)`. There is no positive award to record, and the value is added to a score where higher is worse, so it is never negative.
- **`FuzzResult`** — `points_contributed` becomes `penalty_contributed : int (>= 0)`, and the four-value outcome enum becomes three. `defended` and `gracefully_handled` both meant "the probe did not fire" and were indistinguishable under deduction-only; what survives is `clean` versus `not_applicable`, which score identically but are counted apart because format_spec §4.2's Clean Rate and Attack Surface Coverage need them separate.
- **`PlayerFuzzInvocation`** — `score_delta` (signed) becomes `slop_added : int (>= 0)`, and the running total is documented as sorting **ascending**, since lower slop is better.

**Timing was the whole point.** No model exists for any of the three — `backend/rounds/models.py` has `Round`, `Submission`, `Score` only — so this was a prose edit. Once Stage 5 builds models from this schema it becomes a migration, and Stage 5 is already underway in the fuzzer session.

**Left standing on purpose**, each annotated in place: `FuzzResult.override_by_judge` and `override_reason` (whether the tester judge gets a per-probe override is DECISIONS_OWED **D-18**, unresolved and not a wording call); `FuzzTest.bundle`, which lists two values where the runner ships three; and `intent_dependence` / `applicability_notes`, which presuppose per-test intent classification that FUZZ_RUNNER_SPEC says the schema should not carry. None is a points-model problem and each needs a decision or another session's file.

---

## Substrate rules: buzzer enforcement, budget reframe, and the wrapper carve-out (July 2026, Stage 4 design)

Three changes to the substrate rules, formalized while scoping Stage 4.

**The AI-wrapper category is deliberately NOT prohibited — do not reintroduce a ban.** This is the entry to read before "tightening" anything here later. The Tier A restriction on external credentials was never a written rule; it is structural, a consequence of the firewall and RMM leaving nothing external to reach. It is now stated explicitly in format_spec §5.7 as applying to **player-supplied credentials only**. No anti-wrapper rationale is attached to it, and none should be added. The reasoning: wrappers are the dominant shape of contemporary software, and a league premised on AI as the substrate cannot coherently firewall out the most common thing built on it. The resolution was to supply the credential rather than relax the environment — league-issued proxy keys (§5.8), where the league keeps the key, the model pin, the budget, and the audit trail. If a future edit re-broadens this to "no credentials at Tier A," it has silently re-banned the wrapper category and undone §5.8.

**Buzzer enforcement is one gate with two conditions, and the rollback rule is gone.** Substrate access ends when the budget is exhausted *or* build time is up, enforced identically — the same shape a commercial provider uses to cut an account off at a usage limit. Concretely: **403, not 429** (429 signals retry-later and agentic clients have backoff wired to it, so an agent would retry in a loop while the player watches a spinner; 403 is terminal and surfaces immediately), a **player-facing** response body because it reaches the player through their own client, and **in-flight requests cut rather than allowed to finish** (a request issued at 23:59 would otherwise return usable code after the buzzer). This **replaces** the previous "AI responses are truncated; partial code changes roll back to pre-prompt state" language — there is nothing to roll back in a chat window, because nothing was applied. Human edits at freeze remain a separate, tier-dependent rule (inspector-enforced at Tier A, honor system at Tier B). Cascaded through format_spec §3.1 + §5.5, TIER_A §7, ARCHITECTURE, BUILD_ROADMAP Stage 4, and the two IDEAS agent-freeze entries that defined themselves by reference to the deleted rule.

**The token budget is cost control first, an efficiency signal second.** It is a ceiling that stops runaway loops, not a number calibrated to bind on a normal round and force triage. Earlier drafts credentialed "resourcefulness" as a scored skill; that claim is withdrawn until there is data supporting it. Recorded alongside it in §5.5: cumulative agentic consumption runs far above what is resident in context, because an agentic client re-sends its working context on every step — which is also what makes a 25k per-prompt cap non-functional for agentic use. **No value was changed in this entry.**

---

## Scoring: deduction-only "Slop Score" (June 2026, Stage 5 design)

The resilience score was reworked and renamed in two composed changes, formalized during Stage 5 (fuzz runner) design. Best Overall is still the rank-sum composite with Communication — only the resilience component's shape and name changed.

- **Deduction-only.** Scoring no longer awards points for passing a probe. A probe either detects slop (adds a penalty) or it doesn't (zero). This honors the attacker/defender asymmetry (defending 7 of 8 SQL endpoints is still a breach — the 7 add nothing, the 1 adds full penalty) and resolves the parameterized-SQL-invisibility problem structurally (a defended hidden sink and an absent one both score zero, which is correct — neither is vulnerable). It collapses the prior `provable_defense` / `failure_only` scoring split and the `worst_case` / `additive` aggregation modes into one rule: sum the penalties of fired probes. `evidence_model` survives only as a detection hint.
- **Renamed Resilience Score → Slop Score, sign flipped.** Was `(-∞, 0]`, higher-is-better; now `[0, +∞)`, **lower-is-better, 0 = perfect** (golf-style). Presentation-equivalent, but it closes the loop with the slogans ("no slop survives"; "the fuzz is what separates hacklets from slop"), reads as universally-legible lower-is-better, and coheres with the Vibe Mill → HackLet thesis.

Preserved deliberately: the **"Most Resilient"** award title (aspirational quality vs descriptive measurement), the **"fuzz catalog" / "fuzz runner"** names (fuzzing is the method, slop is the measurement), and **"resilient"** as a quality adjective.

> **Reversed 2026-08-03.** The award is **Slopless Builder**, and the aspirational-title argument recorded above is superseded — it should not be reintroduced. The "fuzz catalog" / "fuzz runner" names and "resilient" as a plain adjective still stand. See the rename entry below and format_spec §4.4.

Cascaded across format_spec.md (§4, canonical), LEAGUE_OPERATIONS.md, the tier ops docs, FUZZ_RUNNER_SPEC.md, IDEAS_FOR_LATER.md, BUILD_ROADMAP.md, ARCHITECTURE.md, claude.md, and the landing copy. **No platform migration:** the shipped Stage-3 scoring uses a judge-entered `engineering_score` stand-in (higher-is-better), intentionally left as-is; the real deduction-only `slop_score` field is born when the Stage-5 runner is built.

> **Correction, 2026-07-30.** This entry originally listed DATA_MODEL.md among the documents the change cascaded to. **It did not.** The 2026-07-28 documentation audit (DOC_STATE.md, contradiction **C-02**) found all three fuzz entities still carrying the retired award-points model a month later: `FuzzTest.points_defended` (positive) / `points_gracefully_handled` / `points_broken` (negative), `FuzzResult.outcome` as a four-value enum with `points_contributed` "can be positive, zero, or negative", and `PlayerFuzzInvocation.score_delta` signed. Fixed on 2026-07-30, while all three were still prose and no model had been built from them — see the entry below.

---

## In progress — Stage 1 close-out (as of 2026-06-18)

- [x] End-to-end acceptance **verified on the live site**: signup → verify email → login → create chapter (pending) → admin approve (verified) → appears in directory → suspend (leaves directory). Full lifecycle walked.
- [x] Real transactional email — Resend SMTP, domain verified (SPF/DKIM), confirmed delivering to inboxes. (`docker-compose.yml` now forwards `EMAIL_*`/`RESEND_API_KEY` to the backend; Sites record renamed from `example.com` to HackLet League so emails read correctly.)
- [ ] ~1 week of stable uptime → Stage 1 officially ships.
- Next: **Stage 2 — events** (Google SSO landed — see below).

### Close-out fixes (the bugs squashed to get acceptance green)
- **Email verification link 400'd** — allauth percent-encodes the key's colons (`%3A`) in the email URL; `useParams()` returned it still-encoded, so the backend rejected a key it never signed. Decode before POSTing.
- **Login didn't update the UI** (then 409 on retry) — the header's auth nav only checked the session on mount and never remounted across client navigation; now re-checks on route change, and login treats `409 (already authenticated)` as success.
- **Pending chapter detail 500'd** — SSR fetches the API as `Host: backend:8000`, which hardened `ALLOWED_HOSTS` rejected (`DisallowedHost` 400 → frontend 500). Allow the internal host; also forward the request's session cookies to SSR so a creator can see their own pending chapter.
- **Status lifecycle** — default is now `pending` (was `unverified`); detail-page banner is state-aware (pending / suspended / not-approved); new owner **`/dashboard`** lists your chapters with status badges (via `/api/chapters/mine/`).

---

## Google SSO (June 2026, post-Stage-1)

Added **"Continue with Google"** on login + signup via **django-allauth socialaccount** (headless redirect flow). The OAuth client is configured from env vars (no DB `SocialApp`); a successful sign-in lands the user straight on `/dashboard`. Getting the headless OAuth flow working surfaced four non-obvious requirements, each worth remembering:

- **`django-allauth[socialaccount]`, not base** — the base package omits the OAuth HTTP/JWT libraries; adding a provider without the extra crash-loops the backend on `ModuleNotFoundError: No module named 'jwt'`.
- **`SameSite=Lax`, not `Strict`** — Google's callback is a cross-site top-level redirect, and a Strict session cookie is dropped on it, losing the OAuth state.
- **Absolute `callback_url`** — allauth doesn't honor a relative return path after the provider round-trip; the button sends `window.location.origin + /dashboard` (matching allauth's reference SPA).
- **Caddy must proxy `/accounts/*` and be reloaded on Caddyfile changes** — the bind-mounted config isn't picked up by `up -d`, so `deploy.sh` now reloads Caddy every deploy.

Also: mounted `accounts/` (under `HEADLESS_ONLY`, allauth.urls serves only the provider OAuth callback), and added a `socialaccount_login_error` frontend fallback so a failed social login lands on a real page.

---

## Chapter CRUD completed (June 2026, post-Stage-1)

Chapter owners can now **edit and delete** their chapters from the dashboard — the U + D that were missing (create/read already existed). Details:
- Update + delete are **owner-scoped** at the queryset level, so a non-owner gets **404, not 403** (existence isn't leaked); covered by new pytest cases.
- **Slugs stay stable** across renames (no broken links / directory churn).
- **`contact_email` is owner-only** — returned to the creator for editing, blank in public API responses.
- Delete is a **hard delete** (cascades the owner membership). Editing a verified chapter does **not** auto-revert it to pending — owner edits are trusted for the pilot.

---

## Stage 1 — Foundation (June 2026)

Deployed the platform — **Django + DRF + PostgreSQL + Next.js behind Caddy** — running on the home Proxmox VM and **live (public, not publicized) at https://hackletleague.com** over HTTPS with production settings.

### Backend (Django)
- Django 5 project (`uv`, split `base/dev/prod` settings, whitenoise), Postgres 16, `/api/healthz` liveness probe.
- Custom **email-based `User`** model (UUID pk, `is_superadmin`, JSON profile) + Django admin.
- `Chapter` + `ChapterMembership` models per DATA_MODEL, with admin (superadmin chapter approval).
- **django-allauth headless** auth — email login, session-based (no JWT), mandatory email verification, `/api/csrf/` for SPA writes.
- DRF API: chapter directory (verified-only), chapter detail, authenticated chapter create (→ owner membership, pending review), `/api/chapters/mine/`, profile `/api/me/`.
- `pytest` smoke tests (custom-user manager, auth gates, chapter create flow, directory filtering) — run in CI.

### Frontend (Next.js 16 / React 19 / Tailwind v4)
- Standalone-output Docker build, served by Caddy at `/`; backend at `/api`, `/admin`, `/_allauth`.
- Terminal/CTF aesthetic ported to the app; shared header/footer; sticky-footer layout.
- Server-rendered chapter **directory** + **detail** pages (SSR via internal API).
- Full **auth flow**: login, signup, email verification, auth-aware nav, **profile** edit, **chapter-creation** form — same-origin session cookies + CSRF (no CORS).

### Infrastructure & deployment
- Portable **Docker Compose** stack (`docker-compose.yml` + `docker-compose.dev.yml`) — host-agnostic; the repo is the portability layer.
- **Caddy** serves the public domain over HTTPS *and* the LAN IP over plain HTTP simultaneously (two site blocks via `SITE_ADDRESS` / `LAN_ADDRESS`).
- Migration workflow: generate via the dev override → commit → rebuild (migrations are committed source).
- DB **backup/restore scripts** + a concrete **Hetzner migration runbook** (clone + `.env` + `pg_dump`/restore + DNS cutover).
- Production settings hardened: `DEBUG=False`, real `SECRET_KEY`, `ALLOWED_HOSTS`, secure cookies, HSTS, `CSRF_TRUSTED_ORIGINS`.
- Transactional email: env-driven SMTP in prod, with a console-log fallback when unconfigured.

### CI/CD & monitoring
- Single GitHub Actions workflow: `backend` (pytest + Postgres) and `frontend` (build) on every PR/push; **`deploy` gated on both passing, push-to-main only**, running on a **self-hosted runner** on the VM via `scripts/deploy.sh`.
- Repo hardening: restricted Actions allowlist, fork-PR approval, read-only workflow token.
- Uptime monitoring documented (UptimeRobot → `/api/healthz`).

### Fixed (ops)
- Migrations weren't persisting (`docker compose run --rm` in a `COPY`-based image) → added the dev-override bind mount + commit-migrations workflow.
- Branch divergence between dev machine and VM → rebase reconcile + `pull.rebase`.
- `ERR_SSL_PROTOCOL_ERROR` on the LAN IP → stale `.env` forced an HTTPS redirect → fixed by the dual-site Caddy config.
- Disk full (12 GB LV) → expanded the Proxmox disk and grew partition → PV → LV → filesystem to 39 GB.
- Next.js 16 dropped the `eslint` config key → removed it.
- `frozen-lockfile` CI mismatch → pinned `pnpm@10` to match the lockfile.

---

## Stage 0 — Landing page (June 2026)

- Static landing page (framework-free), iterated with design feedback:
  - terminal / CTF aesthetic (monospace, near-black + lime, CRT scanlines);
  - competition-platform layout (nav, stats strip, schedule / standings / tiers tables) modeled on Codeforces, CTFtime, and Advent of Code;
  - copy humanized to remove AI tells (rule-of-three, em-dash rhythm, antithesis constructions; first-person voice).
- Buttondown email signup wired to the `iansun20` account.
- Superseded by the Next.js landing in Stage 1.

---

## Documentation

- Reframed HackLet as a **multi-format league** running **HackLet Classical** (the FIDE model) — eight strategic shifts integrated across format_spec, LEAGUE_OPERATIONS, BUILD_ROADMAP, DATA_MODEL, ARCHITECTURE: league-of-formats (`Event.format_type`), FMWC precedent, the two-principle thesis (substrate equality + submission resilience), per-player account lifecycle (+ `WorkstationSession`), OpenAI-compatible AI proxy, Classical-chat vs Agentic-extension, Microsoft Agents League context, fuzz-catalog-as-moat.
- Web-verified and corrected FMWC and Microsoft Agents League facts.
- Created `IDEAS_FOR_LATER.md` (parking lot for out-of-scope ideas).
- Recorded strategic decisions: build-first/CTWC sequencing; **public ≠ publicized**; home VM now / Hetzner later.
