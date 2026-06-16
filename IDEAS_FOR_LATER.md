# Ideas for Later

*The parking lot for good ideas that are out of scope for the current stage. Per [BUILD_ROADMAP.md](BUILD_ROADMAP.md) Rule 2: when the urge to build something outside current-stage scope appears, add it here instead of building it. This file is where good ideas wait their turn.*

For each entry, note **what** the idea is, **why** it's deferred (which stage it likely belongs to, or why it's not yet justified), and any **context** worth preserving so the idea can be picked up cleanly later.

---

## Format & Scoring

- **HackLet Agentic (second format).** HackLet is a league that runs formats, not a single format; Agentic is the anticipated second one, built when the agentic-coding paradigm warrants it and Classical is operating well. Round sketch: 5-min opening + 15-min spec phase + 60-min supervised agent execution + 15-min hardening + 15-min eval/prep + 30-min pitches + 30-min deliberation/awards ≈ **165 min (~3 hr)**. Budgets: **500k tokens**, **60-min agent runtime cap**, **200 accepted-change cap**, **50 fuzz budget**. New categorical award **Best Direction**. **Shares the fuzz catalog with Classical** (the runner is format-agnostic — see FUZZ_RUNNER_SPEC.md). Substrate differs from Classical: VSCodium with one league-built, signed, locked extension (chat sidebar + accept/reject UI for agent-proposed changes), not the portal chat window — the accept/reject step is the format's deliberate-action friction. *Why deferred:* big standalone build (see the Agentic stage in BUILD_ROADMAP). *Context:* the agentic paradigm shift threatens a single-format competition but not a multi-format league.

## Platform & Features

*(none yet)*

## Operations & Community

- **FMWC positioning.** The Financial Modeling World Cup (founded 2020 by Andrew Grigolyunovich, Latvia, after ModelOff was discontinued) is HackLet's structural precedent: a niche measurable skill → recurring tiered competition + persistent rankings + an ESPN2 broadcast (All-Star Battle, 2022) → a real institution. Deploy in pitches to chapter operators / sponsors / employers to answer "*is this real?*" — HackLet applies a pattern that already worked, to a larger domain (AI coding > financial modeling in participant pool and cultural pull). Frame as **template, not parity** — HackLet hasn't earned FMWC's reach. *Verify the specific facts before any public use.*
- **Competitive landscape — Microsoft "Agents League" (AI Skills Fest, June 4–14, 2026).** ~10-day, esports-framed hackathon, ~$55k prize pool, combining live AI coding battles, async project submissions, and a Discord community across three tracks (Creative Apps with GitHub Copilot, Reasoning Agents with Microsoft Foundry, Enterprise Agents for Microsoft 365 Copilot). Structurally different from HackLet: a one-off marketing/skills-fest event vs a recurring credentialing institution; criteria-based/subjective judging vs an objective adversarial fuzz catalog; multi-day multi-track vs a 24-min solo compressed round. Honest read: a hyperscaler entering **validates the category** but is also a **distribution threat HackLet can't match** (Copilot's install base). HackLet's defense is not reach — it's the credential + the fuzz moat. Practical effect: **drop "first / pioneering" language** from positioning. (Verified June 2026 via Microsoft Tech Community.)
- **Testing-center framing.** HackLet workstations parallel certification testing-center rigor (CCIE lab, CISSP proctoring): controlled substrate, identical conditions, audited integrity. Useful for making the credentialing claim legible — the conditions are *why* the score means something.

## Infrastructure & Security

- **Fuzz-runner sandbox hardening doc.** Before Stage 5, update [FUZZ_RUNNER_SPEC.md](FUZZ_RUNNER_SPEC.md) to explicitly treat the runner as a sandbox executing untrusted contestant code, not just a test executor. Must address: container escape, resource exhaustion, network-egress prevention from submissions, and the hidden-pool-must-never-reach-workstations boundary. *Why deferred:* runner is Stage 5; flagged now so it isn't forgotten. *Context:* identified during the foundational design review.
- **Broadcast architecture (deferred details).** Capture via **VNC pull** from each workstation (league pulls the display rather than the workstation pushing). League stats overlay built as a **Next.js dashboard consumable by OBS as a browser source**. Production complexity scales with event tier (chapter → regional → championship). *Belongs to Stage 6.*

## Workstation Fleet Management (Stage 7+)

HackLet workstations are managed via MeshCentral + HackLet-specific
scripts, not a full RMM (Tactical RMM, NetLock, NinjaOne, etc.).

MeshCentral provides:
- Cross-platform agent (signed by league)
- Remote desktop, terminal, file transfer
- Script execution on individual workstations or fleet-wide
- Heartbeat / online status / basic health metrics
- Multi-tenancy (chapters scoped to their workstation groups)

Full RMMs add patch management, software inventory, compliance
reporting, and alerting workflows — none of which HackLet needs.
HackLet workstations are stateless homogeneous appliances managed
via master images (updated between events), not heterogeneous
endpoints requiring per-machine patching.

HackLet-specific logic lives in shell + Python scripts installed
at /opt/hacklet/ as part of the master image. The Django round
state machine pushes commands to MeshCentral via API when round
transitions occur; MeshCentral fans the command out to relevant
workstations; scripts execute and report to the league API directly.

First-party credentialing evidence comes from the HackLet scripts
reporting to the league's audit tables, not from the agent
transport. MeshCentral is implementation detail; the scripts and
their reports are the first-party data.

---

*When an idea here becomes in-scope for the active stage, move it out of this file and into the work.*
