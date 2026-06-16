# HackLet League — Data Model

*The database schema for hackletleague.com. Entities, fields, relationships, and constraints. Read this before writing models, migrations, or queries.*

---

## Overview

The data model centers on a federated platform with chapters as first-class entities. Users have global accounts but scoped memberships in chapters. Events belong to chapters and contain rounds. Rounds contain submissions and scores. Rankings aggregate across various scopes.

All foreign keys cascade carefully — chapter deletion does not cascade to user accounts. Score history is preserved even when underlying entities change. Audit trails are append-only and never deleted.

## Entity Overview

- **User** — Global account on the platform
- **Chapter** — Local operational unit of the league
- **ChapterMembership** — Junction: user roles within a chapter
- **VerificationApplication** — Chapter tier upgrade requests
- **Event** — Competitive gathering operated by a chapter
- **Round** — Atomic competitive unit within an event
- **Submission** — Player's work product in a round
- **FuzzTest** — Catalog entry for an automated test
- **FuzzResult** — Authoritative outcome of one fuzz test against one submission (at code freeze)
- **PlayerFuzzInvocation** — Player-triggered fuzz invocation during build (broadcast visibility)
- **JudgeAssignment** — Junction: judges assigned to events with role specialization
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

The `is_superadmin` flag is the platform-level role for the league operator team. Regular roles are stored per chapter via ChapterMembership.

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

### ChapterMembership

The junction table tracking which users have which roles in which chapters.

```
id                  : UUID primary key
user_id             : FK User
chapter_id          : FK Chapter
roles               : array of enum (owner, admin, judge, player)
status              : enum (pending, active, suspended)
joined_at           : timestamp
approved_by_user_id : FK User, nullable
notes               : text, nullable

unique constraint: (user_id, chapter_id)
```

Multiple roles per membership — a user can be both a judge and a player at the same chapter (subject to event-level conflict checks). Owner role is unique per chapter (enforced by application logic).

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
format_type             : enum (classical) — only 'classical' valid today; structural slot for future formats (e.g. agentic)
status                  : enum (scheduled, registration_open, in_progress, completed, cancelled)
scheduled_start         : timestamp
scheduled_end           : timestamp
actual_start            : timestamp, nullable
actual_end              : timestamp, nullable
player_tier_restriction : enum (collegiate, under_25, open, any)
created_at              : timestamp
created_by_user_id      : FK User

unique constraint: (chapter_id, slug)
```

Events inherit credentialing weight from their chapter's tier (tier A chapter events count globally, tier B/C are local-only).

### Round

The atomic competitive unit within an event. Multi-round events have multiple Round records.

```
id                  : UUID primary key
event_id            : FK Event
round_number        : int (1, 2, 3... within event)
status              : enum (scheduled, opening, build, evaluation, pitching, deliberation, awards, completed)
opening_at          : timestamp (T-5:00)
build_start_at      : timestamp (T+0:00)
build_end_at        : timestamp (T+24:00)
evaluation_end_at   : timestamp (T+36:00)
pitch_end_at        : timestamp (varies by player count)
deliberation_end_at : timestamp
awards_end_at       : timestamp
zamboni_end_at      : timestamp
player_count        : int
prompt_revealed     : text, nullable (round prompt if any)

unique constraint: (event_id, round_number)
```

The round status field tracks lifecycle through all phases. Status transitions are server-authoritative via Django signals.

### Submission

A player's work product in a round.

```
id                      : UUID primary key
round_id                : FK Round
player_user_id          : FK User
status                  : enum (in_progress, submitted_deployed, submitted_failed, dnf)
git_repo_reference      : varchar (path/URL to league-managed repo)
deployed_url            : varchar, nullable (where fuzz runner can reach it)
readme_content          : text
token_budget_used       : int
fuzz_budget_used        : int
attack_surface_coverage : enum (narrow, moderate, broad), nullable
submitted_at            : timestamp, nullable

unique constraint: (round_id, player_user_id)
```

One submission per player per round. Status tracks whether it deployed successfully. Surface coverage is computed from fuzz test applicability after evaluation.

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
override_by_judge   : FK ChapterMembership, nullable (if tester judge overrode)
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
running_score_after      : int (player's accumulated fuzz score after this invocation)
running_budget_remaining : int (player's fuzz budget after this invocation)
invoked_at               : timestamp
results_summary          : jsonb (counts of defended/broken/etc per this invocation)
```

This table is the data source for broadcast overlays and live leaderboards during build phase. Each invocation creates a row visible to commentators and audience. The running_score_after field enables the leaderboard sort to be efficient without recomputing aggregates per request.

## Scoring Entities

### JudgeAssignment

Junction tracking which judges are assigned to which events with which specialization.

```
id                  : UUID primary key
event_id            : FK Event
membership_id       : FK ChapterMembership (the judge's chapter membership)
role                : enum (tester, ux_designer, general)
assigned_at         : timestamp

unique constraint: (event_id, membership_id)
```

A judge can hold one role per event. Role determines which scoring interfaces they see and how their expertise weights certain categorical awards.

### Score

Judge-issued scores for submissions.

```
id                  : UUID primary key
submission_id       : FK Submission
judge_assignment_id : FK JudgeAssignment
score_type          : enum (pitch_quality, cross_examination, creative_coherence, ux_quality, technical_execution, documentation)
value               : decimal (typically 0-100 or 0-25 depending on type)
comments            : text, nullable
submitted_at        : timestamp

unique constraint: (submission_id, judge_assignment_id, score_type)
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
User ──┬─< ChapterMembership >── Chapter
       ├─< Submission           
       └─< Ranking              

Chapter ──┬─< Event ──< Round ──< Submission ──< FuzzResult >── FuzzTest
          ├─< VerificationApplication
          └─< ChapterMembership

JudgeAssignment links ChapterMembership to Event with role specialization
Score links JudgeAssignment to Submission with score type

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

### Cascade Behavior

- User deletion: anonymize rather than delete (preserve ranking history)
- Chapter deletion: only allowed for chapter owner; cascades to events, submissions, scores within that chapter; preserves user accounts
- Event deletion: cascades to rounds, submissions, scores
- Submission deletion: not allowed after round completes (preserves scoring history)

### Uniqueness Enforcement

Chapter owner uniqueness (one owner per chapter) is enforced via application logic since ChapterMembership.roles is an array. A pre-save check ensures only one membership per chapter has 'owner' in roles.

### JSON Field Schemas

The `jsonb` fields (`profile_data`, `documents`, `test_definition`, `details`) have informal schemas documented in their respective application code. Validation happens via Pydantic models or serializers, not database constraints.

### Migration Strategy

Migrations are forward-only. Schema changes accumulate as Django migrations. Periodic squashing of old migrations is acceptable when reviewed. Never modify or delete applied migrations.

---

*This document defines the schema. For how entities relate in request flows and service interactions, see ARCHITECTURE.md. For project conventions about working with this schema, see claude.md.*
