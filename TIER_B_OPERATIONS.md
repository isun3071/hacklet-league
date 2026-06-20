# Tier B Operations

*Operational template for HackLet Tier B events. For tier philosophy and verification, see LEAGUE_OPERATIONS.md §4. For format mechanics and scoring, see format_spec.md. For Tier A and Tier C operational profiles, see TIER_A_OPERATIONS.md and TIER_C_OPERATIONS.md.*

---

## 1. Tier B Identity

Tier B is HackLet's **middle tier** — real competition with policy-based enforcement rather than infrastructure-based enforcement. Tier B sits in the middle of the freedom-integrity tradeoff (LEAGUE_OPERATIONS.md §4): it has league-hosted substrate (providing structural integrity baseline) with honor-system enforcement of budgets and anti-cheating (lighter operational burden than Tier A).

Tier B is useful for:
- Chapters establishing themselves before Tier A verification is feasible
- Smaller communities where Tier A infrastructure investment isn't justified
- Events where credentialing rigor matters but not at full Tier A grade
- Transitional operations as chapters mature toward Tier A capability

Tier B credentialing claims sit **between Tier C-bounded and Tier A-credentialing-grade**. Wins contribute to chapter-local rankings plus partial regional contribution (per LEAGUE_OPERATIONS.md ranking systems). The credential carries community recognition without claiming the full credentialing-grade integrity that Tier A enforced infrastructure provides.

## 2. Infrastructure

Tier B infrastructure is **substantially lighter** than Tier A:

**What's required**:
- League-hosted AI substrate access (same OpenAI-compatible endpoint as Tier A) — see §3
- Chapter-determined workstation policy (chapter-hosted hardware OR BYOD with chapter-determined policy)
- Chapter admin oversight in place of firewall enforcement
- Judge corps as available (minimum 3 members, calibration relaxed from Tier A)
- Documented venue with appropriate setup
- Chapter admin team familiar with league operations

**What's optional**:
- Workstation control (chapter chooses; BYOD acceptable but reduces integrity claims)
- Network firewall (chapter chooses; honor system if BYOD)
- Broadcast infrastructure (not available at Tier B; see §6)
- Multi-day tournament infrastructure (Tier A territory)

**What's not required**:
- RMM workstation control with master image deployment
- Per-player ephemeral Unix accounts with `userdel -r` reset
- Comprehensive audit trail (basic audit at AI substrate level remains)
- Anti-cheating enforcement infrastructure (honor system replaces structural enforcement)

The integrity gap from Tier A is honest. Tier B credentials don't claim what the chapter can't enforce. Players and employers interpret the credentials with appropriate weight.

## 3. AI Substrate at Tier B

The league hosts AI substrate at Tier B identical to Tier A's unified-substrate model (see TIER_A_OPERATIONS.md §3 and format_spec.md §5.3):

- Chat-window interface through hackletleague.com browser tab
- In-IDE agent interface via signed VSCodium extension (when deployed, Stage 12+)
- Unified token budget shared across interfaces
- Season-pinned model (DeepSeek V4 Flash for Season 1)
- OpenAI-compatible chat completions endpoint
- AI calls audit-logged at proxy level

**The substrate difference from Tier A is enforcement**, not capability. Both tiers provide identical AI substrate access. At Tier A, token budgets are enforced server-side at the proxy with no bypass; at Tier B, budgets operate **honor system** with chapter admin oversight.

**Honor system token budgets** mean:
- Players self-report or chapter admin tracks token usage
- Budget overruns are visible (chapter admin can see player consumption through admin portal)
- Repeated violations result in chapter-level consequences (warnings, event eligibility suspension)
- But no firewall prevents continued AI calls beyond budget — the proxy still serves the calls

This is **substantively weaker integrity** than Tier A's enforced budgets. The Most Efficient award has reduced credentialing weight at Tier B because the underlying measurement is honor-system rather than structural (see §8).

**Substrate equality at Tier B** is a partial claim. Every player accesses the same model, same available parameters, same proxy. But budget honor-system means equality isn't fully enforced. Honest framing: "competition is comparable but substrate enforcement is policy-based, not structural."

## 4. Round Timing — Tier B Standard Profile

Tier B uses the **same 135-min round timing as Tier A** (see TIER_A_OPERATIONS.md §4 for phase details). The format clock is unchanged because the round phase structure is tier-agnostic:

```
T+0:00   → T+5:00    (5 min)  — Opening ceremony
T+5:00   → T+29:00  (24 min)  — Build phase
T+29:00  → T+47:00  (18 min)  — Concurrent evaluation + pitch preparation
T+47:00  → T+75:00  (28 min)  — Pitch + cross-examination (8 players × 3.5 min)
T+75:00  → T+93:00  (18 min)  — Deliberation + audience voting (if audience present)
T+93:00  → T+107:00 (14 min)  — Award reveal + closing
T+107:00 → T+135:00 (28 min)  — Zamboni Period (workstation reset if applicable)
─────────────────────────────────────────────────
135 minutes per round
```

### Differences from Tier A Phase Operations

**Opening ceremony**: lighter production rhythm without broadcast requirements. Still serves orientation purpose, but no broadcast intro needed.

**Build phase**: identical mechanics. Players construct under AI substrate access (honor-system budgeted), 24-min Sprint timer.

**Concurrent evaluation + pitch preparation**: identical concurrent structure. Judges evaluate in their portals while players write PITCH.md and prepare live pitches. PITCH.md authoring is optional at Tier B (the artifact exists, but live performance is the primary credentialing dimension as at Tier A).

**Pitch + cross-examination**: identical 28-min structure for 8 players. Live performance with human judges is the primary credentialing dimension. Tier B preserves this dimension that the Tier C MVR's LLM judging cannot replicate.

**Deliberation + audience voting**: 18-min judge deliberation. Audience voting for People's Hacklet contingent on audience presence (see §6). When audience is absent, People's Hacklet drops from the round's awards.

**Award reveal + closing**: 14-min ceremony without broadcast production. Still ceremonial, still has audience reaction when audience is present, but lighter production overhead.

**Zamboni Period**: applies when chapter uses controlled workstations. Some Tier B chapters with BYOD-policy substrate skip the workstation reset (players just close their laptops; no `userdel -r` needed because there were no ephemeral accounts).

### Round Sizing

**8-12 players per round** at Tier B. The 8-player default holds (matches Tier A operational template), but Tier B's flexibility on broadcast and audience requirements allows chapters to scale to 12 if local capacity supports it. 12 is the structural maximum across all tiers.

## 5. Submission Mechanism

Tier B submission depends on chapter workstation policy:

**Chapter-hosted workstations (recommended for stronger credentialing)**: SCP-based submission identical to Tier A. League daemon on workstations captures submissions at T+29:00 to league infrastructure. Player accounts may be ephemeral or persistent per chapter operational preference.

**BYOD policy**: portal upload with grace period identical to Tier C (see TIER_C_OPERATIONS.md §6). T+29 → T+32 grace window for upload completion. Failure to submit by T+32 results in disqualification.

Chapters running Tier B at BYOD substrate produce credentials closer to Tier C credentialing weight; chapters running Tier B with controlled workstations produce credentials closer to Tier A credentialing weight. The underlying tier is the same; the infrastructure determines where on the integrity spectrum the chapter operates.

## 6. Audience and Broadcast

**No broadcast at Tier B**. Broadcast production is Tier A only (see TIER_A_OPERATIONS.md §6). Tier B chapters typically don't have broadcast infrastructure capacity; the operational burden of broadcast production doesn't fit Tier B's operational scope.

**Audience optional at Tier B**. Chapters may invite in-person audience when local capacity supports it. People's Hacklet award is **contingent on audience presence** — available at events with audience, skipped at events without.

The format runs primarily for **competitive purposes** at Tier B without strong audience-design philosophy applying. Lower production overhead than Tier A; lighter operational burden than full broadcast events.

Asynchronous content (written results, post-event recaps, social media coverage) remains viable for Tier B events without requiring live broadcast.

## 7. Fuzz Catalog Evaluation

The fuzz catalog operates at **full strength at Tier B** (catalog is tier-agnostic per LEAGUE_OPERATIONS.md §4). Identical to Tier A: both public and hidden pools execute against every submission. Attack surface enumeration phase. Server-side deployment in ephemeral containers. Catalog evolution feedback applies identically across tiers.

The submission infrastructure may differ (SCP from chapter workstations vs portal upload from BYOD per §5), but downstream catalog evaluation is identical. Substrate equality holds at the **catalog evaluation layer** across all tiers — every submission faces the same deterministic adversary.

## 8. Scoring and Categorical Awards

Per format_spec.md §4, Tier B operates the scoring framework with **modified Most Efficient availability**:

**Available per-round awards**:
- **Most Resilient**: highest Fuzz Score
- **Best Communicator**: highest Communication Score (live pitch + cross-ex with human judges)
- **People's Hacklet**: highest audience vote *contingent on audience presence*
- **Best Overall**: composite rank with progressive tiebreakers
- **Most Efficient**: available with honor-system budget reporting caveat — measurement reliability is reduced from Tier A because budgets aren't enforced; the award still operates but credentialing weight is correspondingly reduced

**Tournament-level categoricals**: Tier B chapters typically don't run multi-day tournaments (that's Tier A territory). Tournament categoricals (Best UX/UI, Most Novel, Iron Player, Comeback Player) are not available at standard Tier B events.

## 9. Live Judging Protocol

Tier B uses **human judge corps** identical to Tier A judging protocol (see TIER_A_OPERATIONS.md §9). Same judge panel composition (tester, UX designer, general engineering judges), same cross-examination structure, same calibration discipline.

**Judge corps may be smaller** at Tier B chapters with limited senior judge availability (3 judges minimum vs Tier A's 4 standard panel). Cross-examination structure adjusts: 3 judges produce 3 questions, 30 seconds per question (90 sec cross-ex window instead of 120 sec). The reduced cross-ex window slightly compresses the pitch phase but preserves the live performance dimension.

Tier B does not use LLM judging. The live performance dimension (pitch + cross-ex with human judges) is preserved because Tier B operates at scales where human judging fits the format clock (8-12 player rounds).

LLM judging at scale is Tier C MVR territory (see TIER_C_OPERATIONS.md §8). Tier B operates at smaller scales where human judging is operationally viable.

## 10. Credentialing Claims

Tier B credentialing sits between Tier C-bounded and Tier A-credentialing-grade:

**Substantive credentialing claims at Tier B**:
- Demonstrated AI-augmented engineering capability against full deterministic fuzz catalog
- Demonstrated live communication capability under pressure (pitch + cross-ex with human judges)
- Demonstrated competitive engagement at structurally-supported substrate
- Chapter-local ranking contribution with partial regional contribution

**Claims explicitly weaker than Tier A**:
- Substrate equality is policy-enforced, not infrastructurally enforced
- Most Efficient credentialing carries reduced weight (honor-system budgets)
- No structural anti-cheating enforcement
- Limited audit capability beyond proxy-level logging
- Does not contribute to global league rankings at credentialing-grade weight
- Does not feed qualifiers to championship-tier events at full credentialing weight

**Credential interpretation for employers**:
- *Hiring for engineering capability signal*: Tier B credentials demonstrate real capability with policy-grade integrity
- *Hiring for elite signal*: Tier A credentials are the appropriate level; Tier B carries reduced signal
- *Hiring with risk tolerance for integrity assumptions*: Tier B credentials are honest signal at policy-enforced grade

The honest framing: Tier B credentials carry **real but bounded** market signal, sitting between the Tier C local-only signal and the Tier A credentialing-grade signal.

## 11. Verification

Light superadmin review (name and basic legitimacy check) per LEAGUE_OPERATIONS.md §4 verification process. No formal Tier B application process; chapters self-elect Tier B operations and superadmin verifies basic legitimacy.

Chapters operating Tier B may later apply for Tier A verification as infrastructure matures and operational experience accumulates. Tier B serves as **graduation tier** toward Tier A for chapters with credentialing ambitions; Tier B also serves as **stable tier** for chapters whose communities don't require Tier A credentialing infrastructure.

## 12. Operational Position

Tier B in the league strategic sequencing (see TIER_C_OPERATIONS.md §14):

**Year 0-1**: Tier B operations not yet active. Initial focus is Tier C MVR validation.

**Year 1-2**: Tier B emerges at chapters with substrate-hosting infrastructure capacity. Chapters that want stronger credentialing than Tier C-bounded but don't yet have Tier A infrastructure operate Tier B as intermediate tier.

**Year 2-3**: Tier B grows as chapter ecosystem matures. Some chapters operate stable Tier B; others use Tier B as transition toward Tier A verification.

**Year 3+**: First Tier A chapters emerge. Tier B continues as middle-ground operational tier serving chapters whose operational scope fits between Tier C accessibility and Tier A credentialing-grade investment.

Tier B's relative timing depends on chapter ecosystem maturation. Some chapters may skip Tier B entirely (going from Tier C directly to Tier A verification when ready); others may operate Tier B as their long-term sustainable tier.
