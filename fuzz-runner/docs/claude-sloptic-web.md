# claude.md: Sloptic web (sloptic.org)

The public web product for Sloptic. A user submits a deployed web app URL and gets its **slop score** (lower
is better), the per-axis breakdown (security / qa / performance), the report card, and its **percentile
against the frozen 2026.1 population**. The GRADER lives in the separate `sloptic/sloptic-main` repo and is
consumed here as the engine. Never fork probe logic into this repo.

## Architecture

- **Frontend** (sloptic.org UI) + **thin API** (enqueues grade jobs) + **worker** (imports `sloptic`, runs the
  pipeline).
- **Grading is ASYNC.** A grade takes minutes and needs a browser (Playwright) + an LLM key, so it is a queued
  job: submit -> poll status -> results. Never block a request on a grade.
- **Percentile** comes from `sloptic`'s frozen curve (`validation/benchmark-curve.json`, 2026.1) plus its
  benchmark-ranking logic.
- Start with a worker in the backend; split the grader into its own hardened, network-isolated service when
  the egress sandbox needs its own context.

## The security model IS the product (do not weaken it)

The grader fires **active attack payloads** (SQLi, command injection, XSS, path traversal, XXE, upload
webshells). Aiming that at an arbitrary user-supplied URL is **unauthorized testing** (a real legal/abuse
problem) and turns the service into an SSRF/DoS relay. So:

- **PASSIVE BY DEFAULT.** An unverified target gets only observational probes (headers, TLS, accessibility,
  performance, soft-404, CWV). Active/injection probes NEVER run on an unverified target. This is legal
  safety, not a feature flag. It costs almost nothing: injection is ~0% of the slop signal on real apps, so
  the passive floor is ~all the value.
- **ACTIVE probing is a gated tier** behind domain-ownership verification (below).
- **EGRESS SANDBOX every outbound fetch** (grade AND verification): block loopback / RFC1918 / link-local /
  `169.254.169.254`. The grader must never reach internal infrastructure.
- **Rate-limit + quota every grade.** Respect robots and bot-challenges; never build anything that defeats
  them.
- **Only test targets the user owns or is authorized to test. Full stop.**

## Domain-ownership verification

Prove control of the origin to be actively tested by serving a token we issue. The durable authorization is a
**grant**, not the token.

- **The grant is ACCOUNT-BOUND, and a verified origin is NEVER globally open.** This is the load-bearing
  control. Active grading checks whether the REQUESTING account holds a grant for the origin: Alice verifying
  `alice.com` writes a grant for Alice; Mallory submitting `alice.com` has no grant and gets PASSIVE only.
  Model it as "this account may actively grade this origin," NEVER "this origin is active-gradable." The token
  file is world-readable and that is fine, reading it confers nothing; an attacker would have to serve THEIR
  OWN issued token, which needs real control, and even then the grant is only theirs.
- **Active grade = a custom domain + TWO independent control proofs: a file token AND a DNS TXT record.** They
  prove DIFFERENT surfaces (control of what is served vs control of the DNS zone), so an attacker who can plant
  a file (open upload / subdomain takeover) still fails the DNS factor. Two files at two paths are NOT two
  factors (same surface); DNS is the independent axis. Both must be present and re-checked at grade time.
  - file token: `https://<origin>/.well-known/sloptic-verification.txt` (body = token)
  - DNS TXT: `_sloptic.<domain>` = the token
- **Platform subdomains (`*.vercel.app`, `*.netlify.app`, ...) get the passive floor.** They cannot edit the
  platform's DNS zone, so the second factor is structurally unavailable; do not substitute a weak same-surface
  proof. Their path to an active grade is "attach a custom domain."
- **Scope + lifetime.** A grant authorizes only URLs under the verified origin (scheme + host + port); a
  redirect must not carry authorization off it. Grants are time-boxed (~90 days) and re-verified before an
  active grade.
- **Layered depth.** Every active grade carries: the two control proofs, the account-bound grant, a logged
  "I own this and authorize active testing" attestation (ToS-bound, so abuse is traceable and bannable), and
  the egress sandbox + rate limits. No single failure opens the active tier.

## Conventions

- **The grader is a dependency.** Pin `sloptic`; call it in `--passive-only` mode for unverified targets and
  the full run only for a verified origin. Do not copy or re-implement probe logic here. (`--passive-only` and
  the per-probe passive/active tag are a small change that lands in `sloptic-main`; this repo depends on it.)
- **A passive grade is a DIFFERENT measurement from a full grade** (fewer probes apply). Label it clearly and
  rank it against a passive-subset curve, or show raw passive slop + axes. Never mix a passive grade onto the
  full-grade percentile.
- **Secrets are server-side only** (LLM key, DB, queue creds). Never ship them to the client bundle, Sloptic
  itself grades for exactly this leak, so leaking one here would be self-parody.
- **Prose:** no em dashes; use commas, colons, parentheses, periods.
