# HackLet League — Architecture

*Service relationships, request flows, deployment topology, and integration points for hackletleague.com.*

---

## Services

The platform runs four primary services in production:

1. **Django backend** — REST API, business logic, AI proxy, scoring engine, Channels for WebSockets
2. **Next.js frontend** — Public site, authenticated portals, role-gated routes
3. **PostgreSQL** — Primary data store for all entities
4. **Redis** (optional, recommended for production) — Channels backend for WebSocket message routing, session storage if not in postgres, cache for hot reads

In development, all four run via docker-compose. In production, they run on a Hetzner VPS via docker-compose with reverse proxy (nginx or Caddy) handling TLS.

External services the platform integrates with:

- **OpenRouter** — AI substrate (DeepSeek V4 Flash for season 1)
- **Future: Email service** (Postmark, SendGrid, or self-hosted) for account verification, password resets, event notifications
- **Future: Object storage** (S3-compatible, possibly Hetzner Object Storage) for chapter documents, broadcast recordings, larger uploads

## Request Flows

### Authentication Flow

1. User visits `/login` on Next.js frontend
2. User submits credentials to Django backend `/api/auth/login`
3. Django validates via django-allauth
4. Django returns session cookie (httpOnly, secure, same-site strict)
5. Frontend stores nothing; cookie carries session for subsequent requests
6. Authenticated requests include the cookie automatically
7. Backend resolves user from session on each request
8. Logout posts to `/api/auth/logout`, session invalidated server-side

Sessions are server-authoritative. JWTs are not used.

### Public Page Flow

1. User visits `/` (or `/about`, `/methodology`, `/leaderboards`, `/chapters/[slug]`)
2. Next.js renders with server-side rendering (SSR)
3. SSR fetches data from Django REST API on the server
4. HTML returned to browser with hydration data
5. Subsequent navigation uses client-side routing where appropriate

Public pages are SEO-friendly through SSR. Cache-control headers allow CDN caching for static-ish content.

### Player AI Chat Flow (during active event)

1. Player at workstation browser is on `/play/event-[id]` (authenticated as player, enrolled in active event)
2. Player types prompt into chat interface
3. Frontend posts to `/api/ai/chat` with prompt
4. Django validates: user is player in this round, round is in build OR evaluation phase (chat retained during prep, files become read-only), budget not exhausted
5. Django retrieves player's running token total for this round
6. Django constructs OpenRouter request with the season's model
7. Django streams response from OpenRouter
8. Django streams tokens back to frontend via WebSocket or SSE
9. Django updates token total incrementally as tokens stream
10. If budget would exceed limit mid-response, Django truncates and signals frontend
11. Frontend displays streamed response in chat UI
12. Frontend never sees the OpenRouter API key

The OpenRouter API key is stored encrypted server-side (environment variable or secret manager). It is added by Django when constructing the upstream request, never exposed to the frontend.

The proxy is also exposed as an **OpenAI-compatible chat completions endpoint** (`/api/v1/chat/completions`), alongside the simple `/api/ai/chat` the portal uses. Any OpenAI-protocol client — the Classical chat window today, an Agentic IDE extension later, CLI tools — targets it with the same session auth, budget enforcement, and audit logging. Compatibility is surface-only: Django pins the season's model, enforces token/fuzz budgets and rate limits server-side, and logs every call; clients cannot choose the model or exceed budget. This decouples the substrate from any specific client choice without changing the API contract.

### Fuzz Trigger Flow (during build phase, local runner)

1. Player clicks a fuzz category trigger button in the league portal
2. Frontend posts to `/api/fuzz/trigger` with category and submission context
3. Django validates: round in build phase, fuzz budget sufficient
4. Django deducts category cost from player's fuzz budget
5. Django responds to frontend with authorization token and category specification
6. Frontend signals local fuzz runner on the workstation (via local API or filesystem signal)
7. Local fuzz runner executes random sample of category tests against player's local deployment (localhost)
8. Results displayed to player in portal — informational only, not scored
9. Local results may be optionally reported back to Django for player's own history

The local fuzz runner contains the public test pool only. The hidden pool exists only on league central infrastructure and runs only at code freeze. Budget enforcement happens server-side at Django even though execution happens locally. Local results are informational; only central results at freeze contribute to scoring.

### Code Submission and Authoritative Fuzz Flow (at code freeze)

1. T+29:00 (round-relative) arrives; Django signals all active player rounds via WebSocket
2. Django updates round status to evaluation; agentic edit capabilities are revoked (for Agentic formats); files in the player's home directory become read-only via filesystem permission flip
3. A league daemon on the workstation copies the player's working directory via SCP to league infrastructure at `/opt/hacklet/submissions/$EVENT_ID/$ROUND_ID/$USER/` (service-account path on the league server, not a personal home directory)
4. League's fuzz infrastructure picks up the submission, deploys it to an ephemeral container, and assigns a port for judge clickaround access
5. Central fuzz runner executes both public AND hidden test pools against deployed submission
6. Results written to FuzzResult records — these are the authoritative scored results
7. Submission status updated based on deployment success (completed/dnf/limited)
8. Results visible to judges in their portal for clickaround context
9. Post-event, completed submissions are mirrored to the public HackLet git org (github.com/hacklet-league/) with player attribution as part of the credentialing artifact archive

SCP-based submission (rather than git push from the workstation) reflects the per-player account lifecycle on workstations. The player's ephemeral, non-sudo Unix account doesn't accumulate git credentials, doesn't maintain long-lived repository state, and is deleted via `userdel -r` at the Zamboni Period. The submission daemon runs as a service account with pre-configured SCP credentials targeting the central path; the player's account is just the source filesystem to copy *from*. The chapter's firewall must allow workstation outbound SCP to the league submission endpoint.

The AI chat interface remains available during pitch preparation even after files become read-only — players who saved budget can use AI for pitch prep; players who tokenmaxxed get no prep assistance. This is consistent with the no-coddling design principle.

### Scoring Flow

1. Judge in `/judge/event-[id]` portal sees their queue of submissions
2. Judge interacts with submission (fuzz override for tester, scorecard for others)
3. Judge submits scores via `/api/scoring/submit`
4. Django validates: user is assigned judge for this event, scores in valid ranges
5. Django writes Score records
6. After all judges complete, scoring engine computes composite scores
7. Scoring engine determines categorical winners and Best Overall
8. Results published to event page, frontend pulls or receives via WebSocket
9. Ranking computation triggered for affected users

### Event Lifecycle Flow

Round status transitions follow a defined state machine:

```
scheduled
   ↓
opening (T+0:00) — round starts with 5-min host introduction
   ↓
build (T+5:00) — 24-min build phase
   ↓
evaluation (T+29:00) — 18-min concurrent: fuzz runner + judges + players prep pitches (AI chat retained, files read-only, agentic disabled)
   ↓
pitching (T+47:00) — 28-min for 8 players at 3.5 min each (60s pitch + 120s cross-ex + 30s transition)
   ↓
deliberation (T+75:00) — 18-min concurrent: judges deliberate + audience votes for People's Hacklet
   ↓
awards (T+93:00) — 14-min reveal ceremony
   ↓
completed (T+107:00)
   ↓
zamboni (T+107:00 to T+135:00) — per-player account teardown + next round preparation
```

Timing reflects HackLet Vibe: Classical Sprint (24-min build); other format variants scale timings proportionally to their timer axis (XP=12min build, Scrum=36min, Agile=48min, Waterfall=72-96min).

Transitions are triggered by:
- Time-based (Django scheduled task checking timestamps)
- Action-based (all judges submitted, all pitches completed, etc.)

State changes emit signals that update relevant clients via WebSocket.

### Workstation Session Lifecycle (per round)

Workstations are not re-imaged every round. At round start the chapter's RMM provisions an ephemeral, non-sudo Unix account from `/etc/skel`; at round end it terminates the player's session and processes and runs `userdel -r`, wiping the home directory and session state in seconds. System state persists untouched between rounds. Full image restoration is exceptional — between events, on a tamper-detection signal, or scheduled maintenance. Each session is recorded as a `WorkstationSession` (see DATA_MODEL.md) for credentialing audit.

The platform does not perform this directly — chapters operate their own RMM (the workstation-autonomy principle in claude.md). The platform records sessions and consumes tamper signals. This is a Stage 7 concern, documented here so the integrity and audit model stays coherent.

## External Integrations

### OpenRouter

Single integration point for AI substrate. Configuration:

- API key in environment variable, encrypted at rest
- Base URL: `https://openrouter.ai/api/v1/`
- Default model: `deepseek/deepseek-v4-flash` (season 1)
- Streaming responses for player chat
- Standard error handling with retries on rate limit

The integration is centralized in `backend/ai_proxy/` Django app. No other app calls OpenRouter directly. Future season model changes happen here.

### Broadcast Infrastructure

Tier A chapters running broadcast-quality events use broadcast infrastructure components:

- **Workstation streaming**: each workstation runs OBS (or equivalent) streaming its display to an RTMP endpoint. Chapter-side or league-side ingest server receives streams.
- **Stats overlay API**: league provides real-time data feeds (token budgets, fuzz budgets, fuzz scores, time remaining) via WebSocket or SSE. Broadcast production composites these into stream overlays.
- **Live leaderboard endpoint**: sortable player-fuzz-score leaderboard, updates as fuzz triggers complete. Display-ready format for broadcast layouts.
- **Commentator dashboard**: dedicated web view showing all players' metrics simultaneously. Used by commentators during broadcast.

For MVP, chapters handle their own video production (cameras, mixers, RTMP outputs). League supplies the data layer (stats, leaderboards, dashboards) that production composites with the video streams. Full integrated broadcast platform is future work.

### Future: Email Service

Account verification, password resets, event notifications, judge assignments. Pluggable via Django's email backend. Initial implementation can use console backend for development, file backend for staging, real service in production.

### Future: Object Storage

Chapter documents (verification application uploads), broadcast recordings, larger user content. S3-compatible API (Hetzner Object Storage or AWS S3) integrated via boto3 or django-storages.

## Deployment Topology

### Production (Hetzner VPS)

Single VPS running:

- nginx or Caddy (TLS termination, reverse proxy)
- Django backend (gunicorn for HTTP, daphne for WebSockets)
- Next.js frontend (Node.js process)
- PostgreSQL (managed via docker)
- Redis (managed via docker)

All services in docker containers, orchestrated via docker-compose. Persistent volumes for postgres data and redis state.

Backup strategy:
- Daily postgres dumps to object storage
- Weekly full backup retention for 30 days
- Monthly snapshots retained for one year

Monitoring:
- Basic uptime monitoring (UptimeRobot or similar)
- Application logs to local files with rotation
- Future: Sentry for error tracking, Plausible for analytics

### Development

Local docker-compose with:

- Django backend in dev mode (auto-reload, debug toolbar)
- Next.js frontend in dev mode (hot reload)
- PostgreSQL in container
- Redis in container

Database seeded with fixtures or factory_boy generated data. Development uses environment variables in `.env.dev` file (gitignored).

### Staging

Optional intermediate environment for testing changes before production. Same topology as production, smaller VPS, isolated database.

## Environment Configuration

Configuration via environment variables, loaded via django-environ:

**Required**:
- `DATABASE_URL` — postgres connection string
- `SECRET_KEY` — Django secret
- `OPENROUTER_API_KEY` — AI substrate access
- `ALLOWED_HOSTS` — comma-separated list
- `DJANGO_SETTINGS_MODULE` — points to dev/staging/prod settings

**Optional**:
- `REDIS_URL` — for Channels and cache (defaults to in-memory in dev)
- `EMAIL_BACKEND` and related — email service configuration
- `SENTRY_DSN` — error tracking
- `S3_BUCKET` and related — object storage

Secrets management in production via Docker secrets or external secret manager. Never commit secrets to git.

## Scaling Considerations

The architecture targets MVP scale (1-2 chapters, dozens of concurrent users at events, hundreds of users total). Scaling concerns deferred until needed:

**Easy scaling (when needed)**:
- Increase VPS size (Hetzner allows resize)
- Move PostgreSQL to managed instance
- Add Redis cluster
- CDN for static assets (Cloudflare)

**Harder scaling (significant work)**:
- Horizontal Django scaling (requires session storage in Redis)
- Read replicas for PostgreSQL
- Separate fuzz runner infrastructure
- Multi-region deployment

These are explicit deferrals. Build for current scale, refactor when scale demands.

## Security Architecture

### Defense in Depth

- TLS everywhere (Let's Encrypt via Caddy or certbot)
- Session cookies httpOnly, secure, same-site strict
- CSRF protection on all state-changing endpoints
- SQL injection prevention via Django ORM (no raw SQL with user input)
- XSS prevention via Django template escaping and React's default escaping
- Rate limiting on auth endpoints, API endpoints, fuzz triggers
- Input validation via DRF serializers / Pydantic models
- Output filtering in serializers (no accidental data exposure)

### Secrets

- OpenRouter API key never reaches frontend
- Database credentials in environment variables only
- Session signing keys in environment variables
- All secrets rotatable without code changes

### Audit Trail

- All significant operations logged to AuditLog
- Authentication events (login, logout, failed attempts)
- Authorization decisions (denied access)
- Score modifications and verification decisions
- Chapter status changes

### Permission Enforcement

- Django middleware checks authentication
- View decorators check role permissions
- django-guardian for object-level (chapter-scoped) permissions
- Never trust client-claimed roles or scopes

## Future Considerations

Explicitly deferred from MVP, documented for awareness:

- **Federation governance UI** — Currently superadmin handles all decisions; future stage adds advisory boards, voting mechanisms
- **Chapter-to-chapter messaging** — Not needed until multiple chapters coordinate
- **Streaming integration** — Live broadcast embedding, video archive
- **Mobile apps** — Web-first for now; native apps deferred
- **Internationalization** — English-only for MVP; i18n added when international chapters appear
- **Multi-region deployment** — Single VPS sufficient until latency becomes issue for global users
- **HackLet Unslop format support** — Pilot operates HackLet Vibe: Classical Sprint; Unslop variants add a slop-generation pipeline (league substrate generates broken application live during round opening, distributed identically to all workstations) and slightly different submission semantics (still SCP-based, same fuzz catalog). Same infrastructure substrate, additional generation/distribution step. Documented in format_spec.md §1 and IDEAS_FOR_LATER.md for Season 2-3 introduction.
- **Agentic format support** — Pilot operates Classical relationship (chat-window AI); Agentic variants add a league-built signed VSCodium extension with accept/reject UI, agent freeze semantics (revert to last accepted edit), and extended timer infrastructure (Agile-foundational at 48 min, Waterfall at 72-96 min). Stage 11+.
- **Post-event public submission archive** — Mirror completed submissions to github.com/hacklet-league/ with player attribution. Becomes part of the credentialing artifact surface — anyone can review what HackLet champions actually built. Lands as operational policy when chapter operations mature.

---

*This document describes how services connect. For the data they operate on, see DATA_MODEL.md. For project conventions, see claude.md. For the competitive format, see format_spec.md.*
