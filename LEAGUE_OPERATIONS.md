# HackLet League — Operations Model

*How the league operates as an institution. Distinct from format_spec.md (what the competition is) and claude.md (how the platform is built). This document covers federation, governance, chapters, roles, and the verification system.*

---

## 1. The League as a Federated Platform

HackLet League is structured as a federated platform that aggregates competitive events run by chapters under shared league standards. The league itself maintains methodology, infrastructure, fuzz catalog, and rankings. Chapters operate their own events using league-supplied substrate and standards. Growth happens through chapter creation and verification, not through league-direct event expansion.

This model parallels how FIDE coordinates national chess federations and how PVSA verifies organizations to issue volunteer service hours. The league sets standards and verifies compliance; chapters operate within those standards.

FIDE is the cleaner model in a second way: it runs *multiple formats* under one institution — classical, rapid, blitz, bullet — and outlives any single one. HackLet is built the same way. It is a league that runs competitive formats, not a single format that a paradigm shift could obsolete. The current format family is **HackLet Vibe** with the foundational variant **Vibe Sprint** (the BU pilot). **HackLet Unslop** is the canonical second format, introduced once Vibe is operationally stable. Additional timer variants, and eventually new format axes beyond Vibe/Unslop, follow as the league matures. The institution, its fuzz catalog, its rankings, and its chapters are the durable assets; individual formats come and go beneath them.

The structural precedent for the whole enterprise is the **Financial Modeling World Cup** (FMWC). Founded in 2020 by Andrew Grigolyunovich (Latvia) after ModelOff was discontinued, FMWC took competitive financial modeling — a niche, measurable skill — to mainstream attention (its All-Star Battle aired on ESPN2 in 2022) through recurring tiered competition and persistent rankings. HackLet applies the same playbook to AI-assisted defensive coding, a domain with a larger participant pool and more cultural relevance. The precedent matters because it answers the first question every chapter operator, sponsor, and player asks — *is this real?* — with a pattern that has already worked: a single measurable skill made into a credentialed competitive institution. HackLet borrows the template, not a claim of equivalent reach.

The league is built as a platform from day one, even though early operations may involve only one or two chapters. The federated architecture is foundation for expansion — chapters as first-class entities exist in the data model and platform UI from the start, ready to accommodate growth without architectural refactoring.

## 2. What the League Provides vs. What Chapters Provide

### League Responsibilities

The league (operated by superadmins) maintains:

- The methodology and format specification
- The fuzz catalog (public and hidden pools)
- The scoring math and ranking infrastructure
- The platform itself (hackletleague.com)
- The sanctioned AI substrate (centralized OpenRouter integration)
- Verification standards for chapters
- Cross-chapter coordination (rankings, qualification flows)
- League-wide events (regional and championship aggregations)

Among these, the **fuzz catalog is the league's strategic asset**. A years-deep, continuously-calibrated adversarial test suite — with a hidden pool that grows each season — is the one thing competitors cannot quickly copy. Formats, time limits, and spectator framing are all replicable; a trustworthy catalog is not. Its depth and calibration are what make a HackLet result a credential rather than a curiosity, which is why the catalog is maintained as a durable, continuously-deepened league asset rather than a build-once artifact.

### Chapter Responsibilities

Each chapter (operated by chapter admins) maintains:

- Their physical venue and workstations
- Their local network and firewall configuration
- Their RMM platform managing chapter workstations
- Their judge corps recruitment and management
- Their player community and event scheduling
- Their compliance with league standards for their verified tier

### The Boundary

The league does not manage chapter infrastructure directly. The platform does not configure chapter workstations, control chapter networks, or operate chapter RMM systems. Chapters are sovereign on their infrastructure within league standards. The league verifies compliance through documentation review and periodic audit rather than through direct control.

This boundary clarifies what the platform actually is: event coordination and credentialing infrastructure, not a workstation management system.

## 3. Chapter Lifecycle and Modes

Chapters exist in one of three operational modes:

### Signup Mode

Default for new chapters and the state between active event seasons. In signup mode:

- The chapter page is publicly visible
- People can browse chapter information
- People can apply for chapter membership
- Chapter admins review and approve membership applications
- No events are scheduled or running
- No live competition data displays

Chapters in signup mode are recruiting and onboarding. This is the appropriate state for new chapters building their member base before running events.

### Active Mode

The operational state during event seasons. In active mode:

- All signup mode capabilities remain
- The chapter has scheduled events visible on the calendar
- Members can register for upcoming events
- Judges can prepare for their assignments
- Live event data streams when events are running
- The chapter participates in league-wide rankings (if verified for tier A)

### Archive Mode

For chapters that have ceased operations, completed a season, or gone dormant. In archive mode:

- The chapter page displays historical content
- Past events remain viewable in the archive
- Past leaderboards remain accessible
- No new registrations or active competition
- The chapter remains part of the league for historical record

Chapter owners control mode transitions. The platform may auto-suggest archive mode after extended inactivity but does not force the change.

## 4. Chapter Tiers and Verification

Chapters are tiered based on their operational rigor. The tier system is a **mechanic-availability gradient**, not just an integrity gradient: each tier credentials what its infrastructure can actually enforce, and operates the format mechanics its infrastructure can actually support. Higher tiers don't "improve" lower tiers; they *enable additional credentialing claims* that depend on additional infrastructure.

The tiers exist because the format's integrity properties hang together with infrastructure dependencies. Token budget enforcement requires firewall isolation plus league-hosted AI substrate (Tier A). Substrate equality as a credentialing claim requires controlled AI access (Tier A). Resource calibration as a measurable skill requires enforceable token usage measurement (Tier A). At lower tiers, these mechanics adjust honestly rather than claiming enforcement that doesn't exist.

The format's load-bearing integrity mechanism — the fuzz catalog — operates at **full strength at every tier**. The fuzz catalog evaluates submissions identically regardless of how they were produced; slop loses to fuzz regardless of who or what produced it. This is what makes lower-tier events produce real format-validation signal even without credentialing-grade enforcement.

### The Freedom-Integrity Tradeoff

The tier system represents a deliberate philosophical tradeoff between two competing values in competitive credentialing:

**Freedom**: players use AI however fits their workflow, no league-imposed substrate constraints, no enforced budgets, no infrastructure restrictions on tool choice.

**Integrity**: enforced equality across players, anti-cheating enforcement, reproducible measurement, market-meaningful credentials that survive employer verification.

These values are **substantively in tension**. Pure freedom undermines credentialing because premium-AI advantages and substrate variance across players turn credentials into "did you pay for premium AI" signals rather than "are you a skilled engineer" signals. Pure integrity constrains authentic workflow because controlled infrastructure forces players into substrates that may not match their actual professional practice.

Each tier articulates a deliberate choice about where to sit on this spectrum:

- **Tier C** maximizes freedom: BYOD substrate, any AI tooling, no enforced budgets, no controlled infrastructure. Credentialing claims are correspondingly bounded — chapter-local rankings only, no global contribution. This is the Minimum Viable Round (MVR) configuration: smallest operational floor that genuinely delivers HackLet competitive infrastructure while honoring player workflow authenticity.

- **Tier A** maximizes integrity: league-hosted substrate, enforced equality, controlled workstation environment, structural anti-cheating, comprehensive audit. Credentialing claims are correspondingly strong — global ranking contribution, market-meaningful credentials, employer-interpretable signal.

- **Tier B** sits in the middle: league-hosted substrate (so structural integrity baseline exists) with honor-system enforcement of budgets and anti-cheating. Credentialing claims sit between Tier C and Tier A.

The tier choice isn't about prestige — it's about operational match between chapter capability and tier requirements, and about which credentialing claim authentically reflects the integrity infrastructure available. A chapter running excellent Tier C events serves its community well; a chapter that claims Tier A without infrastructure capacity damages the credential. Players choose tier based on what they value (freedom or credentialing); both are valid preferences. The format ecosystem respects both.

### Tier Overview

**Tier A (Verified Credentialing)**: the credentialing-grade tier. Tier A chapters have demonstrated infrastructure that makes faking results structurally hard: RMM-controlled workstations, network firewall with allowlist to league infrastructure only, per-player ephemeral Unix accounts, league-hosted AI substrate with enforced token budgets, broadcast streaming infrastructure, audit logging at every layer, judge corps with calibration discipline. Wins contribute to global league rankings. Tier A events run the full 135-min round profile with multi-day tournament structure for regional and championship events. Tier A operations are Year 3+ territory in the league's strategic sequencing. *See TIER_A_OPERATIONS.md for the full operational template.*

**Tier B (Standard Competitive)**: the middle tier — real competition with policy-based enforcement rather than infrastructure-based enforcement. Tier B chapters host the league AI substrate (providing structural integrity baseline) with honor-system enforcement of budgets and anti-cheating (lighter operational burden than Tier A). Useful for chapters establishing themselves, smaller communities, transitional operations toward Tier A. Wins contribute to chapter-local rankings with partial regional contribution. *See TIER_B_OPERATIONS.md for the full operational template.*

**Tier C (Training Tier / MVR)**: HackLet's training tier and Minimum Viable Round (MVR) floor. BYOD substrate, no enforced token budgets, full fuzz catalog evaluation, PITCH.md as written communication artifact. Operates three profiles: the **60-min MVR** (PITCH.md + LLM judging, any cohort 8-100+), **Tier C Extended** (live pitch + cross-examination with human judges, 8-12 players, weekend timeframe), and **multi-round MVR-days**. The truest expression of "we don't legislate AI usage" — players use whatever AI tooling fits their workflow. Credentials are chapter-local. The MVR is also the league's R&D infrastructure: every event generates operational data that informs catalog evolution, sysprompt calibration, format clock validation. *See TIER_C_OPERATIONS.md for the full operational template.*

### Token Budget's Two Functions

Token budgets serve two distinct functions, and both activate only at Tier A:

**Function 1 — League cost control**: when the league hosts the AI substrate (Tier A and Tier B), every player prompt costs the league real money. Token budgets bound that cost so a runaway player can't burn through chapter monthly budget in a single round. This is operational risk management protecting the league's financial sustainability.

**Function 2 — Credentialing the resourcefulness skill**: once enforced, token budgets test a professional skill — working effectively under resource constraints. Real engineers operate under budget caps (compute costs, API quotas). Players who produce defended apps within constrained AI usage demonstrate something employers care about, and per the 2026 tokenmaxxing crisis data this skill is increasingly market-relevant.

Function 2 *requires* Function 1 to be enforced — you can't credential a skill you can't measure. But Function 1 doesn't require Tier A; it requires *the league hosting the AI* in the first place. At Tier B, Function 1 operates with honor-system enforcement (the league hosts AI, but budgets are policy-enforced rather than firewall-enforced); Most Efficient award operates with reduced credentialing weight. At Tier C with BYOD substrate, neither function applies because the league isn't paying for AI and can't enforce the budget anyway. This is why token budgets drop entirely at Tier C rather than operating as honor system theater.

### Three-Tier Verification Architecture

Verification scope scales with credentialing weight. Each tier's audit work matches what its credentials claim.

**Tier C (legitimacy check only)**: chapters are created with light superadmin review (name uniqueness, basic legitimacy). The league does not audit how Tier C chapters run their events. Tier C credentials are chapter-local engagement signal; the league doesn't verify operational integrity because Tier C credentials don't claim it.

**Tier B (written attestation, no per-event inspection)**: chapters seeking Tier B operations submit a written attestation of their anti-cheating policies and a plausible enforcement plan. The attestation must articulate specific policies (substrate access controls, pre-built code prohibitions, player agreements, post-event audit procedures) and describe how the chapter will enforce them at event time. The league reviews the attestation before granting Tier B verification. No on-site inspection per event; the chapter operates Tier B events under its own attested policies. Tier B credentials carry honor-system integrity weight — real but bounded.

**Tier A (chapter verification + per-event on-site inspection)**: Tier A involves two verification layers.

*Chapter-level verification* (one-time, annual re-verification):
1. Chapter owner submits verification application with required documentation
2. Documents reviewed: RMM configuration, network rules, judge corps, venue setup, prior event evidence, specialized variant(s) for which verification is sought
3. Superadmin may request additional information or schedule a verification call
4. If approved, chapter granted Tier A status with badge for the specific verified variants
5. Annual re-verification with possible spot checks during the year

*Event-level inspection* (per Tier A event):
1. Tier A events require a league-appointed inspector on-site during the event
2. Event scheduling involves coordinating with the league to find a date when an inspector is available
3. If no inspector is available for a requested date, the chapter reschedules or downgrades the event to Tier B for that date
4. The inspector verifies infrastructure operates per Tier A standards: RMM deployment, firewall enforcement, ephemeral account provisioning, broadcast capture, judge corps calibration, audit logging
5. Inspector signs off on the event's compliance with Tier A standards before results are published

The two-layer structure means the league co-operates Tier A events with the host chapter. Inspector availability is a hard constraint on Tier A event volume; growth depends on the league's inspector corps capacity (see IDEAS_FOR_LATER.md).

Tier A verification is **per-variant**. A chapter verified for Vibe Sprint isn't automatically verified for Unslop Sprint or Vibe Agile. The verification application specifies which format variants the chapter is verifying for; verification expansion to additional variants requires additional applications.

Chapter variant portfolio: specialization is **common but not required**. Chapters often concentrate Tier A verification on one variant or related variant family for operational efficiency. Chapters with substantial operational capacity may apply for verification across multiple variants over time. The 1-event-1-format rule (see format_spec.md §7.1) means each event commits to one variant, but chapters host many events across varied formats over their lifetime.

Verification may be revoked or events sanctioned if standards slip — see §11 for sanction mechanisms. Chapters can apply for verification at any time after meeting initial requirements. Chapters may apply to expand verification to additional variants as their infrastructure and operational experience grow.


## 5. Role Hierarchy

The platform supports six distinct role levels, with permissions cascading appropriately:

### Superadmin

The league operator (initially the league founder, eventually a small platform team). Powers:

- Full platform control across all chapters
- Chapter approval and tier verification
- Global configuration (methodology, fuzz catalog, model selection)
- Dispute resolution at the league level
- Chapter suspension for standards violations

### Chapter Owner

One designated person per chapter, typically the creator. Powers:

- Chapter lifecycle control (signup/active/archive mode)
- Chapter deletion (unique to owner, not delegated)
- Transfer ownership to another chapter member
- All chapter admin powers
- Chapter-level dispute resolution

### Chapter Admin

Multiple allowed per chapter, appointed by chapter owner. Powers:

- Event creation and scheduling
- Member management (approve, suspend, remove)
- Judge assignment to events
- Chapter configuration within league standards
- Score review and chapter-level appeals

### Judges

Scoped to chapters where invited. Subroles are the four permanent judge roles — tester, UI/UX/HCI, general engineering, and nontech stakeholder — as described in the format spec (§4.1). Constraints:

- Cannot judge events they are competing in (system-enforced)
- Cannot judge cohort peers in qualification events (norm, possibly system-enforced)
- Allowed to play in some chapters while judging in others (cross-chapter overlap is fine)

### Players

Scoped to chapters where enrolled. Compete in events at their chapters. May hold multiple chapter memberships and may simultaneously hold judge role at different chapters subject to conflict rules.

### Public (Unauthenticated)

No login required. Access includes:

- Landing page and methodology
- Chapter directory
- Individual chapter pages
- Global and chapter leaderboards
- Event archives
- Sign-up and sign-in flows
- Audience voting interface during active events (People's Hacklet)

## 6. User Account Model

Users have one global account on hackletleague.com. From a single account, a user can:

- Apply for membership in any chapter
- Hold different roles in different chapters (player at chapter A, judge at chapter B)
- Accumulate league-wide ranking history across all chapters they participate in
- View their full history across chapters

Chapter memberships are scoped per chapter. A user is not automatically a member of a chapter just because they have a platform account. They apply to join, and chapter admins approve.

The platform supports federation from day one by treating chapters as first-class entities in the data model. Even at single-chapter MVP, the architecture supports unlimited chapter growth without refactoring.

## 7. Centralized AI Substrate

The league supplies a single OpenRouter integration that all chapters use. This is centralized rather than chapter-supplied because:

- Substrate equality is foundational to format measurement validity
- Centralized model selection enables format integrity
- Eliminates onboarding friction for chapters
- Allows league cost management and abuse prevention
- Costs are negligible at current model pricing (DeepSeek V4 Flash)

Cost controls are enforced through:

- Per-player token budgets (100,000 per round, server-enforced)
- Per-event bounded total based on player count
- Per-chapter monthly limits with anomaly detection
- Emergency shutoff for usage anomalies

The OpenRouter API key is stored encrypted server-side and never exposed to clients. All AI calls flow through the league's backend proxy.

## 8. Permissionless Chapter Creation with Gated Verification

Anyone with a platform account can create a chapter. Chapter creation includes:

1. Submit chapter creation form (name, description, intended location, contact, requested tier)
2. Automated checks (name uniqueness, no prohibited language)
3. Light superadmin review (1-2 days for tier B/C, full verification for tier A)
4. Approval triggers chapter creation in signup mode
5. Chapter owner can then begin recruiting members and scheduling events

This model enables organic growth (anyone can start a chapter) while protecting credentialing integrity (only verified chapters contribute to global rankings). Most chapters will likely start at tier C or B and apply for tier A verification once their infrastructure is in place.

The brand is protected through review at all tiers (even tier C requires basic legitimacy check) while keeping the barrier low enough that legitimate communities can establish themselves quickly.

## 9. The Platform as Foundation for Expansion

At MVP launch, the league may operate with only one or two chapters. The platform's federated architecture is foundation for expansion rather than current operational necessity. The chapter directory may have one entry at launch; the cross-chapter ranking math may operate on one chapter's data; the verification system may have one verified chapter.

This is appropriate. The architecture supports the institutional scale hacklet aspires to without requiring that scale to exist today. As chapters are added over months and years, the platform accommodates them without architectural changes. New chapter equals new data, not new code.

The institutional design from day one signals to anyone evaluating hacklet (chapter creators, judges, players, sponsors, employers) that this is a platform built for scale, not a single university's project that might someday become institutional.

## 10. Governance Evolution

Early stage: superadmin (league founder) makes all platform decisions, approves all chapters, sets all standards.

Growth stage: superadmin team (small group) shares platform operations. Chapter advisory board may form to provide input on methodology and standards.

Mature stage: formal governance structure with elected representation from verified chapters, clear separation between platform operations and league rulemaking, dispute resolution processes with appeal paths. As additional formats are introduced, rulemaking separates into per-format concerns (each format has its own spec, catalog configuration, and parameters) and league-wide concerns (chapters, verification, rankings infrastructure) shared across all formats.

The governance evolution is intentional but unhurried. Premature formalization adds bureaucracy without value. Governance matures as the league grows and as decisions affecting many chapters become more frequent.

## 11. Sanctions and Integrity Enforcement

Integrity violations are handled with sanctions calibrated to what actually failed. The league operates two distinct sanction tracks because chapter-level integrity failure and player-level integrity failure are different problems requiring different responses.

### Chapter-Level Integrity Failure: Retroactive Event Downgrade

When a chapter's infrastructure or operational standards fail to meet the tier the event was advertised as (Tier A inspector finds RMM gaps, Tier B attestation found violated in practice, pattern of operational issues across multiple events), the affected event(s) are **retroactively downgraded to Tier C-equivalent**.

What this preserves:
- Player participation records remain intact
- Player submission records remain intact
- The event itself remains in the public archive
- Players retain a Tier C-equivalent credential (chapter-local engagement signal, comparable to hackathon participation)
- Players remain eligible for future events at any tier

What this loses:
- Global ranking contribution that the original tier credentials would have carried
- Credentialing-grade signal weight (Tier A) or middle-tier signal weight (Tier B)
- Qualifier feeds to championship events that depended on the original tier's integrity
- The chapter's verification status for the tier in question (until re-earned)

Chapter recovery:
- Chapter can continue operating at Tier C while higher-tier verification is restored
- Chapter applies for re-verification after addressing the issues that triggered the sanction
- Re-verification may be granted faster than initial verification if the issues are addressed clearly

The principle: when a chapter's integrity infrastructure failed players who competed in good faith, the players' effort is preserved at chapter-local credentialing weight while the credentialing-grade claim is appropriately bounded.

### Player-Level Integrity Failure: Individual Result Voiding

When a specific player cheated (used pre-staged code, bypassed substrate restrictions, received unauthorized outside help, gamed the format), the sanction targets only that player's result.

What this preserves:
- Other players' credentials hold at full event-tier weight; their work was real, the event's integrity wasn't compromised for them
- The chapter's verification status (assuming the chapter operated correctly)
- The event itself remains in the public archive

What this loses:
- The cheating player's result for that event is voided
- The cheating player faces additional sanctions appropriate to the violation severity (suspension, review, possible permanent ineligibility for serious or repeated violations)

The principle: precise targeting of the bad actor without collateral damage to legitimate competitors. The sanction targets fraud, not participation.

### Combined Case

When both chapter integrity failure and specific player cheating occur in the same event:
- The event downgrades to Tier C-equivalent for all participants (chapter-level sanction)
- AND the cheating player's individual result is voided (player-level sanction)
- The player who cheated at a compromised event receives neither the Tier C-equivalent fallback nor the original credentialing-grade credential

### Appeals

Chapters and players subject to sanctions have a right to appeal:
1. Initial sanction notice from superadmin with documentation of the alleged violation
2. Affected party has opportunity to respond with their account and supporting evidence
3. Superadmin reviews response and may adjust, sustain, or reverse the sanction
4. For Tier A events, the inspector's findings inform but don't bind the appeal decision

Appeals must be filed within 14 days of sanction notice. Decisions are typically issued within 30 days of appeal filing.

## 12. Operational Integrity: Dogfooding the Catalog

The league runs the fuzz catalog against league infrastructure (hackletleague.com platform code, league-hosted AI substrate, fuzz runner itself) before every public release. The same probes that evaluate player submissions evaluate the league's own production code.

Why:
- The catalog has to apply to the league before it can credibly apply to players. The league's own infrastructure is the catalog's first calibration cohort.
- Dogfooding produces an ongoing audit trail demonstrating the league holds itself to the standard it credentials others against.
- Catalog runs against league infrastructure surface false positives, missed vulnerabilities, and operational gaps that improve catalog quality continuously.
- The credibility of the credentialing claim depends on the catalog being applied symmetrically. The league cannot exempt itself from the standard it imposes.

Operational policy:
- Pre-release: the catalog runs against the candidate build of any league-hosted infrastructure component
- Results are logged with timestamps, catalog version, and outcomes
- Failures block deployment until addressed
- The audit log is internally auditable and may be selectively published as institutional credibility evidence

Dogfooding is also why the catalog evolves continuously rather than being declared finished. Every catalog run against league infrastructure that surfaces a real issue improves the catalog. Player submissions are evaluated against the same catalog the league has already applied to itself.

---

*This document defines how the league operates as an institution. The format itself is defined in format_spec.md. The platform implementation is defined in claude.md, DATA_MODEL.md, and ARCHITECTURE.md.*
