# Tier B Operations

*Operational template for HackLet Tier B events. For tier philosophy and verification, see LEAGUE_OPERATIONS.md §4. For format mechanics and scoring, see format_spec.md. For Tier A and Tier C operational profiles, see TIER_A_OPERATIONS.md and TIER_C_OPERATIONS.md.*

> **Reading the status markers.** Each section below carries a `Status:` line: **BUILT**
> (exists in code, cited to file and line), **DESIGNED** (specified, not implemented),
> **MIXED**, or **SUPERSEDED** (describes a decision that has been replaced). Timing blocks
> additionally carry **ILLUSTRATIVE**. Classifications were verified against source, not
> against other documents. The full audit — including every known cross-document
> contradiction — is in [DOC_STATE.md](DOC_STATE.md).

---

## 1. Tier B Identity

> **Status: DESIGNED** — no Tier B chapter exists. **Redefined 2026-08-03**: Tier B was
> previously "league-hosted AI substrate with honour-system budgets." That definition was
> retired because it did not describe an integrity step — without a firewall the league cannot
> claim substrate exclusivity, and budgets were always enforceable server-side regardless. Tier
> B is now the profile formerly called *Tier C Extended*.

Tier B is **live human judging without controlled infrastructure**. Players compete on their own
machines with their own AI, and then defend their work in a live pitch and cross-examination in
front of the four permanent judge roles. It is a weekend afternoon, 8-12 players per panel, no
firewall, no RMM, no broadcast, and no league inspector.

**The ladder grades on judging rigour, and Tier B is the rung where humans enter.** Each step
buys one specific thing:

| Tier | What it is | What the rung adds |
|---|---|---|
| **C** | PITCH.md, LLM-judged, one hour, scales to 100+ | the accessible floor |
| **B** | live pitch + cross-examination, human judges, BYOD | **live human cross-examination** |
| **A** | the above plus controlled workstations and enforced substrate | **parity you can actually claim** |

That is why Tier B exists. Cross-examination under an informed adversarial panel is the format's
most distinctive credentialing dimension, and before this redefinition it was reachable only by
chapters that could field RMM, a firewall, broadcast, and an on-site inspector — which is Year
3+ territory. Tier B makes it reachable with four judges and an afternoon.

Tier B is useful for:
- Chapters that can field a judge corps but not controlled infrastructure
- Communities that want the live-defence dimension without Tier A's operational burden
- Chapters building toward Tier A verification, since the judging discipline transfers directly

**What Tier B does not claim: substrate equality.** Players bring their own AI, so a competitor
with a premium subscription has a systematic advantage over one on a free tier. That is the same
honest limitation Tier C carries (TIER_C_OPERATIONS.md §3), and it is exactly the gap Tier A's
firewall closes. Tier B credentials therefore claim *demonstrated live defence of work built
under self-selected substrate* — real, and bounded.

**League-hosted substrate is available at any tier and is not what defines one.** A chapter may
opt into the league proxy, in which case the league meters and pays for the inference and the
event records that it did so. That is a convenience the league is buying, not an integrity
claim: only Tier A's firewall makes league substrate *exclusive*, and exclusivity is the whole
of the parity argument (format_spec.md §5.3).

## 2. Infrastructure

> **Status: DESIGNED**.

Tier B infrastructure is **substantially lighter** than Tier A:

**What's required**:
- League-hosted AI substrate access (same OpenAI-compatible endpoint as Tier A) — see §3
- Chapter-determined workstation policy (chapter-hosted hardware OR BYOD with chapter-determined policy)
- Chapter admin oversight in place of firewall enforcement
- Judge corps covering all four permanent roles (calibration relaxed from Tier A, but the roles are not optional — see §9)
- Documented venue with appropriate setup, including a space where players wait without watching pitches ahead of their own (sequestration, format_spec §3.1)
- Chapter admin team familiar with league operations

**What's optional**:
- Workstation control (chapter chooses; BYOD acceptable but reduces integrity claims)
- Network firewall (not required; Tier B makes no exclusivity claim, so there is nothing for a firewall to enforce)
- Broadcast infrastructure (not available at Tier B; see §6)
- Multi-day tournament infrastructure (Tier A territory)

**What's not required**:
- RMM workstation control with master image deployment
- Per-player ephemeral Unix accounts with `userdel -r` reset
- Comprehensive audit trail (basic audit at AI substrate level remains)
- Anti-cheating enforcement infrastructure (honour system replaces structural enforcement; Tier B credentials do not claim what the chapter cannot enforce)

The integrity gap from Tier A is honest. Tier B credentials don't claim what the chapter can't enforce. Players and employers interpret the credentials with appropriate weight.

## 3. AI Substrate at Tier B

> **Status: DESIGNED** — no proxy exists, so the opt-in path below is unbuilt.

**BYOD by default.** Players bring their own laptops and their own AI tooling — chat clients,
IDE agents, whatever fits their workflow. Web search and multiple models are allowed, because
without a firewall any restriction is theatre. No enforced token budgets, because the league is
not paying for the inference.

**League substrate is an option, not a tier property.** A Tier B chapter may opt into the league
proxy. If it does:

- Every player at that event uses the pinned model (format_spec.md §5.3), so *within* the event
  the model is uniform
- The league meters usage server-side and pays for it, so the per-player budget is real and
  enforced — budget enforcement never depended on the firewall
- The event records that it ran on league substrate

What it still does **not** buy is exclusivity. Nothing stops a player alt-tabbing to their own
subscription, so the parity claim stays out of reach and the credential language does not change.
The honest framing is "the league supplied a model" rather than "every player used the same one."

**Substrate equality at Tier B is not a claim**, opt-in or not. See §1.

## 4. Round Timing — Tier B Standard Profile

> **Status: DESIGNED** — **no `tier_b` value exists** in the shipped `timing_profile` enum (`backend/rounds/models.py:19-22`); a Tier B round must currently be scheduled as `tier_a`. Timestamps are ILLUSTRATIVE (see below).

Tier B runs **Tier A's phase shape minus the Zamboni Period** — BYOD means there are no
ephemeral accounts to tear down and no workstations to re-image, so the reset block does not
exist (see TIER_A_OPERATIONS.md §4 for phase contents).

> **Only two things here are fixed.** The **24-minute build clock** is server-enforced and is
> the format's defining constraint. The **per-player pitch slot** (60s pitch + 120s
> cross-examination + 30s transition) is a fairness constraint and identical for every player.
> Everything else below is a *planning estimate*, and the pitch block scales with field size —
> 8 players is 28 minutes, 12 is 42. An afternoon that starts late ends late.

```
  5 min   — Opening
 24 min   — Build phase                        (fixed)
 18 min   — Evaluation + pitch preparation
 28 min   — Pitch + cross-examination          (8 players x 3.5 min; scales with field)
 18 min   — Deliberation
 14 min   — Award reveal + closing
─────────────────────────────────────────────────
~107 minutes at 8 players. No Zamboni: nothing to reset
```
```

### Differences from Tier A Phase Operations

**Opening ceremony**: lighter production rhythm without broadcast requirements. Still serves orientation purpose, but no broadcast intro needed.

**Build phase**: identical mechanics on the player's own machine and their own AI, 24-min Sprint timer. If the chapter opted into league substrate (§3), the budget is metered server-side.

**Concurrent evaluation + pitch preparation**: identical concurrent structure. Judges evaluate in their portals while players write PITCH.md and prepare live pitches. PITCH.md authoring is optional at Tier B (the artifact exists, but live performance is the primary credentialing dimension as at Tier A).

**Pitch + cross-examination**: identical 28-min structure for 8 players. Live performance with human judges is the primary credentialing dimension. Tier B preserves this dimension that the Tier C MVR's LLM judging cannot replicate.

**Deliberation**: 18-min judge deliberation. There is no audience vote at Tier B — People's Hacklet is a broadcast element and Tier B does not broadcast (see §6).

**Award reveal + closing**: 14-min ceremony without broadcast production. Still ceremonial, still has audience reaction when audience is present, but lighter production overhead.

**Zamboni Period**: does not apply. Tier B is BYOD, so there are no ephemeral accounts to tear down and no workstations to re-image — players close their laptops. This is why the Tier B clock is Tier A's shape minus the Zamboni.

### Round Sizing

**8 players per panel** at Tier B, 6-12 workable, matching the Tier A template. **There is no event maximum** — Tier B does not broadcast, so the 8-player cap that binds televised Tier A does not apply here at all. A larger field runs concurrent panels, each staffed with its own four permanent roles, and the limit is how deep the chapter's judge corps goes (format_spec.md §3.2).

## 5. Submission Mechanism

> **Status: DESIGNED** — SCP is Stage 7 and unbuilt; the portal path that does exist has no grace period (DOC_STATE C-20, handed to the platform session).

Tier B submission depends on chapter workstation policy:

**Chapter-hosted workstations (recommended for stronger credentialing)**: SCP-based submission identical to Tier A. League daemon on workstations captures submissions at T+29:00 to league infrastructure. Player accounts may be ephemeral or persistent per chapter operational preference.

**BYOD policy**: portal upload with grace period identical to Tier C (see TIER_C_OPERATIONS.md §6). T+29 → T+32 grace window for upload completion. Failure to submit by T+32 results in disqualification.

Tier B credentials sit above Tier C because the live cross-examination dimension is present and human-judged, and below Tier A because substrate is self-selected. Opting into league substrate (§3) does not move them: the league supplying a model is not the same as every player provably using it.

## 6. Audience and Broadcast

> **Status: DESIGNED**.

**No broadcast at Tier B**. Broadcast production is Tier A only (see TIER_A_OPERATIONS.md §6). Tier B chapters typically don't have broadcast infrastructure capacity; the operational burden of broadcast production doesn't fit Tier B's operational scope.

**Audience optional at Tier B**. Chapters may invite in-person audience when local capacity supports it. **People's Hacklet is not offered at Tier B**, with or without an audience: it is gated on broadcast, not on attendance, and belongs to televised Tier A only (format_spec.md §4.4).

The format runs primarily for **competitive purposes** at Tier B without strong audience-design philosophy applying. Lower production overhead than Tier A; lighter operational burden than full broadcast events.

Asynchronous content (written results, post-event recaps, social media coverage) remains viable for Tier B events without requiring live broadcast.

## 7. Fuzz Catalog Evaluation

> **Status: DESIGNED** — not integrated with the platform.

The fuzz catalog operates at **full strength at Tier B** (catalog is tier-agnostic per LEAGUE_OPERATIONS.md §4). Identical to Tier A: both public and hidden pools execute against every submission. Attack surface enumeration phase. Server-side deployment in ephemeral containers. Catalog evolution feedback applies identically across tiers.

The submission infrastructure may differ (SCP from chapter workstations vs portal upload from BYOD per §5), but downstream catalog evaluation is identical. Substrate equality holds at the **catalog evaluation layer** across all tiers — every submission faces the same deterministic adversary.

## 8. Scoring and Categorical Awards

> **Status: DESIGNED** — Most Efficient's availability here contradicts format_spec §4.4, which retires it per-round and ties it to enforced measurement Tier B does not have (DOC_STATE C-06).

Per format_spec.md §4, Tier B operates the scoring framework with two exclusions — Most Efficient and People's Hacklet, both of which need something Tier B does not have:

**Available per-round awards**:
- **Slopless Builder**: lowest Slop Score
- **Best Communicator**: highest Communication Score (live pitch + cross-ex with human judges)
- **Best Overall**: composite rank with progressive tiebreakers
- **Most Efficient**: **not offered at Tier B.** It requires enforced token measurement across every player, which needs the firewall that makes league substrate exclusive. Tier B has no such guarantee even when it opts into the league proxy (format_spec.md §4.4)

**Tournament-level categoricals**: Tier B chapters typically don't run multi-day tournaments (that's Tier A territory). Tournament categoricals (Best UX/UI, Most Novel, Iron Player, Comeback Player) are not available at standard Tier B events.

## 9. Live Judging Protocol

> **Status: DESIGNED** — four-role panel locked, unimplemented.

Tier B uses **human judge corps** identical to Tier A judging protocol (see TIER_A_OPERATIONS.md §9). Same judge panel composition — the four permanent roles (tester, UI/UX/HCI, general engineering, nontech stakeholder), weighted 30/20/20/30 into the 0-100 Communication axis (format_spec.md §4.1) — same cross-examination structure, same calibration discipline.

**All four roles are required at Tier B too.** An earlier draft let thin-corps chapters drop to three and re-normalize the weights; that is retired. Dropping a role does not merely rescale the axis, it deletes a dimension — a round with no nontech stakeholder has measured nothing about translation to a non-verifier, and no re-weighting recovers that. A chapter that cannot field four judges runs the round without the Communication axis, or does not run it. The cross-examination window is **120 seconds, the same as Tier A** — it is not shortened for a smaller panel, because questions are not rationed per judge and the window is not a function of panel size (format_spec.md §3.1).

> **UNCORROBORATED — the 90-second window appears in this sentence and nowhere else.** Every
> other document in the set carries 60s pitch + 120s cross-ex as the settled clock
> (format_spec.md §3.1, TIER_A §4 and §9, PITCH.md), with no shortened variant. This clause
> shortens the round by 30s per player — four minutes across an 8-player field — and no phase
> block anywhere reflects that. It also presumes the question-rationing mechanism, which is
> itself still open (TIER_A §9). Two readings, both plausible: the 90s figure is a real
> Tier-B accommodation that never propagated to the timing blocks, or it is an artifact of
> deriving 3 × 30s from a rationing model that may not survive. **Not resolved here.**

Tier B does not use LLM judging. The live performance dimension (pitch + cross-ex with human judges) is preserved because Tier B operates at scales where human judging fits the format clock (8-12 player rounds).

LLM judging at scale is Tier C MVR territory (see TIER_C_OPERATIONS.md §8). Tier B operates at smaller scales where human judging is operationally viable.

## 10. Credentialing Claims

> **Status: DESIGNED**.

Tier B credentialing sits between Tier C-bounded and Tier A-credentialing-grade:

**Substantive credentialing claims at Tier B**:
- Demonstrated AI-augmented engineering capability against full deterministic fuzz catalog
- Demonstrated live communication capability under pressure (pitch + cross-ex with human judges)
- Demonstrated competitive engagement at structurally-supported substrate
- Chapter-local ranking contribution with partial regional contribution

**Claims explicitly weaker than Tier A**:
- Substrate equality is policy-enforced, not infrastructurally enforced
- Most Efficient is not available (it needs enforced substrate measurement)
- No structural anti-cheating enforcement
- Limited audit capability beyond proxy-level logging
- Does not contribute to global league rankings at credentialing-grade weight
- Does not feed qualifiers to championship-tier events at full credentialing weight

**Credential interpretation for employers**:
- *Hiring for engineering capability signal*: Tier B credentials demonstrate real capability with policy-grade integrity
- *Hiring for elite signal*: Tier A credentials are the appropriate level; Tier B carries reduced signal
- *Hiring that values demonstrated live defence*: Tier B credentials evidence a player defending their own work under adversarial questioning, on self-selected substrate

The honest framing: Tier B credentials carry **real but bounded** market signal, sitting between the Tier C local-only signal and the Tier A credentialing-grade signal.

## 11. Verification

> **Status: DESIGNED** — no verification workflow exists; chapter approval is manual through Django admin.

Light superadmin review (name and basic legitimacy check) per LEAGUE_OPERATIONS.md §4 verification process. No formal Tier B application process; chapters self-elect Tier B operations and superadmin verifies basic legitimacy.

Chapters operating Tier B may later apply for Tier A verification as infrastructure matures and operational experience accumulates. Tier B serves as **graduation tier** toward Tier A for chapters with credentialing ambitions; Tier B also serves as **stable tier** for chapters whose communities don't require Tier A credentialing infrastructure.

## 12. Operational Position

> **Status: DESIGNED** — planning.

Tier B in the league strategic sequencing (see TIER_C_OPERATIONS.md §14):

**Year 0-1**: Tier B operations not yet active. Initial focus is Tier C MVR validation.

**Year 1-2**: Tier B emerges at chapters that can field a four-role judge corps. It needs no infrastructure a Tier C chapter lacks — the step up is people, not hardware, which is what makes it the realistic second rung.

**Year 2-3**: Tier B grows as chapter ecosystem matures. Some chapters operate stable Tier B; others use Tier B as transition toward Tier A verification.

**Year 3+**: First Tier A chapters emerge. Tier B continues as middle-ground operational tier serving chapters whose operational scope fits between Tier C accessibility and Tier A credentialing-grade investment.

Tier B's relative timing depends on chapter ecosystem maturation. Some chapters may skip Tier B entirely (going from Tier C directly to Tier A verification when ready); others may operate Tier B as their long-term sustainable tier.
