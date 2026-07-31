# AGENTS.md

This file is for Codex, Cursor, and other AI coding assistants beyond Claude Code.

For all project conventions, tech stack decisions, architectural principles, code style, and common pitfalls, read `claude.md` — the content applies to all AI coding assistants working on this project, not just Claude.

Before starting any work, read `BUILD_ROADMAP.md` to understand:
- Which stage is currently active
- What's in scope and out of scope for that stage
- Scope discipline rules that apply to all work

When asked to do work outside the current stage scope, suggest adding the request to `IDEAS_FOR_LATER.md` rather than implementing it. The discipline matters because it prevents the project from becoming an endless design exercise.

Supporting documents (referenced from `claude.md`):
- `format_spec.md` — what HackLet League is as a competitive format (tier-agnostic format definition)
- `LEAGUE_OPERATIONS.md` — how the league operates as a federated institution (governance, tier system overview, verification)
- `TIER_A_OPERATIONS.md` — Tier A operational template (credentialing-grade, full 135-min round profile, broadcast architecture, multi-day tournament template)
- `TIER_B_OPERATIONS.md` — Tier B operational template (middle tier, policy-enforced integrity)
- `TIER_C_OPERATIONS.md` — Tier C operational template (training tier / MVR, BYOD substrate, three profiles: MVR / Extended / multi-round)
- `DATA_MODEL.md` — database schema
- `ARCHITECTURE.md` — service relationships and request flows
- `FUZZ_RUNNER_SPEC.md` — runner architecture (relevant in Stage 5). Owned by a separate session; do not edit it or `fuzz-runner/`.
- `DOC_STATE.md` — per-section status of every doc (BUILT / DESIGNED / MEASURED / ASSUMED / SUPERSEDED) plus the cross-document contradictions `C-01`…`C-22`
- Open calls live **inline**, marked `OPEN —` in the section that owns them. There is no decisions file. If a task requires resolving one, stop and ask rather than choosing.

**There is no root `README.md`.** This line previously said one existed and carried getting-started instructions for human developers; it never did. `DEPLOY.md` covers running and deploying the stack, and `frontend/README.md` is the unmodified Next.js default.

A document describing a mechanism is not evidence the mechanism exists. Before claiming what the platform does, open the file and cite `path.py:line`.
