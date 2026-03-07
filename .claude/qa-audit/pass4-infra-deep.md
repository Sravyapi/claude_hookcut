# HookCut Infrastructure Deep Audit — Pass 4
**Date**: 2026-03-07
**Scope**: Dockerfile, railway.toml, start.sh, Procfile, pyproject.toml, alembic.ini, alembic/env.py, 8 migrations, cloudflare-worker/worker.js, wrangler.toml, docker-compose.yml, docker-compose.prod.yml, app/tasks/celery_app.py, hookcut-frontend/next.config.ts
**Auditor**: Claude Sonnet 4.6 (infrastructure/security mode)

---

## Summary Table

| Severity | Count |
|----------|-------|
| CRITICAL | 5 |
| HIGH | 8 |
| MEDIUM | 10 |
| LOW | 6 |
| **Total** | **29** |

---

## CRITICAL Findings

### [CRITICAL] Migration failure silently swallowed — app starts on broken schema
- **File**: `hookcut-backend/start.sh` line 12
- **Issue**: `alembic upgrade head 2>&1 || echo "WARNING: Alembic migration failed (continuing anyway)"` — if migrations fail (e.g. DB not ready, schema conflict, network error), uvicorn still starts. The app will then hit ORM errors at runtime against a stale or partially-migrated schema.
- **Risk**: Production deploy on a broken schema. New columns introduced by recent migrations (007, 008) will be missing, causing `UndefinedColumn` errors on every request that touches hooks, admin tables, or narm_insights. The error only surfaces after real traffic hits, not at deploy time.
- **Fix**:
  ```bash
  echo "=== Running Alembic migrations ==="
  alembic upgrade head
  # Remove the || fallback entirely — let set -e terminate the script on failure.
  # Railway will mark the deploy as failed and not route traffic.
  ```

---

### [CRITICAL] Hardcoded Google InnerTube API key in source code
- **File**: `cloudflare-worker/worker.js` line 32
- **Issue**: `const INNERTUBE_API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8";` — a Google API key is committed to the repository in plaintext.
- **Risk**: Even if this specific key is a publicly documented "Android client key" used by many open-source projects, committing any API key is a security anti-pattern: (1) if Google rotates or restricts it the worker silently breaks; (2) it normalizes secret-in-source practice; (3) GitHub secret scanning will flag it. If this key carries any quota or billing it can be abused by anyone reading the repo.
- **Fix**: Move to a Cloudflare Worker secret/environment variable:
  ```toml
  # wrangler.toml
  [vars]
  # Non-secret config here
  # Secret: wrangler secret put INNERTUBE_API_KEY
  ```
  ```js
  // worker.js — access via env
  const playerResp = await fetch(
    `https://www.youtube.com/youtubei/v1/player?key=${env.INNERTUBE_API_KEY}`,
  ```

---

### [CRITICAL] Docker container runs as root (no USER directive)
- **File**: `hookcut-backend/Dockerfile` (no USER directive present)
- **Issue**: The image has no `USER` instruction. Every process — uvicorn, alembic, bash — runs as UID 0 inside the container.
- **Risk**: If any dependency has a path traversal or RCE vulnerability (yt-dlp processes untrusted URLs; FFmpeg processes untrusted video data), the attacker gains root inside the container. On Railway with shared kernel this is a container escape risk. yt-dlp and FFmpeg both have historical CVEs involving malformed input.
- **Fix**:
  ```dockerfile
  # After pip install, before CMD:
  RUN groupadd -r hookcut && useradd -r -g hookcut -d /app hookcut && \
      chown -R hookcut:hookcut /app /tmp/hookcut
  USER hookcut
  CMD ["bash", "start.sh"]
  ```

---

### [CRITICAL] Plaintext default credentials committed in alembic.ini
- **File**: `hookcut-backend/alembic.ini` line 3
- **Issue**: `sqlalchemy.url = postgresql://postgres:password@localhost:5432/hookcut` — a database URL with a password (`password`) is committed to the repository.
- **Risk**: If a developer accidentally runs `alembic upgrade head` without `DATABASE_URL` set (or in an environment where `env.py`'s override fails), alembic will attempt to connect to this hardcoded URL. More critically, this credential is committed to git history permanently. Although `env.py` correctly overrides from `DATABASE_URL`, the fallback in `alembic.ini` is still readable by anyone with repo access.
- **Fix**: Replace the static URL with an environment variable placeholder and document that `DATABASE_URL` must be set:
  ```ini
  sqlalchemy.url = %(DATABASE_URL)s
  ```
  Or use a deliberately invalid sentinel:
  ```ini
  sqlalchemy.url = postgresql://OVERRIDE_VIA_DATABASE_URL_ENV_VAR
  ```

---

### [CRITICAL] Worker CORS is fully open (`Access-Control-Allow-Origin: *`) with no rate limiting
- **File**: `cloudflare-worker/worker.js` lines 246–250
- **Issue**: `corsHeaders()` returns `"Access-Control-Allow-Origin": "*"` unconditionally. Combined with the fact that `env.API_KEY` check is entirely **optional** (line 19: `if (env.API_KEY)` — if the secret is not set, all requests are unauthenticated), any browser from any origin can call the transcript worker for free.
- **Risk**: (1) Unauthenticated access if `API_KEY` is not configured in wrangler secrets. (2) Open CORS allows malicious third-party sites to proxy YouTube transcripts through your Cloudflare worker, running up your CF usage bill. (3) No per-IP or per-origin rate limiting means the worker can be used for bulk transcript scraping at HookCut's expense.
- **Fix**:
  ```js
  // Make API_KEY mandatory, not optional:
  if (!env.API_KEY) {
    return json({ error: "Worker not configured" }, 503);
  }
  const auth = request.headers.get("Authorization") || "";
  if (auth !== `Bearer ${env.API_KEY}`) {
    return json({ error: "Unauthorized" }, 401);
  }
  // Restrict CORS to your own domain:
  function corsHeaders(origin) {
    const allowed = ["https://hookcut.nyxpath.com", "http://localhost:3000"];
    const o = allowed.includes(origin) ? origin : allowed[0];
    return { "Access-Control-Allow-Origin": o, ... };
  }
  ```
  Deploy `API_KEY` via `wrangler secret put API_KEY`.

---

## HIGH Findings

### [HIGH] Base image unpinned — `python:3.12-slim` floats to latest patch
- **File**: `hookcut-backend/Dockerfile` line 1
- **Issue**: `FROM python:3.12-slim` with no digest or patch version. The tag `3.12-slim` will resolve to whatever the latest 3.12.x is at build time, meaning a new CVE patch may introduce a breaking change or, conversely, a build may silently stay on an older vulnerable image if Docker caches aggressively.
- **Risk**: Non-reproducible builds. A CVE fix in the base image may or may not be picked up depending on when Railway rebuilds. Security scanners like Trivy can't pin-verify a floating tag.
- **Fix**: Pin to a specific digest:
  ```dockerfile
  FROM python:3.12.9-slim-bookworm@sha256:<digest>
  ```
  Or at minimum pin the patch version: `FROM python:3.12.9-slim`.

---

### [HIGH] Source code bind-mounted over image in docker-compose.prod.yml
- **File**: `hookcut-compose.prod.yml` lines 33, 48
- **Issue**: `volumes: - ./hookcut-backend:/app` in both `backend` and `worker` services. This mounts the host source directory over the container's `/app`, overwriting the built image contents. Any local uncommitted changes (including debug code, `.env` files accidentally placed in the directory) are live in "production."
- **Risk**: Production accidentally runs unbuilt, untested local code. If `hookcut-backend/.env` exists on the host it is now readable inside the container as a file. This also means the Docker build step is effectively bypassed — the Dockerfile's `pip install` and hardening steps apply to the image but the running container uses the host filesystem.
- **Fix**: Remove the source bind mounts from the prod compose. Only mount persistent data volumes:
  ```yaml
  # backend service — remove:
  volumes:
    - ./hookcut-backend:/app   # DELETE THIS LINE
    - /tmp/hookcut:/tmp/hookcut  # keep
  ```

---

### [HIGH] railway.toml missing health check path and memory/CPU limits
- **File**: `hookcut-backend/railway.toml` (entire file, 8 lines)
- **Issue**: No `healthcheckPath`, no `healthcheckTimeout`, no memory or CPU limit directives. Railway's default health check is TCP port probe only — it will mark the service healthy the moment uvicorn's port is open, even if alembic migrations are still running or the DB connection pool is exhausted.
- **Risk**: Railway routes production traffic to an instance before it is ready to serve requests, resulting in 500 errors during deploys. Without memory limits, a runaway FFmpeg or yt-dlp process can OOM the whole container, killing the API server too.
- **Fix**:
  ```toml
  [deploy]
  restartPolicyType = "on_failure"
  restartPolicyMaxRetries = 3
  healthcheckPath = "/api/health"
  healthcheckTimeout = 30
  ```
  Memory/CPU limits are set in Railway's dashboard per-service environment variables (`RAILWAY_MEMORY_LIMIT_MB`).

---

### [HIGH] All dependencies use `~=` (compatible release) — not fully pinned
- **File**: `hookcut-backend/pyproject.toml` lines 7–29
- **Issue**: Every production dependency uses `~=` (e.g. `fastapi~=0.115`, `celery[redis]~=5.4`). This allows minor version bumps without an explicit update (e.g. `fastapi~=0.115` allows `0.115.x` — but `celery~=5.4` allows any `5.x >= 5.4`). There is no lockfile committed (`poetry.lock` or `pip-compile` output).
- **Risk**: A dependency that ships a patch with a breaking change or CVE will be silently picked up on the next Railway build. This is especially dangerous for `cryptography~=42.0` (frequent CVE patches) and `openai~=1.50` (API-breaking changes are common in pre-2.0 libraries).
- **Fix**: Add a `requirements.txt` generated by `pip-compile` or switch to Poetry/uv with a lockfile committed to the repo. At minimum:
  ```bash
  pip install pip-tools
  pip-compile pyproject.toml --output-file requirements.lock.txt
  # Commit requirements.lock.txt and use it in Dockerfile:
  RUN pip install --no-cache-dir -r requirements.lock.txt
  ```

---

### [HIGH] Procfile runs three separate process types — Beat + Worker co-location risk
- **File**: `hookcut-backend/Procfile` lines 2–3
- **Issue**: `worker` and `beat` are separate process types. On Railway free/hobby tier, multiple Procfile process types run in the same dyno/service. If Railway deploys them as separate services, there is no coordination — running two `beat` instances simultaneously (e.g. during a rolling deploy) will cause scheduled tasks to fire twice. There is no `beat` singleton guard.
- **Risk**: Double-firing of scheduled tasks such as `cleanup_expired_files` and free-credit reset could delete files prematurely or grant duplicate free credits.
- **Fix**: For Railway, either (a) combine beat into the worker process: `celery -A app.tasks.celery_app worker --beat --loglevel=info --concurrency=2` (only safe with a single worker replica), or (b) use Redis-based beat scheduler (`celery-redbeat`) which has distributed locking.

---

### [HIGH] Migration 008 uses `alter_column` without `batch_alter_table` — breaks SQLite
- **File**: `hookcut-backend/alembic/versions/008_widen_hook_columns.py` lines 22–24
- **Issue**: `op.alter_column("hooks", "hook_type", type_=sa.Text(), ...)` is called directly. Migration 002 correctly uses `with op.batch_alter_table(...)` for SQLite compatibility. Migration 008 does not, making it incompatible with SQLite.
- **Risk**: If developers run tests against SQLite (the default when `DATABASE_URL` is not set), `alembic upgrade head` will fail with `OperationalError: Cannot add a NOT NULL column with default value NULL` or similar SQLite ALTER TABLE limitation. This breaks the local dev/test workflow and means the migration chain cannot be replayed from scratch in CI.
- **Fix**:
  ```python
  def upgrade() -> None:
      with op.batch_alter_table("hooks") as batch_op:
          batch_op.alter_column("hook_type", type_=sa.Text(), existing_nullable=False)
          batch_op.alter_column("funnel_role", type_=sa.Text(), existing_nullable=False)
  ```

---

### [HIGH] No `task_soft_time_limit` or `task_time_limit` set globally in Celery config
- **File**: `hookcut-backend/app/tasks/celery_app.py` lines 22–34
- **Issue**: `celery_app.conf.update(...)` sets `result_expires=300` and `worker_max_tasks_per_child=20` but does not set `task_soft_time_limit` or `task_time_limit`. Without these, a hung FFmpeg process or a stalled LLM API call can hold a Celery worker process indefinitely.
- **Risk**: A single task that hangs (e.g. FFmpeg waiting on a corrupt video, yt-dlp stuck on a rate-limited response) will consume one of the two worker slots permanently. With `--concurrency=2`, two such tasks will fully starve all other work. The worker will never recover until manually restarted.
- **Fix**:
  ```python
  celery_app.conf.update(
      ...
      task_soft_time_limit=600,   # 10 min — send SIGTERM, task can clean up
      task_time_limit=660,        # 11 min — send SIGKILL if soft limit ignored
  )
  ```

---

### [HIGH] Redis exposed on host port 6379 with no authentication in docker-compose.prod.yml
- **File**: `docker-compose.prod.yml` lines 15–17
- **Issue**: Redis service exposes port `6379:6379` to the host with no `requirepass` or `--requirepass` flag. Any process on the Docker host can connect to Redis and read/write Celery task results, including task arguments which may contain user data (YouTube URLs, session IDs, hook content).
- **Risk**: On a shared VPS or if the host firewall is misconfigured, unauthenticated Redis is accessible from the network. Celery result data is stored in Redis and could be read or poisoned. Redis also allows `CONFIG SET` which can be used for persistence attacks (writing files to host via Redis `SAVE` to an arbitrary path).
- **Fix**:
  ```yaml
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    # Remove the ports mapping entirely — only internal Docker network needed:
    # ports:
    #   - "6379:6379"
    expose:
      - "6379"
  ```

---

## MEDIUM Findings

### [MEDIUM] `result_expires=300` (5 min) too short for long video processing
- **File**: `hookcut-backend/app/tasks/celery_app.py` line 31
- **Issue**: Celery task results expire after 300 seconds. Video analysis + short generation for a long video can easily exceed 5 minutes (yt-dlp download + FFmpeg processing + LLM analysis).
- **Risk**: If a task takes >5 minutes, the result is expired by the time the frontend polls for it. The polling endpoint will return a "not found" result, leaving the session stuck in `pending` state with no error message. Users see an indefinite spinner.
- **Fix**: Increase to at least 1 hour (3600s) or align with `DOWNLOAD_URL_EXPIRES_SECONDS`. The comment says "Railway free Redis has ~25MB limit" — this is a real concern, but task result payloads are small JSON blobs. 3600s is safe:
  ```python
  result_expires=3600,
  ```

---

### [MEDIUM] `COPY . .` in Dockerfile copies `.env`, cookies files, and DB backup into image
- **File**: `hookcut-backend/Dockerfile` line 16
- **Issue**: `COPY . .` copies the entire `hookcut-backend/` directory into the image, including any `.env` files, `cookies_slim.txt`, `cookies_trimmed.txt`, `hookcut.nyxpath.com_cookies.txt`, and `hookcut.db.bak.*` files that are present on the host (confirmed by git status showing these as untracked).
- **Risk**: If the Docker image is pushed to a registry (Docker Hub, Railway's internal registry, or ECR), all secrets and cookies in the build context are baked into the image layer and readable by anyone with pull access. The `hookcut.db.bak` file would contain a full copy of the production database.
- **Fix**: Create `hookcut-backend/.dockerignore`:
  ```
  .env
  .env.*
  *.db
  *.db.bak*
  *_cookies.txt
  cookies_*.txt
  __pycache__/
  .pytest_cache/
  tests/
  storage/
  .git/
  ```

---

### [MEDIUM] Cloudflare Worker has no fallback when primary Player API fails
- **File**: `cloudflare-worker/worker.js` lines 66–68
- **Issue**: If `playerResp.ok` is false, the worker immediately returns a 502 error. The `fetchViaInnertube` function (lines 119–175) is defined as a fallback path but is **never called** from `handleTranscript`. It is dead code.
- **Risk**: If YouTube's Android Player API returns a non-200 (rate limit, regional block, API change), the worker fails hard. The dead `fetchViaInnertube` function was presumably intended as a fallback but was never wired in.
- **Fix**: Wire in the fallback:
  ```js
  if (!playerResp.ok) {
    // Fallback to innertube web client
    const fallbackText = await fetchViaInnertube(videoId, lang);
    if (fallbackText) return json({ text: fallbackText, language: lang });
    return json({ error: `Player API returned ${playerResp.status}` }, 502);
  }
  ```

---

### [MEDIUM] No HEALTHCHECK directive in Dockerfile
- **File**: `hookcut-backend/Dockerfile` (no HEALTHCHECK present)
- **Issue**: Docker has no `HEALTHCHECK` instruction. Docker and orchestrators (including Railway) cannot distinguish between "container running" and "application healthy."
- **Risk**: Docker will report the container as `Up` even if uvicorn has crashed and is being restarted, or if the app is returning 500s. `docker ps` and Railway's dashboard will show green when the service is broken.
- **Fix**:
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1
  ```
  `curl` is available in `python:3.12-slim`. Alternatively install `wget` and use `wget -qO- ...`.

---

### [MEDIUM] PostgreSQL exposed on host port 5432 in docker-compose.prod.yml
- **File**: `docker-compose.prod.yml` lines 5–14
- **Issue**: `ports: - "5432:5432"` exposes PostgreSQL to the host network. The password is `hookcut_dev` — a weak, clearly development credential used in the prod compose file.
- **Risk**: If the host firewall does not block 5432, PostgreSQL is reachable from the internet with a predictable credential. PostgreSQL on its default port is frequently scanned and attacked.
- **Fix**: Remove the port mapping. Services within the compose network can reach postgres by hostname. Only expose via an SSH tunnel or pgbouncer behind a private network when direct access is needed:
  ```yaml
  postgres:
    # Remove ports entirely — internal network only
    expose:
      - "5432"
  ```
  Also change `POSTGRES_PASSWORD: hookcut_dev` to a strong secret loaded from an env file.

---

### [MEDIUM] Celery Beat schedule not defined — scheduled tasks may not register
- **File**: `hookcut-backend/app/tasks/celery_app.py` (no `beat_schedule` in conf)
- **Issue**: `celery_app.conf.update(...)` does not define a `beat_schedule`. The scheduled tasks (`cleanup_expired_files`, free-credit reset) are described in project memory as existing, but if their schedule is defined inside the task module using `@app.on_after_configure` or decorator-based approach, it depends on `include=` loading the module — which only happens when a worker starts, not when beat starts standalone.
- **Risk**: If beat is run without a worker (as in the Procfile `beat:` process), it may not pick up task schedules defined in task modules. Scheduled cleanup will silently not run.
- **Fix**: Define the beat schedule explicitly in `celery_app.py`:
  ```python
  from celery.schedules import crontab
  celery_app.conf.beat_schedule = {
      "cleanup-expired-files": {
          "task": "app.tasks.scheduled.cleanup_expired_files",
          "schedule": crontab(minute="*/30"),
      },
  }
  ```

---

### [MEDIUM] Migration 001 uses `sa.DateTime` without `timezone=True`
- **File**: `hookcut-backend/alembic/versions/001_initial_schema.py` lines 27, 68, 101, etc.
- **Issue**: All `DateTime` columns use `sa.DateTime` without `timezone=True`. PostgreSQL stores these as `TIMESTAMP WITHOUT TIME ZONE`. When the application sets `timezone="UTC"` in Celery and presumably uses UTC datetimes throughout, any drift in the application server's system timezone will cause incorrect timestamps to be stored and queried.
- **Risk**: Date-range queries in admin (`time_range_days` in NARM insights) and session listing will return incorrect results if the server's local timezone ever changes. Free-credit monthly reset logic (`last_free_reset`) is particularly sensitive to timezone errors.
- **Fix**: Future migration to alter all timestamp columns:
  ```python
  op.alter_column("users", "created_at", type_=sa.DateTime(timezone=True))
  # ... for all DateTime columns
  ```
  In SQLAlchemy model definitions, use `sa.DateTime(timezone=True)` from now on.

---

### [MEDIUM] `docker-compose.prod.yml` uses `version: "3.9"` (deprecated)
- **File**: `docker-compose.prod.yml` line 1
- **Issue**: `version: "3.9"` is deprecated in Docker Compose v2. Modern Docker Compose ignores this field and uses the latest schema automatically.
- **Risk**: Low direct risk but indicates the file was written for an older Compose and may rely on behaviors that differ in Compose v2 (e.g., `depends_on` without condition checks — the prod compose has no `condition: service_healthy` on `depends_on`).
- **Fix**: Remove the `version:` key entirely and add health-check conditions to `depends_on`:
  ```yaml
  # Remove: version: "3.9"
  services:
    backend:
      depends_on:
        postgres:
          condition: service_healthy
        redis:
          condition: service_healthy
  ```

---

### [MEDIUM] No Content-Security-Policy header in next.config.ts
- **File**: `hookcut-frontend/next.config.ts` lines 14–28
- **Issue**: `headers()` sets `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, and `Permissions-Policy`, but no `Content-Security-Policy` (CSP).
- **Risk**: Without CSP, any XSS vulnerability in the React frontend (e.g., from unsanitized hook text rendered as HTML, or a malicious npm dependency) can execute arbitrary scripts, exfiltrate auth tokens (JWT/NextAuth session cookies), and make API requests on behalf of users.
- **Fix**:
  ```ts
  { key: "Content-Security-Policy",
    value: "default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self' https://api.hookcut.nyxpath.com; img-src 'self' data: https://i.ytimg.com; frame-ancestors 'none';" }
  ```
  Start with `report-only` mode and tighten from there.

---

### [MEDIUM] `wrangler.toml` missing `compatibility_date` recency check + no route restrictions
- **File**: `cloudflare-worker/wrangler.toml` line 3
- **Issue**: `compatibility_date = "2024-09-25"` is the compat date — this is fine but 6+ months old. More importantly, there are no `routes` defined, meaning the worker is deployed to the default `*.workers.dev` subdomain, publicly discoverable and reachable.
- **Risk**: The worker URL (`hookcut-transcript.{account}.workers.dev`) is publicly known once deployed. Even with `API_KEY` set, the endpoint is discoverable and scannable. No route restriction means the worker responds on all paths.
- **Fix**: Define an explicit route tied to your domain and add a `[triggers]` or `routes` block:
  ```toml
  routes = [
    { pattern = "transcript-worker.hookcut.nyxpath.com/*", zone_name = "hookcut.nyxpath.com" }
  ]
  ```

---

## LOW Findings

### [LOW] Procfile `web` process does not set `--workers` — single uvicorn process
- **File**: `hookcut-backend/Procfile` line 1
- **Issue**: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT` — no `--workers N` flag. Uvicorn runs as a single process.
- **Risk**: All requests are handled by one event loop. CPU-bound work (JSON parsing of large LLM responses) blocks the loop. Under concurrent load, p99 latency will spike.
- **Fix**: Either use `gunicorn` with uvicorn workers (`gunicorn -k uvicorn.workers.UvicornWorker -w 2 app.main:app`), or add `--workers 2` to uvicorn (note: this forks, so connection limits apply).

---

### [LOW] `nodejs` installed in Dockerfile but no version pinned — apt installs Node 18
- **File**: `hookcut-backend/Dockerfile` line 9
- **Issue**: `apt-get install -y nodejs` installs whatever Node.js version is in Debian bookworm's apt repository (Node 18 LTS). The project memory specifies "Must use Node 22" — this applies to the frontend, but if any yt-dlp JS challenge handling requires a newer Node, the wrong version is in the backend image.
- **Risk**: yt-dlp's JS challenge support (for anti-bot bypass) requires a sufficiently new Node.js. Node 18 EOL is April 2025; running an EOL Node in production is a security concern.
- **Fix**: Install Node via NodeSource to get a pinned, supported version:
  ```dockerfile
  RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
      apt-get install -y nodejs
  ```

---

### [LOW] `alembic/env.py` loads `.env` file — may override production environment variables
- **File**: `hookcut-backend/alembic/env.py` lines 4–5
- **Issue**: `load_dotenv()` is called unconditionally. On Railway, environment variables are injected by the platform. If a developer accidentally includes a `.env` file in the Docker build context (see MEDIUM finding about `.dockerignore`), `load_dotenv()` will load it and potentially override Railway's injected `DATABASE_URL`.
- **Risk**: `load_dotenv()` by default does NOT override existing environment variables, so in most cases Railway's variables take precedence. However, this is an implicit assumption. If `load_dotenv(override=True)` is ever added, or if the `.env` file contains a `DATABASE_URL` pointing to a dev database, migrations will run against the wrong database.
- **Fix**: Add `override=False` explicitly (it is the default but makes intent clear) and add a guard:
  ```python
  import os
  from dotenv import load_dotenv
  # Only load .env in local/dev — not in Railway (which injects env vars)
  if not os.environ.get("RAILWAY_ENVIRONMENT"):
      load_dotenv(override=False)
  ```

---

### [LOW] Celery `task_acks_late=True` without `task_reject_on_worker_lost=True`
- **File**: `hookcut-backend/app/tasks/celery_app.py` line 29
- **Issue**: `task_acks_late=True` delays message acknowledgment until task completion. This is correct for at-least-once delivery. However, without `task_reject_on_worker_lost=True`, if a worker is killed (OOM, SIGKILL from Railway), the task message will be re-queued only if the broker detects the connection drop — which can take minutes with default heartbeat settings.
- **Risk**: Tasks may appear to "disappear" from the queue after a worker crash. The session stays in `analyzing` state indefinitely with no re-queue.
- **Fix**:
  ```python
  celery_app.conf.update(
      ...
      task_acks_late=True,
      task_reject_on_worker_lost=True,  # Re-queue on unclean worker exit
  )
  ```

---

### [LOW] `docker-compose.yml` dev Redis has no password, no persistence config
- **File**: `hookcut-compose.yml` lines 15–20
- **Issue**: Dev Redis has no `requirepass` and no `save` configuration. Data is purely in-memory and lost on container restart.
- **Risk**: Low risk for development. However developers running integration tests against this Redis may lose task state unexpectedly. Also, muscle memory from dev Redis (no auth) can bleed into prod configuration mistakes.
- **Fix**: Document explicitly in the compose file that this is dev-only and add a comment that prod uses authenticated Redis.

---

### [LOW] Migration chain uses short numeric revision IDs ("001"–"008") instead of Alembic-generated hashes
- **File**: All migration files, e.g. `001_initial_schema.py` line 12: `revision: str = "001"`
- **Issue**: Alembic normally generates random hex revision IDs to prevent collisions. Using sequential numeric strings ("001", "002") is readable but risks collision if two developers create migrations simultaneously in different branches and both choose the next sequential number.
- **Risk**: Merge conflicts in the migration chain that require manual resolution. In a team environment, two PRs both adding "009_..." would create a fork in the chain that Alembic cannot auto-resolve.
- **Fix**: Use `alembic revision --autogenerate -m "description"` which generates unique hash-based IDs. For existing migrations, this is low priority as the chain is currently linear — but enforce going forward with a pre-commit hook or CI check that validates revision ID format.

---

## Non-Finding Observations (Correctly Implemented)

1. **`task_serializer="json"`** is correctly set. Pickle serializer (the old Celery default) allows remote code execution — JSON is safe.
2. **`worker_prefetch_multiplier=1`** is correctly set. This prevents workers from pulling more tasks than they can process, avoiding starvation of long-running tasks.
3. **`worker_max_tasks_per_child=20`** is correctly set. This prevents memory leaks from FFmpeg/yt-dlp process residue accumulating in the worker's heap.
4. **`enable_utc=True`** is correctly set in Celery config.
5. **Alembic migration chain (001→002→003→004→005→006→007→008)** is correctly chained with no gaps or forks.
6. **Migration 002** correctly uses `batch_alter_table` for SQLite compatibility.
7. **`X-Frame-Options: DENY`** correctly set in next.config.ts.
8. **Migration 003 (role column)** uses `server_default='user'` — safe for existing rows, no data migration needed.
9. **`task_acks_late=True`** is set — correct for video processing tasks that should not be lost on crash.
10. **CF Worker API key check** is present and correct when `env.API_KEY` is set — the gap is only in the optional enforcement.

---

## Prioritized Remediation Order

| Priority | Finding | Effort |
|----------|---------|--------|
| 1 | CRITICAL: Migration failure continues — `start.sh` L12 | 1 line |
| 2 | CRITICAL: No USER in Dockerfile — root process | 4 lines |
| 3 | CRITICAL: Create `.dockerignore` — secrets in image | 10 lines |
| 4 | CRITICAL: INNERTUBE_API_KEY hardcoded | Move to wrangler secret |
| 5 | CRITICAL: CF Worker CORS `*` + optional auth | ~10 lines |
| 6 | HIGH: `task_soft_time_limit` / `task_time_limit` missing | 2 lines |
| 7 | HIGH: `result_expires=300` too short | 1 line |
| 8 | HIGH: Remove source bind mounts from prod compose | 2 lines |
| 9 | HIGH: Redis auth + unexpose port in prod compose | 5 lines |
| 10 | HIGH: Pin base image | 1 line |
| 11 | HIGH: Migration 008 needs batch_alter_table | 4 lines |
| 12 | HIGH: Add health check path to railway.toml | 3 lines |
| 13 | MEDIUM: Add HEALTHCHECK to Dockerfile | 2 lines |
| 14 | MEDIUM: Increase result_expires | 1 line |
| 15 | MEDIUM: CSP header in next.config.ts | 5 lines |
