# HookCut Services Layer -- API Contracts

> Generated from `hookcut-backend/app/services/`, `schemas/`, `models/`, `llm/provider.py`, and `utils/`.
>
> Every public method, its exact signature, return type, dependencies, error handling, and invariants.

---

## Table of Contents

1. [AnalyzeService](#1-analyzeservice)
2. [CreditManager](#2-creditmanager)
3. [HookEngine](#3-hookengine)
4. [TranscriptService](#4-transcriptservice)
5. [VideoMetadataService](#5-videometadataservice)
6. [ShortGenerator](#6-shortgenerator)
7. [StorageService](#7-storageservice)
8. [PaymentService](#8-paymentservice)
9. [SubscriptionService](#9-subscriptionservice)
10. [WebhookService](#10-webhookservice)
11. [Analytics (module-level functions)](#11-analytics-module-level-functions)
12. [LLM Provider Interface](#12-llm-provider-interface)
13. [Utility Modules](#13-utility-modules)
14. [Shared Data Types Reference](#14-shared-data-types-reference)
15. [BillingService](#15-billingservice)
16. [ShortsService](#16-shortsservice)
17. [UserService](#17-userservice)
18. [AdminService](#18-adminservice)

---

## 1. AnalyzeService

**File:** `hookcut-backend/app/services/analyze_service.py`

**Class Purpose:** Central service for the analysis pipeline. All 5 public methods are `@staticmethod`. Covers URL validation, session creation with credit deduction, hook retrieval, regeneration, and hook selection with Short dispatch.

### Public Methods

```python
class AnalyzeService:
    @staticmethod
    def validate_url(req: VideoValidateRequest) -> VideoValidateResponse:
        """
        Validate a YouTube URL: parse video ID, fetch metadata via yt-dlp,
        and check accessibility constraints (not live, not age-restricted,
        public, has duration).

        Returns a response with valid=True/False and either video metadata
        or an error message. Never raises -- all failures are encoded in the
        response object.
        """

    @staticmethod
    def start_analysis(
        db: Session, user_id: str, youtube_url: str, niche: str, language: str
    ) -> dict:
        """
        Full analysis pipeline: validate URL → fetch metadata → check accessibility
        → ensure user exists → check balance → create session → deduct credits →
        dispatch Celery task → track analytics.

        Returns dict with: session_id, task_id, video_title, video_duration_seconds,
        minutes_charged, is_watermarked.

        Raises: InvalidURLError, MetadataFetchError, VideoAccessibilityError,
                InsufficientCreditsError (all subclasses of HookCutError)
        """

    @staticmethod
    def get_hooks(db: Session, session_id: str) -> dict:
        """
        Return session + hooks for a given session ID.
        Returns dict with: session (ORM object), hooks (list of Hook ORM objects).
        Raises: SessionNotFoundError
        """

    @staticmethod
    def regenerate_hooks(db: Session, session_id: str) -> dict:
        """
        Regenerate hooks for a session. 1st regen is free, 2nd+ charges a fee.
        Deletes old hooks, resets session to pending, dispatches new Celery task.
        Returns dict with: session_id, task_id, regeneration_count, fee_charged, currency.
        Raises: SessionNotFoundError, InvalidStateError
        """

    @staticmethod
    def select_hooks(
        db: Session, session_id: str, hook_ids: list[str],
        caption_style: str, time_overrides: dict
    ) -> dict:
        """
        Select 1-3 hooks and dispatch Short generation.
        Validates hook IDs, caption style, time overrides (±10s, min 5s).
        Creates Short records, dispatches generate_short tasks.
        Returns dict with: short_ids, task_ids.
        Raises: SessionNotFoundError, HooksNotReadyError, InvalidStateError
        """

    @staticmethod
    def _ensure_user(db: Session, user_id: str) -> None:
        """Auto-create User + CreditBalance if not present."""
```

### Dependencies

| Dependency | What it does |
|---|---|
| `app.utils.youtube.validate_youtube_url` | Regex extraction of video ID from URL |
| `VideoMetadataService().fetch()` | yt-dlp `--dump-json` call to get metadata |
| `VideoMetadataService().validate_accessibility()` | Business rule checks on metadata |
| `CreditManager(db)` | Balance checks, credit deduction, refunds |
| `run_analysis.delay()` | Celery task dispatch for hook analysis |
| `generate_short.delay()` | Celery task dispatch for Short generation |
| `track()` | Analytics event tracking |
| `get_regen_fee()` | Regeneration fee calculation |
| `VALID_CAPTION_STYLES` | Caption style validation from `ffmpeg_commands.py` |

### Exception Types (from `app.exceptions`)

| Exception | Status | Raised by |
|---|---|---|
| `InvalidURLError` | 400 | `start_analysis` — invalid YouTube URL |
| `MetadataFetchError` | 400 | `start_analysis` — yt-dlp metadata fetch failed |
| `VideoAccessibilityError` | 400 | `start_analysis` — live/private/age-restricted |
| `InsufficientCreditsError` | 402 | `start_analysis` — not enough minutes |
| `SessionNotFoundError` | 404 | `get_hooks`, `regenerate_hooks`, `select_hooks` |
| `HooksNotReadyError` | 400 | `select_hooks` — session not in hooks_ready state |
| `InvalidStateError` | 400 | `regenerate_hooks`, `select_hooks` — wrong session state |

### Invariants

- All methods are `@staticmethod` — no instance state.
- `validate_url` never raises — all failures encoded in response.
- `start_analysis` follows strict order: session created → credits deducted → task dispatched.
- `select_hooks` creates `LearningLog` entries with `hook_type` in event metadata.

---

## 2. CreditManager

**File:** `hookcut-backend/app/services/credit_manager.py`

**Class Purpose:** Manages user credit balances -- deduction (paid -> PAYG -> free), refunds, provisioning, and balance queries. All mutations are transactional with `Transaction` audit logging.

### Constructor

```python
class CreditManager:
    def __init__(self, db: Session):
        """Requires an active SQLAlchemy session. All operations commit through this session."""
```

### Public Methods

```python
def check_balance(self, user_id: str, minutes_needed: float) -> tuple[bool, float]:
    """
    Check if user has enough total minutes across all buckets.

    Returns (has_enough, total_available_minutes).
    """
    # Raises: nothing
    # Side effects: may CREATE a CreditBalance row if none exists (auto-provision)

def deduct(self, user_id: str, minutes: float, session_id: str) -> DeductionResult:
    """
    Deduct minutes in strict order: paid -> PAYG -> free.
    If ANY free minutes are consumed, is_watermarked=True.

    Creates a Transaction(type="credit_deduction") audit record.
    Commits the DB session.
    """
    # Raises: nothing (insufficient balance returned as DeductionResult with success=False)
    # Side effects: mutates CreditBalance, inserts Transaction, commits DB

def refund(
    self,
    user_id: str,
    session_id: str,
    paid_minutes: float = 0,
    payg_minutes: float = 0,
    free_minutes: float = 0,
) -> None:
    """
    Refund credits to the SAME buckets they were deducted from.
    Creates a Transaction(type="credit_refund") audit record.
    Commits the DB session.
    """
    # Raises: nothing
    # Side effects: mutates CreditBalance, inserts Transaction, commits DB

def add_paid_minutes(
    self, user_id: str, minutes: float, provider: str, provider_ref: str
) -> None:
    """
    Provision paid subscription minutes (resets to new allocation, not additive).
    Creates a Transaction(type="subscription_payment") audit record.
    Commits the DB session.
    """
    # Raises: nothing
    # Side effects: RESETS paid_minutes_remaining and paid_minutes_total, commits DB

def add_payg_minutes(
    self,
    user_id: str,
    minutes: float,
    amount: int,
    currency: str,
    provider: str,
    provider_ref: str,
) -> None:
    """
    Add PAYG minutes (additive, no expiry).
    Creates a Transaction(type="payg_purchase") audit record.
    Commits the DB session.
    """
    # Raises: nothing
    # Side effects: increments payg_minutes_remaining, commits DB

def refund_and_fail(
    self, session_id: str, error_msg: str, _logger=None
) -> None:
    """
    Combined operation: refund credits for a failed session and mark it as failed.
    Idempotent on the refund -- checks session.credits_refunded flag.
    Sets session.status = "failed" and session.error_message.
    Commits the DB session.
    """
    # Raises: nothing (logs error if session not found)
    # Side effects: mutates AnalysisSession, may call self.refund(), commits DB

def get_balance(self, user_id: str) -> CreditBalance:
    """
    Return the CreditBalance ORM object for a user. Creates one if it does not exist.
    """
    # Raises: nothing
    # Side effects: may CREATE a CreditBalance row if none exists
```

### Dependencies

| Dependency | Usage |
|---|---|
| `CreditBalance` (model) | Read/write balance buckets |
| `Transaction` (model) | Audit log for every credit mutation |
| `AnalysisSession` (model) | Read/write in `refund_and_fail` |
| `sqlalchemy.orm.Session` | All DB operations |

### Return Type: DeductionResult

```python
@dataclass
class DeductionResult:
    success: bool                # False if insufficient balance
    paid_used: float             # Minutes deducted from paid bucket
    payg_used: float             # Minutes deducted from PAYG bucket
    free_used: float             # Minutes deducted from free bucket
    is_watermarked: bool         # True if any free minutes were used
    error: Optional[str] = None  # Human-readable error if success=False

    @property
    def total_used(self) -> float:
        """Sum of all three buckets."""

    @property
    def credits_source(self) -> str:
        """Returns "paid", "payg", "free", or "mixed"."""
```

### Error Handling

- **No method raises exceptions.** All failures are encoded in return values or silently logged.
- `deduct()` returns `DeductionResult(success=False, error="Insufficient minutes...")` on insufficient balance.
- `refund_and_fail()` logs an error and returns `None` if the session is not found.

### Invariants

- **Deduction order is strict:** paid -> PAYG -> free. Never reversed.
- **Watermark rule:** If `free_used > 0`, then `is_watermarked = True`. No exceptions.
- **Refund idempotency:** `refund_and_fail` checks `session.credits_refunded` before refunding. Safe to call multiple times.
- **add_paid_minutes resets** (not adds): `paid_minutes_remaining = minutes`, not `+= minutes`.
- **add_payg_minutes accumulates:** `payg_minutes_remaining += minutes`.
- **Every mutation creates a Transaction** record for audit trail.
- **Auto-provision:** `_get_or_create_balance` creates a `CreditBalance` with defaults (120 free minutes) if one does not exist.

---

## 3. HookEngine

**File:** `hookcut-backend/app/services/hook_engine.py`

**Class Purpose:** LLM-powered hook identification engine. Sends full transcript to an LLM in one pass and returns exactly 5 ranked hook candidates with holistic scoring.

### Constructor

```python
class HookEngine:
    # No constructor args -- stateless. Instantiate with HookEngine().
```

### Public Methods

```python
def analyze(
    self, transcript: str, niche: str, language: str = "English",
    rules: list[dict] | None = None,
) -> HookEngineResult:
    """
    Identify the 5 best hook segments from a video transcript.

    Retry strategy: 3 attempts total.
      - Attempts 1-2: primary LLM provider (from settings.LLM_PRIMARY_PROVIDER)
      - Attempt 3: fallback provider (gemini->anthropic, openai->anthropic, etc.)
      - Delays: [0s, 5s, 30s] before each attempt

    On success: returns HookEngineResult with exactly 5 HookCandidates.
    On failure: raises HookEngineError after all 3 attempts exhausted.
    """
    # Raises: HookEngineError (after all retries exhausted)
    # Side effects: calls LLM API (primary + possibly fallback), sleeps between retries
```

### Dependencies

| Dependency | Usage |
|---|---|
| `app.llm.provider.get_provider` | Instantiate primary LLM provider |
| `app.llm.provider.get_fallback_provider` | Instantiate fallback LLM provider |
| `app.llm.prompts.hook_identification.build_hook_prompt` | Build the LLM prompt (hardcoded rules) |
| `app.llm.prompts.hook_identification.build_hook_prompt_from_rules` | Build the LLM prompt from admin DB rules (optional) |
| `app.llm.prompts.constants.HOOK_TYPES` | 18 valid hook type strings for validation |
| `app.llm.prompts.constants.FUNNEL_ROLES` | 6 valid funnel role strings for validation |
| `app.utils.time_format.timestamp_to_seconds` | Parse timestamp strings to float seconds |
| `app.config.get_settings` | Read `LLM_PRIMARY_PROVIDER` |

### Return Type: HookEngineResult

```python
@dataclass
class HookEngineResult:
    hooks: list[HookCandidate]       # Always exactly 5 elements
    provider: str                    # e.g. "gemini", "anthropic"
    model: str                       # e.g. "gemini-2.5-flash", "claude-3-haiku"
    attempts: int                    # 1-3, how many attempts were needed
    input_tokens: Optional[int]      # Token usage from LLM response
    output_tokens: Optional[int]
```

### Return Type: HookCandidate

```python
@dataclass
class HookCandidate:
    rank: int                        # 1-5
    hook_text: str                   # Verbatim transcript excerpt
    start_time: str                  # e.g. "1:30" or "1:30+3:45" for composite
    end_time: str                    # e.g. "1:55" or "1:55+4:10" for composite
    start_seconds: float             # Parsed from start_time
    end_seconds: float               # Parsed from end_time
    hook_type: str                   # One of 18 HOOK_TYPES (case-insensitive matched)
    funnel_role: str                 # One of 6 FUNNEL_ROLES (case-insensitive matched)
    scores: dict                     # 7 dimensions, each clamped [0, 10]
    attention_score: float           # Overall score, clamped [0, 10]
    platform_dynamics: str           # LLM analysis of platform fit
    viewer_psychology: str           # LLM analysis of viewer psychology
    improvement_suggestion: str      # LLM-generated actionable creator tip
    is_composite: bool               # True if hook spans multiple non-contiguous segments
```

### Error Handling

- **`HookEngineError`** is the only exception raised from `analyze()`.
- Raised when all 3 retry attempts fail (LLM errors, JSON parse errors, or validation errors).
- The error message includes the last error encountered: `"All 3 hook analysis attempts failed. Last error: ..."`.
- Internal `_parse_and_validate` raises `HookEngineError` for:
  - Invalid JSON from LLM
  - Not exactly 5 hooks
  - Missing required fields (`rank`, `hook_text`, `start_time`, `end_time`, `hook_type`, `funnel_role`)

### Invariants

- **Exactly 5 hooks** returned or exception raised. Never 0-4 or 6+.
- **Score clamping:** All 7 score dimensions and `attention_score` are clamped to `[0, 10]` via `max(0, min(10, float(val)))`.
- **Score dimensions** (all present in `scores` dict, defaulting to 0 if missing):
  - `scroll_stop`, `curiosity_gap`, `stakes_intensity`, `emotional_voltage`, `standalone_clarity`, `thematic_focus`, `thought_completeness`
- **Hook type fuzzy matching:** Case-insensitive match attempted against 18 `HOOK_TYPES`. If no match, the raw value is kept with a warning logged.
- **Funnel role fuzzy matching:** Case-insensitive match with `_` substitution attempted against 6 `FUNNEL_ROLES`. If no match, the raw value is kept with a warning logged.
- **Timestamp parse failure** defaults to `start_seconds=0.0, end_seconds=0.0` (does not raise).
- **Overlap detection** is warn-only (logged, not raised). Non-composite hooks are checked.
- **Retry with backoff:** `[0s, 5s, 30s]` delays. Last attempt uses fallback provider.
- **Stateless:** No DB reads or writes.

---

## 4. TranscriptService

**File:** `hookcut-backend/app/services/transcript.py`

**Class Purpose:** 3-provider cascade for transcript acquisition: youtube-transcript-api -> yt-dlp subtitles -> OpenAI Whisper API. All providers fail gracefully to `None`.

### Constructor

```python
class TranscriptService:
    # No constructor args -- stateless. Instantiate with TranscriptService().
```

### Public Methods

```python
def fetch(self, video_id: str, language: str = "English") -> Optional[TranscriptResult]:
    """
    Attempt to fetch a transcript using a 3-provider cascade:
      1. youtube-transcript-api (fastest, free)
      2. yt-dlp subtitle extraction (downloads .json3/.vtt/.srt)
      3. OpenAI Whisper API (gated by FEATURE_WHISPER_FALLBACK setting)

    Returns None if ALL providers fail. No credits should be deducted
    in that case.
    """
    # Raises: nothing (all provider failures caught, returns None)
    # Side effects:
    #   - Provider 1: HTTP call to YouTube
    #   - Provider 2: shells out to yt-dlp, creates+deletes temp dir
    #   - Provider 3: shells out to yt-dlp for audio, calls OpenAI Whisper API,
    #     creates+deletes temp dir
```

### Dependencies

| Dependency | Usage |
|---|---|
| `youtube_transcript_api.YouTubeTranscriptApi` | Primary transcript source |
| `yt-dlp` (subprocess) | Fallback 1: subtitle extraction; Fallback 2: audio download |
| `openai.OpenAI` | Whisper API transcription (Fallback 2) |
| `app.config.get_settings` | `FEATURE_WHISPER_FALLBACK`, `effective_whisper_key` |

### Return Type

```python
@dataclass
class TranscriptResult:
    text: str                             # Timestamped transcript, format: "[M:SS.cc] text\n..."
    provider: str                         # "youtube_transcript_api", "ytdlp_subtitles", or "whisper_api"
    language_detected: Optional[str]      # Language code if detected (e.g. "en", "hi")
```

### Error Handling

- **Never raises.** All three providers catch all exceptions internally and return `None`.
- Minimum transcript length: 50 characters. Shorter transcripts are treated as failures and `None` is returned.
- Whisper API has a 25MB file size limit. Files exceeding this are skipped with a warning.

### Invariants

- **Cascade order is fixed:** youtube-transcript-api -> yt-dlp -> Whisper. First success wins.
- **Whisper is gated** by `settings.FEATURE_WHISPER_FALLBACK` (default `True`).
- **Temp directories** are always cleaned up (`shutil.rmtree` in `finally` blocks).
- **Transcript format:** `[M:SS.cc] text` with one line per segment/event.
- **Language mapping:** 12 Indian languages + Other. Falls back to `["en"]` for unknown languages.
- **No DB writes.** Stateless.

### Static/Class Methods

```python
@staticmethod
def _get_lang_codes(language: str) -> list[str]:
    """
    Map language name (e.g. "English", "Hindi", "Tamil") to a list of
    YouTube language codes in priority order.
    Returns ["en"] for unrecognized languages.
    """
```

---

## 5. VideoMetadataService

**File:** `hookcut-backend/app/services/video_metadata.py`

**Class Purpose:** Fetch and validate YouTube video metadata via yt-dlp without downloading the video.

### Constructor

```python
class VideoMetadataService:
    # No constructor args -- stateless. Instantiate with VideoMetadataService().
```

### Public Methods

```python
def fetch(self, video_id: str) -> Optional[VideoMetadata]:
    """
    Fetch video metadata using `yt-dlp --dump-json --no-download`.
    Timeout: 30 seconds.

    Returns None on any failure (yt-dlp error, timeout, parse error).
    """
    # Raises: nothing (all errors caught, returns None)
    # Side effects: shells out to yt-dlp

def validate_accessibility(self, metadata: VideoMetadata) -> tuple[bool, Optional[str]]:
    """
    Check business rules for video accessibility:
      - Not a live video
      - Not age-restricted (age_limit < 18)
      - Public (availability == "public" or None)
      - Has a positive duration

    Returns (True, None) if OK, or (False, "Human-readable error") if not.
    """
    # Raises: nothing
    # Side effects: none (pure function)
```

### Return Type

```python
@dataclass
class VideoMetadata:
    video_id: str
    title: str
    duration_seconds: float
    is_live: bool
    age_limit: int
    availability: Optional[str]    # "public", "private", "needs_auth", etc.
```

### Error Handling

- `fetch()` catches `subprocess.TimeoutExpired`, `json.JSONDecodeError`, `KeyError`, `ValueError`, and generic `Exception`. Always returns `None` on failure.
- `validate_accessibility()` never raises.

### Invariants

- **No DB writes.** Stateless.
- **yt-dlp timeout:** 30 seconds.
- **Accessibility rules:**
  - `is_live == True` -> rejected
  - `age_limit >= 18` -> rejected
  - `availability not in (None, "public")` -> rejected
  - `duration_seconds <= 0` -> rejected

---

## 6. ShortGenerator

**File:** `hookcut-backend/app/services/short_generator.py`

**Class Purpose:** Full Short generation pipeline: segment extraction (yt-dlp) -> LLM caption cleanup + title generation -> FFmpeg render (9:16, audio, captions, watermark) -> thumbnail extraction.

### Constructor

```python
class ShortGenerator:
    # No constructor args -- stateless. Instantiate with ShortGenerator().
```

### Public Methods

```python
def generate(
    self,
    youtube_url: str,
    hook: dict,
    session_id: str,
    short_id: str,
    is_watermarked: bool,
    language: str = "English",
    niche: str = "Generic",
    caption_style: str = "clean",
) -> ShortResult:
    """
    End-to-end Short generation:
      1. Extract segment(s) from YouTube via yt-dlp (handles composite hooks)
      2. Clean captions via LLM (parallel with step 1)
      3. Generate Short title via LLM (parallel with step 1)
      4. Generate ASS subtitle file
      5. FFmpeg single-pass render (crop 16:9->9:16, audio normalize, captions with style, watermark)
      6. Extract thumbnail from middle frame

    The hook dict must contain:
      - hook_text: str
      - start_time: str (or start_seconds: float)
      - end_time: str (or end_seconds: float)
      - is_composite: bool (optional, default False)

    caption_style: one of "clean", "bold", "neon", "minimal" — passed to generate_ass_subtitles()

    Creates a temp directory (prefix: hookcut_short_{short_id[:8]}_)
    that is NOT cleaned up -- caller is responsible for cleanup.
    """
    # Raises: ShortGenerationError (wraps all internal failures)
    # Side effects:
    #   - Creates temp directory with video/subtitle/thumbnail files
    #   - Shells out to yt-dlp, ffmpeg, ffprobe
    #   - Calls LLM API (2 calls: caption cleanup + title generation)
```

### Dependencies

| Dependency | Usage |
|---|---|
| `app.llm.provider.get_provider` | LLM for caption cleanup and title generation |
| `app.llm.prompts.caption_cleanup.build_caption_cleanup_prompt` | Prompt for caption cleanup |
| `app.llm.prompts.caption_cleanup.build_title_generation_prompt` | Prompt for title generation |
| `app.utils.time_format.parse_composite_timestamps` | Parse composite hook timestamps |
| `app.utils.ffmpeg_commands.extract_segment` | yt-dlp segment download |
| `app.utils.ffmpeg_commands.concat_segments` | FFmpeg concat for composite hooks |
| `app.utils.ffmpeg_commands.generate_ass_subtitles` | ASS subtitle file generation |
| `app.utils.ffmpeg_commands.render_short` | Single-pass FFmpeg render |
| `app.utils.ffmpeg_commands.extract_thumbnail` | Middle-frame thumbnail extraction |
| `app.utils.ffmpeg_commands.probe_duration` | ffprobe duration query |
| `app.config.get_settings` | `LLM_PRIMARY_PROVIDER` |

### Return Type

```python
@dataclass
class ShortResult:
    video_path: str                      # Absolute path to rendered .mp4
    thumbnail_path: str                  # Absolute path to .jpg (empty string if extraction failed)
    title: str                           # LLM-generated title, max 60 chars
    cleaned_captions: str                # LLM-cleaned caption text
    duration_seconds: Optional[float]    # From ffprobe of rendered output
    file_size_bytes: Optional[int]       # Of rendered .mp4
```

### Error Handling

- **`ShortGenerationError`** is the only exception raised from `generate()`.
- Wraps all internal failures: yt-dlp extraction, FFmpeg render, concat failures.
- **LLM failures in caption cleanup** are caught internally -- falls back to raw `hook_text`.
- **LLM failures in title generation** are caught internally -- falls back to `"Hook Segment"`.
- **Thumbnail extraction failure** is non-fatal -- `thumbnail_path` is set to `""` with a warning.

### Invariants

- **Parallelism:** Steps 1, 2, 3 run in a `ThreadPoolExecutor(max_workers=3)`.
- **Title truncation:** LLM-generated title is truncated to 60 characters.
- **Temp directory is NOT cleaned up** by `generate()`. The caller must handle cleanup.
- **Watermark** is applied only when `is_watermarked=True` (free-tier usage).
- **Max duration cap:** FFmpeg render enforces `MAX_SHORT_DURATION_SECONDS = 60`.
- **No DB writes.** Stateless.

---

## 7. StorageService

**File:** `hookcut-backend/app/services/storage.py`

**Class Purpose:** File storage abstraction. V0: local filesystem. V1: Cloudflare R2 (S3-compatible). Switchable via `FEATURE_R2_STORAGE` flag.

### Constructor

```python
class StorageService:
    def __init__(self):
        """
        Reads settings to determine storage backend:
          - FEATURE_R2_STORAGE=True: initialize boto3 S3 client for Cloudflare R2
          - FEATURE_R2_STORAGE=False: use local ./storage/ directory
        """
```

### Public Methods

```python
def upload(self, local_path: str, key: str) -> str:
    """
    Upload a file to storage.

    R2 mode: uploads to S3 bucket, returns public URL.
    Local mode: copies file to ./storage/{key}, returns local path.

    The key is a slash-separated path (e.g. "sessions/abc/video.mp4").
    """
    # Raises:
    #   - ValueError if key contains path traversal (local mode only)
    #   - boto3 exceptions (R2 mode)
    #   - OSError/IOError (file copy failures)
    # Side effects: writes file to storage backend

def get_download_url(self, key: str, expires_in: int = 3600) -> str:
    """
    Generate a download URL.

    R2 mode: generates a presigned URL (default 1 hour expiry).
    Local mode: returns the local filesystem path.
    """
    # Raises:
    #   - ValueError if key contains path traversal (local mode only)
    #   - boto3 exceptions (R2 mode)
    # Side effects: none

def delete(self, key: str) -> None:
    """
    Delete a file from storage.

    R2 mode: deletes object from S3 bucket.
    Local mode: deletes local file if it exists. No-op if file is missing.
    """
    # Raises:
    #   - ValueError if key contains path traversal (local mode only)
    #   - boto3 exceptions (R2 mode)
    # Side effects: deletes file from storage backend
```

### Dependencies

| Dependency | Usage |
|---|---|
| `boto3` (conditional import) | S3 client for Cloudflare R2 |
| `app.config.get_settings` | `FEATURE_R2_STORAGE`, R2 credentials, `R2_BUCKET_NAME`, `R2_PUBLIC_URL` |

### Error Handling

- **Path traversal protection** in local mode: `_safe_local_path()` resolves the path and verifies it stays within the `./storage/` directory. Raises `ValueError` on traversal.
- R2 mode propagates all boto3/S3 exceptions to the caller.
- Local `delete()` is idempotent -- no error if file does not exist.

### Invariants

- **Content-type detection:** `.mp4` -> `video/mp4`, everything else -> `image/jpeg`.
- **Local mode auto-creates** subdirectories as needed via `os.makedirs`.
- **R2 presigned URL** default expiry: 3600 seconds (1 hour).
- **No DB reads/writes.**

---

## 8. PaymentService

**File:** `hookcut-backend/app/services/payment_service.py`

**Class Purpose:** Unified payment service routing to Stripe (USD/international) or Razorpay (INR/Indian) for subscription and PAYG purchases.

### Constructor

```python
class PaymentService:
    # No constructor args -- stateless. Instantiate with PaymentService().
```

### Public Methods

```python
def create_subscription_checkout(
    self, user_id: str, email: str, plan_tier: str, currency: str
) -> CheckoutSession:
    """
    Create a subscription checkout session.

    Routes: currency=="INR" -> Razorpay, else -> Stripe.
    """
    # Raises:
    #   - NotImplementedError if FEATURE_V0_MODE is True
    #   - stripe.error.* exceptions (Stripe mode)
    #   - razorpay exceptions (Razorpay mode)
    # Side effects: creates checkout session with payment provider

def create_payg_checkout(
    self, user_id: str, email: str, minutes: int, currency: str
) -> CheckoutSession:
    """
    Create a PAYG (pay-as-you-go) minutes purchase checkout session.

    Routes: currency=="INR" -> Razorpay, else -> Stripe.
    """
    # Raises:
    #   - NotImplementedError if FEATURE_V0_MODE is True
    #   - stripe.error.* exceptions (Stripe mode)
    #   - razorpay exceptions (Razorpay mode)
    # Side effects: creates checkout session with payment provider
```

### Return Type

```python
@dataclass
class CheckoutSession:
    checkout_url: str    # URL to redirect user to (empty for Razorpay PAYG -- uses client-side modal)
    session_id: str      # Provider's session/order/subscription ID
    provider: str        # "stripe" or "razorpay"
```

### Module-Level Constants

```python
PLAN_MINUTES = {
    "lite": 100,         # 100 minutes/month
    "pro": 500,          # 500 minutes/month
}

PLAN_PRICES = {
    ("lite", "INR"): 49900,    # Rs 499 in paisa
    ("lite", "USD"): 700,      # $7 in cents
    ("pro", "INR"): 99900,     # Rs 999 in paisa
    ("pro", "USD"): 1300,      # $13 in cents
}

PAYG_RATES = {
    "INR": 10000,   # Rs 100 per 100 minutes in paisa
    "USD": 200,     # $2 per 100 minutes in cents
}
```

### Dependencies

| Dependency | Usage |
|---|---|
| `stripe` (conditional import) | Stripe checkout sessions |
| `razorpay` (conditional import) | Razorpay subscriptions and orders |
| `app.config.get_settings` | All payment keys, `FEATURE_V0_MODE`, `FRONTEND_URL` |

### Error Handling

- Raises `NotImplementedError` when `FEATURE_V0_MODE` is enabled.
- All Stripe and Razorpay SDK exceptions propagate to the caller.

### Invariants

- **V0 mode blocks all payments** via `NotImplementedError`.
- **Currency routing:** `"INR"` -> Razorpay, everything else -> Stripe.
- **PAYG pricing:** `amount = (minutes // 100) * rate_per_100`. Integer division means minutes must be a multiple of 100 for correct pricing.
- **Razorpay subscriptions** are created with `total_count=12` (12 months).
- **Razorpay PAYG** returns `checkout_url=""` because it uses a client-side modal.
- **Stripe redirect URLs:** `{FRONTEND_URL}/billing?success=true` and `{FRONTEND_URL}/billing?cancelled=true`.
- **No DB writes.** Transaction logging is handled by the caller (SubscriptionService, webhook handler).

---

## 9. SubscriptionService

**File:** `hookcut-backend/app/services/subscription_service.py`

**Class Purpose:** Activates or updates a user's subscription, provisions credits, and logs the transaction. Called from webhook handlers after payment confirmation.

### Constructor

```python
class SubscriptionService:
    def __init__(self, db: Session):
        """Requires an active SQLAlchemy session."""
```

### Public Methods

```python
def activate_subscription(
    self,
    user_id: str,
    plan_tier: str,
    provider: str,
    subscription_id: str,
    currency: str,
) -> None:
    """
    Activate or update a subscription:
      1. Set user.plan_tier to the new tier
      2. Create or update the Subscription record (active status)
      3. Provision paid minutes via CreditManager.add_paid_minutes()
      4. Log a Transaction(type="subscription_payment") record
      5. Commit the DB session

    If user_id is not found, silently returns (no-op).
    """
    # Raises: nothing (returns None if user not found)
    # Side effects:
    #   - Mutates User.plan_tier
    #   - Creates/updates Subscription record
    #   - Calls CreditManager.add_paid_minutes() (which resets paid minutes)
    #   - Inserts Transaction record
    #   - Commits DB
```

### Dependencies

| Dependency | Usage |
|---|---|
| `User` (model) | Read/write `plan_tier` |
| `Subscription` (model) | Create/update subscription record |
| `Transaction` (model) | Audit log |
| `CreditManager` | Provision paid minutes |
| `PLAN_MINUTES` (from payment_service) | Look up minutes allocation for plan tier |
| `sqlalchemy.orm.Session` | DB operations |

### Error Handling

- **Never raises.** Silently returns if user not found.
- DB commit failures would propagate as SQLAlchemy exceptions.

### Invariants

- **Subscription period:** 30 days from activation (`current_period_end = now + timedelta(days=30)`).
- **Existing active subscription** for the same provider is updated in-place (plan_tier, subscription_id, period_start).
- **New subscription** is created if no active one exists for that provider.
- **Credit provisioning** delegates to `CreditManager.add_paid_minutes()` which resets (not adds) paid minutes.
- **Double Transaction:** Note that both `activate_subscription` and `CreditManager.add_paid_minutes()` each create a `Transaction(type="subscription_payment")`. This results in two transaction records per activation.

---

## 10. WebhookService

**File:** `hookcut-backend/app/services/webhook_service.py`

**Class Purpose:** Handles business logic for payment webhook events (Stripe and Razorpay). Extracted from billing router to keep routers as thin HTTP adapters. Signature verification stays in the router; business logic (credit grants, subscription management) lives here.

### Public Methods

```python
class WebhookService:
    @staticmethod
    def handle_stripe_checkout_completed(db: Session, data: dict) -> dict:
        """Handle Stripe checkout.session.completed event.
        PAYG: grants minutes via CreditManager.add_payg_minutes().
        Subscription: activates via SubscriptionService.activate_subscription().
        """

    @staticmethod
    def handle_stripe_invoice_paid(db: Session, data: dict) -> dict:
        """Handle Stripe invoice.paid event.
        Subscription renewal: grants monthly minutes via CreditManager.add_paid_minutes().
        """

    @staticmethod
    def handle_stripe_subscription_deleted(db: Session, data: dict) -> dict:
        """Handle Stripe customer.subscription.deleted event.
        Cancels subscription via SubscriptionService.cancel_subscription().
        """

    @staticmethod
    def handle_razorpay_subscription_charged(db: Session, entity: dict, notes: dict) -> dict:
        """Handle Razorpay subscription.charged event.
        Activates subscription via SubscriptionService.activate_subscription().
        """

    @staticmethod
    def handle_razorpay_order_paid(db: Session, entity: dict, notes: dict) -> dict:
        """Handle Razorpay order.paid event (purchase_type=payg).
        Grants PAYG minutes via CreditManager.add_payg_minutes().
        """

    @staticmethod
    def handle_razorpay_subscription_cancelled(db: Session, entity: dict, notes: dict) -> dict:
        """Handle Razorpay subscription.cancelled event.
        Cancels subscription via SubscriptionService.cancel_subscription().
        """
```

### Dependencies

| Dependency | Usage |
|---|---|
| `CreditManager(db)` | Credit grants (PAYG, subscription) |
| `SubscriptionService` | Subscription activation and cancellation |
| `PLAN_MINUTES` | Plan tier → monthly minutes mapping |

### Invariants

- All methods are `@staticmethod` — no instance state.
- All methods return `{"status": "ok"}` or `{"status": "ignored"}`.
- Signature verification is NOT done here — that stays in the billing router.
- Each method delegates to `CreditManager` and/or `SubscriptionService` for the actual mutations.

---

## 11. Analytics (module-level functions)

**File:** `hookcut-backend/app/services/analytics.py`

**Module Purpose:** PostHog analytics event tracking. Lazy-initialized singleton client. All failures are silently swallowed (fire-and-forget).

### Module-Level Functions

```python
def track(user_id: str, event: str, properties: dict | None = None) -> None:
    """
    Track an analytics event in PostHog.
    No-op if POSTHOG_API_KEY is not configured.
    Silently catches and logs all exceptions.
    """
    # Raises: nothing
    # Side effects: HTTP call to PostHog (if configured)

def identify(user_id: str, properties: dict | None = None) -> None:
    """
    Identify a user with properties in PostHog.
    No-op if POSTHOG_API_KEY is not configured.
    Silently catches and logs all exceptions.
    """
    # Raises: nothing
    # Side effects: HTTP call to PostHog (if configured)
```

### Dependencies

| Dependency | Usage |
|---|---|
| `posthog` (conditional import) | PostHog Python SDK |
| `app.config.get_settings` | `POSTHOG_API_KEY`, `POSTHOG_HOST` |

### Invariants

- **Lazy initialization:** PostHog client is created on first call, cached in module global `_posthog_client`.
- **Silent failures:** All exceptions are caught and logged as warnings. Never disrupts the calling code.
- **No-op when unconfigured:** If `POSTHOG_API_KEY` is empty, no client is created and calls are no-ops.

---

## 12. LLM Provider Interface

**File:** `hookcut-backend/app/llm/provider.py`

**Module Purpose:** Abstract LLM provider interface and factory functions used by HookEngine and ShortGenerator.

### Abstract Base Class

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 4000) -> LLMResponse:
        """Generate text from a prompt."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name string (e.g. "gemini", "anthropic", "openai")."""
        pass
```

### Response Type

```python
@dataclass
class LLMResponse:
    text: str                        # Generated text
    provider: str                    # Provider name
    model: str                       # Model identifier
    input_tokens: Optional[int]      # Input token count (if available)
    output_tokens: Optional[int]     # Output token count (if available)
```

### Factory Functions

```python
def get_provider(provider_name: str) -> LLMProvider:
    """
    Factory: instantiate an LLM provider by name.
    Supported: "openai", "anthropic", "gemini".
    """
    # Raises: ValueError for unknown provider names

def get_fallback_provider(primary: str) -> LLMProvider:
    """
    Return the fallback provider for a given primary.
    Mapping: openai->anthropic, anthropic->openai, gemini->anthropic.
    Default fallback: anthropic.
    """
    # Raises: ValueError if fallback provider name is unknown (unlikely)
```

### Fallback Map

| Primary | Fallback |
|---|---|
| `openai` | `anthropic` |
| `anthropic` | `openai` |
| `gemini` | `anthropic` |
| anything else | `anthropic` |

---

## 13. Utility Modules

### 12.1 youtube.py

**File:** `hookcut-backend/app/utils/youtube.py`

```python
def extract_video_id(url: str) -> Optional[str]:
    """
    Extract 11-character YouTube video ID from a URL.
    Supports: standard watch, short URL (youtu.be), /shorts/, /embed/, mobile.
    Returns None if no pattern matches.
    """
    # Raises: nothing

def validate_youtube_url(url: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Validate a YouTube URL.
    Returns (is_valid, video_id, error_message).
    - (True, "dQw4w9WgXcQ", None) on success
    - (False, None, "Human-readable error") on failure
    """
    # Raises: nothing
```

### 12.2 time_format.py

**File:** `hookcut-backend/app/utils/time_format.py`

```python
def timestamp_to_seconds(ts: str) -> float:
    """
    Convert timestamp string to seconds.
    Supported formats: "SS", "M:SS", "MM:SS", "H:MM:SS".
    For composite timestamps (e.g. "1:30+3:45"), returns the FIRST segment's start.
    Strips " [composite]" markers.
    """
    # Raises: ValueError for invalid formats

def parse_composite_timestamps(
    start_time: str, end_time: str
) -> list[tuple[float, float]]:
    """
    Parse composite hook timestamps into (start_seconds, end_seconds) pairs.
    Example: "1:30+3:45", "1:55+4:10" -> [(90.0, 115.0), (225.0, 250.0)]
    Non-composite timestamps return a single-element list.
    """
    # Raises: ValueError if start count != end count
```

### 12.3 ffmpeg_commands.py

**File:** `hookcut-backend/app/utils/ffmpeg_commands.py`

**Public functions** (all imported by ShortGenerator):

```python
def extract_segment(
    youtube_url: str, start_seconds: float, end_seconds: float, output_path: str
) -> FFmpegResult:
    """Download a video segment via yt-dlp --download-sections. Timeout: 120s."""

def concat_segments(segment_paths: list[str], output_path: str) -> FFmpegResult:
    """Concatenate multiple .mp4 segments via FFmpeg concat demuxer. Timeout: 60s."""

def generate_ass_subtitles(
    caption_text: str, duration_seconds: float, output_path: str
) -> str:
    """Generate an ASS subtitle file. Returns the output_path."""

def render_short(
    input_path: str, subtitle_path: str, output_path: str, watermark: bool = False
) -> FFmpegResult:
    """
    Single-pass FFmpeg render: crop 16:9->9:16, scale to 1080x1920,
    burn captions, optional watermark, audio normalize. Timeout: 300s.
    """

def extract_thumbnail(input_path: str, output_path: str) -> FFmpegResult:
    """Extract middle frame as JPG thumbnail. Timeout: 30s."""

def probe_duration(filepath: str) -> Optional[float]:
    """Get video duration via ffprobe. Returns None on failure. Timeout: 10s."""
    # NOTE: This is a public function imported by other modules (ShortGenerator).
```

**Shared Return Type:**

```python
@dataclass
class FFmpegResult:
    success: bool
    output_path: str
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
```

**Module Constants:**

| Constant | Value | Used By |
|---|---|---|
| `SHORTS_WIDTH` | 1080 | render_short |
| `SHORTS_HEIGHT` | 1920 | render_short |
| `VIDEO_CODEC` | `"libx264"` | render_short |
| `ENCODER_PRESET` | `"ultrafast"` | render_short |
| `CRF_QUALITY` | `"21"` | render_short |
| `AUDIO_CODEC` | `"aac"` | render_short |
| `AUDIO_BITRATE` | `"128k"` | render_short |
| `MAX_SHORT_DURATION_SECONDS` | 60 | render_short (`-t` flag) |
| `WATERMARK_TEXT` | `"HookCut"` | render_short |
| `WATERMARK_FONT_SIZE` | 24 | render_short |
| `WATERMARK_OPACITY` | 0.3 | render_short |

### 12.4 LLM Prompt Constants

**File:** `hookcut-backend/app/llm/prompts/constants.py`

**Exported by services (HookEngine validation, schema validation):**

```python
HOOK_TYPES: list[str]    # 18 hook type strings
FUNNEL_ROLES: list[str]  # 6 funnel role strings
NICHES: dict[str, dict]  # 8 niche configs with softRange, stakes, tone, preferredTypes
LANGUAGES: dict[str, dict]  # 13 language configs with label and promptNote

def get_regen_fee(video_duration_seconds: float, currency: str) -> int:
    """
    Return regeneration fee in smallest currency unit (paisa/cents).
    USD: flat $0.30 (30 cents).
    INR: tiered by video duration:
      <=15min: Rs 10 (1000 paisa)
      <=30min: Rs 15 (1500 paisa)
      <=60min: Rs 20 (2000 paisa)
      >60min:  Rs 25 (2500 paisa)
    """
```

---

## 14. Shared Data Types Reference

### DB Models (SQLAlchemy ORM)

**AnalysisSession** (`analysis_sessions`):

| Column | Type | Notes |
|---|---|---|
| `id` | `str(36)` | UUID PK |
| `user_id` | `str(255)` | FK -> users.id |
| `youtube_url` | `str(500)` | |
| `video_id` | `str(20)` | YouTube video ID |
| `video_title` | `str(500)` | |
| `video_duration_seconds` | `float` | |
| `niche` | `str(50)` | |
| `language` | `str(50)` | |
| `status` | `str(30)` | `pending`, `fetching_transcript`, `analyzing`, `hooks_ready`, `generating_shorts`, `completed`, `failed` |
| `transcript_provider` | `str(50)?` | |
| `transcript_text` | `Text?` | |
| `minutes_charged` | `float` | |
| `credits_source` | `str(20)` | `paid`, `free`, `payg`, `mixed` |
| `is_watermarked` | `bool` | |
| `credits_refunded` | `bool` | Idempotency guard for refunds |
| `regeneration_count` | `int` | |
| `error_message` | `Text?` | |
| `task_id` | `str(255)?` | Celery task ID |
| `paid_minutes_used` | `float` | For per-bucket refunds |
| `payg_minutes_used` | `float` | For per-bucket refunds |
| `free_minutes_used` | `float` | For per-bucket refunds |
| `created_at` | `datetime` | |

**Hook** (`hooks`):

| Column | Type | Notes |
|---|---|---|
| `id` | `str(36)` | UUID PK |
| `session_id` | `str(36)` | FK -> analysis_sessions.id |
| `rank` | `int` | 1-5 |
| `hook_text` | `Text` | Verbatim transcript excerpt |
| `start_time` | `str(20)` | e.g. `"1:30"` or `"1:30+3:45"` |
| `end_time` | `str(20)` | |
| `start_seconds` | `float` | |
| `end_seconds` | `float` | |
| `hook_type` | `str(50)` | One of 18 HOOK_TYPES |
| `funnel_role` | `str(30)` | One of 6 FUNNEL_ROLES |
| `scores` | `JSON` | 7-dimension dict, each [0, 10] |
| `attention_score` | `float` | [0, 10] |
| `platform_dynamics` | `Text` | |
| `viewer_psychology` | `Text` | |
| `improvement_suggestion` | `Text` | LLM-generated actionable creator tip |
| `is_composite` | `bool` | |
| `is_selected` | `bool` | Set when user selects for Short generation |
| `created_at` | `datetime` | |

**Short** (`shorts`):

| Column | Type | Notes |
|---|---|---|
| `id` | `str(36)` | UUID PK |
| `session_id` | `str(36)` | FK -> analysis_sessions.id |
| `hook_id` | `str(36)` | FK -> hooks.id |
| `status` | `str(20)` | `queued`, `downloading`, `processing`, `uploading`, `ready`, `failed`, `expired` |
| `caption_style` | `str(20)` | `clean`, `bold`, `neon`, `minimal` (default: `clean`) |
| `start_seconds_override` | `float?` | User-adjusted start time (±10s from original) |
| `end_seconds_override` | `float?` | User-adjusted end time (±10s from original) |
| `is_watermarked` | `bool` | |
| `title` | `str(200)?` | |
| `cleaned_captions` | `Text?` | |
| `video_file_key` | `str(500)?` | Storage key |
| `thumbnail_file_key` | `str(500)?` | Storage key |
| `duration_seconds` | `float?` | |
| `file_size_bytes` | `int?` | |
| `download_url` | `Text?` | |
| `download_url_expires_at` | `datetime?` | |
| `expires_at` | `datetime?` | |
| `error_message` | `Text?` | |
| `task_id` | `str(255)?` | Celery task ID |
| `created_at` | `datetime` | |

**User** (`users`):

| Column | Type | Notes |
|---|---|---|
| `id` | `str(255)` | PK (NextAuth user ID or V0 local) |
| `email` | `str(255)` | Unique, indexed |
| `currency` | `str(3)` | `"USD"` or `"INR"` |
| `plan_tier` | `str(20)` | `"free"`, `"lite"`, `"pro"` |
| `role` | `str(20)` | `"user"` or `"admin"` |
| `created_at` | `datetime` | |
| `updated_at` | `datetime` | Auto-updated |

**CreditBalance** (`credit_balances`):

| Column | Type | Default | Notes |
|---|---|---|---|
| `id` | `str(36)` | UUID | PK |
| `user_id` | `str(255)` | | FK -> users.id, unique |
| `paid_minutes_remaining` | `float` | 0.0 | Subscription minutes left |
| `paid_minutes_total` | `float` | 0.0 | Total provisioned this cycle |
| `free_minutes_remaining` | `float` | 120.0 | Free tier minutes left |
| `free_minutes_total` | `float` | 120.0 | |
| `payg_minutes_remaining` | `float` | 0.0 | PAYG minutes (no expiry) |
| `last_free_reset` | `datetime` | now | |

**Computed property:** `total_available = paid + payg + free`.

**Subscription** (`subscriptions`):

| Column | Type | Notes |
|---|---|---|
| `id` | `str(36)` | UUID PK |
| `user_id` | `str(255)` | FK -> users.id |
| `plan_tier` | `str(20)` | `"lite"`, `"pro"` |
| `currency` | `str(3)` | |
| `provider` | `str(20)` | `"stripe"`, `"razorpay"` |
| `provider_subscription_id` | `str(255)` | |
| `status` | `str(20)` | default `"active"` |
| `current_period_start` | `datetime` | |
| `current_period_end` | `datetime` | |
| `created_at` | `datetime` | |

**Transaction** (`transactions`):

| Column | Type | Notes |
|---|---|---|
| `id` | `str(36)` | UUID PK |
| `user_id` | `str(255)` | FK -> users.id |
| `type` | `str(30)` | `credit_deduction`, `credit_refund`, `subscription_payment`, `payg_purchase`, `regeneration_fee` |
| `session_id` | `str(36)?` | |
| `minutes_amount` | `float?` | |
| `money_amount` | `int?` | Smallest currency unit (paisa/cents) |
| `currency` | `str(3)?` | |
| `provider` | `str(20)?` | |
| `provider_ref` | `str(255)?` | |
| `description` | `Text` | |
| `created_at` | `datetime` | |

**LearningLog** (`learning_logs`):

| Column | Type | Notes |
|---|---|---|
| `id` | `str(36)` | UUID PK |
| `session_id` | `str(36)` | FK -> analysis_sessions.id |
| `event_type` | `str(30)` | `hook_presented`, `hook_selected`, `hook_not_selected`, `regeneration_triggered`, `short_downloaded`, `short_discarded` |
| `hook_id` | `str(36)?` | |
| `video_id` | `str(20)` | |
| `niche` | `str(50)` | |
| `language` | `str(50)` | |
| `event_metadata` | `JSON?` | Stored as column name `metadata` |
| `created_at` | `datetime` | |

### Pydantic Schemas (API layer)

**Request schemas:**

```python
class AnalyzeRequest(BaseModel):
    youtube_url: str
    niche: str = "Generic"       # Validated against NICHES dict keys
    language: str = "English"    # Validated against LANGUAGES dict keys

class VideoValidateRequest(BaseModel):
    youtube_url: str             # No format validation (purpose is to return errors)

class SelectHooksRequest(BaseModel):
    hook_ids: list[str]          # 1-3 unique hook IDs
```

**Response schemas:**

```python
class AnalyzeResponse(BaseModel):
    session_id: str
    task_id: str
    video_title: str
    video_duration_seconds: float
    minutes_charged: float
    is_watermarked: bool

class VideoValidateResponse(BaseModel):
    valid: bool
    video_id: Optional[str] = None
    title: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None

class RegenerateResponse(BaseModel):
    session_id: str
    task_id: str
    regeneration_count: int
    fee_charged: Optional[int] = None     # Smallest currency unit
    currency: Optional[str] = None        # Required if fee_charged is set

class SelectHooksResponse(BaseModel):
    short_ids: list[str]
    task_ids: list[str]

class HookScores(BaseModel):
    scroll_stop: float = 0                # All clamped [0.0, 10.0]
    curiosity_gap: float = 0
    stakes_intensity: float = 0
    emotional_voltage: float = 0
    standalone_clarity: float = 0
    thematic_focus: float = 0
    thought_completeness: float = 0

class HookResponse(BaseModel):
    id: str
    rank: int
    hook_text: str
    start_time: str
    end_time: str
    hook_type: str
    funnel_role: str
    scores: HookScores
    attention_score: float
    platform_dynamics: str
    viewer_psychology: str
    is_composite: bool
    is_selected: bool

class HooksListResponse(BaseModel):
    session_id: str
    status: str
    hooks: list[HookResponse]
    regeneration_count: int

class ShortResponse(BaseModel):
    id: str
    hook_id: str
    status: str
    is_watermarked: bool
    title: Optional[str] = None
    cleaned_captions: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    download_url_expires_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    error_message: Optional[str] = None

class ShortDownloadResponse(BaseModel):
    download_url: str
    expires_at: datetime

class BalanceResponse(BaseModel):
    paid_minutes_remaining: float
    paid_minutes_total: float
    free_minutes_remaining: float
    free_minutes_total: float
    payg_minutes_remaining: float
    total_available: float

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str           # "PENDING", "STARTED", "PROGRESS", "SUCCESS", "FAILURE"
    progress: Optional[int] = None
    stage: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None    # max_length=2000
```

---

## Service Dependency Graph

```
AnalyzeService
  └── VideoMetadataService
        └── yt-dlp (subprocess)
  └── youtube.validate_youtube_url

HookEngine
  └── LLMProvider (primary + fallback)
  └── hook_identification prompt builder
  └── time_format.timestamp_to_seconds

TranscriptService
  └── youtube-transcript-api
  └── yt-dlp (subprocess)
  └── OpenAI Whisper API

ShortGenerator
  └── LLMProvider (caption cleanup + title generation)
  └── ffmpeg_commands (extract_segment, concat_segments, generate_ass_subtitles, render_short, extract_thumbnail, probe_duration)
  └── time_format.parse_composite_timestamps

CreditManager
  └── CreditBalance (model)
  └── Transaction (model)
  └── AnalysisSession (model, in refund_and_fail)

SubscriptionService
  └── CreditManager
  └── User (model)
  └── Subscription (model)
  └── Transaction (model)
  └── PLAN_MINUTES (from PaymentService)

PaymentService
  └── stripe SDK
  └── razorpay SDK

StorageService
  └── boto3 (R2 mode)
  └── local filesystem (V0 mode)

Analytics
  └── posthog SDK
```

---

## 15. BillingService

**File:** `hookcut-backend/app/services/billing_service.py`

**Class Purpose:** Owns all billing/checkout business logic. All methods are `@staticmethod`. Routers call these methods and convert `HookCutError` to `HTTPException`. Covers plans listing, checkout creation (subscription + PAYG), user sync on login, V0 test credit grants, and webhook dispatch for Stripe/Razorpay.

### Public Methods

```python
class BillingService:
    @staticmethod
    def get_plans(db: Session, user_id: str) -> PlansResponse:
        """
        Get available subscription plans for user's currency.
        Returns PlansResponse with current_tier, currency, and list of PlanInfo.
        Falls back to USD plans if user not found.
        """
        # Raises: nothing

    @staticmethod
    def create_checkout(db: Session, user_id: str, plan_tier: str) -> CheckoutResult:
        """
        Create a checkout session for subscription purchase.
        Validates V0 mode guard, plan tier (must be 'lite' or 'pro'), user existence.
        Delegates to PaymentService for actual checkout creation.
        Returns CheckoutResult with checkout_url and session_id.
        """
        # Raises: InvalidStateError (V0 mode or bad tier), UserNotFoundError,
        #         PaymentProcessingError (payment provider failure)

    @staticmethod
    def create_payg_checkout(db: Session, user_id: str, minutes: int) -> CheckoutResult:
        """
        Create a PAYG checkout session.
        Validates V0 mode guard, minutes (must be multiple of 100, minimum 100), user existence.
        Delegates to PaymentService for actual checkout creation.
        Returns CheckoutResult with checkout_url and session_id.
        """
        # Raises: InvalidStateError (V0 mode or bad minutes), UserNotFoundError,
        #         PaymentProcessingError (payment provider failure)

    @staticmethod
    def sync_user(db: Session, user_id: str, email: str) -> dict:
        """
        Ensure user exists in backend after NextAuth login.
        Creates User + CreditBalance if new. Tracks analytics for new signups.
        Returns dict with: user_id, is_new, plan_tier, role.
        """
        # Raises: nothing

    @staticmethod
    def v0_grant_credits(
        db: Session, user_id: str, paid_minutes: float, payg_minutes: float
    ) -> dict:
        """
        V0 only: Grant test credits without payment.
        Returns dict with granted amounts and current balance breakdown.
        """
        # Raises: InvalidStateError (not V0 mode)

    @staticmethod
    def handle_stripe_webhook(db: Session, payload: bytes, signature: str) -> dict:
        """
        Verify Stripe webhook signature and dispatch to WebhookService handlers.
        Handles: checkout.session.completed, invoice.paid, customer.subscription.deleted.
        """
        # Raises: InvalidStateError (bad signature)

    @staticmethod
    def handle_razorpay_webhook(db: Session, payload: bytes, signature: str) -> dict:
        """
        Verify Razorpay webhook signature and dispatch to WebhookService handlers.
        Handles: subscription.charged, order.paid, subscription.cancelled.
        """
        # Raises: InvalidStateError (bad signature)

    @staticmethod
    def _extract_razorpay_entity(body: dict) -> dict:
        """Extract the entity from a Razorpay webhook payload (subscription/order/payment)."""
```

### Dependencies

| Dependency | What it does |
|---|---|
| `app.config.get_settings` | V0 mode flag, Stripe/Razorpay keys |
| `CreditManager(db)` | Balance checks, credit provisioning (V0 grants) |
| `PaymentService()` | Stripe/Razorpay checkout session creation |
| `WebhookService` | Webhook event handling (lazy import) |
| `track()` / `identify()` | Analytics event tracking for user sync |
| `stripe` | Stripe webhook signature verification (lazy import) |
| `razorpay` | Razorpay webhook signature verification (lazy import) |

### Exception Types (from `app.exceptions`)

| Exception | Status | Raised by |
|---|---|---|
| `InvalidStateError` | 400 | `create_checkout`, `create_payg_checkout` (V0 mode/bad input), `v0_grant_credits` (not V0), webhook handlers (bad signature) |
| `UserNotFoundError` | 404 | `create_checkout`, `create_payg_checkout` |
| `PaymentProcessingError` | 500 | `create_checkout`, `create_payg_checkout` (provider failure) |

### Inter-Service Calls

- `BillingService` -> `PaymentService` (checkout creation)
- `BillingService` -> `CreditManager` (V0 credit grants)
- `BillingService` -> `WebhookService` (webhook event dispatch)

### Invariants

- All methods are `@staticmethod` -- no instance state.
- V0 mode blocks real payment flows; `v0_grant_credits` only works in V0 mode.
- `sync_user` is idempotent -- safe to call on every login.
- Webhook handlers verify signatures before processing any events.

---

## 16. ShortsService

**File:** `hookcut-backend/app/services/shorts_service.py`

**Class Purpose:** Owns all Short retrieval and download business logic. All methods are `@staticmethod`. Routers call these methods and convert `HookCutError` to `HTTPException`. Covers local file serving (V0), Short status/details retrieval, presigned download URL generation, and discard tracking.

### Public Methods

```python
class ShortsService:
    @staticmethod
    def serve_local_file(file_key: str) -> tuple[str, str]:
        """
        Resolve a local storage path for serving (V0 only).
        Returns (absolute_file_path, media_type) tuple.
        media_type is 'video/mp4' for .mp4 files, 'image/jpeg' otherwise.
        """
        # Raises: InvalidStateError (R2 mode), ShortNotFoundError (file missing)

    @staticmethod
    def get_short(db: Session, short_id: str) -> ShortResponse:
        """
        Get Short details including status and download URL.
        Generates a presigned thumbnail URL if thumbnail_file_key is set.
        Returns ShortResponse schema.
        """
        # Raises: ShortNotFoundError

    @staticmethod
    def download_short(db: Session, short_id: str) -> ShortDownloadResponse:
        """
        Generate a fresh presigned download URL and log the download event.
        Updates Short.download_url and Short.download_url_expires_at in DB.
        Creates a LearningLog entry with event_type='short_downloaded'.
        Returns ShortDownloadResponse with download_url and expires_at.
        """
        # Raises: ShortNotFoundError, ShortNotReadyError (status != 'ready'),
        #         InvalidStateError (no video_file_key)

    @staticmethod
    def discard_short(db: Session, short_id: str) -> dict:
        """
        Mark a Short as discarded (user chose not to download).
        Creates a LearningLog entry with event_type='short_discarded'.
        Returns {'status': 'discarded'}.
        """
        # Raises: ShortNotFoundError
```

### Dependencies

| Dependency | What it does |
|---|---|
| `StorageService()` | Presigned URL generation, local path resolution |
| `DOWNLOAD_URL_EXPIRES_SECONDS` | TTL for presigned URLs (from `celery_app`) |
| `LearningLog` | Event logging for downloads and discards |
| `Short` model | ORM model with relationship to `AnalysisSession` |

### Exception Types (from `app.exceptions`)

| Exception | Status | Raised by |
|---|---|---|
| `ShortNotFoundError` | 404 | `get_short`, `download_short`, `discard_short`, `serve_local_file` |
| `ShortNotReadyError` | 400 | `download_short` -- status is not 'ready' |
| `InvalidStateError` | 400 | `serve_local_file` (R2 mode), `download_short` (no video file) |

### Inter-Service Calls

- `ShortsService` -> `StorageService` (presigned URLs, local path resolution)

### Invariants

- All methods are `@staticmethod` -- no instance state.
- `download_short` always creates a LearningLog entry via `short.session` relationship navigation.
- `serve_local_file` is V0-only -- raises if StorageService has S3/R2 configured.

---

## 17. UserService

**File:** `hookcut-backend/app/services/user_service.py`

**Class Purpose:** Owns all user profile, balance, and history business logic. All methods are `@staticmethod`. Routers call these methods and convert `HookCutError` to `HTTPException`.

### Public Methods

```python
class UserService:
    @staticmethod
    def get_balance(db: Session, user_id: str) -> BalanceResponse:
        """
        Get current credit balance for the authenticated user.
        Returns BalanceResponse with paid/free/payg minutes and total_available.
        """
        # Raises: nothing (auto-creates balance if missing via CreditManager)

    @staticmethod
    def get_history(
        db: Session, user_id: str, page: int, per_page: int
    ) -> dict:
        """
        Get past analysis sessions for the authenticated user.
        Returns dict with: sessions (list of session dicts), total, page, per_page.
        Sessions ordered by created_at desc.
        """
        # Raises: nothing

    @staticmethod
    def get_profile(db: Session, user_id: str) -> dict:
        """
        Get user profile.
        Returns dict with: id, email, currency, plan_tier, role, created_at.
        """
        # Raises: UserNotFoundError

    @staticmethod
    def update_currency(db: Session, user_id: str, currency: str) -> dict:
        """
        Change preferred currency. Must be 'INR' or 'USD'.
        Returns dict with: currency.
        """
        # Raises: InvalidStateError (bad currency), UserNotFoundError
```

### Dependencies

| Dependency | What it does |
|---|---|
| `CreditManager(db)` | Balance retrieval (with auto-provisioning) |
| `AnalysisSession` model | History queries (ordered by `created_at`) |
| `User` model | Profile retrieval and currency updates |

### Exception Types (from `app.exceptions`)

| Exception | Status | Raised by |
|---|---|---|
| `UserNotFoundError` | 404 | `get_profile`, `update_currency` |
| `InvalidStateError` | 400 | `update_currency` -- invalid currency value |

### Inter-Service Calls

- `UserService` -> `CreditManager` (balance retrieval)

### Invariants

- All methods are `@staticmethod` -- no instance state.
- `get_history` treats page <= 0 as page 1 for offset calculation.
- `update_currency` commits immediately after mutation.

---

## 18. AdminService

**File:** `hookcut-backend/app/services/admin_service.py`

**Class Purpose:** Business logic for the admin dashboard. All 22 methods are `@staticmethod`. Covers dashboard stats, user management, session browsing, audit logs, prompt rule CRUD with versioning, LLM provider configuration, and NARM (Niche-Aware Recommendation Model) insight generation.

### Public Methods (22 total)

| Method | Params | Returns | Purpose |
|--------|--------|---------|---------|
| `get_dashboard_stats` | `db` | `dict` | COUNT queries on users, sessions, shorts, subscriptions + last 10 sessions |
| `list_users` | `db, page, per_page` | `dict` | Paginated users with session counts (subquery) |
| `update_user_role` | `db, user_id, new_role, admin_user` | `User` | Change role + audit log |
| `list_all_sessions` | `db, page, per_page, status` | `dict` | All sessions across users, filterable |
| `get_session_detail` | `db, session_id` | `dict` | Session + hooks + shorts + user email |
| `list_audit_logs` | `db, page, per_page, action` | `dict` | Paginated audit logs with admin email |
| `export_audit_logs` | `db, start_date, end_date` | `list[dict]` | All logs in date range |
| `create_audit_log` | `db, admin_user, action, resource_type, resource_id, before, after, description` | `AdminAuditLog` | Create audit entry (helper) |
| `list_rules` | `db` | `list[PromptRule]` | Active rules (latest version per key) |
| `get_active_rules_as_dicts` | `db` | `list[dict]` | Active rules as plain dicts for prompt building |
| `create_rule` | `db, title, content, rule_key, admin_user` | `PromptRule` | Create custom rule (auto-key if none) |
| `update_rule` | `db, rule_id, admin_user, title, content, is_active` | `PromptRule` | New version (never in-place edit) |
| `revert_rule` | `db, rule_id, target_version_id, admin_user` | `PromptRule` | New version from target content |
| `delete_rule` | `db, rule_id, admin_user` | `None` | Deactivate custom rules only |
| `seed_rules` | `db, admin_user` | `list[PromptRule]` | Bootstrap 17 base rules A-Q |
| `preview_prompt` | `db, niche, language` | `dict` | Build prompt from active DB rules |
| `get_rule_history` | `db, rule_key` | `list[PromptRule]` | All versions for a key |
| `list_providers` | `db` | `list[ProviderConfig]` | All configs (seeds defaults if empty) |
| `update_provider` | `db, provider_name, admin_user, is_enabled, model_id` | `ProviderConfig` | Update + audit |
| `set_primary_provider` | `db, provider_name, admin_user` | `ProviderConfig` | Atomic primary switch |
| `set_api_key` | `db, provider_name, api_key, admin_user` | `ProviderConfig` | Write to .env, store last4 |
| `trigger_narm_analysis` | `db, time_range_days, admin_user` | `list[NarmInsight]` | LLM analysis of LearningLog |
| `get_narm_insights` | `db` | `list[NarmInsight]` | Latest 20 insights |

### Dependencies

| Dependency | What it does |
|---|---|
| `User`, `Subscription` models | User management, subscription counts |
| `AnalysisSession`, `Hook`, `Short` models | Session/hook/short queries and stats |
| `LearningLog` model | NARM aggregate queries |
| `AdminAuditLog`, `PromptRule`, `ProviderConfig`, `NarmInsight` models | Admin-specific data |
| `get_provider()` | LLM provider for NARM insight generation |
| `build_hook_prompt_from_rules()` | Prompt preview from DB rules |
| `get_settings()` | API key reads for provider seeding |

### Exception Types (from `app.exceptions`)

| Exception | Status | Raised by |
|---|---|---|
| `ResourceNotFoundError` | 404 | `update_user_role`, `get_session_detail`, `update_rule`, `revert_rule`, `delete_rule`, `update_provider`, `set_primary_provider`, `set_api_key` |
| `HookCutError` | 500 | `get_dashboard_stats`, `list_users`, `list_all_sessions`, `list_audit_logs`, `export_audit_logs`, `create_rule`, `preview_prompt`, `trigger_narm_analysis`, `delete_rule` (base rules) |

### Inter-Service Calls

- `AdminService` -> `get_provider()` (NARM LLM calls)
- `AdminService` -> `build_hook_prompt_from_rules()` (prompt preview)

### Key Design Decisions

- **Rule versioning**: `update_rule` creates a new row (new version, new ID), deactivates old. Never edits in place.
- **API keys in .env**: `set_api_key` reads .env, finds/replaces the key line, writes back. DB only stores `api_key_last4` and `api_key_set`.
- **NARM LLM call**: Uses `get_provider(settings.LLM_PRIMARY_PROVIDER)` to generate insights from LearningLog aggregates. Falls back to basic data-only insights if LLM fails.
- **Audit helper**: `create_audit_log` is called by every state-changing method, capturing before/after JSON state.
- **Provider seeding**: `list_providers` auto-seeds gemini/anthropic/openai defaults if no configs exist.
