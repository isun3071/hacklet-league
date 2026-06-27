# HackLet League — Data Model

*The database schema for hackletleague.com. Entities, fields, relationships, and constraints. Read this before writing models, migrations, or queries.*

---

## Overview

The data model centers on a federated platform with chapters as first-class entities. Users have global accounts but scoped memberships in chapters. Events belong to chapters and contain rounds. Rounds contain submissions and scores. Rankings aggregate across various scopes.

All foreign keys cascade carefully — chapter deletion does not cascade to user accounts. Score history is preserved even when underlying entities change. Audit trails are append-only and never deleted.

## Entity Overview

- **User** — Global account on the platform
- **Chapter** — Local operational unit of the league
- **ChapterStaff** — Chapter org team + judge corps (organizers and judges; not players)
- **VerificationApplication** — Chapter tier upgrade requests
- **Event** — Competitive gathering operated by a chapter
- **Round** — Atomic competitive unit within an event
- **Submission** — Player's work product in a round
- **FuzzTest** — Catalog entry for an automated test
- **FuzzResult** — Authoritative outcome of one fuzz test against one submission (at code freeze)
- **PlayerFuzzInvocation** — Player-triggered fuzz invocation during build (broadcast visibility)
- **EventParticipant** — Everyone at an event (players, judges, audience) via invite / application / RSVP / corps
- **Score** — Judge-issued scores for submissions
- **Ranking** — Aggregated performance per user per scope per period
- **AuditLog** — Append-only record of significant operations
- **AudienceVote** — People's Hacklet votes from spectators
- **WorkstationSession** — Per-round, per-workstation ephemeral-account lifecycle (audit; Stage 7+)

## Core Entities

### User

The global account for all platform users.

```
id                  : UUID primary key
email               : varchar, unique, indexed
password_hash       : varchar (django handles)
display_name        : varchar
created_at          : timestamp
last_login_at       : timestamp, nullable
is_active           : boolean (default true)
is_superadmin       : boolean (default false)
profile_data        : jsonb (flexible profile fields)
verified_email      : boolean
verification_token  : varchar, nullable
```

The `is_superadmin` flag is the platform-level role for the league operator team. Regular roles are stored per chapter via ChapterStaff.

### Chapter

The local operational unit. First-class entity even at single-chapter MVP.

```
id                  : UUID primary key
slug                : varchar, unique, indexed (URL-friendly identifier)
name                : varchar
description         : text
location_text       : varchar (human-readable location, e.g., "Boston University, MA")
created_by_user_id  : FK User (the chapter owner)
created_at          : timestamp
tier                : enum (A, B, C)
verification_status : enum (unverified, pending, verified, suspended)
mode                : enum (signup, active, archive)
institutional_affiliation : varchar, nullable
contact_email       : varchar
website_url         : varchar, nullable
verified_at         : timestamp, nullable
verified_by_user_id : FK User, nullable (which superadmin verified)
suspended_reason    : text, nullable
```

Chapters at tier C are unverified by default. Tier B chapters require basic approval. Tier A requires full verification documented in VerificationApplication.

### ChapterStaff

A chapter's organizing team and judge corps — the people who plan, run, and judge its events, modeled on hackathon organizers under an MLH-style umbrella. **A chapter is a host/organizer, not a membership society; players are NOT staff** — players relate to *events* via `EventParticipant`, never to chapters. (Replaces the earlier `ChapterMembership` entity, which conflated organizers, judges, and players.)

```
id                  : UUID primary key
user_id             : FK User
chapter_id          : FK Chapter
roles               : array of enum (owner, organizer, judge)
status              : enum (pending, active, suspended)
joined_at           : timestamp
approved_by_user_id : FK User, nullable
notes               : text, nullable

unique constraint: (user_id, chapter_id)
```

A person can hold several roles (e.g. organizer + judge). `judge` here is the chapter's **standing judge corps** (judges who travel/recur); a one-off judge for a single event instead applies via `EventParticipant` (role=judge) and is never ChapterStaff. "Chapter admin" (BUILD_ROADMAP's term) = staff with `owner` or `organizer` role. Owner is unique per chapter (enforced by application logic).

### VerificationApplication

Records of chapter applications for tier upgrades.

```
id                       : UUID primary key
chapter_id               : FK Chapter
submitted_by_user_id     : FK User
tier_requested           : enum (A, B, C)
submitted_at             : timestamp
documents                : jsonb (links to uploaded documents)
reviewer_user_id         : FK User, nullable
review_status            : enum (submitted, under_review, approved, declined, withdrawn)
review_notes             : text, nullable
reviewed_at              : timestamp, nullable
```

Applications track the full lifecycle from submission through decision. Approved applications trigger chapter tier change with audit log entry.

## Event Entities

### Event

A bounded competitive gathering operated by a chapter.

```
id                      : UUID primary key
chapter_id              : FK Chapter
slug                    : varchar (chapter-scoped unique)
name                    : varchar
description             : text
event_tier              : enum (chapter, regional, championship)
format                  : enum (vibe, unslop) — what the player does; foundational format is 'vibe'; 'unslop' added Stage 11
timer                   : enum (xp, sprint, scrum, agile, waterfall) — build-phase duration; foundational timer is 'sprint' (24 min)
access_mode             : enum (invite_only, application) — invite-only vs open application form, set per event
status                  : enum (scheduled, registration_open, registration_closed, in_progress, completed, cancelled)
scheduled_start         : timestamp
scheduled_end           : timestamp
actual_start            : timestamp, nullable
actual_end              : timestamp, nullable
player_tier_restriction : enum (collegiate, under_25, open, any)
created_at              : timestamp
created_by_user_id      : FK User

unique constraint: (chapter_id, slug)
```

The `(format, timer)` pair identifies the variant: e.g., `(vibe, sprint)` is HackLet Vibe Sprint, `(unslop, agile)` is HackLet Unslop Agile. Per the 1-event-1-format rule (format_spec.md §7.1), each event commits to one variant for its lifetime. The two-axis taxonomy is intentional — the earlier "Relationship" axis (Classical vs Agentic) has been retired in favor of the unified-substrate model where the league hosts both chat-window and agent-interface clients with a shared token budget (see format_spec.md §1, §5.3). 3 formats × 5 timers = 15 sanctioned variants.

Events inherit credentialing weight from their chapter's tier (tier A chapter events count globally, tier B/C are local-only).

### Round

The atomic competitive unit within an event. Multi-round events have multiple Round records.

```
id                  : UUID primary key
event_id            : FK Event
round_number        : int (1, 2, 3... within event)
timing_profile      : enum (tier_a, tier_c_mvr, tier_c_extended) — selects the phase set + clock
status              : enum (scheduled, opening, build, evaluation, judging, awards, completed)
opening_at          : timestamp   ── universal anchors (present in every profile):
build_start_at      : timestamp      opening → build → freeze
build_end_at        : timestamp      (build_end_at is the code-freeze instant)
phase_schedule      : JSON — post-freeze phase boundaries, keyed by phase, per profile:
                        tier_a          → evaluation_end, pitch_end, deliberation_end, awards_end, zamboni_end
                        tier_c_mvr      → pitch_write_end, judging_end, awards_end
                        tier_c_extended → evaluation_end, pitch_end, deliberation_end, awards_end
player_count        : int
prompt_revealed     : text, nullable (round prompt if any)

unique constraint: (event_id, round_number)
```

The three operational profiles share the same opening → build → freeze head but diverge after freeze — the MVR runs PITCH.md-writing + LLM-judging where Tier A runs live pitch + human deliberation — so the post-freeze boundaries live in `phase_schedule` (JSON), keyed by the phases that profile actually uses, with `timing_profile` selecting the set. The `status` enum is a superset; the active subset depends on `timing_profile`. (If per-phase querying or independent phase-state transitions are later needed, promote `phase_schedule` to a normalized `RoundPhase` child table — round_id, phase_key, starts_at, ends_at, sequence.) Status transitions are server-authoritative via Django signals.

### Submission

A player's work product in a round.

```
id                      : UUID primary key
round_id                : FK Round
player_user_id          : FK User
status                  : enum (in_progress, submitted, submitted_deployed, submitted_failed, dnf)
archive                 : file (uploaded zip; stored privately, never extracted until the Stage 5 sandbox)
archive_filename        : varchar (player's original filename, for display)
deployed_url            : varchar, nullable (where fuzz runner can reach it)
readme_content          : text
token_budget_used       : int
fuzz_budget_used        : int
attack_surface_coverage : enum (narrow, moderate, broad), nullable
submitted_at            : timestamp, nullable

unique constraint: (round_id, player_user_id)
```

One submission per player per round. **Submissions are uploaded directly to the platform as a single zip archive — NOT via git** (git was removed as a needless middleman + attack surface). The archive is stored on private storage and served only through an auth-gated download endpoint; it is never extracted or run until the Stage 5 sandbox pipeline. Status lifecycle: `in_progress` (checked in) → `submitted` (archive captured at code-freeze) → `submitted_deployed` / `submitted_failed` (set by the Stage 5 deploy pipeline); `dnf` if never submitted. Surface coverage is computed from fuzz test applicability after evaluation (Stage 5).

### WorkstationSession

Per-round, per-workstation account lifecycle record — auditable evidence of substrate integrity for credentialing (which player occupied which workstation under which ephemeral account, and that it was torn down). Per-round reset is account-only (`userdel -r`); full image restoration is exceptional and recorded here. Not implemented until workstation hardening (Stage 7); modeled now so the audit trail is designed in.

```
id                  : UUID primary key
round_id            : FK Round
player_user_id      : FK User
workstation_id      : varchar (chapter-local workstation identifier)
account_name        : varchar (ephemeral Unix account created for this session)
account_created_at  : timestamp
account_deleted_at  : timestamp, nullable
image_restored      : boolean (true if a full image restore ran for this session, vs account-only reset)
tamper_flag         : boolean (set if tamper detection fired)
notes               : text, nullable
```

A set `tamper_flag` forces image restoration before the workstation is reused. Local fuzz runner state lives in the player's home directory and is wiped with the account at round end.

## Fuzz Catalog Entities

### FuzzTest

The catalog of automated tests. Grows to hundreds of entries over seasons.

```
id                  : UUID primary key
bundle              : enum (security, qa)
category            : varchar (e.g., "SQL Injection", "File Upload", "Idempotency", "Error Handling")
subcategory         : varchar, nullable (variant grouping within category)
name                : varchar (human-readable test name)
description         : text (what the test does)
pool                : enum (public, hidden)
difficulty_tier     : enum (1, 2, 3, 4, 5)
intent_dependence   : enum (universal, intent_sensitive)
applicability_notes : text (guidance for judges when intent_sensitive)
test_definition     : jsonb (the actual test specification)
points_defended     : int (positive value)
points_gracefully_handled : int, nullable (only for non-adversarial)
points_broken       : int (negative value)
attack_type         : enum (adversarial, non_adversarial)
variant_group_id    : UUID, nullable (groups syntactic variants of same logical attack)
created_at          : timestamp
deprecated_at       : timestamp, nullable
```

Tests are split into two bundles (security and QA) reflecting their different correctness models. Security tests are universally correct. QA tests are tagged for intent-dependence. Variant groups bind tests that probe the same logical attack with different syntactic presentations. The applicability_notes field guides tester judges in deciding whether an intent-sensitive test applies to a given submission. Deprecated tests remain in the schema but don't run in new events.

### FuzzResult

The outcome of one fuzz test against one submission. Records only **authoritative results** from central fuzz infrastructure at code freeze. Local fuzz runner results during build are informational only and not stored in this table.

```
id                  : UUID primary key
submission_id       : FK Submission
fuzz_test_id        : FK FuzzTest
outcome             : enum (defended, gracefully_handled, not_applicable, broken)
points_contributed  : int (can be positive, zero, or negative)
override_by_judge   : FK EventParticipant, nullable (if the tester judge overrode)
override_reason     : text, nullable
ran_at              : timestamp

unique constraint: (submission_id, fuzz_test_id)
```

Results capture both the automated outcome and any tester judge overrides. Points contributed reflects the final value after override consideration. All results are from central infrastructure execution; local-runner intelligence-gathering during build is not persisted.

### PlayerFuzzInvocation

Records each player-triggered fuzz invocation during build phase. Used for broadcast leaderboard, audience-visible score accumulation, and budget tracking. Does not contribute to authoritative scoring (that's FuzzResult).

```
id                       : UUID primary key
submission_id            : FK Submission
category                 : varchar (the fuzz category triggered)
budget_cost              : int (fuzz budget consumed)
score_delta              : int (signed score change from this invocation)
running_score_after      : int (player's accumulated slop score after this invocation)
running_budget_remaining : int (player's fuzz budget after this invocation)
invoked_at               : timestamp
results_summary          : jsonb (counts of defended/broken/etc per this invocation)
```

This table is the data source for broadcast overlays and live leaderboards during build phase. Each invocation creates a row visible to commentators and audience. The running_score_after field enables the leaderboard sort to be efficient without recomputing aggregates per request.

## Scoring Entities

### EventParticipant

Everyone associated with an event as a person — **players, judges, and non-competing audience** — regardless of how they joined (invited, applied/RSVP'd, or drawn from the chapter judge corps). This single entity also replaces the old `JudgeAssignment` (a judge is just a participant with `role=judge`). It is the join point for access modes and all person-roles at an event.

```
id                   : UUID primary key
event_id             : FK Event
user_id              : FK User, nullable (null until an emailed invite is claimed)
email                : varchar, nullable (carries an invite to a not-yet-registered person)
role                 : enum (player, judge, audience)
judge_specialization : enum (tester, ux_designer, general), nullable (judge role only)
source               : enum (invited, applied, corps)  # corps = drawn from the chapter's ChapterStaff judge corps
status               : enum (pending, registered, declined, rejected, withdrawn)
chapter_staff_id     : FK ChapterStaff, nullable (set for corps judges → their standing corps record)
token                : varchar, nullable (single-use claim token for emailed invites)
invited_by_user_id   : FK User, nullable
decided_by_user_id   : FK User, nullable (organizer who approved/rejected an application)
created_at           : timestamp
responded_at         : timestamp, nullable

unique constraint: (event_id, user_id)   -- where user_id is not null
unique constraint: (event_id, email)     -- where email is not null
```

The `status` lifecycle covers both access modes and both join paths:
- **invite_only**: an organizer creates the row (`source=invited`, `status=pending`, by email or known user) → invitee claims/accepts → `registered`.
- **application / RSVP**: a logged-in user self-creates the row (`source=applied`, `status=pending`) via the "I want to compete" / "I want to judge" / "I want to attend" buttons → organizer approves (`registered`) or rejects (`rejected`); audience RSVPs may auto-register where a chapter allows open attendance.
- **corps judge**: an organizer pulls a standing judge from `ChapterStaff` (`source=corps`, `chapter_staff_id` set), typically straight to `registered`.

`role`+`judge_specialization` determine which scoring interfaces a judge sees and how their expertise weights categorical awards.

**Audience** participants (`role=audience`) are non-competing spectators — RSVP'd attendees tracked for headcount and in-person People's Hacklet eligibility. They carry no `judge_specialization`, no `chapter_staff`, and never the `corps` source; they don't count toward the player cap, and may optionally link to an `AudienceVote`. (Anonymous walk-in audience and anonymous voting still work through `AudienceVote` with no EventParticipant row.)

### Score

Judge-issued scores for submissions.

```
id                  : UUID primary key
submission_id       : FK Submission
judge_participant_id: FK EventParticipant (a participant with role=judge)
score_type          : enum (pitch_quality, cross_examination, creative_coherence, ux_quality, technical_execution, documentation)
value               : decimal (typically 0-100 or 0-25 depending on type)
comments            : text, nullable
submitted_at        : timestamp

unique constraint: (submission_id, judge_participant_id, score_type)
```

Multiple score types per judge per submission. Scoring math aggregates these into composite scores per submission.

### Ranking

Aggregated performance per user per scope per period.

```
id                  : UUID primary key
user_id             : FK User
scope               : enum (global, chapter, regional)
scope_reference_id  : UUID, nullable (chapter_id if scope=chapter, region_id if scope=regional)
period              : enum (current_season, persistent, all_time)
season_year         : int, nullable (for current_season)
rank                : int
rank_points         : decimal
events_competed     : int
last_event_at       : timestamp
updated_at          : timestamp

unique constraint: (user_id, scope, scope_reference_id, period, season_year)
```

Rankings are computed periodically (probably after each event completes). Global rankings only include tier A chapter events for credentialing integrity.

**Stage 3 computation** (`rankings/services.py`). Each finalized (completed) round awards every player *placement points* = `field_size − overall_rank + 1` (1st of N → N, ties share a rank and its points), scaled by an *event-tier weight* (chapter ×1, regional ×2, championship ×3 — format_spec §7 "weighted by event tier"). A scope's `rank_points` is the sum across all its completed rounds; `rank` is the standard-competition (1224) ordering by points; `events_competed` counts distinct events; `last_event_at` is the latest round's freeze/finish. Recompute runs on round **complete** *and* **cancel** (so voiding a finished round drops it), and fully rebuilds the affected scope — idempotent and self-healing. Stage 3 populates two slots: **chapter** (period `all_time`, one board per chapter, all events) and **global** (period `all_time`, Tier A chapters only). Regional scope and the `current_season` period are modeled but deferred until a season entity exists.

## Audit Entities

### AuditLog

Append-only record of significant operations.

```
id                  : UUID primary key
timestamp           : timestamp, indexed
actor_user_id       : FK User, nullable (system events have no actor)
action              : varchar (e.g., "chapter.verified", "score.modified", "user.suspended")
resource_type       : varchar (e.g., "Chapter", "Submission", "User")
resource_id         : UUID
details             : jsonb (action-specific data)
ip_address          : varchar, nullable
user_agent          : text, nullable
```

Audit logs are *never modified or deleted*. Database triggers or application discipline enforces append-only. Used for compliance, dispute resolution, and credentialing integrity.

### AudienceVote

People's Hacklet votes from spectators.

```
id                  : UUID primary key
round_id            : FK Round
submission_id       : FK Submission
voter_session       : varchar (anonymous session ID, not user_id necessarily)
voter_user_id       : FK User, nullable (if authenticated)
voted_at            : timestamp

unique constraint: (round_id, voter_session) or (round_id, voter_user_id)
```

Anonymous voting is allowed (low integrity requirements for audience awards). Rate limiting and basic anti-bot prevents trivial abuse.

## Key Relationships

```
User ──┬─< ChapterStaff >── Chapter
       ├─< EventParticipant >── Event
       ├─< Submission           
       └─< Ranking              

Chapter ──┬─< Event ──< Round ──< Submission ──< FuzzResult >── FuzzTest
          ├─< VerificationApplication
          └─< ChapterStaff

EventParticipant links a User (player or judge) to an Event; corps judges also link to ChapterStaff
Score links EventParticipant (role=judge) to Submission with score type

AuditLog references any entity via resource_type + resource_id
AudienceVote references Round and Submission
```

## Indexes

Beyond standard primary key and foreign key indexes:

- `User.email` — unique index (login lookups)
- `Chapter.slug` — unique index (URL routing)
- `Event.scheduled_start` — for upcoming event queries
- `Submission.round_id` — for round result aggregation
- `FuzzResult.submission_id` — for submission scoring
- `Ranking(scope, scope_reference_id, period, season_year)` — for leaderboard queries
- `AuditLog.timestamp` — for time-range audit queries
- `AuditLog(resource_type, resource_id)` — for entity-specific audit queries

## Data Constraints and Notes

### Who the platform models

`ChapterStaff` and `EventParticipant` model only people **directly and HackLet-specifically** involved: organizers, judges, players, audience — and, later, HackLet-trained **commentators / broadcast crew** (deferred to Tier A / Stage 6; the role enums are intentionally extensible). Generic event services that aren't HackLet-specific — catering, security, janitorial, room setup/teardown — are **not modeled**; a chapter arranges those as one-off services outside the platform. The test: if a role does the same job for non-HackLet events, it isn't a HackLet entity. Commentators/crew are the exception because Tier A needs commentary grounded in the format's technical vocabulary (race conditions, SQLi, insecure upload, DoS, TTFB).

### Cascade Behavior

- User deletion: anonymize rather than delete (preserve ranking history)
- Chapter deletion: only allowed for chapter owner; cascades to events, submissions, scores within that chapter; preserves user accounts
- Event deletion: cascades to rounds, submissions, scores, and event participants
- Submission deletion: not allowed after round completes (preserves scoring history)

### Uniqueness Enforcement

Chapter owner uniqueness (one owner per chapter) is enforced via application logic since ChapterStaff.roles is an array. A pre-save check ensures only one ChapterStaff row per chapter has 'owner' in roles.

### JSON Field Schemas

The `jsonb` fields (`profile_data`, `documents`, `test_definition`, `details`) have informal schemas documented in their respective application code. Validation happens via Pydantic models or serializers, not database constraints.

### Migration Strategy

Migrations are forward-only. Schema changes accumulate as Django migrations. Periodic squashing of old migrations is acceptable when reviewed. Never modify or delete applied migrations.

---

*This document defines the schema. For how entities relate in request flows and service interactions, see ARCHITECTURE.md. For project conventions about working with this schema, see claude.md.*
