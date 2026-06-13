# Ideas for Later

*The parking lot for good ideas that are out of scope for the current stage. Per [BUILD_ROADMAP.md](BUILD_ROADMAP.md) Rule 2: when the urge to build something outside current-stage scope appears, add it here instead of building it. This file is where good ideas wait their turn.*

For each entry, note **what** the idea is, **why** it's deferred (which stage it likely belongs to, or why it's not yet justified), and any **context** worth preserving so the idea can be picked up cleanly later.

---

## Format & Scoring

*(none yet)*

## Platform & Features

*(none yet)*

## Operations & Community

*(none yet)*

## Infrastructure & Security

- **Fuzz-runner sandbox hardening doc.** Before Stage 5, update [FUZZ_RUNNER_SPEC.md](FUZZ_RUNNER_SPEC.md) to explicitly treat the runner as a sandbox executing untrusted contestant code, not just a test executor. Must address: container escape, resource exhaustion, network-egress prevention from submissions, and the hidden-pool-must-never-reach-workstations boundary. *Why deferred:* runner is Stage 5; but flagged now so it isn't forgotten. *Context:* identified during the foundational design review.

---

*When an idea here becomes in-scope for the active stage, move it out of this file and into the work.*
