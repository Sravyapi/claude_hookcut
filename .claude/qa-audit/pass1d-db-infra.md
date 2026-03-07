# HookCut Infrastructure & DB Audit — Pass 1D
**Date**: 2026-03-07
**Auditor**: Principal DevOps / Infrastructure perspective
**Scope**: Deployment, DB migrations, Celery, storage, config, observability, dependencies, Cloudflare Worker

---

## Summary Table

| Area | Issue | Severity | Production Risk |
|---|---|---|---|
| Docker | Dockerfile single-stage; running as root | HIGH | Container escape risk; large image layers cached for security vulnerabilities |
| Docker (prod) | `docker-compose.prod.yml` uses hardcoded dev password for Postgres | HIGH | DB accessible with `hookcut_dev` credential in "prod" config |
| Docker (prod) | No health checks on backend/worker services | MEDIUM | Deployment succeeds with broken app; load balancer routes to unhealthy container |
| Docker (prod) | No memory/CPU limits on any service | MEDIUM | One runaway FFmpeg job starves all other containers |
| Docker (prod) | No restart policy on Postgres/Redis in prod compose | LOW | Infra services won't recover on crash |
| Celery | `run_analysis` task has no time limit (no `soft_time_limit` / `time_limit`) | HIGH | A hung LLM call or transcript fetch can hold a worker indefinitely, exhausting concurrency |
| Celery | `max_retries=0` on both tasks — no automatic retry | MEDIUM | Transient network errors (LLM API, YouTube) result in permanent failures with credit refund |
| Celery | No dead-letter queue configured | MEDIUM | Permanently failed tasks leave no trace beyond DB status; no operational visibility |
| Celery | Result backend TTL 5 min vs polling window | MEDIUM | Frontend polling can miss task result if poll interval > 5 min or task is slow |
| Celery | Beat schedule not protected against double-run | MEDIUM | If two beat processes run, `reset_free_credits` will double-reset (idempotent) and `cleanup_expired_files` will overlap — safe but wasteful |
| Celery | `worker_max_tasks_per_child=20` with only 2 workers | LOW | Workers restart frequently, temporarily dropping concurrency to 1 during restart |
| Database | `analysis_sessions.transcript_text` is unbounded `Text` | MEDIUM | Multi-hour videos can yield 200KB+ transcripts per row; no server-side limit enforced |
| Database | `learning_logs.hook_id` has no FK constraint | MEDIUM | Orphaned log entries if hooks are deleted; no referential integrity |
| Database | `transactions.session_id` has no FK constraint | MEDIUM | Dangling transaction records possible; no cascade on session deletion |
| Database | Missing index on `shorts.expires_at` | MEDIUM | `cleanup_expired_files` full-scans entire `shorts` table every hour |
| Database | Missing index on `analysis_sessions.created_at` | LOW | Admin session browser sorts by created_at without a single-column index (composite exists) |
| Database | `narm_insights.confidence` is `String(20)` in DB but expected as float in code | MEDIUM | Type mismatch causes silent coercion or runtime errors in NARM confidence scoring |
| Database | Migration 008 uses `op.alter_column` without `batch_alter_table` | HIGH | **Will crash on SQLite** — SQLite does not support `ALTER COLUMN TYPE` outside batch mode |
| Database | `alembic.ini` hardcodes `postgresql://postgres:password@localhost:5432/hookcut` | MEDIUM | Accidental migration against wrong DB if `DATABASE_URL` env is unset during `alembic upgrade head` |
| Database | `start.sh` migration failure is silent (`|| echo WARNING ... continuing`) | HIGH | App starts with schema mismatch if migration fails; errors are swallowed |
| Database | `video_duration_seconds` type mismatch: model is `Float`, migration 002 changes to `Integer` | LOW | Model and migration are inconsistent; float data truncated silently on Postgres |
| Storage | Local storage URL hardcodes `127.0.0.1:8000` | HIGH | Download URLs break in multi-replica or Railway deployment where backend is not on localhost |
| Storage | No disk quota or cleanup trigger for local storage | HIGH | `storage/` directory grows unboundedly if R2 is disabled; disk full kills the entire process |
| Storage | `storage/` directory is inside the app working dir | MEDIUM | `./hookcut-backend:/app` Docker volume mount exposes storage contents in build context |
| Storage | Expired URL check is not server-side enforced for local storage | MEDIUM | `download_url_expires_at` is tracked in DB but local HTTP URLs never expire |
| Config | `NEXTAUTH_SECRET` missing at startup crashes the app, but validation is skipped in `TESTING=true` mode | LOW | Test suite can mask misconfiguration |
| Config | `DATABASE_URL` default is relative SQLite path `sqlite:///hookcut.db` | HIGH | Celery workers will use different paths than web process; validation blocks this but only at runtime |
| Config | `RAZORPAY_WEBHOOK_SECRET` and Stripe keys present but no validation that they are set when payments enabled | MEDIUM | Payment webhook signature verification silently skips if keys empty |
| Observability | `/health` endpoint does not check DB connectivity or Redis reachability | HIGH | Health check returns 200 even if DB is down; Railway considers service healthy when it is not |
| Observability | Sentry traces_sample_rate hardcoded at `0.1`; not configurable | LOW | Cannot tune sampling without code change |
| Observability | Sentry environment hardcoded as `"production"` regardless of `DEBUG` flag | LOW | Debug-mode deployments report errors as production incidents |
| Observability | No Celery monitoring (no Flower, no StatsD) | MEDIUM | No way to observe stuck tasks, queue depth, or worker health in production |
| Observability | PostHog key blank by default; analytics silently disabled | LOW | No operational visibility into user funnel in production until key is configured |
| Railway | `railway.toml` sets `restartPolicyMaxRetries=3`; after 3 crashes Railway stops restarting | MEDIUM | Persistent crash loop (e.g. bad migration) leaves service permanently stopped |
| Railway | Procfile `worker` and `beat` lines both use `--concurrency=2`; beat should not have concurrency | LOW | Beat scheduler does not execute tasks; workers do. `--concurrency` on beat is harmless but misleading |
| Cloudflare Worker | `INNERTUBE_API_KEY` is hardcoded as a public YouTube API key in `worker.js` | MEDIUM | This key is a well-known public InnerTube key but hardcoding any key in source is bad practice |
| Cloudflare Worker | `Access-Control-Allow-Origin: *` — no origin restriction | MEDIUM | Any domain can call the transcript worker directly, bypassing the backend and burning Cloudflare CPU quota |
| Cloudflare Worker | `fetchViaInnertube()` function is defined but never called from `handleTranscript()` | LOW | Dead code; intended as a fallback but not wired up |
| Cloudflare Worker | `wrangler.toml` has no `workers_dev = false` or route binding | LOW | Worker is accessible at the public `workers.dev` subdomain forever even after production route is set |
| Dependencies | Frontend packages use `^` (caret) semver — non-pinned | MEDIUM | `npm install` in CI can pull breaking minor versions of Radix UI, Framer Motion, etc. |
| Dependencies | Backend uses `~=` (compatible release) — reasonably safe but not fully pinned | LOW | Patch-level updates to `celery`, `sqlalchemy`, `openai` etc. can introduce regressions |
| Dependencies | `@remotion/cli`, `@remotion/player`, `remotion` are full production dependencies | MEDIUM | Remotion bundles are large (>50MB); they should be `devDependencies` if only used for pre-rendering marketing videos |
| Cost Risk | No maximum video duration enforced in `start_analysis` | HIGH | `VideoTooLongError` exists but is never raised; a 10-hour video will charge 600 minutes, exhaust credits, and consume LLM tokens for a huge transcript |
| Cost Risk | `run_analysis` has no input token cap on transcript sent to LLM | HIGH | Very long transcripts (10-hour video) sent directly to Gemini; token cost unbounded |
| Cost Risk | Local storage never cleaned until `expires_at` scheduled task — but task runs hourly | LOW | Up to 1 hour of disk accumulation before cleanup; acceptable on small scale |

---

## Detailed Findings

### 1. Database Schema & Migrations

#### 1.1 Migration 008 — Missing batch_alter_table for SQLite (CRITICAL)
**File**: `hookcut-backend/alembic/versions/008_widen_hook_columns.py`

```python
def upgrade() -> None:
    op.alter_column("hooks", "hook_type", type_=sa.Text(), existing_nullable=False)
    op.alter_column("hooks", "funnel_role", type_=sa.Text(), existing_nullable=False)
```

Migration 002 correctly wraps its `alter_column` in `with op.batch_alter_table("analysis_sessions") as batch_op:` for SQLite compatibility. Migration 008 does not. On SQLite (used locally and in CI), this will raise `OperationalError: Cannot add a NOT NULL column with default value NULL`. On PostgreSQL (Railway production) it works fine, but the dev environment breaks, causing confusion. The `downgrade()` has the same problem.

**Fix**: Wrap both `alter_column` calls in `with op.batch_alter_table("hooks") as batch_op:`.

#### 1.2 start.sh swallows migration failures (HIGH)
**File**: `hookcut-backend/start.sh`, line 12

```bash
alembic upgrade head 2>&1 || echo "WARNING: Alembic migration failed (continuing anyway)"
```

If `alembic upgrade head` fails (permission error, locked table, migration bug), the server starts with an out-of-date or broken schema. The exit code is discarded. This is a common cause of cryptic runtime errors in production.

**Fix**: Remove `|| echo "..."`. Let `set -e` propagate the failure and fail the container start. Railway will then mark the deploy as failed and keep the previous version running.

#### 1.3 alembic.ini hardcodes a dev connection string (MEDIUM)
**File**: `hookcut-backend/alembic.ini`, line 3

```
sqlalchemy.url = postgresql://postgres:password@localhost:5432/hookcut
```

`alembic/env.py` overrides this with `DATABASE_URL` env var, but only when the env var is present. Running `alembic upgrade head` locally without `DATABASE_URL` set will silently target this hardcoded connection, potentially migrating the wrong database. It should read from `.env` as a safe default or use a placeholder that fails fast.

#### 1.4 Missing indexes on frequently queried columns (MEDIUM)
- `shorts.expires_at`: The `cleanup_expired_files` scheduled task queries `WHERE status = 'ready' AND expires_at < NOW()` every hour. There is an index on `status` (`idx_shorts_status`) but not on `expires_at`. Combined queries with two conditions benefit from a composite index `(status, expires_at)`.
- `learning_logs.niche` and `learning_logs.language`: NARM analysis aggregates by these fields but neither has an index.
- `analysis_sessions.status`: Covered by `idx_sessions_status` — OK.

#### 1.5 Missing FK constraints for referential integrity (MEDIUM)
- `learning_logs.hook_id` (column exists, nullable) — no `ForeignKey("hooks.id")` in migration 001. If a hook is deleted and cascade doesn't fire (e.g., direct SQL), orphaned log entries accumulate.
- `transactions.session_id` (column exists, nullable) — no FK constraint. Transaction records can outlive sessions.

#### 1.6 narm_insights.confidence type mismatch (MEDIUM)
**File**: `hookcut-backend/alembic/versions/007_add_admin_tables.py`, line 67

```python
sa.Column("confidence", sa.String(20), nullable=False, server_default="medium"),
```

The Memory file notes: "NarmInsight confidence type str→float mismatch" was fixed in audit #4. The DB column is `String(20)` which stores "high"/"medium"/"low". However, the Pydantic schema at some point expected `float`. Verify that the current `NarmInsight` Pydantic schema has `confidence: str` and the admin frontend does not try to render it as a numeric gauge.

#### 1.7 video_duration_seconds model/migration type drift (LOW)
Migration 001 creates `video_duration_seconds` as `sa.Float`. Migration 002 alters it to `sa.Integer`. The SQLAlchemy model (`session.py` line 19) declares it as `Mapped[float] = mapped_column(Float)`. There is a mismatch: the DB column is `INTEGER` on Postgres but the ORM maps it as `Float`. Python will auto-coerce integer → float without error, but a Postgres EXPLAIN will show `integer` type, meaning any code writing fractional seconds will truncate them.

#### 1.8 Unbounded transcript_text column (MEDIUM)
`analysis_sessions.transcript_text` is `sa.Text` with no length limit. For a 2-hour video, a transcript can easily be 150–300KB. At scale (10,000 sessions), this is 1.5–3GB stored inline in Postgres. For a production system, transcripts should be stored in object storage (R2) with only the key in the DB, or at minimum a hard `CHECK` constraint limiting the column to a reasonable size.

---

### 2. Celery / Task Queue

#### 2.1 run_analysis has no time limit (HIGH)
**File**: `hookcut-backend/app/tasks/analyze_task.py`, line 16

```python
@celery_app.task(bind=True, max_retries=0)
def run_analysis(self, session_id: str):
```

`generate_short` has `soft_time_limit=600, time_limit=660`. `run_analysis` has neither. A stalled transcript fetch (6-provider cascade with Whisper as the last resort, which itself involves a yt-dlp audio download) or a hung Gemini connection could hold a worker thread indefinitely. With `--concurrency=2`, one stuck `run_analysis` task halves available throughput and will never release until the worker process is killed.

**Fix**: Add `soft_time_limit=300, time_limit=360` to `run_analysis`. Handle `SoftTimeLimitExceeded` the same way `generate_short` does.

#### 2.2 No automatic retries on transient failures (MEDIUM)
Both tasks set `max_retries=0`. Transient errors — a 429 from Gemini, a brief Redis connection blip, a YouTube rate limit — result in immediate credit refund and permanent failure. The user must restart. A sensible retry policy with exponential backoff (2 retries, 30/90s delays) would eliminate the majority of transient failures transparently.

The risk of retrying with credit deduction already applied is real but can be mitigated by checking `session.credits_refunded` at the start of each retry.

#### 2.3 No dead-letter queue (MEDIUM)
Celery is configured with Redis as the broker. There is no DLQ configured. When a task fails permanently (after max_retries or with `max_retries=0` and an unhandled exception), the task result lives in Redis with `result_expires=300` (5 minutes) and is then gone. There is no way to replay failed tasks or inspect them after the fact. Operations teams have no visibility.

**Fix**: Configure a dedicated `failed_tasks` queue with `task_routes` or use `celery_dead_letter_exchange` (RabbitMQ feature, not available for Redis). At minimum, write task failures to a `TaskFailureLog` table before the result expires.

#### 2.4 Result TTL vs. polling window (MEDIUM)
`result_expires=300` (5 minutes). The frontend poll `usePollTask` uses exponential backoff up to 5s intervals. If analysis takes longer than 5 minutes (e.g., Whisper fallback), the Celery result is gone before the frontend checks it. The task DB status in `analysis_sessions` is the source of truth, but the Celery task state (PROGRESS metadata with stage/progress) will return `PENDING` after expiry, which the frontend might misinterpret as "still waiting."

The polling should rely on the DB-persisted status, not the Celery result backend. This appears to be the design intent but needs verification in the frontend polling logic.

#### 2.5 Beat schedule not idempotent under double-run (MEDIUM)
`reset_free_credits` resets every user's balance unconditionally. If beat runs twice on the 1st of the month (e.g., two beat containers in Railway), all users get two resets — both are the same value (`120.0`), so the second reset is a no-op (idempotency is accidental). However, `cleanup_expired_files` processes the same expired shorts twice if two beats overlap. The second run finds no expired shorts and exits cleanly, so this is safe in practice, but deploying multiple beat containers should be explicitly prevented.

#### 2.6 Worker concurrency vs. task weight (LOW)
Both tasks are heavy: `run_analysis` calls LLM APIs + transcript cascade; `generate_short` downloads video + runs FFmpeg. Both are CPU/IO intensive. With `--concurrency=2`, a single Railway service runs both worker types on the same process. There is no task routing to separate "CPU-heavy" (FFmpeg) from "IO-heavy" (LLM) queues. In production, FFmpeg rendering can saturate a single CPU for several minutes while LLM tasks wait.

---

### 3. Docker / Railway Deployment

#### 3.1 Container runs as root (HIGH)
**File**: `hookcut-backend/Dockerfile`

The Dockerfile has no `USER` directive. All processes inside the container run as `root` (UID 0). If there is an RCE vulnerability in the FFmpeg or yt-dlp pipeline (both process untrusted user-supplied URLs and video data), an attacker would have full root access inside the container.

**Fix**: Add `RUN useradd -m -u 1000 hookcut` and `USER hookcut` after the install step.

#### 3.2 Single-stage build; no multi-stage optimization (MEDIUM)
The Dockerfile copies the entire source tree, installs dependencies, and runs in the same layer. Build secrets or `.env` files accidentally present in the build context would be baked into the image. The image also contains build tools (`pip`, `setuptools`) that are not needed at runtime.

Additionally, `yt-dlp` is installed via `pip install yt-dlp` (unpinned version) during `apt-get`, not as a project dependency. It will receive arbitrary updates on every rebuild.

**Fix**: Use a multi-stage build. Add a `.dockerignore` that explicitly excludes `.env*`, `cookies*.txt`, `*.db`, and `storage/`.

#### 3.3 docker-compose.prod.yml uses dev password (HIGH)
**File**: `docker-compose.prod.yml`, lines 8-9

```yaml
POSTGRES_PASSWORD: hookcut_dev
DATABASE_URL: postgresql://hookcut:hookcut_dev@postgres:5432/hookcut
```

The file is named `prod` but uses the same `hookcut_dev` password as the local dev compose. This is the file teams reach for when deploying with Docker Compose. If deployed to a VPS with the Postgres port even briefly exposed, the DB is accessible with a known credential.

**Fix**: Remove the inline password. Use `env_file: .env.prod` or Docker secrets. The `POSTGRES_PASSWORD` should be populated from an environment variable: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}`.

#### 3.4 No health checks for backend/worker in prod compose (MEDIUM)
`docker-compose.prod.yml` has no `healthcheck` for the `backend`, `worker`, or `beat` services. Docker and deployment systems cannot detect an unhealthy application. Postgres and Redis have health checks in the dev compose but those were not carried to the prod compose.

#### 3.5 No memory/CPU resource limits (MEDIUM)
FFmpeg rendering of a 60-second video at 1080p can use 2–4GB RAM. With `--concurrency=2`, two simultaneous renders can OOM the container. There are no `mem_limit`, `memswap_limit`, or `cpus` constraints in either compose file or Railway configuration. A single job can starve all other containers sharing the host.

#### 3.6 railway.toml restart cap (MEDIUM)
**File**: `hookcut-backend/railway.toml`

```toml
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

After 3 failed restarts (e.g., from a bad migration on deploy), Railway stops restarting the service and marks it as crashed. This is correct for truly broken deploys, but a transient external dependency failure (Redis not ready yet) can cause 3 fast failures and a permanent stop. Consider increasing to 10 retries with an exponential backoff policy, or checking that `start.sh` has proper readiness logic.

---

### 4. Storage & Files

#### 4.1 Local storage URL hardcodes 127.0.0.1 (HIGH)
**File**: `hookcut-backend/app/services/storage.py`, line 66

```python
return f"http://127.0.0.1:8000/api/storage/{key}"
```

When `FEATURE_R2_STORAGE=false` (the current production default), download URLs are generated as `http://127.0.0.1:8000/...`. On Railway, the frontend is on a different domain (Vercel). These URLs will work only if the user is on the same machine as the backend — which is never the case in production. Every Short download attempt will fail silently or return a browser-side network error.

**Fix**: Use `settings.BACKEND_URL` (to be added) or derive the URL from the request's host header in the `/api/storage/{key}` endpoint.

#### 4.2 Unbounded local disk growth (HIGH)
When `FEATURE_R2_STORAGE=false`, every generated Short is copied to `storage/` in the app working directory. The `cleanup_expired_files` scheduled task runs every hour and deletes files whose `expires_at` has passed (24h TTL by default). However:
- If the beat worker is not running, cleanup never fires.
- The `storage/` directory is on the container's ephemeral filesystem; if it fills before cleanup fires, FFmpeg and yt-dlp operations will fail with "No space left on device" and the container may crash.
- There is no pre-generation disk check.

Railway's ephemeral filesystem is typically small (1–4GB). A few large 4K video Shorts can fill it quickly.

#### 4.3 Expired URL enforcement gap for local storage (MEDIUM)
`short.download_url_expires_at` is stored in the DB and checked by `ShortsService.get_download_url()` to regenerate the URL when expired. For R2 presigned URLs, an expired URL actually returns 403 from R2. For local storage, the HTTP URL never actually expires — the file is still accessible at the same path indefinitely until the scheduled cleanup runs. The `download_url_expires_at` column is only meaningful for R2 mode.

---

### 5. Environment Variables & Config

#### 5.1 DATABASE_URL default is relative SQLite path (HIGH)
**File**: `hookcut-backend/app/config.py`, line 12

```python
DATABASE_URL: str = "sqlite:///hookcut.db"
```

The validator at line 87 catches this and raises `ValueError`, so startup will fail. But the failure message only appears if `NEXTAUTH_SECRET` is also set. If `NEXTAUTH_SECRET` is missing, the first validator branch raises before the SQLite path check runs. The ordering of validation errors matters and could confuse operators.

#### 5.2 No validation that payment keys are set when payments are enabled (MEDIUM)
`FEATURE_V0_MODE: bool = False` (payments enabled by default). However, `STRIPE_SECRET_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET` are all `str = ""` with no startup validation. The webhook signature verification in `WebhookService` will silently skip validation if the secret is empty, meaning any unauthenticated POST to `/api/billing/webhook` will be accepted as valid. This is a **payment security vulnerability**.

#### 5.3 No maximum video duration enforced (HIGH)
`VideoTooLongError` is defined in `exceptions.py` line 41 but never raised. `analyze_service.py` calculates `minutes_needed = metadata.duration_seconds / 60.0` and passes it through without any upper bound. A malicious or careless user can submit a 10-hour video, which:
1. Deducts 600 free minutes (if available) or charges pro-rata.
2. Sends a ~500KB transcript to Gemini (costing many tokens).
3. Runs `run_analysis` with no time limit (see §2.1) potentially for hours.

**Fix**: Add `if metadata.duration_seconds > MAX_VIDEO_DURATION_SECONDS: raise VideoTooLongError()` to `AnalyzeService.start_analysis`. A reasonable limit is 3600s (1 hour).

#### 5.4 WHISPER_API_KEY falls back to OPENAI_API_KEY silently (LOW)
The `effective_whisper_key` property silently uses `OPENAI_API_KEY` if `WHISPER_API_KEY` is unset. This is documented behavior but means unexpected charges to the OpenAI account if Whisper fallback fires frequently.

---

### 6. Observability

#### 6.1 /health endpoint does not check infrastructure (HIGH)
**File**: `hookcut-backend/app/main.py`, lines 66-68

```python
@app.get("/health")
async def health():
    return {"status": "ok", "version": APP_VERSION}
```

This endpoint always returns 200 as long as the Python process is alive. It does not:
- Test a DB query (even `SELECT 1`)
- Ping Redis
- Check that Celery workers are alive

Railway and load balancers use this endpoint to determine service health. A DB connection pool exhaustion or Redis outage will make all API calls fail while the health endpoint continues to return 200.

**Fix**: Add a `try: db.execute(text("SELECT 1"))` and a `redis_client.ping()` to the health endpoint. Return 503 if either fails.

#### 6.2 No Celery task monitoring (MEDIUM)
There is no Flower deployment, no StatsD integration, and no task queue depth metrics. In production, there is no way to:
- See how many tasks are queued
- Identify stuck/long-running tasks
- Monitor worker memory usage
- Alert on task failure rate

At minimum, a Flower instance should be deployed alongside the worker, or the health endpoint should expose queue depth via `celery_app.control.inspect().active()`.

#### 6.3 Sentry environment and sample rate hardcoded (LOW)
**File**: `hookcut-backend/app/main.py`, lines 27-30

```python
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=0.1,
    environment="production",
)
```

`environment` is hardcoded as `"production"` even when `settings.DEBUG=True`. This causes staging/development Sentry errors to appear in the production environment in Sentry's UI. `traces_sample_rate` should be configurable via `SENTRY_TRACES_SAMPLE_RATE` env var.

#### 6.4 No structured logging (LOW)
All log calls use `logger.info(f"...")` with f-strings. Logs are unstructured plain text. On Railway, logs are streamed to stdout and collected, but there is no JSON log format, no correlation IDs, and no tracing between the web process and Celery worker for a given `session_id`. Structured logging (e.g., `python-json-logger`) with `session_id` in every log record would dramatically improve debuggability.

---

### 7. Dependency Security

#### 7.1 Backend — compatible-release (`~=`) versioning (LOW)
**File**: `hookcut-backend/pyproject.toml`

All dependencies use `~=` (compatible release), meaning `~=0.115` allows `0.115.x` but not `0.116`. This is reasonable but not fully reproducible. A `requirements.lock` file generated by `pip-compile` (pip-tools) with exact hashes would guarantee identical builds across environments.

Notable versions:
- `celery[redis]~=5.4` — Celery 5.4 has known issues with task acks on Redis broker; ensure >= 5.4.2
- `cryptography~=42.0` — Pin to latest 42.x to get security patches; 42.0.0 had CVEs fixed in later 42.x
- `openai~=1.50` — OpenAI client has had breaking changes in 1.x; pinning to a minor is good but a lockfile is better

#### 7.2 Frontend — caret (`^`) versioning (MEDIUM)
**File**: `hookcut-frontend/package.json`

All runtime dependencies use `^` (caret), meaning `npm install` will pull the latest compatible minor/patch. Key risks:
- `framer-motion: ^12.34.4` — Major version is pinned, but 12.x has had animation API changes
- `@sentry/nextjs: ^10.40.0` — Sentry has had breaking changes between minor versions
- `next: 16.1.6` — This is pinned exactly (no `^`), which is correct for the framework

The `package-lock.json` exists and should be committed. CI must use `npm ci` (not `npm install`) to honour the lockfile.

#### 7.3 Remotion in production dependencies (MEDIUM)
`@remotion/cli`, `@remotion/player`, and `remotion` at `^4.0.434` are in `dependencies` (not `devDependencies`). These are used only for pre-rendering marketing demo videos (`remotion:render:*` scripts). Remotion bundles Chromium and is extremely large (~200MB). It should not be installed in production builds.

**Fix**: Move to `devDependencies`. Ensure `npm install --production` or `npm ci --omit=dev` is used in the Vercel build.

---

### 8. Cloudflare Worker

#### 8.1 Hardcoded InnerTube API key (MEDIUM)
**File**: `cloudflare-worker/worker.js`, line 32

```javascript
const INNERTUBE_API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8";
```

This is a well-known public YouTube InnerTube API key (same one used by many open-source YouTube clients). It is not a secret. However, committing any API key to source code is bad practice. YouTube has previously rotated this key, which would break the worker without a code deploy. It should be a Worker environment variable: `env.INNERTUBE_API_KEY`.

#### 8.2 CORS allows all origins (MEDIUM)
**File**: `cloudflare-worker/worker.js`, line 247

```javascript
"Access-Control-Allow-Origin": "*",
```

The worker is protected by an optional API key (`env.API_KEY`). However, with `Allow-Origin: *`, browser-side JavaScript from any domain can call the worker directly (the API key is still checked). This is a low-severity issue since the auth header is still validated, but it means browser devtools will show the endpoint and its response format to curious users. Restrict to the backend's domain if possible.

#### 8.3 fetchViaInnertube is dead code (LOW)
**File**: `cloudflare-worker/worker.js`, line 119

`fetchViaInnertube()` is defined (130+ lines) but never called from `handleTranscript()`. The handler only calls the Android Player API. If this was intended as a fallback, it is not wired up.

#### 8.4 No rate limiting in the worker itself (LOW)
The worker has no per-IP or per-video-ID rate limiting. A Cloudflare Workers free plan has 100,000 requests/day. If the backend scales or if the endpoint is scraped, this quota can be exhausted. Cloudflare's built-in rate limiting rules should be configured on the worker route.

---

### 9. Cost Risks

#### 9.1 No maximum video duration (HIGH)
As detailed in §5.3, there is no upper bound on video length. A 4-hour video would:
- Consume 240 free minutes or 240 minutes of paid quota
- Send potentially 2MB+ of transcript text to Gemini (Gemini 2.5 Flash charges ~$0.075/1M input tokens; 500K tokens ≈ $0.04 per analysis, manageable, but without a cap one malformed/extreme case is unbounded)
- Hold a Celery worker for potentially 10+ minutes
- Store a very large `transcript_text` row in Postgres

**Recommended limit**: 3,600 seconds (1 hour). Raise `VideoTooLongError`.

#### 9.2 No LLM input token guard (MEDIUM)
`HookEngine.analyze()` sends the full transcript to the LLM with no truncation or token pre-check. Gemini 2.5 Flash has a 1M token context window, so it won't error, but cost scales linearly with input. A transcript over ~100K tokens (roughly 1 hour of dense speech) should be chunked or summarized before LLM processing.

#### 9.3 Celery task with no time limit accrues LLM cost (HIGH)
If `run_analysis` has no time limit (§2.1) and the LLM API is slow (e.g., Gemini under heavy load), the task will spin indefinitely, potentially retrying the LLM call 3 times (internal retry logic in `HookEngine`) without releasing the worker. Combined with no task timeout, this creates potential for runaway API spend during provider outages.

#### 9.4 Whisper fallback cost (LOW)
If all 5 primary transcript providers fail, Whisper is used as a last resort. Whisper charges $0.006/minute of audio. A 60-minute video costs $0.36 per fallback. The `FEATURE_WHISPER_FALLBACK: bool = True` default means this runs automatically for all transcript failures. Consider disabling in production until the Cloudflare Worker is deployed and proven reliable.

---

### 10. Additional Minor Issues

#### 10.1 cookies.txt committed to repo (HIGH — ALREADY IN GIT STATUS)
**File**: `hookcut-backend/cookies.txt`, `cookies_slim.txt`, `cookies_trimmed.txt`, `hookcut.nyxpath.com_cookies.txt`

These appear in `git status` as untracked but the files exist on disk. YouTube cookies contain authenticated session tokens. If any of these files are ever committed to the repository, they expose the YouTube account. Confirm these files are in `.gitignore` and audit git history to ensure they were never committed.

#### 10.2 hookcut.db database file on disk
**File**: `hookcut-backend/hookcut.db` (visible in directory listing)

A SQLite database file exists in the backend directory. If this is a development or backup database, it must not be committed to git and must not be copied into the Docker image. Confirm `.gitignore` includes `*.db`.

#### 10.3 Default SQLite fallback in production config
The `DATABASE_URL` default of `sqlite:///hookcut.db` is a footgun. If `DATABASE_URL` is somehow not set in the Railway environment, the validator will catch it at startup (relative path check). However, if `TESTING=true` is set accidentally in production, validation is entirely skipped and the app silently uses SQLite, which Celery workers cannot share with the web process (different file paths in different containers).

#### 10.4 Hardcoded Node path in package.json scripts
**File**: `hookcut-frontend/package.json`

```json
"dev": "... /opt/homebrew/opt/node@22/bin/node ...",
"remotion:studio": "/opt/homebrew/opt/node@22/bin/node ..."
```

The dev script hardcodes a macOS Homebrew Node path. This breaks on any non-macOS developer machine and in CI/CD environments (Vercel build, GitHub Actions). The `"build"` script uses plain `next build` which works fine; only `dev` and remotion scripts are affected.

---

## Prioritized Fix List

### Immediate (Pre-Production Blockers)

1. **Add `soft_time_limit=300, time_limit=360` to `run_analysis` task** — without this, a stuck LLM call can halt all analysis permanently
2. **Fix `start.sh` to fail hard on migration error** — currently swallows all migration failures
3. **Fix `storage.get_download_url` for local mode** — current `127.0.0.1` URL is always broken in Railway production
4. **Add max video duration check in `AnalyzeService.start_analysis`** — no upper bound exposes LLM cost risk
5. **Validate Razorpay/Stripe webhook secrets at startup when payments are enabled** — empty secrets accept all unauthenticated webhooks
6. **Fix `/health` to check DB + Redis** — Railway health routing is blind to infrastructure failures

### Short-Term (Within 1 Sprint)

7. Fix migration 008 to use `batch_alter_table` for SQLite compatibility
8. Add composite index `(status, expires_at)` on `shorts` table
9. Add `USER hookcut` non-root user to Dockerfile
10. Remove hardcoded `hookcut_dev` password from `docker-compose.prod.yml`
11. Add resource limits to docker-compose services
12. Move Remotion packages to `devDependencies`
13. Configure Sentry environment from `settings.DEBUG` flag

### Medium-Term (Operational Improvements)

14. Add a Celery task failure audit table or external DLQ
15. Deploy Flower for Celery monitoring
16. Add structured logging with session_id correlation
17. Pin frontend dependencies (use `npm shrinkwrap` or Renovate with exact pinning)
18. Add `workers_dev = false` and route binding to `wrangler.toml`
19. Add per-IP rate limiting rules to the Cloudflare Worker route
20. Wire up `fetchViaInnertube` as a fallback in the CF worker or remove the dead code
