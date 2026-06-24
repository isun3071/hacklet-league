# Changelog

Notable changes to HackLet League, organized by build stage (see [BUILD_ROADMAP.md](BUILD_ROADMAP.md)).
This is a human-readable summary; the authoritative record is the git history.

---

## Scoring: deduction-only "Slop Score" (June 2026, Stage 5 design)

The resilience score was reworked and renamed in two composed changes, formalized during Stage 5 (fuzz runner) design. Best Overall is still the rank-sum composite with Communication — only the resilience component's shape and name changed.

- **Deduction-only.** Scoring no longer awards points for passing a probe. A probe either detects slop (adds a penalty) or it doesn't (zero). This honors the attacker/defender asymmetry (defending 7 of 8 SQL endpoints is still a breach — the 7 add nothing, the 1 adds full penalty) and resolves the parameterized-SQL-invisibility problem structurally (a defended hidden sink and an absent one both score zero, which is correct — neither is vulnerable). It collapses the prior `provable_defense` / `failure_only` scoring split and the `worst_case` / `additive` aggregation modes into one rule: sum the penalties of fired probes. `evidence_model` survives only as a detection hint.
- **Renamed Resilience Score → Slop Score, sign flipped.** Was `(-∞, 0]`, higher-is-better; now `[0, +∞)`, **lower-is-better, 0 = perfect** (golf-style). Presentation-equivalent, but it closes the loop with the slogans ("no slop survives"; "the fuzz is what separates hacklets from slop"), reads as universally-legible lower-is-better, and coheres with the Vibe Mill → HackLet thesis.

Preserved deliberately: the **"Most Resilient"** award title (aspirational quality vs descriptive measurement), the **"fuzz catalog" / "fuzz runner"** names (fuzzing is the method, slop is the measurement), and **"resilient"** as a quality adjective.

Cascaded across format_spec.md (§4, canonical), LEAGUE_OPERATIONS.md, the tier ops docs, FUZZ_RUNNER_SPEC.md, IDEAS_FOR_LATER.md, BUILD_ROADMAP.md, DATA_MODEL.md, ARCHITECTURE.md, claude.md, and the landing copy. **No platform migration:** the shipped Stage-3 scoring uses a judge-entered `engineering_score` stand-in (higher-is-better), intentionally left as-is; the real deduction-only `slop_score` field is born when the Stage-5 runner is built.

---

## In progress — Stage 1 close-out (as of 2026-06-18)

- [x] End-to-end acceptance **verified on the live site**: signup → verify email → login → create chapter (pending) → admin approve (verified) → appears in directory → suspend (leaves directory). Full lifecycle walked.
- [x] Real transactional email — Resend SMTP, domain verified (SPF/DKIM), confirmed delivering to inboxes. (`docker-compose.yml` now forwards `EMAIL_*`/`RESEND_API_KEY` to the backend; Sites record renamed from `example.com` to HackLet League so emails read correctly.)
- [ ] ~1 week of stable uptime → Stage 1 officially ships.
- Next: **Stage 2 — events** (Google SSO landed — see below).

### Close-out fixes (the bugs squashed to get acceptance green)
- **Email verification link 400'd** — allauth percent-encodes the key's colons (`%3A`) in the email URL; `useParams()` returned it still-encoded, so the backend rejected a key it never signed. Decode before POSTing.
- **Login didn't update the UI** (then 409 on retry) — the header's auth nav only checked the session on mount and never remounted across client navigation; now re-checks on route change, and login treats `409 (already authenticated)` as success.
- **Pending chapter detail 500'd** — SSR fetches the API as `Host: backend:8000`, which hardened `ALLOWED_HOSTS` rejected (`DisallowedHost` 400 → frontend 500). Allow the internal host; also forward the request's session cookies to SSR so a creator can see their own pending chapter.
- **Status lifecycle** — default is now `pending` (was `unverified`); detail-page banner is state-aware (pending / suspended / not-approved); new owner **`/dashboard`** lists your chapters with status badges (via `/api/chapters/mine/`).

---

## Google SSO (June 2026, post-Stage-1)

Added **"Continue with Google"** on login + signup via **django-allauth socialaccount** (headless redirect flow). The OAuth client is configured from env vars (no DB `SocialApp`); a successful sign-in lands the user straight on `/dashboard`. Getting the headless OAuth flow working surfaced four non-obvious requirements, each worth remembering:

- **`django-allauth[socialaccount]`, not base** — the base package omits the OAuth HTTP/JWT libraries; adding a provider without the extra crash-loops the backend on `ModuleNotFoundError: No module named 'jwt'`.
- **`SameSite=Lax`, not `Strict`** — Google's callback is a cross-site top-level redirect, and a Strict session cookie is dropped on it, losing the OAuth state.
- **Absolute `callback_url`** — allauth doesn't honor a relative return path after the provider round-trip; the button sends `window.location.origin + /dashboard` (matching allauth's reference SPA).
- **Caddy must proxy `/accounts/*` and be reloaded on Caddyfile changes** — the bind-mounted config isn't picked up by `up -d`, so `deploy.sh` now reloads Caddy every deploy.

Also: mounted `accounts/` (under `HEADLESS_ONLY`, allauth.urls serves only the provider OAuth callback), and added a `socialaccount_login_error` frontend fallback so a failed social login lands on a real page.

---

## Chapter CRUD completed (June 2026, post-Stage-1)

Chapter owners can now **edit and delete** their chapters from the dashboard — the U + D that were missing (create/read already existed). Details:
- Update + delete are **owner-scoped** at the queryset level, so a non-owner gets **404, not 403** (existence isn't leaked); covered by new pytest cases.
- **Slugs stay stable** across renames (no broken links / directory churn).
- **`contact_email` is owner-only** — returned to the creator for editing, blank in public API responses.
- Delete is a **hard delete** (cascades the owner membership). Editing a verified chapter does **not** auto-revert it to pending — owner edits are trusted for the pilot.

---

## Stage 1 — Foundation (June 2026)

Deployed the platform — **Django + DRF + PostgreSQL + Next.js behind Caddy** — running on the home Proxmox VM and **live (public, not publicized) at https://hackletleague.com** over HTTPS with production settings.

### Backend (Django)
- Django 5 project (`uv`, split `base/dev/prod` settings, whitenoise), Postgres 16, `/api/healthz` liveness probe.
- Custom **email-based `User`** model (UUID pk, `is_superadmin`, JSON profile) + Django admin.
- `Chapter` + `ChapterMembership` models per DATA_MODEL, with admin (superadmin chapter approval).
- **django-allauth headless** auth — email login, session-based (no JWT), mandatory email verification, `/api/csrf/` for SPA writes.
- DRF API: chapter directory (verified-only), chapter detail, authenticated chapter create (→ owner membership, pending review), `/api/chapters/mine/`, profile `/api/me/`.
- `pytest` smoke tests (custom-user manager, auth gates, chapter create flow, directory filtering) — run in CI.

### Frontend (Next.js 16 / React 19 / Tailwind v4)
- Standalone-output Docker build, served by Caddy at `/`; backend at `/api`, `/admin`, `/_allauth`.
- Terminal/CTF aesthetic ported to the app; shared header/footer; sticky-footer layout.
- Server-rendered chapter **directory** + **detail** pages (SSR via internal API).
- Full **auth flow**: login, signup, email verification, auth-aware nav, **profile** edit, **chapter-creation** form — same-origin session cookies + CSRF (no CORS).

### Infrastructure & deployment
- Portable **Docker Compose** stack (`docker-compose.yml` + `docker-compose.dev.yml`) — host-agnostic; the repo is the portability layer.
- **Caddy** serves the public domain over HTTPS *and* the LAN IP over plain HTTP simultaneously (two site blocks via `SITE_ADDRESS` / `LAN_ADDRESS`).
- Migration workflow: generate via the dev override → commit → rebuild (migrations are committed source).
- DB **backup/restore scripts** + a concrete **Hetzner migration runbook** (clone + `.env` + `pg_dump`/restore + DNS cutover).
- Production settings hardened: `DEBUG=False`, real `SECRET_KEY`, `ALLOWED_HOSTS`, secure cookies, HSTS, `CSRF_TRUSTED_ORIGINS`.
- Transactional email: env-driven SMTP in prod, with a console-log fallback when unconfigured.

### CI/CD & monitoring
- Single GitHub Actions workflow: `backend` (pytest + Postgres) and `frontend` (build) on every PR/push; **`deploy` gated on both passing, push-to-main only**, running on a **self-hosted runner** on the VM via `scripts/deploy.sh`.
- Repo hardening: restricted Actions allowlist, fork-PR approval, read-only workflow token.
- Uptime monitoring documented (UptimeRobot → `/api/healthz`).

### Fixed (ops)
- Migrations weren't persisting (`docker compose run --rm` in a `COPY`-based image) → added the dev-override bind mount + commit-migrations workflow.
- Branch divergence between dev machine and VM → rebase reconcile + `pull.rebase`.
- `ERR_SSL_PROTOCOL_ERROR` on the LAN IP → stale `.env` forced an HTTPS redirect → fixed by the dual-site Caddy config.
- Disk full (12 GB LV) → expanded the Proxmox disk and grew partition → PV → LV → filesystem to 39 GB.
- Next.js 16 dropped the `eslint` config key → removed it.
- `frozen-lockfile` CI mismatch → pinned `pnpm@10` to match the lockfile.

---

## Stage 0 — Landing page (June 2026)

- Static landing page (framework-free), iterated with design feedback:
  - terminal / CTF aesthetic (monospace, near-black + lime, CRT scanlines);
  - competition-platform layout (nav, stats strip, schedule / standings / tiers tables) modeled on Codeforces, CTFtime, and Advent of Code;
  - copy humanized to remove AI tells (rule-of-three, em-dash rhythm, antithesis constructions; first-person voice).
- Buttondown email signup wired to the `iansun20` account.
- Superseded by the Next.js landing in Stage 1.

---

## Documentation

- Reframed HackLet as a **multi-format league** running **HackLet Classical** (the FIDE model) — eight strategic shifts integrated across format_spec, LEAGUE_OPERATIONS, BUILD_ROADMAP, DATA_MODEL, ARCHITECTURE: league-of-formats (`Event.format_type`), FMWC precedent, the two-principle thesis (substrate equality + submission resilience), per-player account lifecycle (+ `WorkstationSession`), OpenAI-compatible AI proxy, Classical-chat vs Agentic-extension, Microsoft Agents League context, fuzz-catalog-as-moat.
- Web-verified and corrected FMWC and Microsoft Agents League facts.
- Created `IDEAS_FOR_LATER.md` (parking lot for out-of-scope ideas).
- Recorded strategic decisions: build-first/CTWC sequencing; **public ≠ publicized**; home VM now / Hetzner later.
