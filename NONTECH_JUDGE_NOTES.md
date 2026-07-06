# Nontech / Stakeholder Judge — Design Notes

*Working notes, not canonical yet. Captures the stakeholder-judge deep-dive. Flags open questions honestly rather than pretending they're resolved.*

---

## 1. Rubric structure: two rubrics, not one, not four

Four judges: tester/resilience, ui/ux, general engineering, nontech stakeholder.

**The three technical judges share ONE rubric.** They are all measuring the same underlying skill (can this person defend technical decisions under informed adversarial pressure) through three different entry angles. Tester probes correctness-and-intent, ui/ux probes human-facing choices, general probes architecture and tradeoffs. Same skill, three lenses. Giving them three separate rubrics would pretend they measure three different traits when they measure one trait through three windows, and would produce incoherent scoring where a player "wins" one and "loses" another for reasons that are really just which judge pressed harder.

**The nontech stakeholder judge gets a SEPARATE rubric.** It measures a genuinely different thing: can you make a skeptical non-engineer understand and trust what you built, without bullshitting and without drowning them. This is the FDE-facing-the-VP skill, where fluency and honesty pull against each other. A technically-perfect answer that leaves the stakeholder confused is a pass on the tech rubric and a fail on the stakeholder rubric, and that divergence is signal, not noise. Forcing translation-skill through a technical-correctness lens loses exactly the thing the stakeholder judge exists to catch.

---

## 2. The tester judge catches what the fuzzer structurally can't

The fuzzer scores whether the artifact runs and isn't slop. It cannot judge *intent-dependent* correctness. Example: at-most-once vs at-least-once delivery semantics. Whether duplicate delivery is a bug or the intended design is a question the fuzzer can't answer because it doesn't know the player's intent. The tester judge covers that gap. The fuzzer tests the artifact, the humans test the reasoning.

---

## 3. Per-format stakeholder relationship (the core insight)

The stakeholder judge is not one confused role. Each format puts the FDE in front of a different *kind* of stakeholder in a different phase of a relationship, and the judge's information-state should match.

### Vibe — the CES attendee (cold-acquisition stakeholder)
Full model in section 4A. Short version: the judge takes a **CES-attendee posture**, jaded, overstimulated, has seen forty products today, owes the player nothing, has no wound and no need you're solving. Vibe is greenfield, so the player has to *create desire from a standing start* in someone with zero reason to care. Cold-by-design, and the coldness IS the confound-control (a CES attendee is neutral-to-jaded about every category, so any pull toward adoption is attributable to the *pitch*, not to the judge happening to like the product category).

### Unslop — "did you actually fix it" (anxious-incumbent stakeholder)
Full model in section 4B. Short version: the judge KNOWS what was broken (they lived with the broken app and felt the bugs), but has NO idea what the player did, it's "AI witchcraft" to them, and they need convincing the fire is out. Information asymmetry (knows the wound, not the surgery) IS the test. The stakeholder evaluates *whether to believe you*, not the code. Wins on credible reassurance without condescension and without jargon-drowning; dismissive fails, jargon flood fails. The winner makes a frightened non-technical person trust it's safe to sleep. Distinct FDE sub-skill: trust-me-it's-fixed to a non-verifier.

### Underspecified — the customer whose vague brief you interpreted
The stakeholder judge WRITES the vague prompt (one prompt for all 8 players), holds the unspoken intent, and gets to insist on it in cross-ex. The person grilling you about your interpretation IS the person whose half-formed request you interpreted. "No, I wanted it for internal users, obviously" hits completely differently coming from the person who wrote the vague brief and knows they were vague. See section 5 for the full underspecified treatment.

**Consequence for the rubric:** one nontech rubric with a shared spine (clarity, no-bullshit, no-condescension, appropriate compression) plus a per-format top note, because "win the cold stranger," "reassure the scared incumbent," and "satisfy the ambiguity-author" have partially different success criteria.

---

## 4A. Vibe stakeholder — the CES attendee, in full

### Posture
Jaded, overstimulated, attention-poor. Has seen thousands of products, most of it junk, and knows it. Did NOT come looking for the player's thing. Fifteen seconds of attention before drifting to the next booth. The hardest cold-persuasion posture: no wound, no need, no investment, no reason to care. The player has to *manufacture desire from a standing start in someone who owes them nothing.*

### Why CES-posture is the right frame
It bakes in the confound-control. A CES attendee is *supposed* to be neutral-to-jaded about every category (they've seen nine recipe apps today and are tired). So the judge isn't "someone who loves recipe apps," and any lean-in is attributable to the *pitch*, not to category-taste luck. The coldness is the leveler that makes the pitch the variable instead of the product category.

### What it grades (cold-start persuasion under attention scarcity)
- **Immediate legibility.** Did you make the value land *fast*, or bury the lede so the attendee has to work to understand why they'd want this. A CES attendee who has to squint has already walked away.
- **Reading and adjusting to disinterest.** The attendee is *visibly* unimpressed at first (that's the posture). A good pitcher notices the glazing-over and pivots ("okay you don't care about the feature list, here's the one thing that matters"). A bad pitcher runs the rehearsed script into a wall. Only testable with a cold judge, a warm one gives nothing to read.
- **Demonstrated-real over vaporware.** CES is notorious for slick demos of nonexistent things, so the jaded default is "does it actually work." Vibe's structure helps: the app *runs* (built in the 24 min), so a sharp pitcher leans on "this is live, try it." Rewards shown-real over promised-real, maps to the FDE "I don't do slideware" instinct.

### CES-posture solves vibe's no-shared-substrate problem
Vibe's weakness was that the judge has no common anchor across 8 totally different apps. The CES frame dissolves it: a CES attendee doesn't compare products to each other, they render an independent "did this booth make me stop" verdict on each. You don't walk CES ranking booth twelve against booth five, you note which three made you stop. So the judge needs a *consistent internal bar* ("did this make me, jaded, stop and care"), not a shared substrate, and the posture makes absolute-not-relative scoring *natural* instead of a discipline the judge has to fight for.

### Honest scoping
Vibe is the *hardest* posture (create want from nothing) which makes it the best show (the visible jaded-to-interested turn is great TV) and the *thinnest credential slice*, because "made a stranger want a thing" is the most sales-adjacent of the three skills, furthest from the engineering-judgment core. Not a flaw, just honest: vibe carries the show and a real but thinner slice of the credential.

### Flash-over-substance is caught by the panel, not by the CES judge
CES rewards flash, and flash can outrun substance (killer pitch, mediocre app). But the fuzzer already scored the slop, and the tester judge is in the same panel ("cool pitch, falls over when you do X"). So the CES attendee is *free* to be purely a persuasion-judge, dazzle-able and all, because the truth of whether the thing is any good is enforced by the machine and the tech judges next to them. Stakeholder measures "did you make me want it"; the panel makes sure wanting-it can't survive the thing being garbage.

**Open fork:** does the CES attendee "adopt" (keep the product) or just rate the pitch? Changes what winning vibe means. Not decided.

---

## 4B. Unslop stakeholder — the anxious incumbent, in full

### Delivery: one slop, nine copies, frozen endpoint
The machined slop is served at a **frozen endpoint**. Judges (and players) *use* the running app there; judges never edit it. Players download/receive separate editable copies of the same original, fix their own copy, and their fixed copies go into containers for fuzzing and testing. One slop, nine copies: eight player copies (edited, containerized, scored) plus the judge-facing served version (used, never edited).

Serving the running app at an endpoint **structurally enforces the stakeholder judge's cluelessness**: they hit a URL and use a black box, they see behavior, there's no code to look at. "Clueless about the surgery" isn't a rule anyone has to obey, it's the delivery mechanism. The stakeholder judge should NEVER get code access (that would collapse the non-verifier test). Frozen = frozen-at-serve per session: if the app is stateful, each judge gets an ephemeral clean instance so one judge's poking doesn't corrupt the *before* for the next. The judge's version is the frozen before-photo; the players' containers hold the eight divergent afters. Slots into existing fuzz-container infra with one serve-the-original step at the front.

### The 42-minute soak
Judge has *access* to the running slop for the players' full window (24 build + 18 prep = 42 min) to mess around, use it normally, and *feel* the bugs. Required grind can be shorter than 42 (a small app might be fully felt in 20; a bored judge on minute 35 who's found everything might start inventing severity to stay engaged). Access matches the players' window; the grind doesn't have to.

### Why felt-pain beats a bug list
The stakeholder's authority comes from having *felt* the pain, not from knowing the diagnosis. A bug list makes them an *informed* judge (that's the underspecified posture). The anxious incumbent has *scars*, symptom-knowledge not cause-knowledge ("it keeps logging me out," "search never works," "it lost my data once"), experienced as a user. So in cross-ex they test the only way a real non-technical user can: **they try to reproduce the pain they remember.** "Before, when I tried to save, it just hung, is that fixed? Let me try." That's the cleanest non-verifier test and it only works with real remembered pain.

### Shared origin makes one judge's pain probe all eight fairly
All eight players start from the identical broken codebase, so the judge's 42-min knowledge of "how copy zero breaks" applies to every player's starting point. The judge felt bug X, so bug X was in every player's copy, so "what did you do about the save-hang" is a fair question to all eight. Shared origin is what lets one judge's experiential knowledge probe eight players fairly.

### Catches fixed-vs-merely-hidden
Under a 24-min clock a player might *suppress the symptom* (swallow the error so it looks fine on a quick try) rather than fix it. A bug-list judge might miss that. A judge who learned the *texture* of the failure knows the exact sequence that triggered the hang and can reproduce it precisely instead of surface-poking. This catches symptom-suppression-disguised-as-fixing, which is exactly the AI-slop failure mode (AI loves to make errors *disappear from view* without resolving them). The experiential judge is the *user-side* fake-fix detector.

### Bullshitting the non-verifier is structurally blocked (no special rubric clause needed)
The dark version (smooth player convinces the anxious stakeholder it's fixed when it isn't) is caught without a dedicated anti-bullshit clause on the stakeholder rubric, because the judges grill as a **shared panel**: the fuzzer already scored the residual slop, the tester judge read the code and can dismantle a false "it's totally fixed" live in front of the stakeholder, and the stakeholder can reproduce the remembered pain from the user side. Three sensors, same table. So the stakeholder judge is *free* to purely measure reassurance-quality (clear, honest, non-condescending, non-jargon) and trust the panel to enforce truth.

### Real divergence you do NOT reconcile
The stakeholder judge (satisfied: "I'm not getting logged out anymore") and the tester judge (finds a residual race condition) can *both be right*. On the tech rubric: partial, residual slop. On the stakeholder rubric: yes, the non-verifier trusts it. That divergence is real signal, the exact FDE tension where "good enough that the customer stops worrying" and "actually fully correct" come apart. Do NOT collapse the two scores into one. The divergence is the measurement. (The dishonest version of the divergence, reassured-but-actually-broken-and-bluffed, is the panel-caught case above.)

---

## 4. Context rooting: use the judge's real day job

The stakeholder judge's brief and context are rooted in where they *actually work*, lightly anonymized. Reduces persona-training overhead (no invented persona, they draw on real operational knowledge), and makes cross-ex answers cohere because the judge knows the real answers instead of improvising.

**Name-stripped to kill prestige confound.** "Used car dealer with an inventory bug" not "Carfax"; "payment processor" not "Stripe"; "CRM company" not "HubSpot." The name only adds noise (tests brand familiarity instead of interpretation). Removing it removes a confound the same way the AI removes the typing-speed confound.

Context arrives as something like: "car dealership, sells exclusively used cars, inventory system miscounts, we're selling nonexistent cars and claiming out-of-stock on cars we have." Real practitioners write far more plausible prompts than we can author on the fly, because they're reporting real mess, not inventing it.

---

## 5. Underspecified, in full

### 5.1 Don't tune the ambiguity
Same discipline as "don't tune the slop." Real ambiguity is messy, raw, unfair, not pre-balanced with a tasteful spread of defensible readings. Tuned/balanced ambiguity tests a fake skill (rhetorical commitment to an arbitrary choice, a debate skill) instead of the real one (discernment about likely intent under bad information, plus graceful recovery when wrong). Balanced ambiguity structurally removes the possibility of being *wrong*, which removes the getting-it-wrong-and-recovering moment, which is THE FDE moment.

### 5.2 Fairness comes from same-brief-for-all-8, not from balanced brief
Exactly like the shared slop codebase. Whatever's lopsided or frustrating or secretly-one-answer about the brief, it's the same for all 8, so it isn't unfairness *between players*. Equality is in the brief being *shared*, not the brief being *balanced*. This dissolves the "one bad prompt poisons the round" worry: only floor is "coherent, plausible brief," not "fair brief."

### 5.3 Company context is load-bearing for scoring fairness
Context is what converts a wrong read from *bad luck* into *missed signal that was actually there*. Without context, "make me something for the team" has no fact making one reading right, so scoring the read would be unfair (rewarding a lucky guess). With context ("inventory miscounts"), there IS a discernible right direction, so a player who builds a flashy sales page instead of fixing inventory truth *missed available signal*, and the judge can rightly point at overlooked context. Context legitimizes the whole scoring ladder.

### 5.4 Multiple latent axes from one plain sentence
Not stacked hidden puzzles (that would tip into mind-reading). Latent axes all *derivable from the words*, so it's reading, not guessing. Example brief: **"car dealership, inventory miscounts, holiday season next week."**
- **"inventory miscounts"** → correctness axis: must be accurate, and handle the ambiguous cases gracefully (flag low-confidence instead of guessing wrong).
- **"holiday season"** → throughput axis: high demand, must hold up under load.
- **"starts next week"** → deployability axis: modular, ready to deploy fast, adoptable in the customer's real timeline.

The three are in *tension* (accuracy pulls slow-and-thorough, throughput pulls fast-and-approximate, deployability pulls simple-and-modular). You can't max all three. The brief doesn't say which to prioritize, so the player reads the situation, picks a defensible balance, and defends it. One judgment with three forces, not three checkboxes. The cross-ex presses the one decision from three angles, which fits the tight 2-min clock because it's one thread.

### 5.5 Urgency shapes the solution space, not the clock
Every player still gets 24 minutes. Urgency ("holiday season next week") changes what a *correct solution looks like* (fast-executing, fast-working, accurate, deployable now), not the deadline. Deadline urgency would just test typing-under-panic, which the AI flattens anyway.

### 5.6 Hidden edge case: general-resilient survives it, naive breaks
The vague surface hides a specific worst case a *general* solution should survive without being told. Illustrative example (off-the-cuff but structurally sound): inventory can't classify at intake because certain car brands have near-identical winged logos, so a Chrysler gets tagged as Aston Martin, corrupting the count. A player who builds intake classification that flags low-confidence matches for human review survives it without ever hearing "Aston Martin." A player who builds classify-and-commit assuming high confidence walks straight into it. This tests whether general instincts produce robustness on unseen cases, which is the same AI-slop-catching disposition as the fuzzer, relocated to the design layer. Revealed via cross-ex late, exactly how real stakeholders drip out the most important detail last.

### 5.7 Players have AI, so domain-unfamiliarity is not an excuse or a confound
If a player doesn't know how dealership inventory works, they ask the AI, in the round, on the clock. Asking the AI to close the domain gap is itself a scored steering behavior: the player who asks "what breaks in real dealership inventory systems, what are the ambiguous-classification edge cases" is far more likely to build something general enough to survive the hidden case. Domain obscurity stops being a fairness problem and becomes a discriminator (reflexively-asks vs reflexively-assumes). Judges can root context in the weirdest niche of their real job without advantaging players who happen to know that world.

### 5.8 Scoring ladder for the read (three tiers)
- **Nailed the read** (top): demonstrates the primary construct, discernment, plus composure. Under the edge-case framing this means the build's generality survived the hidden worst case.
- **Missed the read but owned it** (credited, capped well below top): recovery is real FDE skill (getting it wrong through no fault and handling it), but it's *partial credit, not a substitute*. Capping it well below the top matters as incentive design: if recovery scored close to nailing it, players would deliberately pick a safe-wrong reading they can defend beautifully (sandbagging the interpretation to show off recovery). The gap keeps expected value of *trying to nail it* higher than *planning to gracefully miss*.
- **Missed and handled badly** (floor): argued with the stakeholder, folded, or bluffed. Arguing best-practice at a stakeholder whose house is on fire is a real FDE failure.

The insistent stakeholder (who wrote the brief, holds the unspoken intent) tests grace under a customer's unreasonable-but-real certainty about a thing they never clearly said. Not testing mind-reading; testing recovery.

---

## 6. Reproducibility: the two-client-types problem and the fix

The "vague client" is actually two different creatures that grade the same performance oppositely:
- **Type 1, genuinely doesn't know what they want.** Vagueness is real emptiness, no secret right answer. Grades *facilitation* (did you guide me somewhere good). Confident-commit annoys them; collaborative discovery serves them.
- **Type 2, knows exactly, communicated it badly.** Vagueness is encryption. Grades *discernment toward a fixed target* (did you land near what I meant). Confident-commit-to-the-right-reading impresses them; pure facilitation that never converges fails them.

Same player performance swings on which mode showed up = the reproducibility crack. The killer is a judge whose target *forms in reaction to the performances* ("only found out what I wanted at the pitch phase"), because then whoever articulated it best retroactively *became* the answer key, and everyone before them was graded against a key that didn't exist yet.

**The fix: pre-commit and freeze, BEFORE the round begins.**
1. Judge picks their real-domain problem.
2. Judge commits, frozen and timestamped to the platform, *before* writing anything: which client type they are, and (if Type 2) the specific sealed intent. Uneditable after (same integrity mechanic as the sha-256 submission freeze; if the intent isn't frozen before round start, they run as Type 1 by default).
3. *Then* the judge writes the vague brief and introduces it.

This converts "target forms in reaction to players" (unreproducible) into "target exists, then players are measured against it" (reproducible within round). Because intent is sealed first, even a live on-stage intro is safe: it's a *presentation of a fixed thing*, not the *creation* of it.

**What this buys and doesn't:**
- *Within a round*: reproducible. All 8 face the same pre-committed type and (if Type 2) the same sealed intent.
- *Across rounds*: still varies (one round is facilitation-type, another discernment-type). This is honest, because both are real FDE situations and a credential that only tested one would be *less* valid. Just don't oversell two underspecified credentials as having tested the identical thing.

**Type is hidden from players.** Reading which client you've got (lost-and-needs-guidance vs knows-but-can't-say) is itself a huge FDE meta-skill; you diagnose it live from how they respond. Misreading the type is its own failure mode, so hiding it makes that testable. Leetcode parallel holds without the rot: grinding both flavors builds real diagnostic muscle, but the infinite case space (AI-machined briefs, real judge domains) means you can't memorize which flavor or what it's about. Grind produces skill, not answers.

---

## 7. On-stage intro during the 5-min intro phase

Good idea, because the *spoken* version is where the type-diagnosis signal is richest. A written brief is flavor-neutral (you can't tell lost from knows-but-can't-say from text). Spoken, the lost client trails off and hedges; the specific-but-inarticulate client jabs with frustrated certainty. The intro carries the signal that makes the hidden-type test readable at all.

Safe *because* intent is pre-sealed (section 6), so live delivery can't retroactively write the answer key. The only remaining risk is presentation *leakage varying per telling* (judge warmer/chattier on round three than round one, accidentally telegraphing more). Fix: **one shared delivery to all 8 at once, or recorded-once**, never eight separate live tellings. Same-brief-for-all-8 principle applied to the spoken version.

---

## 8. Cross-ex concision (anti-filibuster)

The 1-min pitch + 2-min cross-ex compression is construct-valid, not just televisable: real technical communication is compression under a busy stakeholder's constraints. But short cross-ex creates a filibuster exploit (eat the clock on an easy question to deny the judge the hard one).

**Fix at the rubric level, scoring the PLAYER not the judge.** Not "did the judge get their question in" (that makes the player liable for the judge's clock management). Instead: **"responsiveness and concision: did the player answer what was asked and yield the floor, or filibuster / dodge / over-explain to run the clock."** Scores the player's behavior (fair), maps to a real skill (answer, don't drown them, give them their time back), and *prevents* the exploit because a rational player facing that rubric answers tight and yields, which means the judge gets *more* questions in. Nuance the judges must hold: length justified by a genuinely hard question is thoroughness, not padding. Lightly judge-dependent, but "padding vs thorough" is a distinction competent people make intuitively.

---

## 9. Slop-score reveal timing (relevant to cross-ex, not only nontech)

Withhold the slop score through the *blind* pitch and cross-ex, because the highest-value signal (does this person know their own work well enough to find its weakness *without* the machine telling them) only exists if they defend blind. Handing them the fuzzer's verdict first lets them parrot the machine and *look* like they have the instinct. Ideal sequence: build → fuzzer runs (hidden) → blind pitch + cross-ex → reveal *as a cross-ex beat* ("the fuzzer found X, you didn't mention it, talk to me") so you also catch own-your-failures-gracefully. Fallback if the 2-min clock can't fit a reveal beat: withhold entirely until after cross-ex and protect the self-knowledge signal (the more load-bearing of the two for the thesis).

---

## 10. Open questions (not resolved tonight)

- **Aggregation.** Each of the four judges produces an independent 0-100 and you average? Or the three technical judges collectively produce one technical score and the nontech produces the other half? Leaning: each judge scores their own rubric fully; technical = average of the three technical judges; communication total = weighted blend of technical-average and nontech. Not decided.
- **Granularity.** Score the specific answers (anchored, less bias, more mechanical) or the whole-cross-ex defense holistically (truer to what defense-under-pressure is, more subjective)? Leaning: mostly per-answer anchored with a small holistic composure modifier. Not decided.
- **Anti-bullshit floor.** Almost certainly needs its own scored band. The whole credential is "catches AI slop, doesn't fold to fluent confidence," so the rubric must reward "I don't actually know, I'd have to test that" over confident-wrong, or it credentials the exact sycophancy-vulnerability it's meant to screen out. A bluffed-and-caught answer should take a *bigger* hit than honest-uncertainty. Load-bearing, not a footnote.
- **Cross-round comparability.** Accepted that underspecified varies (facilitation-type vs discernment-type, different judge domains). Is any comparability floor wanted so one chapter's brief isn't wildly gentler than another's, or is raw variance fine (honest to reality, both are real FDE situations)? Leaning: raw variance is fine, don't oversell standardization. Not firmly decided.
