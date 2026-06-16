# HackLet League — Operations Model

*How the league operates as an institution. Distinct from format_spec.md (what the competition is) and claude.md (how the platform is built). This document covers federation, governance, chapters, roles, and the verification system.*

---

## 1. The League as a Federated Platform

HackLet League is structured as a federated platform that aggregates competitive events run by chapters under shared league standards. The league itself maintains methodology, infrastructure, fuzz catalog, and rankings. Chapters operate their own events using league-supplied substrate and standards. Growth happens through chapter creation and verification, not through league-direct event expansion.

This model parallels how FIDE coordinates national chess federations and how PVSA verifies organizations to issue volunteer service hours. The league sets standards and verifies compliance; chapters operate within those standards.

FIDE is the cleaner model in a second way: it runs *multiple formats* under one institution — classical, rapid, blitz, bullet — and outlives any single one. HackLet is built the same way. It is a league that runs competitive formats, not a single format that a paradigm shift could obsolete. HackLet Classical (format_spec.md) is the first and currently only operational format; an Agentic format is anticipated as agentic coding matures. The institution, its fuzz catalog, its rankings, and its chapters are the durable assets; individual formats come and go beneath them.

The structural precedent for the whole enterprise is the **Financial Modeling World Cup** (FMWC). Founded in 2020 by Andrew Grigolyunovich after the discontinuation of ModelOff, FMWC took spreadsheet modeling — a niche, measurable skill — to ESPN-broadcast competitive sport via collegiate feeder tiers and persistent rankings. HackLet applies the same playbook to AI-assisted defensive coding, a domain with a larger participant pool and more cultural relevance. The precedent matters because it answers the first question every chapter operator, sponsor, and player asks — *is this real?* — with a pattern that has already worked: a single measurable skill made into a credentialed competitive institution. HackLet borrows the template, not a claim of equivalent reach.

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

Chapters are tiered based on their operational rigor. Tiers determine what credentialing weight their events carry.

### Tier A (Verified)

Chapters that have demonstrated infrastructure meeting league standards for credentialing-grade events. Tier A requirements include:

- RMM-controlled workstations with verified configuration
- Network firewall with allowlist to league infrastructure only
- Master image deployment for workstation consistency
- Judge corps of at least 3 members, including at least one tester judge and one UX designer judge
- Documented venue with appropriate setup
- Chapter admin team trained on league operations

Tier A chapters contribute to global league rankings. Their events count toward credentialing claims. Their winners qualify for regional and national events. Tier A status requires application, documentation review, and superadmin approval. Annual re-verification ensures continued compliance.

### Tier B (Standard)

Chapters running events with chapter-policy-enforced anti-cheating rather than infrastructure-verified anti-cheating. Tier B chapters:

- Operate events using available infrastructure (may include BYOD setups)
- Enforce anti-cheating through honor system and chapter admin oversight
- Contribute to chapter-local rankings only
- Do not contribute to global league rankings
- Do not feed qualifiers to higher-tier events

Tier B is appropriate for chapters establishing themselves, smaller communities, or events where infrastructure-grade rigor isn't feasible. It allows real hacklet operation without the verification burden.

### Tier C (Practice)

Chapters running events for learning and community building. Tier C chapters:

- Operate without anti-cheating enforcement requirements
- Run events freely for member practice
- Do not contribute to any rankings
- Use the platform to learn the format and develop community

Tier C is for chapter development, new format introduction, and pure educational use.

### Verification Process

Tier B and C chapters are created with light superadmin review (name and basic legitimacy check). Tier A verification involves:

1. Chapter owner submits verification application with required documentation
2. Documents reviewed: RMM configuration, network rules, judge corps, venue setup, prior event evidence
3. Superadmin may request additional information or schedule a verification call
4. If approved, chapter granted tier A status with badge
5. Annual re-verification with possible spot checks during the year

Verification may be revoked if standards slip. Chapters can apply for verification at any time after meeting initial requirements.

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

Scoped to chapters where invited. Subroles include tester, UX designer, and general engineering judge as described in the format spec. Constraints:

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

---

*This document defines how the league operates as an institution. The format itself is defined in format_spec.md. The platform implementation is defined in claude.md, DATA_MODEL.md, and ARCHITECTURE.md.*
