# HookCut — Production QA Audit Report

**Date**: 2026-03-07
**Auditors**: Claude Code (multi-pass: static analysis × 5, live API testing, DB audit, infra deep-dive, UI read-through)
**Target**: https://hookcut.nyxpath.com / https://api.hookcut.nyxpath.com
**Verdict**: **NOT production-ready** — 19 Critical issues must be resolved before any paying user onboards.

---

## Severity Summary

| Severity | Count | Pre-Launch Blocker? |
|----------|-------|---------------------|
| CRITICAL | 19 | YES — data breaches, financial fraud, full crashes |
| HIGH | 44 | YES — significant risk to users and finances |
| MEDIUM | 37 | SOON — degraded experience or intermittent failures |
| LOW | 24 | EVENTUALLY — polish, resilience, best practices |
| **Total** | **124** | |

---

## Section 1 — CRITICAL Issues

---

### CRIT-01 — V0 Mode Active in Production: Entire API Is Unauthenticated
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/middleware/auth.py:32-48`, `hookcut-backend/app/config.py`, Railway environment variables
**Evidence**: `GET /api/user/history` returns 54 real sessions. `GET /api/user/balance` returns live balance. `POST /api/analyze` starts real analysis — all with zero auth token.
**Impact**: Every protected API operation is public. Any person on the internet can read all user data, initiate analysis jobs at your Gemini cost, and manipulate their own balance.
**Recommended Solution**: Set `FEATURE_V0_MODE=False` in Railway environment variables. This single change resolves CRIT-01, CRIT-08, HIGH-30, and multiple IDOR vulnerabilities at their root cause.

---

### CRIT-02 — v0-Grant Endpoint: 9,999 Free Minutes, No Authentication
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/routers/billing.py:73-84`
**Evidence**:
```
POST /api/billing/v0-grant  (no token)
→ {"balance": {"paid": 9999.0, "payg": 9999.0, "total": 20002.1}}
```
Repeatable infinitely. ~333 hours of Gemini API usage per call.
**Impact**: Unlimited free credits for anyone. Unbounded Gemini API cost.
**Recommended Solution**: Remove this endpoint entirely before launch. If needed for testing, protect with `Depends(get_admin_user)` and move to an admin-only route.

---

### CRIT-03 — IDOR: Session Hooks Readable Without Auth or Ownership Check
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/routers/analysis.py:64-98`
**Evidence**: `GET /api/sessions/{any-uuid}/hooks` returns 5 full AI-scored hooks for any session with no token and no ownership verification.
**Impact**: Private AI analysis, hook scores, improvement suggestions, and hook text are readable by anyone who knows or guesses a session UUID. UUIDs are returned in API responses, making them enumerable.
**Recommended Solution**:
```python
@router.get("/sessions/{session_id}/hooks")
async def get_hooks(session_id: str, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    session = db.get(AnalysisSession, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=404)
```
Apply the same pattern to `regenerate` and `select_hooks`.

---

### CRIT-04 — IDOR: Short Endpoints Have No Auth or Ownership Check
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/routers/shorts.py:32-56`
**Impact**: Anyone can read metadata, download the video file, or **permanently discard** another user's generated Short.
**Recommended Solution**: Add `user_id: str = Depends(get_current_user_id)` to all three short endpoints (`get_short`, `get_download_url`, `discard_short`). Verify `short.session.user_id == user_id` before operating.

---

### CRIT-05 — Webhook Replay Attack: No Idempotency on Payment Events
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/services/webhook_service.py:10-90`
**Evidence**: Both Stripe and Razorpay webhook handlers provision credits on every delivery. Stripe retries failed webhooks for 3 days.
**Impact**: One legitimate payment → unlimited credit grants via replay. Financial fraud risk.
**Recommended Solution**: Create a `processed_webhooks(provider VARCHAR, event_id VARCHAR, processed_at TIMESTAMP, PRIMARY KEY (provider, event_id))` table. Before processing: `SELECT 1 WHERE provider=? AND event_id=?`. If exists, return 200 immediately. After processing: `INSERT INTO processed_webhooks ...`.

---

### CRIT-06 — Stripe Metadata `minutes` Field Has No Cap
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/services/webhook_service.py:27-28`
**Evidence**:
```python
minutes = int(metadata.get("minutes", 100))  # no max cap
```
**Impact**: A misconfigured Stripe product or tampered webhook payload can provision unlimited minutes.
**Recommended Solution**:
```python
MAX_MINUTES_PER_PURCHASE = 10000  # largest legitimate package
minutes = min(int(metadata.get("minutes", 100)), MAX_MINUTES_PER_PURCHASE)
```

---

### CRIT-07 — `.env` Write Not Atomic: All Secrets Can Be Wiped
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/services/admin_service.py:991-1016`
**Impact**: `open(env_path, "w")` truncates the file immediately. If the process is killed before `writelines()` completes, the entire `.env` is empty — all secrets, API keys, DB credentials wiped.
**Recommended Solution**:
```python
import tempfile, os
tmp_path = env_path + ".tmp"
with open(tmp_path, "w") as f:
    f.writelines(new_lines)
os.replace(tmp_path, env_path)  # atomic on POSIX
get_settings.cache_clear()
get_provider.cache_clear()
```

---

### CRIT-08 — Rate Limiting Broken: 12 Requests, Zero 429s
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/middleware/rate_limit.py`, Railway Redis configuration
**Evidence**: 12 consecutive `POST /api/analyze` requests, all HTTP 200, no 429.
**Root Cause**: Rate limiter keys to `user.id` which is `v0_local_user` for all unauthenticated requests — every anonymous request shares one bucket that never fills up. Also: Redis `INCR` + `EXPIRE` are not in the same transaction (window slides).
**Recommended Solution**: Fix CRIT-01 first. Then use a Lua script for atomic INCR+EXPIRE. Use IP-based key as fallback for unauthenticated requests:
```lua
local key = KEYS[1]; local limit = tonumber(ARGV[1]); local window = tonumber(ARGV[2])
local count = redis.call("INCR", key)
if count == 1 then redis.call("EXPIRE", key, window) end
if count > limit then return 0 end
return 1
```

---

### CRIT-09 — Swagger UI Exposed in Production
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/main.py` (FastAPI constructor args)
**Evidence**: `/docs`, `/redoc`, `/openapi.json` all return HTTP 200 in production.
**Impact**: Full API surface, all endpoint signatures, all request schemas, and an interactive testing console are visible to anyone. Removes all security-through-obscurity.
**Recommended Solution**:
```python
app = FastAPI(
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)
```

---

### CRIT-10 — React Rules of Hooks Violation in Dashboard: Production Crash
**Severity**: CRITICAL
**Files Affected**: `hookcut-frontend/src/app/dashboard/page.tsx:~247`
**Evidence**: `useMemo` called after two conditional early `return` statements (`if authStatus === "loading"`, `if authStatus === "unauthenticated"`). React throws "Rendered more hooks than during previous render" on every auth state transition.
**Impact**: Dashboard crashes for 100% of users on first load. The core product feature is inaccessible.
**Recommended Solution**: Move ALL `useMemo`, `useCallback`, and `useState` calls unconditionally to the top of the component, above all conditional returns. The conditionals must come after all hook calls.

---

### CRIT-11 — React Rules of Hooks Violation in url-step.tsx: Framer Motion Crash
**Severity**: CRITICAL
**Files Affected**: `hookcut-frontend/src/components/url-step.tsx:~104`
**Evidence**: `useTransform` (a React hook from framer-motion) is called inside a JSX `style={{...}}` expression — i.e., conditionally, inside a render return.
**Impact**: Corrupts hook call order on every render. Causes render loops or crashes in URL input step, blocking the primary user workflow.
**Recommended Solution**:
```tsx
// Before JSX return:
const borderOpacity = useTransform(scrollY, [0, 100], [0, 1]);
const borderStyle = useTransform(scrollY, [0, 100], ['0px', '1px solid ...']);
// Then use in JSX: style={{ opacity: borderOpacity }}
```

---

### CRIT-12 — All Supabase Tables Have RLS Disabled
**Severity**: CRITICAL
**Files Affected**: Supabase PostgreSQL (project `hetfjabbzxzhjyztlwoe`) — all 13 public tables
**Evidence**: All 13 tables confirmed `rowsecurity = false` via Supabase MCP query.
**Impact**: If the Supabase anon key leaks (e.g., exposed in a frontend bundle or accidentally committed), ALL user data — balances, sessions, hooks, transactions, short metadata — is fully readable and writable with no database-level protection.
**Recommended Solution**:
```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_only" ON users TO service_role USING (true) WITH CHECK (true);
-- Repeat for: credit_balances, analysis_sessions, hooks, shorts, transactions, learning_logs
-- anon role gets no policy (default deny)
```

---

### CRIT-13 — `/api/storage/{file_key}` Has Zero Authentication
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/services/storage.py:37`, `hookcut-backend/app/routers/` (storage endpoint)
**Impact**: Any unauthenticated request can download any stored Short video file by guessing the file key (UUIDs, readable from the unauthenticated history endpoint).
**Recommended Solution**: Add `user_id: str = Depends(get_current_user_id)` to `GET /api/storage/{file_key}`. Join through `shorts → sessions` to verify `session.user_id == user_id`.

---

### CRIT-14 — `start.sh` Swallows Migration Failure: App Boots on Broken Schema
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/start.sh:12`
**Evidence**:
```bash
alembic upgrade head 2>&1 || echo "WARNING: Alembic migration failed (continuing anyway)"
```
**Impact**: If migrations fail (DB not ready, schema conflict, network error), uvicorn still starts. Missing columns from migrations 007/008 cause `UndefinedColumn` errors on every real request. The deploy appears green while requests are failing.
**Recommended Solution**: Remove the `||` fallback entirely. `set -e` at line 1 will terminate the script and Railway will mark the deploy as failed:
```bash
echo "=== Running Alembic migrations ==="
alembic upgrade head
```

---

### CRIT-15 — Empty Webhook Secret Bypasses HMAC Validation
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/services/webhook_service.py`, `hookcut-backend/app/config.py`
**Impact**: If `STRIPE_WEBHOOK_SECRET` or `RAZORPAY_WEBHOOK_SECRET` are unset (empty string), HMAC comparison against an empty-string secret can silently pass, accepting any payload as authenticated.
**Recommended Solution**: Add startup validation in `app/main.py` or `config.py`:
```python
if not settings.STRIPE_WEBHOOK_SECRET:
    raise ValueError("STRIPE_WEBHOOK_SECRET must be set in production")
```

---

### CRIT-16 — No Maximum Video Duration Enforced: Unbounded LLM Cost
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/app/services/analyze_service.py`, `hookcut-backend/app/exceptions.py` (`VideoTooLongError` exists but is never raised)
**Impact**: A 10-hour YouTube video passes all validation, triggers full transcript download (~200k tokens), and submits a $0.10+ Gemini request per analysis. With no rate limiting (CRIT-08), this is a cost explosion vector.
**Recommended Solution**:
```python
# In analyze_service.py, after fetching video metadata:
MAX_VIDEO_MINUTES = int(os.getenv("MAX_VIDEO_MINUTES", "60"))
if video_duration_seconds > MAX_VIDEO_MINUTES * 60:
    raise VideoTooLongError(f"Video exceeds {MAX_VIDEO_MINUTES}-minute limit")
```

---

### CRIT-17 — YouTube InnerTube API Key Hardcoded in Source Code
**Severity**: CRITICAL
**Files Affected**: `cloudflare-worker/worker.js:32`
**Evidence**: `const INNERTUBE_API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8";` committed in plaintext.
**Impact**: (1) This key is committed to git history permanently. (2) If Google restricts it, the worker silently breaks. (3) Normalizes committing secrets in source. GitHub secret scanning will flag it.
**Recommended Solution**: Move to a Cloudflare Worker secret:
```bash
wrangler secret put INNERTUBE_API_KEY
```
```js
// worker.js — access via env parameter:
`https://www.youtube.com/youtubei/v1/player?key=${env.INNERTUBE_API_KEY}`
```

---

### CRIT-18 — `alembic.ini` Contains Hardcoded Database Password
**Severity**: CRITICAL
**Files Affected**: `hookcut-backend/alembic.ini:3`
**Evidence**: `sqlalchemy.url = postgresql://postgres:password@localhost:5432/hookcut` committed in the repo.
**Impact**: Password is permanently in git history. Any developer running `alembic` without `DATABASE_URL` set connects to this URL.
**Recommended Solution**:
```ini
sqlalchemy.url = postgresql://OVERRIDE_VIA_DATABASE_URL_ENV_VAR
```
The `alembic/env.py` already correctly overrides from `DATABASE_URL` — this just prevents the fallback from being a real credential.

---

### CRIT-19 — Cloudflare Worker CORS Open (`*`) + Authentication Optional
**Severity**: CRITICAL
**Files Affected**: `cloudflare-worker/worker.js:19-24, 246-250`
**Evidence**: `"Access-Control-Allow-Origin": "*"` + `if (env.API_KEY)` — auth only enforced if the secret was deployed.
**Impact**: (1) If `API_KEY` was never set in wrangler secrets, the worker is fully unauthenticated — any page on the internet can call it. (2) Open CORS allows third-party sites to proxy transcripts through your Cloudflare worker at your cost.
**Recommended Solution**:
```js
// Make API_KEY mandatory
if (!env.API_KEY) return json({ error: "Worker not configured" }, 503);
if (auth !== `Bearer ${env.API_KEY}`) return json({ error: "Unauthorized" }, 401);

// Restrict CORS
function corsHeaders(requestOrigin) {
  const allowed = ["https://api.hookcut.nyxpath.com", "https://hookcut.nyxpath.com"];
  const origin = allowed.includes(requestOrigin) ? requestOrigin : allowed[0];
  return { "Access-Control-Allow-Origin": origin, ... };
}
```

---

## Section 2 — HIGH Risk Issues

---

### HIGH-01 — `/api/auth/sync` Accepts Caller-Controlled Email as Query Parameter
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/routers/billing.py:62-68`
**Impact**: Caller can claim any email including `admin@hookcut.com`. Email appears in server access logs.
**Recommended Solution**: Derive email from the Google OAuth JWT server-side. Move to request body. Use `EmailStr` for validation.

---

### HIGH-02 — Short Poller Has No Max Poll Count: Infinite Loop
**Severity**: HIGH
**Files Affected**: `hookcut-frontend/src/hooks/useShortPoller.ts`
**Impact**: Shorts stuck in `queued` or `processing` (confirmed: many shorts permanently stuck in DB) poll forever — memory leak, infinite network requests, mobile battery drain.
**Recommended Solution**:
```ts
const MAX_POLLS = 120; // 10 minutes at 5s intervals
if (pollCount >= MAX_POLLS) {
  setError("Short generation timed out. Please try again.");
  return;
}
```

---

### HIGH-03 — `secure: false` on OAuth Cookies in Production
**Severity**: HIGH
**Files Affected**: `hookcut-frontend/src/lib/auth.ts:~35`
**Impact**: PKCE state and session cookies transmitted over HTTP. Interception risk on any non-HTTPS path or network.
**Recommended Solution**:
```ts
secure: process.env.NODE_ENV === "production"
```

---

### HIGH-04 — Admin Routes Accessible to Any Authenticated User (Client-Side Check Only)
**Severity**: HIGH
**Files Affected**: `hookcut-frontend/src/proxy.ts` (middleware), `hookcut-frontend/src/app/admin/layout.tsx`
**Impact**: Any logged-in user can navigate to `/admin/*`. The role check only fires in `layout.tsx` on the client — there is a window of admin UI access.
**Recommended Solution**: Check admin role in `proxy.ts` middleware. Store `isAdmin` in the NextAuth JWT token during the `jwt` callback, then read it in the middleware:
```ts
const token = await getToken({ req });
if (pathname.startsWith("/admin") && !token?.isAdmin) {
  return NextResponse.redirect("/");
}
```

---

### HIGH-05 — Dashboard Link Missing for Non-Admin Authenticated Users
**Severity**: HIGH
**Files Affected**: `hookcut-frontend/src/components/header.tsx:~146`
**Impact**: Regular users have no navigation link to their own dashboard — they must know the URL.
**Recommended Solution**:
```tsx
{status === "authenticated" && (
  <Link href="/dashboard">Dashboard</Link>
)}
```

---

### HIGH-06 — Short Generation Failures Silently Discarded: Spinner Forever
**Severity**: HIGH
**Files Affected**: `hookcut-frontend/src/components/short-card.tsx`, `hookcut-frontend/src/hooks/useShortPoller.ts`
**Impact**: `useShortPoller` sets `error` state but `ShortCard` never reads it. Failed shorts show a permanent loading spinner with no error message.
**Recommended Solution**: In `short-card.tsx`, consume the `error` return from `useShortPoller`:
```tsx
const { short, error } = useShortPoller(shortId);
if (error) return <div className="error-state">Generation failed. <button onClick={retry}>Retry</button></div>
```

---

### HIGH-07 — Celery Analysis Task Has No Time Limit: Worker Hangs Indefinitely
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/tasks/analyze_task.py`, `hookcut-backend/app/tasks/celery_app.py`
**Impact**: A hung yt-dlp call or stalled LLM request blocks a Celery worker forever. With 2 workers, 2 stuck tasks = complete work stoppage.
**Recommended Solution**:
```python
@celery_app.task(bind=True, max_retries=0, soft_time_limit=600, time_limit=660)
def run_analysis(self, ...):
```
Also add globally in `celery_app.py`:
```python
task_soft_time_limit=600,
task_time_limit=660,
```

---

### HIGH-08 — LLM Providers (Anthropic, OpenAI) Have No Timeout
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/llm/anthropic_provider.py:17-33`, `hookcut-backend/app/llm/openai_provider.py:17-30`
**Impact**: A stalled API call blocks a worker thread indefinitely.
**Recommended Solution**:
```python
# Anthropic:
response = client.messages.create(..., timeout=120)
# OpenAI:
response = client.chat.completions.create(..., timeout=120)
```

---

### HIGH-09 — Transcript Inserted Into LLM Prompt With No Length Cap
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/llm/prompts/hook_identification.py:26-75`
**Impact**: A 4-hour video = ~100k tokens. No truncation. Context overflow and Gemini cost explosion.
**Recommended Solution**:
```python
MAX_TRANSCRIPT_CHARS = 60_000  # ~15k tokens
if len(transcript) > MAX_TRANSCRIPT_CHARS:
    logger.warning(f"Transcript truncated from {len(transcript)} to {MAX_TRANSCRIPT_CHARS} chars")
    transcript = transcript[:MAX_TRANSCRIPT_CHARS] + "\n[TRANSCRIPT TRUNCATED]"
```

---

### HIGH-10 — `time.sleep(30)` Blocks Celery Worker During LLM Retry
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/services/hook_engine.py:70`
**Impact**: One LLM retry = one Celery worker dead for 30 seconds. With 2 workers and 2 retries each, all work stops for 60 seconds.
**Recommended Solution**:
```python
# Replace:
time.sleep(RETRY_DELAYS[attempt])
# With:
raise self.retry(countdown=RETRY_DELAYS[attempt])
```

---

### HIGH-11 — Credit Check/Deduct Race Condition: Balance Can Go Negative
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/services/analyze_service.py:104-130`, `hookcut-backend/app/services/credit_manager.py`
**Impact**: Two concurrent requests both pass the balance check, both deduct, resulting in negative balance and free analysis.
**Recommended Solution**: Use `SELECT ... FOR UPDATE` inside `deduct()`:
```python
balance = db.execute(
    select(CreditBalance).where(CreditBalance.user_id == user_id).with_for_update()
).scalar_one()
```

---

### HIGH-12 — Double Refund Race in `refund_and_fail`
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/services/credit_manager.py:183-206`
**Impact**: Two concurrent task failures for the same session can both execute the refund.
**Recommended Solution**:
```python
result = db.execute(
    update(AnalysisSession)
    .where(AnalysisSession.id == session_id, AnalysisSession.credits_refunded == False)
    .values(credits_refunded=True)
)
if result.rowcount == 0:
    return  # already refunded
# proceed with credit addition
```

---

### HIGH-13 — DB Connection Pool Exhaustion Under Load
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/models/base.py:23`
**Impact**: `pool_size=5`, no `max_overflow`. With 4 Celery workers each maintaining their own pool, connections exhaust Supabase's free tier limit.
**Recommended Solution**:
```python
engine = create_engine(url, pool_size=3, max_overflow=7, pool_timeout=30, pool_pre_ping=True)
```

---

### HIGH-14 — Missing FK on `transactions.session_id`
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/models/billing.py:19`
**Impact**: Orphaned transaction records accumulate with no referential integrity.
**Recommended Solution**:
```python
session_id = Column(String(36), ForeignKey("analysis_sessions.id", ondelete="SET NULL"), nullable=True)
```

---

### HIGH-15 — Debug-Sentry Endpoint: Unauthenticated DoS
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/main.py:70-73`
**Impact**: `GET /debug-sentry` raises `ValueError` unconditionally when `DEBUG=True`. Any caller can spam error logs. Confirmed accessible when `DEBUG=True`.
**Recommended Solution**: Remove entirely. If needed: add auth guard and only register when `DEBUG=True`.

---

### HIGH-16 — Simultaneous First-Login Race: Duplicate User / Unhandled 500
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/services/billing_service.py:125-153`
**Impact**: Two concurrent first-login OAuth callbacks for the same email cause two `INSERT` attempts. `email UNIQUE` constraint catches it but the unhandled `IntegrityError` returns HTTP 500.
**Recommended Solution**: Use upsert pattern:
```python
from sqlalchemy.dialects.postgresql import insert
stmt = insert(User).values(...).on_conflict_do_update(index_elements=["email"], set_={"updated_at": now})
db.execute(stmt)
```

---

### HIGH-17 — Temp Directories Leak on Task Failure: Disk Fill Risk
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/tasks/generate_short_task.py:105-107`, `hookcut-backend/app/services/short_generator.py`
**Impact**: `shutil.rmtree(work_dir)` only called on success path. Every failed short generation leaks 100MB–2GB of video data. On Railway free tier, disk fills over time.
**Recommended Solution**:
```python
try:
    result = ShortGenerator(...).generate(...)
finally:
    shutil.rmtree(work_dir, ignore_errors=True)
```

---

### HIGH-18 — Stripe Webhook Body Buffered Before Signature Check
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/routers/billing.py:89-98`
**Impact**: Large malicious payloads are buffered before the missing signature header is detected.
**Recommended Solution**: Check `stripe-signature` header presence first, return 400 immediately if missing.

---

### HIGH-19 — Blocking Stripe SDK Call Inside Async Event Loop
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/services/billing_service.py:195-218`
**Impact**: Synchronous Stripe Python SDK called in `async def` route blocks the entire FastAPI event loop.
**Recommended Solution**:
```python
import anyio
event = await anyio.to_thread.run_sync(
    lambda: stripe.Webhook.construct_event(payload, sig, secret)
)
```

---

### HIGH-20 — Admin Bulk Export Returns 10,000 Records Synchronously
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/services/admin_service.py:350-394`
**Impact**: 10,000 rows of `before_state`/`after_state` JSON blobs in one HTTP response. Memory exhaustion and gateway timeout.
**Recommended Solution**: Cap at 1,000 per page. Use `StreamingResponse` for large exports or background task + download URL pattern.

---

### HIGH-21 — NARM Analysis Runs Synchronously: 3-Minute HTTP Request
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/services/admin_service.py:1040-1266`
**Impact**: `POST /admin/narm/analyze` blocks for up to 180 seconds (Gemini timeout). Gateway and reverse proxy will kill the connection.
**Recommended Solution**: Move to background Celery task. Return `{"task_id": "..."}` immediately. Admin polls for completion.

---

### HIGH-22 — `set_api_key` Accepts 10MB API Key
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/schemas/admin.py:179-181`
**Impact**: Unbounded `api_key: str` field. A 10MB request body passes Pydantic validation and gets written to `.env`.
**Recommended Solution**:
```python
api_key: str = Field(..., min_length=10, max_length=512, pattern=r'^[A-Za-z0-9_\-]+$')
```

---

### HIGH-23 — `auth/sync` Does Not Validate Email Format
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/routers/billing.py:62-68`
**Impact**: Any string accepted as email. Combined with HIGH-01, this allows arbitrary strings to reach the users table.
**Recommended Solution**: `email: EmailStr` (Pydantic validates format).

---

### HIGH-24 — Celery Result TTL 5 Minutes: Results Expire Before Frontend Polls
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/tasks/celery_app.py:31`
**Evidence**: `result_expires=300` (5 minutes). Comment says "Railway free Redis has ~25MB limit" — but task result payloads are small JSON blobs.
**Impact**: Analysis of a 10+ minute video can take longer than 5 minutes. Results expire, leaving sessions stuck with no error.
**Recommended Solution**:
```python
result_expires=3600,  # 1 hour
```

---

### HIGH-25 — Payment Parameters Sent as URL Query Strings
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/routers/billing.py:29-46`
**Impact**: `plan_tier`, `minutes` appear in server access logs, browser history, and referrer headers.
**Recommended Solution**: Move all payment parameters to Pydantic request body schemas.

---

### HIGH-26 — No Max Length on `youtube_url` Field
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/schemas/analysis.py:7`
**Impact**: A 10,000-character URL passes validation and reaches the network layer.
**Recommended Solution**: `youtube_url: str = Field(..., max_length=2048)`

---

### HIGH-27 — Missing Index on `analysis_sessions.task_id`: Full Table Scan per Callback
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/models/session.py`, database
**Impact**: Every Celery task completion looks up session by `task_id`. No index = full table scan. Performance degrades linearly with user growth.
**Recommended Solution**: Add via Alembic migration:
```sql
CREATE UNIQUE INDEX idx_sessions_task_id ON analysis_sessions (task_id);
```

---

### HIGH-28 — Scheduled Cleanup Uses OFFSET Pagination: O(N²) at Scale
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/tasks/scheduled.py:30-47, 54-90`
**Impact**: `LIMIT/OFFSET` requires PostgreSQL to scan all prior rows. At 100,000 users: `OFFSET 80000` reads 80,000 rows to skip them.
**Recommended Solution**: Keyset pagination:
```python
WHERE id > last_seen_id ORDER BY id LIMIT 100
```

---

### HIGH-29 — `updated_at` Not Updated on Bulk SQL Operations
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/models/user.py:18-19`
**Impact**: SQLAlchemy ORM-level `onupdate` doesn't fire on `db.execute(update(...))`. `updated_at` silently stale after admin role changes.
**Recommended Solution**: Either always use ORM object updates, or add a PostgreSQL `BEFORE UPDATE` trigger on the `users` table.

---

### HIGH-30 — `localhost:3000` in CORS Origins in Production
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/main.py:46-48`
**Impact**: V0 mode adds `http://localhost:3000` to production CORS origins. Any webpage running locally can make credentialed cross-origin API calls.
**Recommended Solution**: Resolved by fixing CRIT-01 (disable V0 mode). Verify `CORS_ORIGINS` Railway env var after.

---

### HIGH-31 — No Backend Security Response Headers
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/main.py` (middleware registration)
**Evidence**: Live test: no `X-Frame-Options`, `X-Content-Type-Options`, `HSTS`, or `CSP` on `api.hookcut.nyxpath.com`.
**Recommended Solution**:
```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response
app.add_middleware(SecurityHeadersMiddleware)
```

---

### HIGH-32 — Razorpay Webhook Returns HTTP 500 on Invalid Signature
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/routers/billing.py` (Razorpay webhook handler)
**Impact**: Invalid/missing signature causes an unhandled exception → HTTP 500 with stack trace. Leaks internal error details to attackers.
**Recommended Solution**: Catch `InvalidStateError` / `hmac.compare_digest` failure and return `JSONResponse({"detail": "Invalid signature"}, status_code=400)`.

---

### HIGH-33 — SSRF via Cobalt API Redirect URLs
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/utils/ffmpeg_commands.py` (Cobalt API call)
**Impact**: Cobalt API response URL fetched with `follow_redirects=True`. A compromised Cobalt response could redirect to internal AWS metadata, Redis, or internal services.
**Recommended Solution**: Validate Cobalt-returned URL is `https://` and domain-matches expected Cobalt endpoints. Set `follow_redirects=False`.

---

### HIGH-34 — Docker Container Runs as Root
**Severity**: HIGH
**Files Affected**: `hookcut-backend/Dockerfile` (no `USER` directive)
**Impact**: yt-dlp and FFmpeg both process untrusted external URLs/video data. Any path traversal or RCE CVE in these tools runs as UID 0.
**Recommended Solution**:
```dockerfile
RUN groupadd -r hookcut && useradd -r -g hookcut -d /app hookcut \
    && chown -R hookcut:hookcut /app /tmp/hookcut
USER hookcut
```

---

### HIGH-35 — Source Code Bind-Mounted in `docker-compose.prod.yml`
**Severity**: HIGH
**Files Affected**: `docker-compose.prod.yml:33, 48`
**Impact**: `volumes: - ./hookcut-backend:/app` mounts local source over the built image. Local `.env` files inside the directory become readable in the container. Docker build hardening is bypassed at runtime.
**Recommended Solution**: Remove all source bind mounts from the prod compose. Only mount persistent data volumes (`/tmp/hookcut`).

---

### HIGH-36 — `railway.toml` Missing Health Check Path
**Severity**: HIGH
**Files Affected**: `hookcut-backend/railway.toml`
**Impact**: Railway marks service healthy the moment the TCP port opens — even if migrations are still running. Traffic is routed before the app is ready, causing 500s during every deploy.
**Recommended Solution**:
```toml
[deploy]
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
healthcheckPath = "/api/health"
healthcheckTimeout = 30
```

---

### HIGH-37 — All Python Dependencies Use Floating Version Specifiers: No Lockfile
**Severity**: HIGH
**Files Affected**: `hookcut-backend/pyproject.toml:7-29`
**Impact**: `celery~=5.4` allows any `5.x >= 5.4`. A patch release with a breaking change or CVE is silently picked up on next Railway build. No lockfile means builds are not reproducible.
**Recommended Solution**: Add a `requirements.lock.txt` via `pip-compile`:
```bash
pip install pip-tools && pip-compile pyproject.toml -o requirements.lock.txt
```
Use lockfile in Dockerfile: `RUN pip install --no-cache-dir -r requirements.lock.txt`

---

### HIGH-38 — Procfile Beat + Worker Co-Location: Double-Firing of Scheduled Tasks
**Severity**: HIGH
**Files Affected**: `hookcut-backend/Procfile`
**Impact**: If Railway runs `beat` and `worker` as co-located processes (or if a rolling deploy creates two beat instances briefly), scheduled tasks (`cleanup_expired_files`, free-credit reset) fire twice. Could grant duplicate free credits or double-delete files.
**Recommended Solution**: Use Redis-based locking (`celery-redbeat`) which prevents concurrent beat instances. Or combine beat into the worker: `celery -A app.tasks.celery_app worker --beat --concurrency=2`.

---

### HIGH-39 — Migration 008 Breaks SQLite: Missing `batch_alter_table`
**Severity**: HIGH
**Files Affected**: `hookcut-backend/alembic/versions/008_widen_hook_columns.py`
**Impact**: Direct `op.alter_column()` fails on SQLite. Local dev/CI running tests against SQLite cannot run `alembic upgrade head`, breaking the local development workflow and CI migration replay.
**Recommended Solution**:
```python
def upgrade() -> None:
    with op.batch_alter_table("hooks") as batch_op:
        batch_op.alter_column("hook_type", type_=sa.Text(), existing_nullable=False)
        batch_op.alter_column("funnel_role", type_=sa.Text(), existing_nullable=False)
```

---

### HIGH-40 — Redis Exposed on Host Port 6379 Without Authentication
**Severity**: HIGH
**Files Affected**: `docker-compose.prod.yml:15-17`
**Impact**: Any process on the Docker host can read/write Celery task results, inject task arguments, and execute Redis `CONFIG SET` persistence attacks.
**Recommended Solution**: Remove port mapping entirely. Use `expose: ["6379"]` (internal only). Add `--requirepass ${REDIS_PASSWORD}`:
```yaml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}
  expose: ["6379"]
```

---

### HIGH-41 — `docker-compose.prod.yml` Hardcoded Weak DB Password
**Severity**: HIGH
**Files Affected**: `docker-compose.prod.yml` (POSTGRES_PASSWORD)
**Evidence**: `POSTGRES_PASSWORD: hookcut_dev` committed in repo.
**Recommended Solution**: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}` — load from `.env` file excluded from git.

---

### HIGH-42 — Docker Base Image Unpinned: Non-Reproducible Builds
**Severity**: HIGH
**Files Affected**: `hookcut-backend/Dockerfile:1`
**Impact**: `FROM python:3.12-slim` floats to latest `3.12.x`. Security scanners cannot verify the image digest. A breaking patch may surface silently.
**Recommended Solution**: `FROM python:3.12.9-slim-bookworm` — pin the patch version at minimum.

---

### HIGH-43 — Node.js Version in Dockerfile Is EOL (Node 18 from apt)
**Severity**: HIGH
**Files Affected**: `hookcut-backend/Dockerfile:9`
**Impact**: `apt-get install -y nodejs` installs Node 18 (EOL April 2025). yt-dlp's JS challenge support may require a newer Node. Running EOL Node in production is a security exposure.
**Recommended Solution**:
```dockerfile
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs
```

---

### HIGH-44 — Celery `task_reject_on_worker_lost` Not Set: Tasks Disappear on Worker Crash
**Severity**: HIGH
**Files Affected**: `hookcut-backend/app/tasks/celery_app.py:29`
**Impact**: `task_acks_late=True` is set (correct) but without `task_reject_on_worker_lost=True`, a SIGKILL'd worker can cause task messages to not be re-queued for minutes. Sessions stay stuck in `analyzing` state.
**Recommended Solution**:
```python
task_acks_late=True,
task_reject_on_worker_lost=True,
```

---

## Section 3 — Medium Issues

| # | Location | Files Affected | Issue | Recommended Solution |
|---|----------|---------------|-------|---------------------|
| MED-01 | `rate_limit.py:51` | `app/middleware/rate_limit.py` | INCR+EXPIRE not atomic — window slides and resets on each request | Use Lua script: `INCR key; if count==1 then EXPIRE key window end` |
| MED-02 | `gemini_provider.py:35` | `app/llm/gemini_provider.py` | 180s Gemini timeout × 3 cascade = 540s (exceeds task limit) | Set `timeout=120` per call; max cascade 3 × 120s = 360s, within 600s task limit |
| MED-03 | `gemini_provider.py:24` | `app/llm/gemini_provider.py` | `maxOutputTokens = max_tokens * 2` with no upper guard | Add `max(min(max_tokens * 2, 8192), 1024)` |
| MED-04 | `caption_cleanup.py:3` | `app/llm/caption_cleanup.py` | Hook text embedded verbatim in follow-up LLM prompt — prompt injection from LLM output | Sanitize LLM output before re-embedding: strip control chars, limit to alphanumeric/punctuation |
| MED-05 | `provider.py:30` | `app/llm/provider.py` | `@lru_cache` on provider — API key updated via `set_api_key` doesn't take effect until restart | Already partially fixed (cache cleared in admin_service). Verify `get_provider.cache_clear()` is called after key write |
| MED-06 | `transcript.py:268` | `app/llm/transcript.py` | 9 hardcoded Piped/Invidious instances — no circuit breaker, stale list | Add health check and remove instances that return 5xx > 50% of time |
| MED-07 | `short_generator.py:67` | `app/services/short_generator.py` | `ThreadPoolExecutor` shares SQLAlchemy `Session` — not thread-safe | Pass a new `db` session to each thread, or execute serially |
| MED-08 | `analytics.py:8` | `app/utils/analytics.py` | `_posthog_client` global not thread-safe at initialization | Use `threading.Lock()` around initialization |
| MED-09 | `admin_service.py:480` | `app/services/admin_service.py` | Rule key auto-assignment uses lexicographic max — `Z2 > Z10` | Use integer parsing: `max(int(k[1:]) for k in rule_keys) + 1` |
| MED-10 | `admin_service.py:700` | `app/services/admin_service.py` | `seed_rules` aborts if ANY rules exist — partial seeds not resumable | Use upsert pattern on `(rule_key, version)` unique key |
| MED-11 | `narm_insights` table | `alembic/versions/007_add_admin_tables.py:67` | `confidence` column is `VARCHAR(20)` but code uses it as float | Add migration: `ALTER TABLE narm_insights ALTER COLUMN confidence TYPE FLOAT USING confidence::float` |
| MED-12 | `analysis_sessions` table | `app/models/session.py` | `task_id` has no UNIQUE constraint — two sessions can share a task_id | `CREATE UNIQUE INDEX idx_sessions_task_id ON analysis_sessions (task_id);` |
| MED-13 | `hooks/shorts/transactions` | `app/models/` | No `updated_at` column on these tables | Add `updated_at = Column(DateTime, onupdate=datetime.utcnow)` in a migration |
| MED-14 | `user_service.py` | `app/services/user_service.py` | Two DB queries (count + data) for history — extra round trip | Use window function `COUNT(*) OVER()` to get total in same query |
| MED-15 | `analyze_task.py:108` | `app/tasks/analyze_task.py` | Redundant SELECT after flush | Remove; use already-fetched session object |
| MED-16 | `transcript.py Whisper` | `app/llm/transcript.py` | Downloads full audio before size check — 2GB possible | Check video duration first; reject >60min before download |
| MED-17 | `ffmpeg_commands.py` | `app/utils/ffmpeg_commands.py` | Cobalt fallback downloads full video before trim — 2-4GB for long videos | Use `--download-sections` / byte-range requests if available |
| MED-18 | `billing.py` | `app/routers/billing.py` | `PATCH /api/user/currency` and several user endpoints lack auth check even without V0 mode | Audit all endpoints with `verify_requires_auth` — ensure `get_current_user_id` is explicit |
| MED-19 | `health endpoint` | `app/main.py` | `/health` returns `{"status":"ok"}` only — no DB, Redis, or provider connectivity check | Add: `db.execute(text("SELECT 1"))`, `redis.ping()`, return degraded/healthy |
| MED-20 | Supabase | All tables | No PITR backups on Supabase free tier — up to 24h data loss window | Upgrade to Supabase Pro for PITR, or schedule daily pg_dump to external storage |
| MED-21 | `scheduled.py` | `app/tasks/scheduled.py` | Cleanup tasks not idempotent — concurrent runs (two beat instances) double-process rows | Add `WHERE processed = FALSE` + atomic `UPDATE ... RETURNING` pattern |
| MED-22 | `storage.py:65` | `app/services/storage.py` | Local V0 download URL hardcoded to `127.0.0.1:8000` | Use `settings.API_BASE_URL` dynamically |
| MED-23 | `celery_app.py` | `app/tasks/celery_app.py` | No dead letter queue configured — failed tasks silently dropped | Add `task_routes` with a `dead_letter` queue and retry policy |
| MED-24 | `admin_service.py:1165` | `app/services/admin_service.py` | NARM prompt embeds raw LLM-injectable JSON — prompt injection from learning log data | Serialize JSON as escaped string literal, not raw interpolation |
| MED-25 | `admin_service.py:236` | `app/services/admin_service.py` | Full transcript returned in admin session detail — can be 100KB+ | Truncate to 500 chars in API response; add `?include_transcript=true` opt-in |
| MED-26 | `schemas/user.py:4` | `app/schemas/user.py` | No `max_length` on currency field | `currency: str = Field(..., max_length=3, pattern=r'^[A-Z]{3}$')` |
| MED-27 | `utils/ffmpeg_commands.py:18` | `app/utils/ffmpeg_commands.py` | cookies.txt created world-readable (no `chmod 0600`) | `os.chmod(cookie_path, 0o600)` after write |
| MED-28 | `localStorage` | `hookcut-frontend/src/` | Session IDs stored in `localStorage` — XSS exfiltration risk | Move to React state (in-memory) or httpOnly cookies |
| MED-29 | `pricing/page.tsx` | `hookcut-frontend/src/app/pricing/page.tsx` | `handleUpgrade` and `handlePaygPurchase` errors silently `console.warn` — no user feedback | Add error state + toast: `setError("Checkout unavailable. Try again.")` |
| MED-30 | `settings/page.tsx` | `hookcut-frontend/src/app/settings/page.tsx` | Currency save failure silently ignored | Add error toast on catch |
| MED-31 | `Dockerfile:16` | `hookcut-backend/Dockerfile` | `COPY . .` bakes `.env`, cookie files, and `hookcut.db.bak` into Docker image layer | Create `hookcut-backend/.dockerignore` with `.env`, `*.db`, `*cookies*.txt`, `storage/` |
| MED-32 | `worker.js:119-175` | `cloudflare-worker/worker.js` | `fetchViaInnertube` fallback function defined but never called — dead code | Wire in as fallback when Player API returns non-200 |
| MED-33 | `Dockerfile` | `hookcut-backend/Dockerfile` | No `HEALTHCHECK` directive — Docker reports container "Up" even when app crashes | `HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:${PORT:-8000}/api/health \|\| exit 1` |
| MED-34 | `docker-compose.prod.yml:5-14` | `docker-compose.prod.yml` | PostgreSQL exposed on host port 5432 with weak `hookcut_dev` password | Remove `ports:` mapping; use `expose: ["5432"]` + strong secret |
| MED-35 | `celery_app.py` | `app/tasks/celery_app.py` | No `beat_schedule` defined in Celery config — scheduled tasks may not register when beat runs standalone | Define explicitly: `celery_app.conf.beat_schedule = {"cleanup": {"task": "...", "schedule": crontab(...)}}` |
| MED-36 | `001_initial_schema.py` | `alembic/versions/001_initial_schema.py` | All `DateTime` columns timezone-naive — incorrect behavior if server timezone drifts | Future migration: `ALTER COLUMN ... TYPE TIMESTAMP WITH TIME ZONE` |
| MED-37 | `next.config.ts` | `hookcut-frontend/next.config.ts` | No `Content-Security-Policy` header | Add CSP in `headers()` function starting with `report-only` mode |

---

## Section 4 — Low Priority Issues

| # | Location | Files Affected | Issue | Recommended Solution |
|---|----------|---------------|-------|---------------------|
| LOW-01 | `config.py:93` | `app/config.py` | JWT secret length warning (31 chars), not exception — weak secret accepted | Change warning to `raise ValueError("JWT_SECRET must be ≥ 32 chars")` in prod |
| LOW-02 | `main.py:67` | `app/main.py` | Version string exposed in `/health` response | Remove version from health response or gate behind admin auth |
| LOW-03 | `admin confirm dialog` | Admin frontend pages | No focus trap, no `role="dialog"` on admin confirmation modals — inaccessible | Add `role="dialog"` + `aria-modal="true"` + `FocusTrap` from shadcn |
| LOW-04 | `login/page.tsx:150-155` | `src/app/auth/login/page.tsx` | Terms of Service and Privacy Policy are `<span>` not `<a>` — not keyboard navigable | Replace with `<Link href="/terms">` and `<Link href="/privacy">` |
| LOW-05 | `admin/audit/page.tsx` | `src/app/admin/audit/page.tsx` | `URL.revokeObjectURL` called before download may initiate | Move revoke inside a `setTimeout(() => URL.revokeObjectURL(url), 1000)` |
| LOW-06 | `hooks table` | `app/models/hook.py` | Dual time representation (varchar `start_time` + float `start_seconds`) — can diverge | Consolidate to float seconds only; derive display format in frontend |
| LOW-07 | `prompt_rules table` | `alembic/versions/007_add_admin_tables.py` | No UNIQUE constraint on `(rule_key, version)` — duplicate rule versions possible | `CREATE UNIQUE INDEX idx_rules_key_version ON prompt_rules (rule_key, version);` |
| LOW-08 | `admin/rules page` | `src/app/admin/rules/page.tsx` | Generic "Failed to load data" toast for all error types | Map error codes to specific messages |
| LOW-09 | `progress-step.tsx` | `src/components/progress-step.tsx` | Elapsed timer never stops after all shorts complete | Stop timer on all shorts reaching terminal state |
| LOW-10 | `progress-step.tsx` | `src/components/progress-step.tsx` | `isPending` prop passed but never used in component | Remove unused prop from interface |
| LOW-11 | `header.tsx` | `src/components/header.tsx` | Mobile menu close animation never fires (AnimatePresence missing) | Wrap mobile menu with `<AnimatePresence>` |
| LOW-12 | `usePollTask.ts` | `src/hooks/usePollTask.ts` | No request deduplication — multiple in-flight polls possible under tab switch | Use `useRef` flag to prevent concurrent polls |
| LOW-13 | Procfile | `hookcut-backend/Procfile` | Uvicorn runs as single process — no `--workers` flag | Use `gunicorn -k uvicorn.workers.UvicornWorker -w 2` for multi-process |
| LOW-14 | `alembic.ini` | `hookcut-backend/alembic.ini` | Short numeric revision IDs ("001"–"008") risk collision on team branches | Enforce Alembic-generated hash IDs via pre-commit hook going forward |
| LOW-15 | `alembic/env.py` | `hookcut-backend/alembic/env.py` | `load_dotenv()` called unconditionally — could override Railway env vars if `.env` is in image | Guard with `if not os.environ.get("RAILWAY_ENVIRONMENT"): load_dotenv()` |
| LOW-16 | Celery config | `app/tasks/celery_app.py` | `task_acks_late=True` without `task_reject_on_worker_lost=True` — tasks disappear on SIGKILL | Add `task_reject_on_worker_lost=True` |
| LOW-17 | `wrangler.toml` | `cloudflare-worker/wrangler.toml` | No `routes` defined — worker deployed to public `.workers.dev` subdomain, discoverable | Add explicit route: `routes = [{ pattern = "transcript-worker.hookcut.nyxpath.com/*" }]` |
| LOW-18 | `docker-compose.prod.yml` | `docker-compose.prod.yml` | `version: "3.9"` deprecated in Compose v2 | Remove `version:` key; add `condition: service_healthy` to `depends_on` |
| LOW-19 | CQ | `app/tasks/celery_app.py` | `get_settings()` called at module import — missing env vars crash Celery startup before tasks are registered | Lazy-initialize settings inside the Celery app factory |
| LOW-20 | `ai-hook-finder/error.tsx` | `src/app/ai-hook-finder/error.tsx` | Error and loading pages use light theme on dark app — visually jarring | Apply dark glass-morphism theme consistent with rest of app |
| LOW-21 | `admin_service.py:350` | `app/services/admin_service.py` | `export_audit_logs` up to 10,000 rows — memory risk | Cap at 1,000 rows per export with pagination |
| LOW-22 | `CQ-12` | `src/app/admin/audit/page.tsx` | `URL.revokeObjectURL` called before download may complete | Use `setTimeout` with 1s delay before revoke |
| LOW-23 | DB | All DateTime columns | Missing indexes: `transactions.session_id`, `learning_logs.niche`, `shorts.expires_at`, `shorts.download_url_expires_at` | Add in a single migration |
| LOW-24 | `docker-compose.yml` | `docker-compose.yml` | Dev Redis has no password, no persistence config — leads to muscle memory mistakes in prod | Add comment: `# DEV ONLY — no auth, no persistence` |

---

## Section 5 — Infrastructure Audit (Deep-Dive)

**Source**: `pass4-infra-deep.md` — 21 files audited: Dockerfile, railway.toml, start.sh, Procfile, pyproject.toml, alembic.ini, alembic/env.py, 8 migrations, cloudflare-worker/worker.js, wrangler.toml, docker-compose.yml, docker-compose.prod.yml, celery_app.py, next.config.ts

**Critical infra issues are already captured in CRIT-14 through CRIT-19 and HIGH-34 through HIGH-44 above.**

### Correctly Implemented (Do Not Change)
- `task_serializer="json"` — prevents Pickle RCE, correct
- `worker_prefetch_multiplier=1` — prevents task starvation, correct
- `worker_max_tasks_per_child=20` — prevents memory leaks from FFmpeg residue, correct
- `enable_utc=True` in Celery — correct
- Migration chain 001→008: linear, no gaps or forks
- Migration 002 correctly uses `batch_alter_table` for SQLite
- Migration 003 `role` column uses `server_default='user'` — safe for existing rows
- `task_acks_late=True` — correct for at-least-once video processing delivery
- CF Worker API key check is present and correct when secret is deployed

---

## Section 6 — UI/UX Audit

### Visual Design
The dark glass-morphism aesthetic is consistent and well-executed across the public marketing pages. The pricing page card layout, gradient borders, and animations are polished. The login page is clean with good spacing.

---

### UX-01 — Dashboard Crashes on Auth State Transition (Critical)
**Files Affected**: `src/app/dashboard/page.tsx:~247`
→ See CRIT-10.

### UX-02 — Short Generation Failures Show Permanent Spinner
**Files Affected**: `src/components/short-card.tsx`
→ See HIGH-06.

### UX-03 — Dashboard Link Missing for Non-Admin Users
**Files Affected**: `src/components/header.tsx:~146`
→ See HIGH-05.

### UX-04 — Pricing Page Requires Login to View — Public Info Behind Auth Wall
**Files Affected**: `hookcut-frontend/src/proxy.ts` (middleware)
**Issue**: `/pricing` redirects unauthenticated users to login. Public pricing is a standard marketing page that should be accessible without sign-in — it directly impacts conversion.
**Recommended Solution**: Remove `/pricing` from protected routes in proxy.ts middleware.

### UX-05 — Mock/Placeholder Thumbnails in UI: Looks Unfinished
**Files Affected**: `hookcut-frontend/src/components/marketing-home.tsx` (hero demo section), `hookcut-frontend/src/components/hooks-step.tsx` (hook cards demo)
**Issue**: The marketing/demo sections use placeholder or hardcoded mock YouTube thumbnails (generic grey blocks or stock images). First-time visitors see an unfinished look in the product demo area. This directly impacts conversion — the core value proposition ("we extract hooks from YouTube videos") needs to look real.
**Recommended Solution**: Replace static placeholders with a real embedded demo: either (a) a looping GIF/video of the actual product in use, or (b) a static screenshot of a real analysis result for a well-known YouTube video. Use `https://img.youtube.com/vi/{videoId}/maxresdefault.jpg` as the thumbnail source pattern — real thumbnails are freely available without auth.

### UX-06 — Fake Testimonials on Login Page
**Files Affected**: `hookcut-frontend/src/app/auth/login/page.tsx:9-25`
**Issue**: Login page displays three rotating testimonials attributed to "Alex M. — Content Creator", "Sarah K. — YouTube Producer", "James T. — Indie Creator" with quotes like "Generated 50 Shorts from one podcast." These are clearly fabricated (no customers yet confirmed in audit briefing). Presenting fake social proof as real user testimonials is deceptive and may violate FTC guidelines in the US / Consumer Protection laws in India.
**Recommended Solution**: Replace with factual product claims ("No subscription required", "5 free minutes included", "AI-powered hook detection") or remove the testimonial section until real users can provide actual quotes. If keeping the rotating content, label it as "What creators say about hooks like this" and make it generic tips, not fake testimonials.

### UX-07 — Checkout/PAYG Errors Silently Swallowed
**Files Affected**: `hookcut-frontend/src/app/pricing/page.tsx:152-166, 168-182`
**Issue**: Both `handleUpgrade` and `handlePaygPurchase` use `console.warn()` on error — users see nothing if checkout fails. Payment failures are the highest-stakes error in the app.
**Recommended Solution**: Add toast or inline error state:
```tsx
} catch (err) {
  toast.error("Checkout failed. Please try again or contact support.");
}
```

### UX-08 — Login Hardcodes `callbackUrl: "/"` — Deep Link Intent Lost
**Files Affected**: `hookcut-frontend/src/app/auth/login/page.tsx:122`
**Issue**: `signIn("google", { callbackUrl: "/" })` always redirects to home after login, ignoring any `?callbackUrl=` query param. Users clicking "Upgrade to Pro" → login → land on home, not pricing.
**Recommended Solution**:
```tsx
const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";
signIn("google", { callbackUrl })
```

### UX-09 — Admin Error Toasts All Say "Failed to Load Data"
**Files Affected**: `hookcut-frontend/src/app/admin/` (multiple pages)
**Issue**: Generic error message regardless of what operation failed (load users, save rule, delete session). Admins can't diagnose issues.
**Recommended Solution**: Map operations to specific messages: "Failed to load users", "Failed to save rule", "Failed to delete session".

### UX-10 — Elapsed Timer Never Stops After Completion
**Files Affected**: `hookcut-frontend/src/components/progress-step.tsx`
**Issue**: The analysis elapsed timer continues incrementing after all shorts are complete.
**Recommended Solution**: Stop timer when `analysisStatus === "complete"` or all shorts reach terminal states.

### UX-11 — `ai-hook-finder` Error/Loading Pages Use Light Theme
**Files Affected**: `hookcut-frontend/src/app/ai-hook-finder/error.tsx`, `loading.tsx`
**Issue**: Next.js error/loading boundary pages for `/ai-hook-finder` use default light styling, jarring against the dark glass-morphism app theme.
**Recommended Solution**: Apply dark theme classes matching the rest of the app.

### UX-12 — Mobile Menu Close Animation Never Fires
**Files Affected**: `hookcut-frontend/src/components/header.tsx`
**Issue**: Mobile menu lacks `<AnimatePresence>` wrapper — exit animation never plays. Menu disappears abruptly.
**Recommended Solution**: Wrap mobile menu toggle with `<AnimatePresence mode="wait">`.

### UX-13 — No CSP Nonce — Nonce Attributes Set to `undefined` in HTML
**Files Affected**: `hookcut-frontend/src/app/layout.tsx`, `hookcut-frontend/next.config.ts`
**Issue**: Live page source shows `nonce="undefined"` on script tags — a CSP nonce setup was started but not completed. This means the CSP nonce feature is broken (the nonces don't match), which would block scripts if a CSP header were ever added.
**Recommended Solution**: Either complete the nonce implementation properly using Next.js middleware nonce injection, or remove all nonce attributes until the implementation is ready.

### UX-14 — Terms of Service and Privacy Policy are `<span>` Not `<a>`
**Files Affected**: `hookcut-frontend/src/app/auth/login/page.tsx:150-156`
**Issue**: Legal links are non-interactive `<span>` elements. Not keyboard navigable, not crawlable by search engines, and potentially a compliance issue (GDPR, India IT rules require accessible privacy links).
**Recommended Solution**: `<Link href="/privacy">Privacy Policy</Link>` and `<Link href="/terms">Terms of Service</Link>` — also implies these pages need to be created.

---

## Section 7 — Load Testing Notes

Load testing agents hit the credit limit before completing. Based on the live API testing conducted in Pass 2, the following performance risks are well-evidenced:

| Finding | Evidence | Risk |
|---------|---------|------|
| Rate limiting inactive | 12 consecutive requests, all 200 | Unlimited analysis at Gemini cost |
| No concurrency limits | All requests share `v0_local_user` rate bucket | One IP can starve all workers |
| Single Uvicorn process | `Procfile` — no `--workers` flag | High p99 latency under concurrent load |
| Pool size 5 per process | `models/base.py` | Connection exhaustion at ~20+ concurrent users |
| Redis result TTL 5min | `celery_app.py` | Results lost before frontend polls on long videos |

A formal load test script (50 concurrent users, 100 requests each) should be run after CRIT-01 (V0 mode) is fixed — current results would be invalid since all requests share a single bucket.

---

## Section 8 — Observability Gaps

| # | Severity | Description | Recommended Solution |
|---|----------|-------------|---------------------|
| OBS-01 | HIGH | Sentry DSN not configured — zero error tracking | Set `SENTRY_DSN` in Railway; `sentry_sdk.init()` already coded |
| OBS-02 | HIGH | PostHog not configured — no user analytics | Set `NEXT_PUBLIC_POSTHOG_KEY` and `POSTHOG_API_KEY` |
| OBS-03 | HIGH | No structured JSON logging — logs not queryable in Railway | Add `python-json-logger` or configure uvicorn JSON log formatter |
| OBS-04 | HIGH | No Celery monitoring — no visibility into stuck tasks | Deploy Flower: `celery -A app.tasks.celery_app flower --port=5555` |
| OBS-05 | MEDIUM | `/health` returns `{"status":"ok"}` only — doesn't verify DB, Redis, providers | Add `db.execute(text("SELECT 1"))` + `redis.ping()` checks |
| OBS-06 | MEDIUM | No alerting on Gemini API errors or rate limits | Add Sentry alert rule for `GeminiAPIError` exception class |
| OBS-07 | MEDIUM | No alerting on negative credit balance anomalies | Add monitoring query: `SELECT * FROM credit_balances WHERE total_seconds < 0` |
| OBS-08 | LOW | No request correlation ID in API responses | Add `X-Request-ID` header middleware |

---

## Section 9 — Missing Features (Not Bugs)

| # | Priority | Feature | Notes |
|---|----------|---------|-------|
| FEAT-01 | HIGH | Email/password signup | Google OAuth only currently — blocks B2B, users without Google |
| FEAT-02 | HIGH | Razorpay integration | Keys not configured; India-primary payment gateway |
| FEAT-03 | HIGH | Sentry error tracking | Code ready, DSN not set |
| FEAT-04 | HIGH | PostHog analytics | Code ready, keys not set |
| FEAT-05 | MEDIUM | Terms of Service page | Linked from login but page doesn't exist |
| FEAT-06 | MEDIUM | Privacy Policy page | Linked from login but page doesn't exist |
| FEAT-07 | MEDIUM | Celery task monitoring (Flower) | No visibility into worker health |
| FEAT-08 | MEDIUM | Webhook idempotency table | Required for CRIT-05 fix |
| FEAT-09 | MEDIUM | Health check with dependency verification | Required for railway.toml `healthcheckPath` |
| FEAT-10 | LOW | Cloudflare Worker deployment | `wrangler deploy` not yet run — transcript fallback not active |

---

## Section 10 — Prioritized Fix Order (4 Sprints)

### SPRINT 1: Pre-Launch Blockers (Fix before any paying user — estimated 2-3 engineering days)

```
[ ] 1.  CRIT-01  — Set FEATURE_V0_MODE=False in Railway (1 min, 1-line env change)
[ ] 2.  CRIT-09  — Disable Swagger UI in production (app/main.py, 3 lines)
[ ] 3.  CRIT-14  — Remove migration failure fallback in start.sh (1 line delete)
[ ] 4.  CRIT-10  — Fix useMemo after conditional return in dashboard/page.tsx
[ ] 5.  CRIT-11  — Fix useTransform inside JSX in url-step.tsx
[ ] 6.  CRIT-02  — Remove or admin-guard v0-grant endpoint
[ ] 7.  CRIT-03  — Add auth + ownership check to GET /sessions/{id}/hooks
[ ] 8.  CRIT-04  — Add auth + ownership check to all shorts endpoints
[ ] 9.  CRIT-13  — Add auth to GET /api/storage/{file_key}
[ ] 10. CRIT-12  — Enable RLS on Supabase (users, credit_balances, sessions, hooks, shorts, transactions)
[ ] 11. CRIT-08  — Fix rate limiting (verify Redis URL, fix key for anon users)
[ ] 12. CRIT-17  — Move INNERTUBE_API_KEY to wrangler secret
[ ] 13. CRIT-18  — alembic.ini: replace hardcoded DB password with sentinel
[ ] 14. CRIT-19  — CF Worker: make API_KEY mandatory, restrict CORS
[ ] 15. CRIT-15  — Add startup validation for webhook secrets
[ ] 16. CRIT-16  — Add MAX_VIDEO_MINUTES enforcement in analyze_service
[ ] 17. HIGH-02  — Add MAX_POLLS to useShortPoller.ts
[ ] 18. HIGH-03  — Set secure: true on NextAuth cookies
[ ] 19. HIGH-04  — Add admin role check to proxy.ts middleware
[ ] 20. HIGH-05  — Show Dashboard link for all authenticated users
[ ] 21. HIGH-06  — Show short generation error in ShortCard
[ ] 22. HIGH-31  — Add security headers middleware to FastAPI
[ ] 23. HIGH-36  — Add healthcheckPath to railway.toml
[ ] 24. UX-04   — Remove /pricing from protected routes
[ ] 25. UX-06   — Remove fake testimonials from login page
```

### SPRINT 2: Financial Safety & Reliability (Week 2)

```
[ ] 26. CRIT-05  — Implement webhook idempotency (processed_webhooks table)
[ ] 27. CRIT-06  — Cap minutes from Stripe metadata
[ ] 28. CRIT-07  — Make .env write atomic (temp file + os.replace)
[ ] 29. HIGH-07  — Add soft_time_limit=600 to run_analysis task
[ ] 30. HIGH-08  — Add timeouts to Anthropic + OpenAI SDK calls
[ ] 31. HIGH-09  — Truncate transcript to 60k chars before LLM
[ ] 32. HIGH-10  — Replace time.sleep(30) with self.retry(countdown=30)
[ ] 33. HIGH-11  — Add SELECT FOR UPDATE to credit deduction
[ ] 34. HIGH-12  — Fix double-refund race in refund_and_fail
[ ] 35. HIGH-17  — Wrap work_dir cleanup in try/finally
[ ] 36. HIGH-22  — Add max_length to SetApiKeyRequest.api_key
[ ] 37. HIGH-24  — Increase result_expires to 3600
[ ] 38. HIGH-27  — Add unique index on analysis_sessions.task_id
[ ] 39. HIGH-28  — Replace OFFSET pagination with keyset in scheduled tasks
[ ] 40. HIGH-34  — Add non-root USER to Dockerfile
[ ] 41. HIGH-35  — Remove source bind mounts from docker-compose.prod.yml
[ ] 42. HIGH-40  — Add Redis auth + remove port 6379 exposure
[ ] 43. HIGH-41  — Replace hardcoded DB password in docker-compose.prod.yml
[ ] 44. MED-31   — Create .dockerignore to exclude .env, cookies, DB files
```

### SPRINT 3: Security Hardening & Code Quality (Week 3)

```
[ ] 45. CRIT-07  — Complete .env atomic write (cache invalidation)
[ ] 46. HIGH-01  — Move email in auth/sync to body, derive from JWT
[ ] 47. HIGH-25  — Move payment params to request body
[ ] 48. HIGH-26  — Add max_length=2048 to youtube_url
[ ] 49. HIGH-32  — Fix Razorpay webhook 500 → 400 on invalid signature
[ ] 50. HIGH-33  — Add SSRF validation on Cobalt API redirect URLs
[ ] 51. HIGH-37  — Add requirements.lock.txt (pip-compile)
[ ] 52. HIGH-38  — Fix Beat scheduling (use celery-redbeat)
[ ] 53. HIGH-39  — Fix migration 008 with batch_alter_table
[ ] 54. HIGH-42  — Pin Docker base image to specific patch version
[ ] 55. HIGH-43  — Upgrade Node.js in Dockerfile to Node 22
[ ] 56. HIGH-44  — Add task_reject_on_worker_lost=True
[ ] 57. MED-11   — Fix narm_insights.confidence column type (varchar → float)
[ ] 58. MED-12   — Add UNIQUE constraint on analysis_sessions.task_id
[ ] 59. MED-35   — Define beat_schedule explicitly in celery_app.py
[ ] 60. MED-37   — Add CSP header to next.config.ts
[ ] 61. UX-07    — Add user-facing error message on checkout failure
[ ] 62. UX-08    — Fix callbackUrl in login page to read from searchParams
[ ] 63. UX-05    — Replace mock thumbnails with real demo content
```

### SPRINT 4: Observability & Polish (Week 4 — before paid marketing)

```
[ ] 64. OBS-01   — Configure Sentry DSN in Railway
[ ] 65. OBS-02   — Configure PostHog keys
[ ] 66. OBS-05   — Add DB/Redis ping to /health endpoint
[ ] 67. OBS-04   — Deploy Celery Flower monitoring
[ ] 68. UX-09    — Fix generic admin error toast messages
[ ] 69. UX-10    — Stop elapsed timer on completion
[ ] 70. UX-13    — Fix nonce="undefined" in HTML (complete or remove)
[ ] 71. UX-14    — Fix Terms/Privacy <span> → <Link>
[ ] 72. FEAT-05  — Create /terms page
[ ] 73. FEAT-06  — Create /privacy page
[ ] 74. LOW-04   — Fix login Terms/Privacy accessibility
[ ] 75. MED-23   — Add missing DB indexes (expires_at, niche, session_id)
[ ] 76. MED-36   — Add timezone=True to DateTime columns in future migrations
[ ] 77. LOW-17   — Add explicit route to wrangler.toml
[ ] 78. MED-32   — Wire fetchViaInnertube as CF Worker fallback
[ ] 79. FEAT-10  — Deploy Cloudflare Worker (wrangler deploy)
```

---

## Summary

HookCut has a solid technical architecture with thoughtful patterns (Celery task separation, LLM cascade, credit system design). The codebase is clean and well-structured. However, **19 critical issues must be resolved before any real user onboards**:

- The most urgent: **V0 mode is active in production** — the entire API is effectively unauthenticated (CRIT-01). This single env change fixes ~8 downstream issues.
- **Dashboard crashes for every user** due to React Rules of Hooks violation (CRIT-10).
- **All 13 Supabase tables have RLS disabled** — a compromised anon key exposes all user data (CRIT-12).
- **Hardcoded YouTube API key and database password** are committed in source (CRIT-17, CRIT-18).
- **Fake testimonials on the login page** are a legal and trust risk (UX-06).
- **Mock/placeholder thumbnails** make the product look unfinished (UX-05).

**Sprint 1 estimated time**: 2–3 engineering days for a focused developer.
**Blocking**: Do not launch paid marketing until Sprint 1 + Sprint 2 are complete.

---

*Report generated by Claude Code multi-pass audit. Source files: `pass1a-backend.md` (91 issues), `pass1b-frontend.md` (30 issues), `pass1c-security.md` (34 issues), `pass1d-db-infra.md` (infra audit), `pass2-api-testing.md` (12 live findings), `pass3-website.md` (8 website findings), `pass4-infra-deep.md` (29 infra deep-dive findings), direct frontend code review.*
