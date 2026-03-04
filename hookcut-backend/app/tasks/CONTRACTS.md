# HookCut Celery Task Layer -- Contracts

> Authoritative contract document for every Celery task in the HookCut backend.
> Covers task registration, input/output schemas, DB session patterns, state machines,
> retry logic, frontend polling contracts, inter-service calls, and invariants.

---

## Table of Contents

1. [Celery Infrastructure](#1-celery-infrastructure)
2. [Task: `run_analysis`](#2-task-run_analysis)
3. [Task: `generate_short`](#3-task-generate_short)
4. [Task: `reset_free_credits`](#4-task-reset_free_credits)
5. [Task: `cleanup_expired_files`](#5-task-cleanup_expired_files)
6. [Frontend Polling Contract](#6-frontend-polling-contract)
7. [Cross-Cutting Invariants](#7-cross-cutting-invariants)

---

## 1. Celery Infrastructure

### Broker & Backend

```python
# app/tasks/celery_app.py
celery_app = Celery(
    "hookcut",
    broker=settings.REDIS_URL,      # default: redis://localhost:6379/0
    backend=settings.REDIS_URL,     # same Redis instance
    include=[
        "app.tasks.analyze_task",
        "app.tasks.generate_short_task",
        "app.tasks.scheduled",
    ],
)
```

### Global Configuration

| Setting                      | Value      | Meaning                                                      |
|------------------------------|------------|--------------------------------------------------------------|
| `task_serializer`            | `"json"`   | All task args and return values serialized as JSON            |
| `accept_content`             | `["json"]` | Only JSON payloads accepted                                  |
| `result_serializer`          | `"json"`   | Results stored in Redis as JSON                              |
| `timezone`                   | `"UTC"`    | All timestamps in UTC                                        |
| `enable_utc`                 | `True`     | UTC enforcement                                              |
| `task_track_started`         | `True`     | Tasks report STARTED state (enables `self.update_state`)     |
| `task_acks_late`             | `True`     | Message acknowledged AFTER task completes (crash-safe)       |
| `worker_prefetch_multiplier` | `1`        | One message at a time (optimal for long-running tasks)       |
| `result_expires`             | `3600`     | Task results expire from Redis after 1 hour (seconds)        |

### Shared Constants

`celery_app.py` exports constants used across task modules and routers:

| Constant | Value | Used By |
|---|---|---|
| `ERROR_MSG_MAX_LEN` | `500` | `analyze_task`, `generate_short_task` — error message truncation |
| `FREE_MONTHLY_MINUTES` | `120.0` | `scheduled.reset_free_credits` — monthly credit reset |
| `DOWNLOAD_URL_EXPIRES_SECONDS` | `3600` | `generate_short_task`, `routers/shorts.py` — presigned URL TTL |

Import pattern: `from app.tasks.celery_app import celery_app, ERROR_MSG_MAX_LEN`

### Queue Assignment

No explicit queue routing is configured. All four tasks run on the **default queue** (`celery`).

### Beat Schedule (Periodic Tasks)

| Schedule Name                  | Task                                        | Cron                                    |
|--------------------------------|---------------------------------------------|-----------------------------------------|
| `monthly-free-credit-reset`    | `app.tasks.scheduled.reset_free_credits`    | 1st of month, 00:05 UTC                |
| `hourly-expired-file-cleanup`  | `app.tasks.scheduled.cleanup_expired_files` | Every hour at :30 minutes              |

### DB Session Pattern (All Tasks)

Tasks do **not** use FastAPI's request-scoped `get_db()` generator. Instead they call:

```python
# app/dependencies.py
from app.models.base import get_session_factory

def get_db_session() -> Session:
    """Direct session factory for use in Celery tasks (non-generator)."""
    return get_session_factory()()
```

Every task follows this pattern:

```python
db = get_db_session()
try:
    # ... task body ...
finally:
    db.close()
```

The session is manually closed in a `finally` block. There is no context manager, no `yield`, and no automatic rollback on exception -- the task must explicitly call `db.commit()` or `db.rollback()`.

**Engine configuration** (from `app/models/base.py`):
- SQLite: `check_same_thread=False`, WAL journal mode, `PRAGMA synchronous=NORMAL`
- PostgreSQL: `pool_size=5`, `pool_pre_ping=True`, `connect_timeout=10`
- Session factory: `autocommit=False`, `autoflush=False`

---

## 2. Task: `run_analysis`

### Task Registration

```python
# app/tasks/analyze_task.py
@celery_app.task(bind=True, max_retries=0)
def run_analysis(self, session_id: str):
```

| Property             | Value                                   |
|----------------------|-----------------------------------------|
| Celery registered name | `app.tasks.analyze_task.run_analysis` |
| Queue                | default (`celery`)                      |
| `bind`               | `True` (task instance available as `self`) |
| `max_retries`        | `0` (Celery-level retry disabled)       |
| Rate limit           | None configured at task level           |
| Soft time limit      | None configured                         |
| Hard time limit      | None configured                         |

### Input Contract

```python
def run_analysis(self, session_id: str) -> dict
```

| Parameter    | Type  | Source                                                                 |
|-------------|-------|------------------------------------------------------------------------|
| `session_id` | `str` | UUID v4 string. Passed by the API route via `run_analysis.delay(session.id)`. |

**Preconditions:** The `AnalysisSession` row **must already exist** in the DB with `status="pending"` and credits already deducted. The caller (API route) creates the session, deducts credits, commits the transaction, and only then dispatches the task.

**Dispatch sites:**

1. `POST /api/analyze` (initial analysis) — via `AnalyzeService.start_analysis()`:
```python
# app/services/analyze_service.py
task = run_analysis.delay(session.id)
session.task_id = task.id
db.commit()
```

2. `POST /api/sessions/{session_id}/regenerate` (hook regeneration) — via `AnalyzeService.regenerate_hooks()`:
```python
# app/services/analyze_service.py
session.status = "pending"
db.commit()
task = run_analysis.delay(session.id)
session.task_id = task.id
db.commit()
```

### Output Contract

**Return type:** `dict` serialized to JSON in Redis.

**Success result:**

```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "hooks_count": 5,
  "provider": "gemini",
  "attempts": 1
}
```

| Field         | Type  | Description                                           |
|---------------|-------|-------------------------------------------------------|
| `session_id`  | `str` | Echo of the input session ID                          |
| `hooks_count` | `int` | Number of hooks stored (always 5 on success)          |
| `provider`    | `str` | LLM provider that produced the result (e.g. `"gemini"`, `"anthropic"`) |
| `attempts`    | `int` | Number of LLM attempts taken (1-3)                    |

**Error result:**

```json
{
  "error": "Human-readable error message"
}
```

| Field   | Type  | Description                                                       |
|---------|-------|-------------------------------------------------------------------|
| `error` | `str` | Error description. Truncated to 200 chars for unexpected errors.  |

**Critical behavioral note:** Both success and error cases return a `dict` via `return`. The task catches all exceptions internally and never raises to Celery, so **the Celery task status will always be `SUCCESS`** from Celery's perspective. The caller must inspect the presence of `result["error"]` to detect logical failure. The Celery `FAILURE` state is never reached under normal operation.

### State Machine

```
                      API creates session
                             |
                             v
                     +---------------+
                     |    pending     |  (DB: AnalysisSession.status)
                     +-------+-------+
                             |
               run_analysis picks up task
                             |
                             v
                  +---------------------+
                  | fetching_transcript  |  DB commit + Celery PROGRESS(10%)
                  +----------+----------+
                             |
                    transcript fetch OK?
                   /                    \
                  NO                    YES
                  |                      |
                  v                      v
            +--------+         +----------------+
            | failed |         |   analyzing    |  DB commit + Celery PROGRESS(40%)
            +--------+         +-------+--------+
            (refund)                    |
                              HookEngine.analyze()
                             /                    \
                           FAIL                   OK
                            |                      |
                            v                      v
                      +--------+          Celery PROGRESS(80%)
                      | failed |          store hooks + LearningLogs
                      +--------+               |
                      (refund)                 v
                                       +--------------+
                                       |  hooks_ready |  DB commit + Celery PROGRESS(100%)
                                       +--------------+
                                               |
                                          return dict
                                               |
                                               v
                                       Celery: SUCCESS
```

**Dual status storage:** Status is tracked in BOTH the `AnalysisSession.status` DB column AND the Celery result backend (Redis). These serve different consumers:
- **DB status**: Used by `GET /api/sessions/{session_id}/hooks` to gate the hooks response
- **Celery status**: Used by `GET /api/tasks/{task_id}` for frontend progress polling

| DB Status              | Celery State   | Celery Meta                                           | Trigger                         |
|------------------------|----------------|-------------------------------------------------------|---------------------------------|
| `pending`              | `PENDING`      | --                                                    | Session created by API          |
| `fetching_transcript`  | `PROGRESS`     | `{"stage": "Fetching transcript...", "progress": 10}` | Task begins execution           |
| `analyzing`            | `PROGRESS`     | `{"stage": "Analyzing hooks...", "progress": 40}`     | Transcript fetched successfully |
| *(saving hooks)*       | `PROGRESS`     | `{"stage": "Saving hooks...", "progress": 80}`        | LLM analysis completed          |
| `hooks_ready`          | `PROGRESS`     | `{"stage": "Hooks ready!", "progress": 100}`          | Hooks persisted to DB           |
| *(task returns)*       | `SUCCESS`      | `{result dict}`                                       | `return` statement              |
| `failed`               | `SUCCESS`      | `{error dict}`                                        | Any failure path (note: still `SUCCESS` from Celery's view) |

**AnalysisSession.status -- all possible values:**

| Status                 | Meaning                                                    |
|------------------------|------------------------------------------------------------|
| `pending`              | Created, Celery task dispatched but not yet started        |
| `fetching_transcript`  | Worker is fetching transcript from YouTube                 |
| `analyzing`            | Worker is running LLM hook identification                  |
| `hooks_ready`          | Hooks generated, awaiting user selection                   |
| `generating_shorts`    | Short generation tasks dispatched (set by select-hooks API)|
| `completed`            | All Shorts ready for download                              |
| `failed`               | Analysis or generation failed; credits refunded            |

### DB Models Read/Written

| Model              | Read | Write | Details                                                  |
|--------------------|:----:|:-----:|----------------------------------------------------------|
| `AnalysisSession`  | Yes  | Yes   | Read by primary key. Writes: `status`, `transcript_provider`, `transcript_text`, `error_message`, `credits_refunded` |
| `Hook`             | Yes  | Yes   | Deletes all existing hooks for session (regeneration support). Inserts exactly 5 new `Hook` rows. Re-queries after flush to get generated IDs. |
| `LearningLog`      |      | Yes   | Inserts one `hook_presented` event per hook (5 total)    |
| `CreditBalance`    |      | Yes   | Via `CreditManager.refund_and_fail()` on failure paths   |
| `Transaction`      |      | Yes   | Via `CreditManager.refund()` on failure paths            |

**Transaction boundaries (commits):**

1. **Commit 1:** `session.status = "fetching_transcript"` -- signals task has started
2. **Commit 2:** `session.transcript_provider`, `session.transcript_text`, `session.status = "analyzing"` -- transcript persisted
3. **Commit 3 (failure path, via CreditManager.refund):** Inserts `Transaction` record (`type="credit_refund"`), updates `CreditBalance` buckets
4. **Commit 4 (failure path, via CreditManager.refund_and_fail):** Sets `session.status = "failed"`, `session.error_message`, `session.credits_refunded = True`
5. **Commit 5 (success path):** All 5 `Hook` inserts + all 5 `LearningLog` inserts + `session.status = "hooks_ready"` -- **single atomic commit**

### Retry Logic

**Celery-level:** Disabled (`max_retries=0`). The task will never be re-queued by Celery's retry mechanism.

**Application-level retry (inside `HookEngine.analyze`):**

```python
# app/services/hook_engine.py
MAX_RETRIES = 3
RETRY_DELAYS = [0, 5, 30]  # seconds of sleep before each attempt (longer for rate limits)
```

| Attempt | Delay Before | Provider Used                         | On Failure                    |
|---------|-------------|---------------------------------------|-------------------------------|
| 1       | 0s          | Primary (`settings.LLM_PRIMARY_PROVIDER`, default: Gemini) | Continue to attempt 2 |
| 2       | 5s          | Primary (same)                        | Continue to attempt 3         |
| 3       | 30s         | Fallback (Anthropic, via `get_fallback_provider`) | Raise `HookEngineError` |

**Exceptions that trigger internal retry:** Any exception from `provider.generate()` (LLM API errors, timeouts, rate limits) or from `_parse_and_validate()` (invalid JSON, wrong hook count, missing required fields, etc.).

**Permanent failure:** After 3 failed attempts, `HookEngineError` is raised with the message: `"All 3 hook analysis attempts failed. Last error: {last_error}"`. The task catches it, calls `CreditManager.refund_and_fail()`, and returns `{"error": str(e)}`.

**Idempotency considerations:** Partially idempotent on regeneration. Old hooks are deleted before new ones are inserted: `db.query(Hook).filter_by(session_id=session_id).delete()`. However, `LearningLog` entries are append-only and would duplicate if the task were somehow re-executed for the same session without cleanup.

### Inter-Service Calls

#### 1. TranscriptService.fetch

```python
# app/services/transcript.py
TranscriptService().fetch(
    video_id: str,    # from session.video_id
    language: str     # from session.language
) -> Optional[TranscriptResult]
```

```python
@dataclass
class TranscriptResult:
    text: str                            # timestamped transcript text
    provider: str                        # "youtube_transcript_api" | "ytdlp_subtitles" | "whisper_api"
    language_detected: Optional[str]     # language code if detected
```

**Provider cascade (3-level fallback):**

| Order | Provider                 | Method                          | Timeout | Condition                        |
|-------|--------------------------|--------------------------------------|---------|----------------------------------|
| 1     | youtube-transcript-api   | `_try_youtube_transcript_api`   | N/A     | Always tried first               |
| 2     | yt-dlp subtitle extract  | `_try_ytdlp_subtitles`         | 60s     | Tried if #1 fails                |
| 3     | OpenAI Whisper API       | `_try_whisper_api`              | 120s    | Tried if #1 and #2 fail AND `FEATURE_WHISPER_FALLBACK=True` |

Returns `None` on total failure (all providers failed). **Never raises exceptions** -- all errors are caught internally and logged at DEBUG level.

#### 2. HookEngine.analyze

```python
# app/services/hook_engine.py
HookEngine().analyze(
    transcript: str,  # from TranscriptResult.text
    niche: str,       # from session.niche
    language: str,    # from session.language (default "English")
    rules: list[dict] | None = None,  # optional admin DB rules (dicts with rule_key + content)
) -> HookEngineResult
```

```python
@dataclass
class HookEngineResult:
    hooks: list[HookCandidate]   # exactly 5 items
    provider: str                # e.g. "gemini", "anthropic"
    model: str                   # e.g. "gemini-2.5-flash"
    attempts: int                # 1-3
    input_tokens: Optional[int]
    output_tokens: Optional[int]

@dataclass
class HookCandidate:
    rank: int                    # 1-5
    hook_text: str               # transcript excerpt
    start_time: str              # e.g. "2:30" or "1:00+3:15" (composite)
    end_time: str                # e.g. "3:00" or "1:30+3:45" (composite)
    start_seconds: float         # parsed numeric start
    end_seconds: float           # parsed numeric end
    hook_type: str               # one of 18 hook types
    funnel_role: str             # one of 6 funnel roles
    scores: dict                 # 7-dimension scoring dict (keys below)
    attention_score: float       # 0.0-10.0 aggregate score
    platform_dynamics: str       # LLM-generated platform analysis
    viewer_psychology: str       # LLM-generated psychology analysis
    is_composite: bool           # True if hook spans non-contiguous segments
```

**Scores dict keys** (all clamped to [0, 10]):
```python
{
    "scroll_stop": float,
    "curiosity_gap": float,
    "stakes_intensity": float,
    "emotional_voltage": float,
    "standalone_clarity": float,
    "thematic_focus": float,
    "thought_completeness": float
}
```

**Raises:** `HookEngineError` on total failure (3 attempts exhausted). The task catches this specifically.

#### 3. CreditManager.refund_and_fail

```python
# app/services/credit_manager.py
CreditManager(db).refund_and_fail(
    session_id: str,
    error_msg: str,
    _logger=logger     # optional, defaults to module logger
) -> None
```

**Behavior:**
1. Looks up `AnalysisSession` by `session_id`
2. If `session.credits_refunded` is `False` AND `session.minutes_charged > 0`:
   - Calls `self.refund()` with the exact per-bucket amounts stored on the session (`paid_minutes_used`, `payg_minutes_used`, `free_minutes_used`)
   - Sets `session.credits_refunded = True`
3. Sets `session.status = "failed"`
4. Sets `session.error_message = error_msg`
5. Commits the transaction

**Refund atomicity:** The refund creates a `Transaction` record (type: `"credit_refund"`) and updates `CreditBalance` buckets in a single `db.commit()`. The subsequent `session.status = "failed"` commit is separate.

### Error Propagation Summary

| Exception Source            | Exception Type       | Handling in Task                                      |
|-----------------------------|----------------------|-------------------------------------------------------|
| `TranscriptService.fetch`   | Returns `None`       | `refund_and_fail()`, return `{"error": "Transcript unavailable"}` |
| `HookEngine.analyze`        | `HookEngineError`    | `refund_and_fail()`, return `{"error": str(e)}`       |
| Any other code              | `Exception`          | Caught by outer try/except, `refund_and_fail()`, return `{"error": str(e)}` |
| `refund_and_fail` itself    | `Exception`          | Logged via `logger.exception()`, swallowed (task still returns error dict) |

---

## 3. Task: `generate_short`

### Task Registration

```python
# app/tasks/generate_short_task.py
@celery_app.task(bind=True, max_retries=0)
def generate_short(self, short_id: str):
```

| Property               | Value                                            |
|------------------------|--------------------------------------------------|
| Celery registered name | `app.tasks.generate_short_task.generate_short`   |
| Queue                  | default (`celery`)                               |
| `bind`                 | `True`                                           |
| `max_retries`          | `0` (Celery-level retry disabled)                |
| Rate limit             | None configured                                  |
| Soft time limit        | None configured                                  |
| Hard time limit        | None configured                                  |

### Input Contract

```python
def generate_short(self, short_id: str) -> dict
```

| Parameter  | Type  | Source                                                                        |
|-----------|-------|-------------------------------------------------------------------------------|
| `short_id` | `str` | UUID v4 string. Passed by the API route via `generate_short.delay(short.id)`. |

**Preconditions:** The `Short` row **must already exist** in the DB with `status="queued"`. The parent `AnalysisSession` must exist with `status="generating_shorts"`. The parent `Hook` must exist with `is_selected=True`.

**Dispatch site** (`POST /api/sessions/{session_id}/select-hooks`):

```python
# app/routers/analysis.py
for hook_id in req.hook_ids:               # 1-3 hooks
    override = req.time_overrides.get(hook_id)
    short = Short(
        session_id=session_id,
        hook_id=hook_id,
        status="queued",
        caption_style=req.caption_style,
        start_seconds_override=override.start_seconds if override else None,
        end_seconds_override=override.end_seconds if override else None,
        is_watermarked=session.is_watermarked,
    )
    db.add(short)
    db.flush()                              # get short.id

    task = generate_short.delay(short.id)   # dispatch
    short.task_id = task.id

session.status = "generating_shorts"
db.commit()
```

Up to **3 `generate_short` tasks** are dispatched from a single API request.

### Output Contract

**Success result:**

```json
{
  "short_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "ready",
  "title": "The AI trick nobody talks about",
  "duration": 28.5
}
```

| Field       | Type             | Description                             |
|-------------|------------------|-----------------------------------------|
| `short_id`  | `str`            | Echo of input Short ID                  |
| `status`    | `str`            | Always `"ready"` on success             |
| `title`     | `str`            | LLM-generated title, max 60 chars       |
| `duration`  | `float \| None`  | Duration in seconds                     |

**Error result:**

```json
{
  "error": "Human-readable error message"
}
```

Same pattern as `run_analysis`: the task catches all exceptions and returns a dict, so **Celery status is always `SUCCESS`**. Logical failure is indicated by the presence of `error` in the result dict.

### State Machine

```
         API creates Short record
                    |
                    v
             +-----------+
             |   queued   |  (DB: Short.status)
             +-----+-----+
                   |
       generate_short picks up task
                   |
                   v
           +---------------+
           |  processing   |  DB commit + Celery PROGRESS(10%)
           +-------+-------+
                   |
      ShortGenerator.generate()
     /                          \
   FAIL                        OK
    |                           |
    v                           v
+--------+              Celery PROGRESS(80%)
| failed |              storage upload (video + thumbnail in parallel)
+--------+                     |
    |                          v
    |                    +---------+
    |                    |  ready  |  DB commit + Celery PROGRESS(100%)
    |                    +---------+
    |                          |
    |               _check_session_completion()
    |                          |
    |                 all shorts ready?
    |                /                 \
    |              YES                 NO
    |               |                   |
    |               v                   |
    |    session.status =              (wait for
    |      "completed"               other shorts)
    |
    +---> _check_all_shorts_failed()
                   |
          all shorts failed?
         /                  \
       YES                  NO
        |                    |
        v                    |
  session.status =          (some shorts
    "failed"               may still succeed)
  (credits refunded)
```

**Short.status -- all possible values:**

| Status        | Meaning                                        | Set By                              |
|---------------|------------------------------------------------|-------------------------------------|
| `queued`      | Short record created, task dispatched          | API route (`select-hooks`)          |
| `processing`  | Task has started; downloading + rendering      | `generate_short` task               |
| `ready`       | Video generated, uploaded, download URL set    | `generate_short` task               |
| `failed`      | Generation failed, `error_message` populated   | `generate_short` task (except path) |
| `expired`     | File TTL exceeded, storage files deleted        | `cleanup_expired_files` beat task   |

**Note:** The `Short` model comment lists `downloading` and `uploading` as possible status values, but the task code never sets them. Only `queued`, `processing`, `ready`, `failed`, and `expired` are used in practice.

**AnalysisSession.status transitions triggered by this task:**

| Condition                      | Session Status Change                     |
|--------------------------------|-------------------------------------------|
| All shorts reach `ready`       | `generating_shorts` -> `completed`        |
| ALL shorts reach `failed`      | `generating_shorts` -> `failed` (with credit refund) |
| Mix of ready/failed            | Remains `generating_shorts` until the last short resolves |

### DB Models Read/Written

| Model              | Read | Write | Details                                                          |
|--------------------|:----:|:-----:|------------------------------------------------------------------|
| `Short`            | Yes  | Yes   | Read by primary key. Writes: `status`, `title`, `cleaned_captions`, `video_file_key`, `thumbnail_file_key`, `duration_seconds`, `file_size_bytes`, `download_url`, `download_url_expires_at`, `expires_at`, `error_message` |
| `AnalysisSession`  | Yes  | Yes   | Read for `youtube_url`, `is_watermarked`, `language`, `niche`. Writes `status` on session completion/failure. |
| `Hook`             | Yes  |       | Read for `start_time`, `end_time`, `start_seconds`, `end_seconds`, `hook_text`, `is_composite` |
| `CreditBalance`    |      | Yes   | Via `CreditManager.refund_and_fail()` only if ALL shorts fail    |
| `Transaction`      |      | Yes   | Via `CreditManager.refund()` only if ALL shorts fail             |

**Transaction boundaries (commits):**

1. **Commit 1:** `short.status = "processing"` -- marks task active
2. **Commit 2 (success):** Atomic commit of all Short metadata: `status = "ready"`, `title`, `cleaned_captions`, `video_file_key`, `thumbnail_file_key`, `duration_seconds`, `file_size_bytes`, `download_url`, `download_url_expires_at`, `expires_at`
3. **Commit 3 (success, conditional):** `session.status = "completed"` -- only if `_check_session_completion` determines all shorts are ready
4. **Commit (failure path):** `short.status = "failed"`, `short.error_message = str(e)[:500]`
5. **Commit (all-failed path):** Via `CreditManager.refund_and_fail` -- session status set to `"failed"`, credits refunded, transaction logged

### Retry Logic

**Celery-level:** Disabled (`max_retries=0`).

**Application-level:** None. Unlike `run_analysis`, there is no internal retry loop. If `ShortGenerator.generate()` fails, the exception propagates immediately to the task's except block.

**LLM calls within ShortGenerator** (caption cleanup and title generation) are fire-and-forget with graceful fallback:
- If caption cleanup LLM call fails: raw `hook_text` is used as captions
- If title generation LLM call fails: `"Hook Segment"` is used as the title
- These LLM failures **never** cause the task itself to fail

**Idempotency:** NOT idempotent. Re-running the task would re-download from YouTube, re-render via FFmpeg, and re-upload to storage, creating duplicate storage objects. Previous video/thumbnail files would be orphaned since the old `video_file_key` is overwritten in the DB.

### Inter-Service Calls

#### 1. ShortGenerator.generate

```python
# app/services/short_generator.py
ShortGenerator().generate(
    youtube_url: str,        # from session.youtube_url
    hook: dict,              # constructed from Hook model fields (shape below)
    session_id: str,         # from session.id
    short_id: str,           # from short.id
    is_watermarked: bool,    # from short.is_watermarked
    language: str,           # from session.language (default "English")
    niche: str,              # from session.niche (default "Generic")
) -> ShortResult
```

**The `hook` dict shape passed by the task:**

```python
hook = {
    "start_time": hook.start_time,         # str, e.g. "2:30"
    "end_time": hook.end_time,             # str, e.g. "3:00"
    "start_seconds": hook.start_seconds,   # float
    "end_seconds": hook.end_seconds,       # float
    "hook_text": hook.hook_text,           # str
    "is_composite": hook.is_composite,     # bool
}
```

**Return type:**

```python
@dataclass
class ShortResult:
    video_path: str              # absolute path to rendered MP4 in temp dir
    thumbnail_path: str          # absolute path to thumbnail JPG in temp dir
    title: str                   # LLM-generated title (max 60 chars)
    cleaned_captions: str        # LLM-cleaned caption text
    duration_seconds: Optional[float]
    file_size_bytes: Optional[int]
```

**Raises:** `ShortGenerationError` on failure (segment extraction failed, FFmpeg render failed, etc.).

**Internal pipeline (6 steps):**

| Step | Operation                       | Parallelism                        |
|------|---------------------------------|------------------------------------|
| 1    | yt-dlp segment extraction       | ThreadPoolExecutor (3 workers)     |
| 2    | LLM caption cleanup             | ThreadPoolExecutor (3 workers)     |
| 3    | LLM title generation            | ThreadPoolExecutor (3 workers)     |
| 4    | ASS subtitle generation         | Sequential (after steps 1-3)       |
| 5    | FFmpeg single-pass render       | Sequential                         |
| 6    | Thumbnail extraction            | Sequential (non-fatal if fails)    |

Steps 1-3 run in parallel via `ThreadPoolExecutor(max_workers=3)`.

#### 2. StorageService.upload (called twice in parallel)

```python
# app/services/storage.py
StorageService().upload(
    local_path: str,   # absolute path to local file
    key: str           # storage key
) -> str               # returns access URL (R2) or local filesystem path
```

**Storage keys used:**
- Video: `"shorts/{short_id}/video.mp4"`
- Thumbnail: `"shorts/{short_id}/thumbnail.jpg"`

Upload is parallelized via `ThreadPoolExecutor(max_workers=2)`.

**Storage backend** (determined by `FEATURE_R2_STORAGE` flag):
- `False` (default): Local filesystem under `{cwd}/storage/`
- `True`: Cloudflare R2 (S3-compatible) via boto3

#### 3. StorageService.get_download_url

```python
StorageService().get_download_url(
    key: str,           # storage key
    expires_in: int     # seconds, hardcoded to 3600
) -> str               # presigned URL (R2) or local path (filesystem)
```

#### 4. _check_session_completion (helper function)

```python
# app/tasks/generate_short_task.py
def _check_session_completion(db, session):
```

Queries `COUNT(Short.id) WHERE session_id = ? AND status = 'ready'` and `COUNT(Short.id) WHERE session_id = ?`. If all shorts are ready, sets `session.status = "completed"` and commits.

#### 5. _check_all_shorts_failed (helper function)

```python
# app/tasks/generate_short_task.py
def _check_all_shorts_failed(db, session):
```

Queries `COUNT(Short.id) WHERE session_id = ? AND status = 'failed'` and `COUNT(Short.id) WHERE session_id = ?`. If ALL shorts have failed, calls `CreditManager(db).refund_and_fail()` with message `"All Short generations failed. Credits refunded."`.

### Error Propagation Summary

| Exception Source                  | Exception Type            | Handling in Task                                    |
|-----------------------------------|---------------------------|-----------------------------------------------------|
| `ShortGenerator.generate`         | `ShortGenerationError`    | Caught, `short.status = "failed"`, check all-failed |
| `StorageService.upload`           | Any                       | Caught by outer except, same as above               |
| `StorageService.get_download_url` | Any                       | Caught by outer except, same as above               |
| Any other code                    | `Exception`               | Caught, `short.status = "failed"`, `error_message` stored (truncated to 500 chars), check all-failed |
| Inner exception handling          | `Exception`               | Logged via `logger.exception()`, swallowed          |

### Temp File Lifecycle

1. `ShortGenerator.generate()` creates a temp directory: `hookcut_short_{short_id[:8]}_*` via `tempfile.mkdtemp()`
2. Files within: `segment.mp4` (or `seg_0.mp4`...`combined.mp4` for composites), `captions.ass`, `output.mp4`, `thumbnail.jpg`
3. After successful upload, the task cleans up: `shutil.rmtree(work_dir, ignore_errors=True)`
4. **On failure, temp files remain** -- cleanup only happens on the success path. No periodic cleanup of orphaned temp dirs exists.

### Short Expiration

On success, the `Short` record receives two independent expiry times:

```python
# File expiration (when storage files are deleted by cleanup_expired_files)
short.expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.TEMP_FILE_TTL_HOURS)
# Default TEMP_FILE_TTL_HOURS = 24

# Download URL expiration (presigned URL validity)
short.download_url_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
```

The frontend can request a fresh download URL at any time via `POST /api/shorts/{short_id}/download` (as long as the Short hasn't expired).

---

## 4. Task: `reset_free_credits`

### Task Registration

```python
# app/tasks/scheduled.py
@celery_app.task
def reset_free_credits():
```

| Property               | Value                                            |
|------------------------|--------------------------------------------------|
| Celery registered name | `app.tasks.scheduled.reset_free_credits`         |
| Queue                  | default (`celery`)                               |
| `bind`                 | `False`                                          |
| `max_retries`          | Default (3, Celery default)                      |
| Rate limit             | None configured                                  |
| Schedule               | Celery Beat: 1st of each month at 00:05 UTC      |

### Input Contract

No parameters. Triggered exclusively by Celery Beat.

### Output Contract

```json
{
  "reset_count": 1234
}
```

| Field         | Type  | Description                              |
|---------------|-------|------------------------------------------|
| `reset_count` | `int` | Number of `CreditBalance` rows updated   |

### Behavior

Iterates over ALL `CreditBalance` rows in batches of 500:

```python
balance.free_minutes_remaining = 120.0    # reset to 120 free minutes
balance.free_minutes_total = 120.0
balance.last_free_reset = datetime.now(timezone.utc)
```

Commits after each batch of 500 (not a single transaction for all rows).

### DB Models Read/Written

| Model           | Read | Write | Details                                                     |
|-----------------|:----:|:-----:|-------------------------------------------------------------|
| `CreditBalance` | Yes  | Yes   | Resets `free_minutes_remaining`, `free_minutes_total`, `last_free_reset` for every row |

### Error Handling

No explicit error handling beyond the `finally: db.close()`. If a batch fails mid-way, previously committed batches persist -- **partial reset is possible**. This is acceptable because the operation is idempotent (re-running sets the same values).

### Retry Logic

Uses Celery's default retry behavior (`max_retries=3`). No custom `autoretry_for` or `retry_backoff` is configured, so retries use Celery's default 180-second countdown.

---

## 5. Task: `cleanup_expired_files`

### Task Registration

```python
# app/tasks/scheduled.py
@celery_app.task
def cleanup_expired_files():
```

| Property               | Value                                              |
|------------------------|----------------------------------------------------|
| Celery registered name | `app.tasks.scheduled.cleanup_expired_files`        |
| Queue                  | default (`celery`)                                 |
| `bind`                 | `False`                                            |
| `max_retries`          | Default (3, Celery default)                        |
| Rate limit             | None configured                                    |
| Schedule               | Celery Beat: every hour at :30 minutes             |

### Input Contract

No parameters. Triggered exclusively by Celery Beat.

### Output Contract

```json
{
  "cleaned": 42
}
```

| Field     | Type  | Description                            |
|-----------|-------|----------------------------------------|
| `cleaned` | `int` | Number of expired Shorts processed     |

### Behavior

Queries Shorts matching `status = "ready" AND expires_at < now()` in batches of 500:

```python
for short in expired:
    if short.video_file_key:
        storage.delete(short.video_file_key)       # delete video from storage
    if short.thumbnail_file_key:
        storage.delete(short.thumbnail_file_key)   # delete thumbnail from storage
    short.status = "expired"
    short.download_url = None
```

Commits after each batch of 500.

### DB Models Read/Written

| Model   | Read | Write | Details                                                        |
|---------|:----:|:-----:|----------------------------------------------------------------|
| `Short` | Yes  | Yes   | Filters by `status="ready"` + `expires_at < now()`. Sets `status="expired"`, clears `download_url`. |

### Inter-Service Calls

```python
# app/services/storage.py
StorageService().delete(key: str) -> None
```

Deletes from R2 (S3 `delete_object`) or local filesystem (`os.remove`) depending on `FEATURE_R2_STORAGE` flag. Local delete is a no-op if the file doesn't exist.

### Error Handling

No explicit error handling. If `storage.delete()` fails for one file, the exception will abort the current batch. Previously committed batches persist. The Short whose deletion failed will remain in `status="ready"` and be retried on the next hourly run.

### Retry Logic

Uses Celery's default retry behavior (`max_retries=3`).

---

## 6. Frontend Polling Contract

### Polling Configuration

```typescript
// hookcut-frontend/src/lib/types.ts
export const POLL_CONFIG = {
  initial: 1000,      // 1 second initial interval
  multiplier: 1.5,    // exponential backoff multiplier
  max: 5000,          // cap at 5 seconds
} as const;
```

**Backoff sequence:** 1000ms, 1500ms, 2250ms, 3375ms, 5000ms, 5000ms, 5000ms, ...

### Analysis Task Polling (`usePollTask`)

**Hook:** `usePollTask(taskId, sessionId, onComplete, onError, onProgress)`

**File:** `hookcut-frontend/src/hooks/usePollTask.ts`

**Endpoint polled:** `GET /api/tasks/{task_id}`

**Response schema (backend `TaskStatusResponse`):**

```typescript
interface TaskStatus {
  task_id: string;
  status: "PENDING" | "STARTED" | "PROGRESS" | "SUCCESS" | "FAILURE";
  progress: number | null;    // 0-100
  stage: string | null;       // human-readable stage description
  result: Record<string, unknown> | null;  // only populated on SUCCESS
  error: string | null;       // only populated on FAILURE (max 2000 chars)
}
```

**Backend implementation** (`app/routers/tasks.py`):

```python
result = celery_app.AsyncResult(task_id)
status = result.status

if status == "PROGRESS":
    meta = result.info or {}
    progress = meta.get("progress")
    stage = meta.get("stage")
elif status == "SUCCESS":
    task_result = result.result
    progress = 100
elif status == "FAILURE":
    error = str(result.info) if result.info else "Unknown error"
```

**Polling behavior by Celery status:**

| Celery Status | Frontend Callback                                      | Continue Polling? |
|---------------|--------------------------------------------------------|:-----------------:|
| `PENDING`     | `onProgress(0, "Waiting for worker...")`               | Yes               |
| `STARTED`     | `onProgress(0, "Waiting for worker...")`               | Yes               |
| `PROGRESS`    | `onProgress(status.progress, status.stage)`            | Yes               |
| `SUCCESS`     | `onComplete(status)` -- caller must check `result.error` | No              |
| `FAILURE`     | `onError(status.error \|\| "Task failed. Please try again.")` | No          |

**Critical nuance:** Because `run_analysis` and `generate_short` both catch all exceptions internally and return dicts, the Celery status will virtually always be `SUCCESS`. The `FAILURE` state would only occur if the Celery worker itself crashes (OOM, SIGKILL, etc.). The frontend's `onComplete` callback **must inspect `status.result.error`** to detect logical failures.

**Timeout:** None. Polling continues indefinitely with exponential backoff capped at 5 seconds. If the `fetch()` call throws (network error), polling stops immediately and `onError("Lost connection. Please try again.")` is called.

**Cleanup:** The hook returns `{ isPolling, stopPolling }`. The effect cleanup function cancels polling when the component unmounts or when `taskId`/`sessionId` changes.

### Short Generation Polling (`useShortPoller`)

**Hook:** `useShortPoller(shortId, enabled)`

**File:** `hookcut-frontend/src/hooks/useShortPoller.ts`

**Endpoint polled:** `GET /api/shorts/{short_id}`

**Response schema (backend `ShortResponse`):**

```typescript
interface Short {
  id: string;
  hook_id: string;
  status: string;          // "queued" | "processing" | "ready" | "failed" | "expired"
  is_watermarked: boolean;
  title: string | null;
  cleaned_captions: string | null;
  duration_seconds: number | null;
  file_size_bytes: number | null;
  download_url: string | null;
  download_url_expires_at: string | null;
  thumbnail_url: string | null;
  error_message: string | null;
}
```

**Polling behavior by Short.status:**

| Short Status  | Frontend Action                          | Continue Polling? |
|---------------|------------------------------------------|:-----------------:|
| `queued`      | Show loading state                       | Yes               |
| `processing`  | Show loading state                       | Yes               |
| `ready`       | Show video player and download button    | No                |
| `failed`      | Show `error_message`                     | No                |
| `expired`     | (not typically reached during polling)   | No                |

**Key difference from analysis polling:** This poller queries the **Short model directly** via the REST endpoint (not the Celery task status). It sees the DB-level `Short.status`, not the Celery state or progress metadata. There is no progress percentage or stage information -- only the status transition from `queued` -> `processing` -> `ready`/`failed`.

**Same exponential backoff** as the analysis poller (1s -> 1.5s -> ... -> 5s cap). No explicit timeout.

### Complete Frontend Flow

```
1. User submits URL + niche + language
   -> POST /api/analyze
   <- { session_id, task_id, video_title, video_duration_seconds,
        minutes_charged, is_watermarked }

2. Frontend polls analysis task via usePollTask
   -> GET /api/tasks/{task_id}  (every 1-5s with exponential backoff)
   <- TaskStatus { status, progress, stage, result, error }

   Progress stages seen:
     10% - "Fetching transcript..."
     40% - "Analyzing hooks..."
     80% - "Saving hooks..."
    100% - "Hooks ready!"

3. Analysis complete -> frontend fetches hooks
   -> GET /api/sessions/{session_id}/hooks
   <- { session_id, status: "hooks_ready", hooks: [5 HookResponse objects],
        regeneration_count }

4. User selects 1-3 hooks
   -> POST /api/sessions/{session_id}/select-hooks  { hook_ids: [...] }
   <- { short_ids: [...], task_ids: [...] }

5. Frontend polls each Short via useShortPoller (one per short_id)
   -> GET /api/shorts/{short_id}  (per short, every 1-5s with backoff)
   <- Short { id, status, title, download_url, ... }

6. Short ready -> user downloads
   -> POST /api/shorts/{short_id}/download
   <- { download_url, expires_at }  (URL valid for 1 hour)
```

---

## 7. Cross-Cutting Invariants

### Admin Audit Logging
Admin actions are logged synchronously within `AdminService` methods (not via Celery tasks). The `AdminAuditLog` model stores all admin actions with before/after state for revertability. No background task queue is involved — audit entries are committed in the same DB transaction as the action.

### Credit Deduction Timing

Credits are deducted **BEFORE** the Celery task is dispatched, **AFTER** the `AnalysisSession` is created:

```python
# app/routers/analysis.py -- POST /api/analyze

# Step 1: Create session to get a real session_id
session = AnalysisSession(user_id=user_id, ..., status="pending")
db.add(session)
db.flush()  # <-- generates session.id (UUID)

# Step 2: Deduct credits with real session_id
deduction = credit_mgr.deduct(user_id, minutes_needed, session_id=session.id)
# CreditManager.deduct() creates a Transaction with the real session_id
session.paid_minutes_used = deduction.paid_used
session.payg_minutes_used = deduction.payg_used
session.free_minutes_used = deduction.free_used
db.commit()  # <-- session + deduction atomically committed

# Step 3: Dispatch task AFTER commit
task = run_analysis.delay(session.id)
session.task_id = task.id
db.commit()
```

This ordering ensures:
- The `Transaction` record always references a real `session_id` (not a placeholder)
- Credits are reserved before any async work begins
- If task dispatch fails (Redis down), credits are deducted and the session exists with `status="pending"` but no `task_id` -- the user has lost credits with no work done (no automatic recovery mechanism exists)

### Credit Refund Guarantee

**Analysis failures:** If the analysis task fails for any reason, credits are refunded to the **exact same buckets** they were deducted from:

```python
# app/services/credit_manager.py
self.refund(
    user_id=session.user_id,
    session_id=session.id,
    paid_minutes=session.paid_minutes_used,
    payg_minutes=session.payg_minutes_used,
    free_minutes=session.free_minutes_used,
)
session.credits_refunded = True  # prevents double-refunding
```

The `credits_refunded` boolean flag on `AnalysisSession` is checked before refunding: `if not session.credits_refunded and session.minutes_charged > 0`.

**Short generation failures:** Credits are only refunded if **ALL** shorts in the session fail. Partial failure (e.g., 1 of 3 shorts fails, 2 succeed) does **not** trigger any refund.

### Concurrency Assumptions

- **Multiple `run_analysis` tasks:** Can run concurrently for different sessions. No cross-session locking. Two analysis tasks for the same session should not occur under normal operation (the API ensures a new task is only dispatched when the session is in `pending` or `hooks_ready`/`completed` state for regeneration).

- **Multiple `generate_short` tasks for the same session:** Up to 3 can run concurrently (one per selected hook). They share the same session row but write to different `Short` rows. The `_check_session_completion` and `_check_all_shorts_failed` helpers query aggregate counts, creating a **benign race condition**: if two shorts complete simultaneously, both may see `total == ready` and both set `session.status = "completed"`. This is safe because the write is idempotent.

- **`worker_prefetch_multiplier=4`:** Each worker process may prefetch up to 4 tasks from the broker.

- **`task_acks_late=True`:** If a worker crashes mid-task, the unacknowledged message returns to the queue and is re-delivered to another worker. Combined with `max_retries=0`, this means the task body will re-execute from scratch. For `generate_short`, this can create duplicate storage objects. For `run_analysis`, old hooks are deleted before new ones are inserted, so the re-execution is mostly safe (except for duplicate `LearningLog` entries).

### Ordering Constraints

| Constraint | Enforced By |
|-----------|------------|
| `AnalysisSession` must exist before `run_analysis.delay()` | API route creates and commits session first |
| `Short` record must exist before `generate_short.delay()` | API route creates, flushes, and commits Short first |
| Credits must be deducted before task dispatch | API route deducts and commits before `.delay()` |
| Hooks must be in `hooks_ready` to allow `select-hooks` | API route checks `session.status == "hooks_ready"` (HTTP 400 otherwise) |
| Session must be in `hooks_ready` or `completed` to allow `regenerate` | API route checks status (HTTP 400 otherwise) |
| Short must have `status="ready"` to allow download | Shorts router checks `short.status != "ready"` (HTTP 400 otherwise) |

### Configuration Dependencies

| Setting                         | Default                       | Used By                                           |
|---------------------------------|-------------------------------|---------------------------------------------------|
| `REDIS_URL`                     | `redis://localhost:6379/0`    | Celery broker + result backend                    |
| `DATABASE_URL`                  | `sqlite:///hookcut.db`        | All tasks via `get_db_session()` (must be absolute path for Celery workers) |
| `TEMP_FILE_TTL_HOURS`           | `24`                          | `generate_short` (sets `Short.expires_at`)        |
| `LLM_PRIMARY_PROVIDER`          | `"gemini"`                    | `HookEngine` (analysis), `ShortGenerator` (captions/title) |
| `FEATURE_WHISPER_FALLBACK`      | `True`                        | `TranscriptService` (enables 3rd fallback provider) |
| `FEATURE_R2_STORAGE`            | `False`                       | `StorageService` (local filesystem vs Cloudflare R2) |
| `MAX_CONCURRENT_ANALYSES`       | `10`                          | Defined in config but **not enforced** at task level |
| `RATE_LIMIT_ANALYSES_PER_HOUR`  | `10`                          | Defined in config but **not enforced** at task level |

### SQLite Absolute Path Invariant

The `DATABASE_URL` **must** use an absolute path when SQLite is the backend:

```
sqlite:////absolute/path/hookcut.db   (4 slashes: sqlite:/// + /absolute/path)
```

This is validated at startup in `Settings.validate_required_settings()`. Celery workers run in a separate process (potentially with a different working directory) from the FastAPI server. A relative path would resolve to a different file, causing the worker to operate on an empty or wrong database.

### Result Expiry

Celery task results are stored in Redis with `result_expires=3600` (1 hour). After this, `celery_app.AsyncResult(task_id)` returns `PENDING` status regardless of whether the task actually ran. The frontend should complete its polling well within this window.

### Known Edge Cases

1. **Task dispatch failure:** If Redis is down when `.delay()` is called, the API route will raise an unhandled exception. Credits will have been deducted (committed) but no task will run. The session stays in `pending` forever. No automatic recovery exists.

2. **Worker crash during `generate_short`:** Due to `task_acks_late=True`, the task re-executes on another worker. The first worker's temp files are orphaned. The re-execution may create duplicate storage objects under the same key (overwriting is benign for S3/R2, but creates orphaned inodes on local filesystem).

3. **Simultaneous session completion:** If 2-3 `generate_short` tasks complete at the exact same moment, `_check_session_completion` may be called concurrently. Both will read the same counts and both will set `session.status = "completed"`. This is idempotent and harmless.

4. **Partial Short failure with no refund:** If 1 of 3 shorts fails and 2 succeed, no credits are refunded. The user receives fewer shorts than expected but is charged the full analysis amount. This is by design -- credits cover the analysis, not individual short generation.

5. **LearningLog duplication on crash recovery:** If `run_analysis` crashes after committing hooks + learning logs but before returning, the re-execution (via `task_acks_late`) will delete and re-insert hooks but will append duplicate `LearningLog` entries (since learning logs are never deleted).
