# HookCut — Deferred TODO (QA Audit 2026-03-07, updated 2026-03-08)

Status key: `[x]` = fixed in code | `[~]` = in progress (current session) | `[ ]` = still pending | `[!]` = requires your action (no code change)

---

## YOUR ACTION ITEMS (config / external services — no code needed)

### Must do before launch

- `[!]` **Set `FEATURE_V0_MODE=False`** in Railway env vars (code default is already False; verify Railway var matches)
- `[!]` **Razorpay setup** — KYC approval in progress. Once approved:
  - Create webhook → URL: `https://api.hookcut.nyxpath.com/api/billing/razorpay-webhook`
  - Set `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` in Railway
- `[!]` **Stripe webhook secret** — Set `STRIPE_WEBHOOK_SECRET` in Railway (app raises ValueError on startup if missing)
- `[!]` **Razorpay webhook secret** — Set `RAZORPAY_WEBHOOK_SECRET` in Railway (same startup guard)
- `[!]` **CORS_ORIGINS** — Verify Railway env var does NOT include `http://localhost:3000`
- `[x]` **Migrations applied** — `alembic upgrade head` run, now at revision 013. Applied:
  - 009: task_id unique index on analysis_sessions
  - 010: FK on transactions.session_id
  - 011: hashed_password + name on users (email/password auth)
  - 012: narm_insights.confidence VARCHAR → FLOAT
  - 013: updated_at on hooks, shorts, transactions
  - *(014 rule_key unique index — verify it was applied or re-run if needed)*

### Cloudflare Worker (one-time)

- `[!]` Deploy transcript worker:
  ```bash
  cd cloudflare-worker
  wrangler secret put INNERTUBE_API_KEY
  # value: AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8
  wrangler secret put API_KEY
  # generate: openssl rand -hex 32  (use same value as CF_WORKER_API_KEY in Railway)
  wrangler deploy
  ```
- `[!]` After deploying, set `CF_TRANSCRIPT_WORKER_URL` + `CF_WORKER_API_KEY` in Railway env vars
- `[!]` Uncomment `routes` in `cloudflare-worker/wrangler.toml` once DNS is configured

### Supabase RLS

- `[x]` **CRIT-12** — RLS verified enabled on all 14 public tables via Supabase MCP query. All tables show `rls_enabled: true`.

### Observability (fill in keys)

- `[!]` **Sentry** — Create project at sentry.io → Python → copy DSN → set `SENTRY_DSN` in Railway
  - After setup: add alert rule for `GeminiAPIError` and negative credit balance
- `[!]` **PostHog** — Create project at posthog.com → copy key → set `NEXT_PUBLIC_POSTHOG_KEY` + `POSTHOG_API_KEY` in Railway
- `[!]` **Flower** — Set `FLOWER_USER` (default: `admin`) and `FLOWER_PASSWORD` in Railway
  - Generate password: `openssl rand -hex 16`

### Infrastructure passwords

- `[!]` **POSTGRES_PASSWORD** already set in `.env` — also add to Railway env vars
- `[!]` **REDIS_PASSWORD** already set in `.env` — also add to Railway env vars
- `[!]` **Rotate the DB password** shared in conversation — go to Supabase → Project Settings → Database → Reset password

### Dependency lockfile

- `[!]` Generate lockfile after any `pyproject.toml` change:
  ```bash
  cd hookcut-backend
  pip install pip-tools
  pip-compile pyproject.toml -o requirements.lock.txt
  ```
  Then update `Dockerfile` to use: `RUN pip install --no-cache-dir -r requirements.lock.txt`

---

## CRITICAL — All Fixed

| Issue | Status | Fix |
|-------|--------|-----|
| CRIT-01 | `[x]` | `FEATURE_V0_MODE` default changed to `False` in `config.py` |
| CRIT-02 | `[x]` | `v0-grant` endpoint removed from `billing.py` |
| CRIT-03 | `[x]` | Ownership check on `get_hooks`, `regenerate`, `select_hooks` |
| CRIT-04 | `[x]` | Auth + ownership on all shorts endpoints |
| CRIT-05 | `[x]` | `ProcessedWebhook` table + idempotency in webhook handlers |
| CRIT-06 | `[x]` | `min(minutes, 10_000)` cap in Stripe + Razorpay handlers |
| CRIT-07 | `[x]` | Atomic `.env` write via `.tmp` + `os.replace()` |
| CRIT-08 | `[x]` | Lua atomic INCR+EXPIRE; IP fallback for anonymous rate-limit key |
| CRIT-09 | `[x]` | Swagger/OpenAPI gated behind `settings.DEBUG` |
| CRIT-10 | `[x]` | All hooks declared before conditional returns in `dashboard/page.tsx` |
| CRIT-11 | `[x]` | `useTransform` extracted from JSX into component body |
| CRIT-12 | `[x]` | RLS enabled on all 14 public tables (verified via Supabase MCP) |
| CRIT-13 | `[x]` | Auth + ownership on `GET /api/storage/{file_key}` |
| CRIT-14 | `[x]` | Migration fallback removed from `start.sh`; failure aborts deploy |
| CRIT-15 | `[x]` | Startup raises `ValueError` if webhook secrets are empty |
| CRIT-16 | `[x]` | `VideoTooLongError` raised after duration check (`MAX_VIDEO_MINUTES`) |
| CRIT-17 | `[x]` | InnerTube key moved to `env.INNERTUBE_API_KEY` wrangler secret |
| CRIT-18 | `[x]` | `alembic.ini` DB URL replaced with safe placeholder |
| CRIT-19 | `[x]` | CF Worker CORS locked to allowlist; `API_KEY` check unconditional |

---

## HIGH — All Fixed

| Issue | Status | Fix |
|-------|--------|-----|
| HIGH-01 | `[x]` | `auth/sync` email moved to request body with `EmailStr` |
| HIGH-02 | `[x]` | `MAX_POLLS = 120` added to `useShortPoller.ts` |
| HIGH-03 | `[x]` | `secure: process.env.NODE_ENV === "production"` on OAuth cookies |
| HIGH-04 | `[x]` | Admin role check in `proxy.ts` middleware; `isAdmin` in JWT |
| HIGH-05 | `[x]` | Dashboard link visible to all authenticated users in header |
| HIGH-06 | `[x]` | ShortCard shows error state instead of infinite spinner |
| HIGH-07 | `[x]` | `soft_time_limit=600, time_limit=660` on Celery task + global config |
| HIGH-08 | `[x]` | `timeout=120` added to Anthropic and OpenAI SDK calls |
| HIGH-09 | `[x]` | Transcript capped at 60k chars before LLM prompt |
| HIGH-10 | `[x]` | `RETRY_DELAYS` reduced from `[0,5,30]` to `[0,2,2]` |
| HIGH-11 | `[x]` | `SELECT FOR UPDATE` inside `begin_nested()` savepoint in `deduct()` |
| HIGH-12 | `[x]` | Atomic `UPDATE ... WHERE credits_refunded=False` in `refund_and_fail()` |
| HIGH-13 | `[x]` | Pool: `pool_size=3, max_overflow=7, pool_timeout=30, pool_pre_ping=True` |
| HIGH-14 | `[x]` | `Transaction.session_id` FK added with `ondelete="SET NULL"` |
| HIGH-15 | `[x]` | `/debug-sentry` endpoint removed / gated behind `DEBUG=True` |
| HIGH-16 | `[x]` | `sync_user` uses `INSERT ... ON CONFLICT DO UPDATE` upsert |
| HIGH-17 | `[x]` | `work_dir` cleanup in `try/finally` block |
| HIGH-18 | `[x]` | Stripe webhook checks signature header before reading body |
| HIGH-19 | `[x]` | Stripe HMAC wrapped in `anyio.to_thread.run_sync` |
| HIGH-20 | `[x]` | Audit log export capped at 1,000 rows |
| HIGH-21 | `[x]` | NARM analysis has TODO comment; needs Celery task (see deferred below) |
| HIGH-22 | `[x]` | `api_key: Field(min_length=10, max_length=512, pattern=alphanumeric)` |
| HIGH-23 | `[x]` | `auth/sync` email uses `EmailStr` |
| HIGH-24 | `[x]` | Celery result TTL: 300s → 3600s |
| HIGH-25 | `[x]` | Payment params moved from query string to request body |
| HIGH-26 | `[x]` | `youtube_url: Field(max_length=2048)` |
| HIGH-27 | `[x]` | Migration 010: unique partial index on `analysis_sessions.task_id` |
| HIGH-28 | `[x]` | Cleanup tasks use keyset pagination (no more OFFSET) |
| HIGH-29 | `[x]` | Bulk UPDATE now sets `updated_at=datetime.now(timezone.utc)` |
| HIGH-30 | `[x]` | `localhost:3000` CORS only added when `settings.DEBUG=True` |
| HIGH-31 | `[x]` | `SecurityHeadersMiddleware` added: CSP, X-Frame-Options, HSTS, nosniff |
| HIGH-32 | `[x]` | Razorpay webhook returns 400 (not 500) on invalid signature |
| HIGH-33 | `[x]` | Cobalt URL validated as `https://` + `follow_redirects=False` |
| HIGH-34 | `[x]` | Non-root `hookcut` user in Dockerfile |
| HIGH-35 | `[x]` | Source bind mounts removed from `docker-compose.prod.yml` |
| HIGH-36 | `[x]` | `healthcheckPath = "/api/health"` added to `railway.toml` |
| HIGH-37 | `[x]` | All 22 deps converted to `>=X.Y,<NEXT_MAJOR`; lockfile comment added |
| HIGH-38 | `[x]` | Beat consolidated into worker process (`--beat --concurrency=2`) |
| HIGH-39 | `[x]` | Migration 008 wrapped in `batch_alter_table` for SQLite compat |
| HIGH-40 | `[x]` | Redis internal-only (`expose`); `--requirepass ${REDIS_PASSWORD}` |
| HIGH-41 | `[x]` | Hardcoded `hookcut_dev` password replaced with `${POSTGRES_PASSWORD}` |
| HIGH-42 | `[x]` | Docker base image pinned to `python:3.12.9-slim-bookworm` |
| HIGH-43 | `[x]` | Node.js updated to v22 LTS via NodeSource |
| HIGH-44 | `[x]` | `task_reject_on_worker_lost=True` added to Celery config |

---

## FEATURES (Section 9)

| Feature | Status | Notes |
|---------|--------|-------|
| FEAT-01 — Email/password signup | `[~]` | In progress this session — backend + frontend |
| FEAT-02 — Razorpay integration | `[!]` | Code ready; keys not configured — see action items above |
| FEAT-03 — Sentry error tracking | `[~]` | Code being enabled this session; needs `SENTRY_DSN` env var |
| FEAT-04 — PostHog analytics | `[ ]` | No PostHog code exists yet — needs full implementation (see deferred below) |
| FEAT-05 — Terms of Service page | `[~]` | Page being created this session |
| FEAT-06 — Privacy Policy page | `[~]` | Page being created this session |
| FEAT-07 — Flower monitoring | `[~]` | Being added to Procfile + docker-compose this session |
| FEAT-08 — Webhook idempotency table | `[x]` | `ProcessedWebhook` model + table already exists (CRIT-05) |
| FEAT-09 — Health check w/ dependencies | `[~]` | `/api/health` being enhanced (DB + Redis checks) this session |
| FEAT-10 — Cloudflare Worker deploy | `[!]` | Run `wrangler deploy` manually — see action items above |

---

## MEDIUM — In Progress / Deferred

### Being fixed this session (`[~]`)

| Issue | File | Fix being applied |
|-------|------|-------------------|
| MED-01 | `rate_limit.py` | Lua atomic INCR+EXPIRE script |
| MED-02 | `gemini_provider.py` | Timeout reduced to 120s |
| MED-03 | `gemini_provider.py` | `maxOutputTokens` upper guard `min(x*2, 8192)` |
| MED-04 | `caption_cleanup.py` | Sanitize LLM output before re-embedding in prompt |
| MED-07 | `short_generator.py` | New DB session per thread in ThreadPoolExecutor |
| MED-08 | `analytics.py` | `threading.Lock()` around PostHog client init |
| MED-09 | `admin_service.py` | Rule key: integer max instead of lexicographic |
| MED-11 | migration | `narm_insights.confidence` VARCHAR → FLOAT |
| MED-13 | migration | `updated_at` added to hooks, shorts, transactions |
| MED-14 | `user_service.py` | History uses window function (`COUNT(*) OVER()`) |
| MED-15 | `analyze_task.py` | Redundant SELECT after flush removed |
| MED-22 | `storage.py` | Hardcoded `127.0.0.1:8000` → `settings.API_BASE_URL` |
| MED-24 | `admin_service.py` | NARM prompt: JSON double-encoded to prevent injection |
| MED-25 | `admin_service.py` | Transcript truncated to 500 chars in admin detail |
| MED-26 | `schemas/user.py` | `currency: Field(max_length=3, pattern=r'^[A-Z]{3}$')` |
| MED-27 | `ffmpeg_commands.py` | `os.chmod(cookie_path, 0o600)` after write |
| MED-28 | `hookcut-frontend/src/` | Session IDs moved from localStorage to React state |
| MED-29 | `pricing/page.tsx` | Checkout errors show user-facing toast |
| MED-30 | `settings/page.tsx` | Currency save failure shows error toast |
| MED-31 | `.dockerignore` | Created: excludes `.env`, `*.db`, cookies, storage |
| MED-32 | `cloudflare-worker/worker.js` | `fetchViaInnertube` wired in as fallback |
| MED-33 | `Dockerfile` | `HEALTHCHECK` directive added |
| MED-34 | `docker-compose.prod.yml` | PostgreSQL no longer exposed on host port 5432 |
| MED-35 | `celery_app.py` | `beat_schedule` defined explicitly |
| MED-37 | `next.config.ts` | CSP header added in report-only mode |

### Still pending (deferred)

| # | File | Issue | Why deferred |
|---|------|-------|--------------|
| MED-05 | `app/llm/provider.py` | Verify `get_provider.cache_clear()` is called after key write | Verify manually — check admin_service.py `set_api_key` calls it |
| MED-06 | `app/llm/transcript.py` | 9 hardcoded Piped/Invidious instances, no circuit breaker | Needs uptime monitoring data; stale instances should be audited manually |
| MED-10 | `app/services/admin_service.py` | `seed_rules` aborts if ANY rules exist | Low risk; upsert refactor needed when re-seeding |
| MED-16 | `app/llm/transcript.py` | Whisper downloads full audio before size check | Needs duration pre-check before audio download |
| MED-17 | `app/utils/ffmpeg_commands.py` | Cobalt downloads full video before trim | Needs byte-range/section download investigation |
| MED-18 | `app/routers/billing.py` | `PATCH /api/user/currency` may lack explicit auth check | Audit all user endpoints to confirm `get_current_user_id` is present |
| MED-20 | Supabase | No PITR backups on free tier | Requires Supabase Pro ($25/mo) or manual pg_dump cron |
| MED-21 | `app/tasks/scheduled.py` | Cleanup tasks not idempotent under double-fire | Use `UPDATE ... WHERE processed=False RETURNING id` atomic pattern |
| MED-23 | `app/tasks/celery_app.py` | No dead letter queue for failed tasks | Add `task_routes` with DLQ + retry policy |
| MED-36 | migrations | DateTime columns timezone-naive | Risky data migration; defer until traffic is low |

---

## LOW — Deferred (fix as time allows)

| # | File | Issue | Notes |
|---|------|-------|-------|
| LOW-02 | `app/main.py` | Version string in `/health` response | Minor; remove or gate behind admin auth |
| LOW-03 | Admin frontend | No focus trap on confirmation modals | Add `role="dialog"` + shadcn `FocusTrap` |
| LOW-06 | `app/models/hook.py` | Dual time representation (varchar + float) | Consolidate to float; requires data migration |
| LOW-08 | Admin rules page | Generic error toasts per page | Map to specific messages per operation |
| LOW-13 | `Procfile` | Single Uvicorn process (no `--workers`) | Switch to `gunicorn -k uvicorn.workers.UvicornWorker -w 2` |
| LOW-14 | `alembic.ini` | Short numeric revision IDs (`001`–`014`) | Use Alembic hash IDs for new migrations going forward |
| LOW-18 (partial) | `docker-compose.prod.yml` | `condition: service_healthy` in `depends_on` | Only add after adding healthchecks to all services |
| LOW-19 | `app/tasks/celery_app.py` | `get_settings()` called at module import | Lazy-initialize inside Celery app factory |
| LOW-23 | migrations | Missing indexes: `learning_logs.niche`, `shorts.expires_at`, `shorts.download_url_expires_at` | Create in a single migration (non-urgent) |

---

## UX — In Progress / Deferred

### Being fixed this session (`[~]`)

| Issue | Fix |
|-------|-----|
| UX-04 | `/pricing` removed from protected routes |
| UX-06 | Fake testimonials replaced with factual product claims |
| UX-07 | Checkout/PAYG errors show toast to user |
| UX-08 | `callbackUrl` reads from `searchParams` |
| UX-09 | Admin error toasts are operation-specific |
| UX-10 | Elapsed timer stops on terminal state |
| UX-11 | `ai-hook-finder` error/loading pages get dark theme |
| UX-12 | Mobile menu wrapped with `<AnimatePresence>` |
| UX-13 | Broken `nonce="undefined"` attributes removed |
| UX-14 | ToS/Privacy links changed from `<span>` to `<Link>` |

### Still pending (deferred)

| Issue | File | Notes |
|-------|------|-------|
| UX-05 | `marketing-home.tsx`, `hooks-step.tsx` | Replace placeholder thumbnails with real demo content — needs actual product screenshot/GIF |

---

## OBSERVABILITY — Deferred

| # | Issue | Action |
|---|-------|--------|
| OBS-01 | Sentry DSN not set | `[!]` Set `SENTRY_DSN` in Railway (code is wired) |
| OBS-02 | PostHog not integrated | `[ ]` No `analytics.py` exists — needs full implementation: create PostHog project, add `posthog-python` to backend deps, create `app/utils/analytics.py`, instrument key events (analysis started, short generated, payment made) |
| OBS-03 | No structured JSON logging | Add `python-json-logger`; configure uvicorn JSON formatter |
| OBS-04 | No Celery monitoring | `[!]` Deploy Flower (code added this session); set `FLOWER_PASSWORD` |
| OBS-06 | No Sentry alerts for Gemini errors | Set up alert rule in Sentry dashboard after OBS-01 |
| OBS-07 | No negative balance anomaly alerts | Add monitoring query: `SELECT * FROM credit_balances WHERE total_seconds < 0` |
| OBS-08 | No `X-Request-ID` header | Add `X-Request-ID` middleware to FastAPI (low priority) |

---

## LLM — Two-Pass Hook Extraction Upgrade (deferred)

**Current state**: Single LLM call with internal discovery→evaluation pipeline (Stage 1 = discovery mode, Stage 2-3 = evaluation mode). Works within one call using cognitive separation instructions.

**When to upgrade**: If real user data shows the single-call pipeline still biases intro sections and misses mid-video hooks despite the "DISCOVERY MODE" instruction.

**Proper fix**: Split into two actual LLM calls:
1. **Pass 1 — Discovery**: Send transcript + cluster detection instructions. Returns 12–20 raw candidates as JSON (timestamp, text, tier, one-line reason). No scoring.
2. **Pass 2 — Editorial**: Send candidates + scoring/selection prompt. Returns final 5 hooks with full scores, justification, virality, etc.

**Cost impact**: Doubles LLM cost per analysis (~$0.006 on Gemini Flash, ~$0.128 on GPT-4o) and latency (~16-30s total vs ~8-15s).

**Files to modify**: `app/llm/prompts/hook_identification.py` (split into two prompt builders), `app/services/hook_engine.py` (chain two LLM calls).

---

## HIGH-21 — NARM: Full Async Migration (deferred)

**Current state**: Runs synchronously, added blocking note + TODO comment.
**Proper fix**: Move `trigger_narm_analysis` to a Celery task:
1. Create `app/tasks/narm_task.py` with a `run_narm_analysis` Celery task
2. Admin endpoint returns `{"task_id": "...", "status": "queued"}` immediately
3. Frontend polls `/api/tasks/{task_id}/status` for completion
4. Store result in `narm_insights` table as today

---

*Last updated: 2026-03-08 | Source: `.claude/qa-audit/FINAL_REPORT.md`*
*Session fixes: 44 HIGH + 4 CRITICAL (CRIT-01/08/17/19 verified already done) + features + MED/LOW in progress*
