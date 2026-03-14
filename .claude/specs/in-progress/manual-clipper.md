# Manual Clipper Feature — Implementation Spec (v2)

## Overview
Add a "Manual Clipper" mode to HookCut alongside the existing AI Hook Detection. Users scrub a YouTube video via the embedded YouTube IFrame Player API, set start/end timestamps, and generate clips with the same processing pipeline (resize, captions, audio normalization, silence padding). No LLM cost for hook identification — but LLM is still used for caption cleanup and title generation per clip.

---

## 1. Plan Tier Restructure

### BREAKING CHANGE: Current → New Plan Mapping

Current plans in code (`billing_service.py`):
- Free: 120 min/mo, watermarked
- Lite: 499 INR/mo, 100 min watermark-free
- Pro: 999 INR/mo, 500 min watermark-free

**New structure (5 tiers):**

| Tier | Price (INR) | Price (USD) | AI Minutes | Manual Clipper | Watermark | Notes |
|---|---|---|---|---|---|---|
| **Free** | 0 | 0 | 120 min/mo (existing) | 120 min/mo source video | Yes (logo) | Separate pools for AI vs manual |
| **Lite** | 199/mo | ~$2.50/mo | 0 | 100 min/mo | No | Manual-only tier. New tier. |
| **Pro** | 499/mo | $7/mo | 200 min/mo | Unlimited | No | Was "Lite" at 499 INR with 100 min AI. Now 200 min AI + unlimited manual. |
| **Pro Max** | 999/mo | $13/mo | 500 min/mo | Unlimited | No | Was "Pro" at 999 INR with 500 min AI. Now also unlimited manual. |
| **PAYG** | 5/min AI, 2/min manual | — | On-demand | On-demand | No | Existing PAYG rate for AI stays; add 2 INR/min manual rate |

### Migration Path for Existing Subscribers
- Existing "Lite" (499 INR) subscribers → auto-migrate to "Pro" (same price, more features)
- Existing "Pro" (999 INR) subscribers → auto-migrate to "Pro Max" (same price, more features)
- No one loses features — this is purely additive
- Razorpay: retire old plan IDs, create new ones. Handle via webhook for subscription renewal.

### Credit System Changes

**`CreditBalance` model** — add these fields:
```python
manual_clip_minutes_remaining: Float = 0.0
manual_clip_minutes_total: Float = 0.0
```

**`CreditManager` deduction logic** — new method `deduct_manual_credits()`:
- Pro/Pro Max: skip deduction entirely (unlimited manual clips)
- Lite: deduct from `manual_clip_minutes_remaining`
- Free: deduct from `manual_clip_minutes_remaining` (separate from AI pool)
- PAYG: deduct from `payg_minutes_remaining` at 2 INR/min rate
- Deduction order for manual: Manual pool → PAYG → reject (do NOT fall through to AI pool)

**Free re-clip for paid AI users:**
- If user has a non-expired `AnalysisSession` (status=`completed` or `hooks_ready`) for the same `video_id` AND `source_type="ai"`, manual clips on that video are free
- Check: `AnalysisSession.query(user_id=X, video_id=Y, source_type="ai", status IN ("completed", "hooks_ready"), created_at > now() - 24h)`
- 24-hour window — not forever, not just the browser session (user might close and reopen)

### Monthly Reset
- On subscription renewal: reset `manual_clip_minutes_remaining` to plan allocation (100 for Lite, unlimited for Pro/Pro Max)
- Free tier: reset both AI and manual pools to 120 each on the 1st of the month

---

## 2. Aspect Ratio Selection (Both Modes)

### Supported Ratios
| Ratio | Resolution | Use Case |
|---|---|---|
| **9:16** (default) | 1080×1920 | YouTube Shorts, TikTok, Reels |
| **1:1** | 1080×1080 | Instagram Feed, Twitter/X |
| **4:5** | 1080×1350 | Instagram Feed, Facebook |

### When Selected
- **AI mode**: After hook selection, before "Generate Shorts" button. Per-batch (all selected hooks get same ratio).
- **Manual mode**: In clip settings panel. Per-batch (all clips in queue get same ratio).

### Backend Changes
- **`schemas/shorts.py`**: Add `aspect_ratio: Literal["9:16", "1:1", "4:5"] = "9:16"` to `SelectHooksRequest`
- **`short_generator.py`**: Replace hardcoded `1080x1920` with:
  ```python
  ASPECT_RESOLUTIONS = {
      "9:16": (1080, 1920),
      "1:1": (1080, 1080),
      "4:5": (1080, 1350),
  }
  ```
  Update `render_short()` FFmpeg scale filter to use `ASPECT_RESOLUTIONS[aspect_ratio]`.
  Update crop filter: for 1:1 and 4:5, center-crop the source to target aspect before scaling.
- **`tasks.py`**: Pass `aspect_ratio` through to `ShortGenerator.generate()`
- **Short model**: Add `aspect_ratio: String = "9:16"` column

### Frontend Changes
- **New component `src/components/shared/aspect-ratio-picker.tsx`**: 3 visual buttons showing ratio shape (tall rect, square, slightly-tall rect) with platform labels below each
- **AI results page**: Insert picker above "Generate Shorts" button
- **Manual clipper**: Include in clip settings panel

---

## 3. Manual Clipper — Frontend

### New Page: `/clip` (requires auth)

**Entry points:**
1. Top nav "Clipper" link (always visible, next to existing nav items)
2. AI results page: "Or clip it yourself" section with button → `/clip?url={youtube_url}&session={session_id}`
   - When `session` param is present, backend knows to skip credit deduction (free re-clip flow)

**Page layout:**

#### 3.1 URL Input
- Same YouTube URL input component as home page (extract and reuse)
- If `?url=` query param present, auto-populate and auto-load
- Validate URL client-side, extract video ID
- Show loading skeleton while YouTube player initializes

#### 3.2 YouTube Embed Player
Use YouTube IFrame Player API (`YT.Player`).

```typescript
// Key API methods used:
player.getCurrentTime(): number  // seconds with ~250ms precision
player.getDuration(): number
player.seekTo(seconds: number, allowSeekAhead: boolean)
player.getVideoData(): { title: string, video_id: string }
player.getPlayerState(): number  // -1 unstarted, 0 ended, 1 playing, 2 paused, 3 buffering
```

**Important constraints:**
- YouTube IFrame API `getCurrentTime()` has ~250ms precision — display time with 1 decimal place (e.g., "1:23.4"), not frame-accurate
- Some videos disable embedding (`playsinline` / embed restrictions) — detect via `onError` event (error code 150 = embed not allowed). Show message: "This video cannot be embedded. Try a different video."
- Age-restricted videos won't load in embed — same error handling
- Load the IFrame API script dynamically, not in `<head>`. Use a `useYouTubePlayer` custom hook that returns `{ player, isReady, error }`.
- Player size: responsive, max-width 800px, 16:9 aspect ratio maintained via `aspect-ratio: 16/9` CSS

**Duration validation:**
- After `onReady`, check `player.getDuration()`. If > 7200 (2 hours), show error: "Videos over 2 hours are not supported for manual clipping." and disable the scrubber.
- If duration is 0 (live stream or unknown), show: "Live streams are not supported."

#### 3.3 Timeline Scrubber
Custom dual-handle range slider built with React (not a library — keep it lightweight).

**Visual design (dark glass-morphism theme):**
- Full width of video player container
- Track: 8px tall, rounded, `bg-white/10` base with `bg-gradient-to-r from-violet-500 to-cyan-500` for selected range
- Two circular handles (20px diameter), frosted glass effect, with subtle glow on drag
- Playback needle: thin (2px) white vertical line that moves with video playback (update via `requestAnimationFrame` polling `getCurrentTime()` at ~15fps)
- Time labels: on handles as floating tooltips during drag, format `MM:SS.s` (one decimal)
- Below track: left-aligned "0:00", right-aligned total duration

**Interaction:**
- Drag handles to set start/end
- Click anywhere on track to seek video to that position
- "Set Start" button: snaps start handle to current playback position
- "Set End" button: snaps end handle to current playback position
- "Preview Selection" button: calls `player.seekTo(start)`, plays, auto-pauses at end time (poll `getCurrentTime` and pause when >= end)
- Keyboard: Tab to focus handles, Left/Right arrow ±1s, Shift+Arrow ±5s
- Min clip duration: 3 seconds (prevent accidentally empty clips)
- Handles cannot cross each other (start always < end)

**Performance:**
- Playback needle: use `requestAnimationFrame` with 66ms throttle (~15fps) — polling `getCurrentTime()` is cheap
- Handle drag: use pointer events (not mouse events) for touch support
- Debounce `seekTo()` calls during drag to max 1 per 200ms

#### 3.4 Clip Queue Panel
Below the scrubber.

- "Add Clip" button (accent color, prominent): saves current start/end as a new clip entry
- Clip list: each entry shows:
  - Clip number badge (#1, #2, ...)
  - Start time → End time (e.g., "1:23.4 → 2:15.0")
  - Duration (e.g., "51.6s")
  - "Edit" button (loads clip back into scrubber for adjustment)
  - "Remove" button (trash icon)
- Clips sorted by order added (not by timestamp)
- Total duration display: "Total: 3m 24s" (sum of all clip durations)
- **Silent 10-clip limit**: After 10 clips, "Add Clip" button becomes disabled. If somehow triggered, return: "You've created the maximum number of clips from this video."
- Empty state: "Set start and end points above, then click Add Clip"

#### 3.5 Clip Settings Panel
Side panel or collapsible section (below queue on mobile, beside queue on desktop).

- **Aspect Ratio**: shared `AspectRatioPicker` component — 9:16 (default), 1:1, 4:5
- **Caption Style**: Clean, Bold, Neon, Minimal — reuse existing caption style picker
- **Captions toggle**: Switch, default On. When Off, skip transcript fetch and subtitle generation.
- **Audio normalization toggle**: Switch, default On.
- All settings apply to ALL clips in the batch (not per-clip)

#### 3.6 Cost Preview & Generate Button
- Show estimated cost before generating:
  - Free: "X clips · Y min total · Watermarked"
  - Lite: "X clips · Y min total · Z min remaining after"
  - Pro/Pro Max: "X clips · No credit deduction"
  - PAYG: "X clips · Y min total · ₹Z estimated cost"
  - Free re-clip: "X clips · No credit deduction (from your AI analysis)"
- "Generate X Clips" primary button
- Disable button if insufficient credits (show "Insufficient minutes" with link to pricing)
- On click: POST to `/api/clips/generate`, receive task IDs, transition to generating state

#### 3.7 Generation Progress & Results
- Reuse existing polling infrastructure (`usePollTask` hook)
- Show progress for each clip: "Clip #1: Downloading... 45%" / "Clip #2: Processing..."
- As each clip completes, show the existing `ShortCard` component (inline video preview, download, discard)
- If all clips succeed: show success summary
- If some fail: show per-clip error messages with "Retry" button per clip

#### 3.8 State Management
`useReducer` with discriminated union (same pattern as `home-state-machine.tsx`):

```typescript
type ClipperState =
  | { step: "input"; url: string; error: string }
  | { step: "video_loaded"; videoId: string; videoTitle: string; duration: number; clips: ClipEntry[]; settings: ClipSettings; error: string }
  | { step: "generating"; videoId: string; videoTitle: string; clips: ClipEntry[]; taskIds: string[]; completedClips: ShortResult[]; error: string }
  | { step: "complete"; videoId: string; videoTitle: string; results: ShortResult[]; error: string }

type ClipEntry = {
  id: string;  // client-generated UUID for React key
  startTime: number;
  endTime: number;
}

type ClipSettings = {
  aspectRatio: "9:16" | "1:1" | "4:5";
  captionStyle: "clean" | "bold" | "neon" | "minimal";
  captionsEnabled: boolean;
  audioNormalization: boolean;
}

type ClipperAction =
  | { type: "LOAD_VIDEO"; videoId: string; videoTitle: string; duration: number }
  | { type: "LOAD_VIDEO_ERROR"; error: string }
  | { type: "ADD_CLIP"; startTime: number; endTime: number }
  | { type: "REMOVE_CLIP"; clipId: string }
  | { type: "EDIT_CLIP"; clipId: string; startTime: number; endTime: number }
  | { type: "UPDATE_SETTINGS"; settings: Partial<ClipSettings> }
  | { type: "START_GENERATE"; taskIds: string[] }
  | { type: "CLIP_COMPLETE"; taskId: string; result: ShortResult }
  | { type: "CLIP_FAILED"; taskId: string; error: string }
  | { type: "RESET" }
```

**Session persistence**: Store state in `sessionStorage` with 2-hour TTL (same as home page). Key: `hookcut_clipper_${videoId}`. Restore on page load if URL matches.

#### 3.9 Mobile Responsiveness
- YouTube player: full width, 16:9 aspect ratio maintained
- Scrubber: full width, touch-friendly handles (44px touch target per WCAG)
- Clip queue + settings: stack vertically on mobile (currently side-by-side on desktop)
- "Set Start" / "Set End" buttons: larger on mobile (48px height)
- Preview button: full width on mobile

---

## 4. Manual Clipper — Backend

### 4.1 New Schemas (`app/schemas/clip.py`)

```python
from pydantic import BaseModel, field_validator
from typing import Literal, Optional

class ClipSegment(BaseModel):
    start_time: float  # seconds
    end_time: float    # seconds

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("time must be non-negative")
        return v

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

class GenerateClipsRequest(BaseModel):
    youtube_url: str
    clips: list[ClipSegment]  # 1-10 items
    caption_style: Literal["clean", "bold", "neon", "minimal"] = "clean"
    captions_enabled: bool = True
    audio_normalization: bool = True
    aspect_ratio: Literal["9:16", "1:1", "4:5"] = "9:16"
    ai_session_id: Optional[str] = None  # for free re-clip flow

    @field_validator("clips")
    @classmethod
    def validate_clip_count(cls, v):
        if len(v) == 0:
            raise ValueError("At least one clip is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 clips per video")
        return v

    @field_validator("clips")
    @classmethod
    def validate_min_duration(cls, v):
        for clip in v:
            if clip.duration < 3.0:
                raise ValueError(f"Clip duration must be at least 3 seconds (got {clip.duration:.1f}s)")
        return v

    @field_validator("clips")
    @classmethod
    def validate_max_source_duration(cls, v):
        # Each clip's end_time must be <= 7200 (2 hours)
        for clip in v:
            if clip.end_time > 7200:
                raise ValueError("Clips cannot extend beyond 2 hours into the video")
        return v

class GenerateClipsResponse(BaseModel):
    session_id: str
    task_ids: list[str]  # one per clip, same order as input clips
    total_duration_seconds: float
    minutes_deducted: float
    is_free_reclip: bool
```

### 4.2 New Service (`app/services/clip_service.py`)

```python
class ClipService:
    @staticmethod
    def generate_clips(
        db: Session,
        user_id: str,
        request: GenerateClipsRequest,
    ) -> GenerateClipsResponse:
        """
        1. Validate YouTube URL (reuse existing validate_youtube_url())
        2. Check free re-clip eligibility:
           - If ai_session_id provided, verify it belongs to this user,
             same video_id, source_type="ai", status in ("completed", "hooks_ready"),
             created_at within 24 hours
           - If eligible: is_free_reclip = True, skip credit deduction
        3. If not free re-clip: check & deduct manual clip minutes
           - Pro/Pro Max: no deduction
           - Others: deduct total_duration from manual pool
        4. Check clip count for this video_id:
           - Query Short.count where session.video_id == video_id AND session.user_id == user_id
           - If existing + new > 10, reject
        5. Create AnalysisSession with source_type="manual":
           - youtube_url, video_id, video_title (from URL or client can pass it)
           - status="generating_shorts" (skip analysis states)
           - transcript_text=None, transcript_provider=None
           - minutes_charged = total_duration (or 0 if free re-clip)
           - is_watermarked = user is free tier
        6. For each clip: create Short record:
           - session_id, hook_id=None (IMPORTANT: make hook_id nullable!)
           - source_type="manual"
           - start_seconds_override = clip.start_time
           - end_seconds_override = clip.end_time
           - aspect_ratio = request.aspect_ratio
           - caption_style = request.caption_style
           - status="queued"
        7. For each clip: enqueue generate_short Celery task
        8. Return session_id + task_ids
        """
```

### 4.3 New Router (`app/routers/clip.py`)

```python
# POST /api/clips/generate
# Auth: required (get_current_user dependency)
# Rate limit: 5 requests per 15 minutes
# Request: GenerateClipsRequest
# Response: GenerateClipsResponse
# Errors:
#   400: Invalid URL, invalid clips, min duration, max clips exceeded
#   402: Insufficient manual clip minutes
#   403: Unauthorized
#   429: Rate limited
```

### 4.4 Model Changes

**`AnalysisSession` model — add:**
```python
source_type: String = "ai"  # "ai" or "manual"
```
- No other changes needed. For manual sessions, transcript/analysis fields stay NULL.

**`Short` model — changes:**
```python
hook_id: String, nullable=True  # CRITICAL: currently NOT nullable. Must migrate.
source_type: String = "ai"      # "ai" or "manual"
aspect_ratio: String = "9:16"   # "9:16", "1:1", "4:5"
```
- **BREAKING**: `hook_id` must become nullable. Manual clips have no associated hook.
- Migration must handle existing data (all existing shorts have hook_id set, so no data issue).

**`CreditBalance` model — add:**
```python
manual_clip_minutes_remaining: Float = 0.0
manual_clip_minutes_total: Float = 0.0
```

### 4.5 Caption Handling for Manual Clips

**This is the most nuanced part.** AI mode gets transcript during analysis. Manual mode has no analysis phase.

When `captions_enabled=True` for a manual clip:
1. `ShortGenerator.generate()` must fetch transcript for the clip's time range
2. Use the existing transcript cascade: CF Worker → YouTube captions → Whisper fallback
3. Extract only the segment matching `[start_time, end_time]` from the full transcript
4. Pass to LLM for caption cleanup (same as AI mode)
5. If transcript fetch fails entirely: generate clip WITHOUT captions, set a warning flag on the Short: `captions_failed: bool = False` (new field). Frontend shows: "Captions unavailable for this clip"

**Optimization**: If multiple clips are from the same video, fetch the transcript ONCE and cache it for the session. Don't re-fetch per clip.
- Store on the AnalysisSession: `transcript_text` (same field used by AI mode)
- First clip task fetches and saves; subsequent tasks read from DB

**When `captions_enabled=False`:** Skip transcript fetch entirely. No LLM call for caption cleanup. No subtitle burn-in. Title still auto-generated via LLM (short call, cheap).

### 4.6 Title Generation for Manual Clips

Manual clips still need a title for the Short card UI. Two options:
- **Option A**: LLM generates title from the caption text (same as AI mode) — requires transcript
- **Option B**: Use video title + clip number: "{Video Title} - Clip 1"

Use Option A when captions are enabled (LLM is already running for cleanup). Fallback to Option B when captions disabled or transcript unavailable.

### 4.7 `ShortGenerator.generate()` Signature Changes

Current signature:
```python
def generate(self, youtube_url, hook, session_id, short_id, is_watermarked, language, niche, caption_style, on_progress)
```

**New signature** (backwards compatible via defaults):
```python
def generate(
    self,
    youtube_url: str,
    hook: Optional[dict],  # None for manual clips
    session_id: str,
    short_id: str,
    is_watermarked: bool,
    language: str = "English",
    niche: str = "Generic",
    caption_style: str = "clean",
    aspect_ratio: str = "9:16",
    captions_enabled: bool = True,
    audio_normalization: bool = True,
    source_type: str = "ai",
    # For manual clips (when hook is None):
    start_seconds: Optional[float] = None,
    end_seconds: Optional[float] = None,
    video_title: Optional[str] = None,  # for fallback title generation
    cached_transcript: Optional[str] = None,  # avoid re-fetching
    on_progress: Optional[Callable] = None,
) -> ShortResult
```

When `hook` is None (manual clip):
- Use `start_seconds` / `end_seconds` directly instead of `hook["start_seconds"]` / `hook["end_seconds"]`
- If `captions_enabled=False`: skip transcript fetch, skip LLM caption cleanup, skip ASS subtitle generation
- If `audio_normalization=False`: skip loudnorm filter in FFmpeg chain
- Title: LLM-generated from captions, or `f"{video_title} - Clip"` if no captions

### 4.8 Watermark Changes

**Current**: Text watermark — "HookCut" text, 24px, 0.3 opacity (in `short_generator.py`)

**New**: Logo watermark — PNG image overlay:
- **Asset**: `hookcut-backend/app/assets/hookcut-watermark.png` — transparent PNG of HookCut logo. Must be created manually (not auto-generated). Min resolution: 400x400px for quality at 18% of 1080px width.
- **FFmpeg filter chain** (replaces current text watermark):
  ```
  [1:v]scale=iw*0.18:-1,colorchannelmixer=aa=0.6[watermark];
  [0:v][watermark]overlay=W-w-40:H-h-40[out]
  ```
  - Scale watermark to 18% of output width (~194px on 1080 wide)
  - 60% opacity via alpha channel mixer
  - Bottom-right with 40px padding from edges
  - Works for all aspect ratios (uses relative W/H)
- **When applied**: `is_watermarked=True` on the Short (free tier only, both AI and manual mode)
- **Burned in**: Part of FFmpeg render, not a post-process. Cannot be removed.

---

## 5. Navigation & UX Flow

### 5.1 Top Nav
Add "Clipper" link in header nav. Position: after "Pricing", before user menu.
- Icon: `Scissors` from lucide-react
- On mobile hamburger: add as menu item

### 5.2 AI Results Page Integration
After the 5 hook cards, add:
```
─── Or clip it yourself ───
[Open Manual Clipper →]
```
- Styled as a subtle divider, not a prominent CTA (don't distract from the AI results)
- Button navigates to `/clip?url={youtube_url}&session={session_id}`
- Session ID enables free re-clip validation on backend

### 5.3 Post-Generation Cross-Sell
After manual clips are generated, show a subtle upsell:
- "Want AI to find the best hooks automatically? [Try AI Analysis →]"
- Only show to Lite and Free tier users (Pro/Pro Max already have both)

---

## 6. Error Handling Matrix

| Scenario | User Sees | Backend |
|---|---|---|
| Video embed blocked (error 150) | "This video cannot be embedded. Try a different video." | N/A (client-side) |
| Video > 2 hours | "Videos over 2 hours are not supported." | 400 validation |
| Live stream | "Live streams are not supported." | 400 validation |
| Age-restricted video | "This video is restricted and cannot be clipped." | N/A (client-side) |
| Clip < 3 seconds | "Minimum clip duration is 3 seconds." | 400 validation |
| > 10 clips on video | "You've created the maximum number of clips from this video." | 400 validation |
| Insufficient minutes | "Insufficient minutes. [Upgrade →]" with link to pricing | 402 |
| Transcript unavailable | Clip generates without captions; warning shown | `captions_failed=True` on Short |
| yt-dlp download failure | "Failed to download video segment. The video may be unavailable." | 500, Short status="failed" |
| FFmpeg processing failure | "Processing failed. Please try again." | 500, Short status="failed" |
| Concurrent session on same video | Allow — don't block. Each session is independent. | Normal flow |

---

## 7. Rate Limiting & Abuse Prevention

- **Generate endpoint**: 5 requests per 15 min per user (same Redis-based limiter as analysis)
- **URL validation**: Reuse existing YouTube URL regex
- **Total daily minutes per user**: Soft cap of 60 minutes of generated output per day for free tier (prevents abuse). Not enforced for paid tiers.
- **Video ID dedup**: If user submits same video twice in clipper, show their existing clips first: "You have X existing clips from this video. Add more?"
- **Silent 10-clip limit per video**: Enforced server-side. Count includes both AI-generated and manual clips for the same `video_id` + `user_id`.

---

## 8. Database Migration

Single migration file: `008_add_manual_clipper_support.py`

```sql
-- 1. Make Short.hook_id nullable (BREAKING but safe — all existing rows have values)
ALTER TABLE shorts ALTER COLUMN hook_id DROP NOT NULL;

-- 2. Add source_type to sessions and shorts
ALTER TABLE analysis_sessions ADD COLUMN source_type VARCHAR(10) DEFAULT 'ai' NOT NULL;
ALTER TABLE shorts ADD COLUMN source_type VARCHAR(10) DEFAULT 'ai' NOT NULL;

-- 3. Add aspect_ratio to shorts
ALTER TABLE shorts ADD COLUMN aspect_ratio VARCHAR(5) DEFAULT '9:16' NOT NULL;

-- 4. Add captions_failed flag
ALTER TABLE shorts ADD COLUMN captions_failed BOOLEAN DEFAULT FALSE NOT NULL;

-- 5. Add manual clip balance to credit_balance
ALTER TABLE credit_balances ADD COLUMN manual_clip_minutes_remaining FLOAT DEFAULT 0.0 NOT NULL;
ALTER TABLE credit_balances ADD COLUMN manual_clip_minutes_total FLOAT DEFAULT 0.0 NOT NULL;

-- 6. Index for free re-clip lookup
CREATE INDEX idx_sessions_video_user_source ON analysis_sessions(video_id, user_id, source_type, created_at);

-- 7. Index for clip count check
CREATE INDEX idx_shorts_session_source ON shorts(session_id, source_type);
```

---

## 9. CONTRACTS.md Updates

### Backend Services CONTRACTS.md — add:
```
ClipService (app/services/clip_service.py)
  generate_clips(db, user_id, request: GenerateClipsRequest) → GenerateClipsResponse
    - Validates URL, checks credits, creates session + shorts, enqueues tasks
    - Free re-clip: checks ai_session_id ownership + 24h window
    - Raises: InsufficientCreditsError, ValidationError, NotFoundError
```

### Backend Routers CONTRACTS.md — add:
```
POST /api/clips/generate
  Auth: required
  Rate limit: 5/15min
  Request: GenerateClipsRequest
  Response: GenerateClipsResponse
  Errors: 400 (validation), 402 (credits), 429 (rate limit)
```

---

## 10. Admin Dashboard Changes

Add to existing admin dashboard stats:
- **Clips by source**: Pie chart — AI vs Manual clip counts
- **Manual clipper usage**: Line chart — daily minutes consumed
- **Lite tier conversions**: Count of Lite subscribers
- **Free re-clip rate**: % of manual clips that were free (from AI sessions)

Add to admin sessions list:
- `source_type` column with filter (AI / Manual / All)

---

## 11. Testing Requirements

### Backend Tests (new file: `tests/test_clip_service.py`)
- Generate clips — happy path (1 clip, 5 clips, 10 clips)
- Validation: > 10 clips rejected, < 3s clip rejected, > 2hr rejected
- Credit deduction: Lite user minutes deducted, Pro user no deduction
- Free re-clip: valid AI session → no deduction
- Free re-clip: expired AI session (>24h) → deduction applied
- Free re-clip: wrong user's session → rejected
- Watermark flag: free tier → is_watermarked=True
- Source type: manual clips get source_type="manual"
- Aspect ratio: all 3 ratios stored correctly

### Backend Tests (new file: `tests/test_clip_router.py`)
- Auth required
- Rate limiting
- Request validation (schema errors)
- Credit check (402 on insufficient)

### Backend Tests (modify: `tests/test_short_generator.py`)
- Aspect ratio: 9:16, 1:1, 4:5 produce correct resolutions
- Watermark: logo overlay in FFmpeg command when is_watermarked=True
- Captions disabled: no transcript fetch, no subtitle burn-in
- Audio normalization disabled: no loudnorm in FFmpeg chain
- Manual clip: hook=None path works

---

## 12. Files to Create/Modify

### Backend — New Files
| File | Purpose |
|---|---|
| `app/schemas/clip.py` | `GenerateClipsRequest`, `ClipSegment`, `GenerateClipsResponse` |
| `app/services/clip_service.py` | `ClipService.generate_clips()` |
| `app/routers/clip.py` | `POST /api/clips/generate` |
| `app/assets/hookcut-watermark.png` | Logo watermark PNG (must be created manually) |
| `alembic/versions/008_add_manual_clipper_support.py` | DB migration |
| `tests/test_clip_service.py` | Service tests |
| `tests/test_clip_router.py` | Router tests |

### Backend — Modified Files
| File | Changes |
|---|---|
| `app/main.py` | Register clip router |
| `app/models/session.py` | Add `source_type` |
| `app/models/short.py` | Make `hook_id` nullable, add `source_type`, `aspect_ratio`, `captions_failed` |
| `app/models/credit_balance.py` | Add `manual_clip_minutes_remaining/total` |
| `app/tasks.py` | Add `aspect_ratio`, `captions_enabled`, `audio_normalization`, `source_type` params |
| `app/services/short_generator.py` | Aspect ratio resolution map, logo watermark, optional captions/normalization, `hook=None` path |
| `app/services/billing_service.py` | Lite plan, manual credit deduction, monthly reset for manual pool |
| `app/services/credit_manager.py` | `deduct_manual_credits()` method |
| `app/schemas/shorts.py` | Add `aspect_ratio` to `SelectHooksRequest` |
| `app/schemas/billing.py` | Add `pro_max` tier, update `PlanInfo`, add `manual_clip_minutes` to `BalanceResponse` |
| `app/routers/admin.py` | Source type filter on sessions, manual clip stats |
| `app/utils/ffmpeg_commands.py` | `ASPECT_RESOLUTIONS` dict, watermark overlay filter function |
| `tests/test_short_generator.py` | Aspect ratio + watermark + captions-off tests |

### Frontend — New Files
| File | Purpose |
|---|---|
| `src/app/clip/page.tsx` | Manual clipper page (auth-gated) |
| `src/components/clip/youtube-player.tsx` | YouTube IFrame API wrapper hook + component |
| `src/components/clip/timeline-scrubber.tsx` | Dual-handle range slider |
| `src/components/clip/clip-queue.tsx` | List of queued clips |
| `src/components/clip/clip-settings.tsx` | Aspect ratio + caption style + toggles |
| `src/components/clip/clip-state-machine.tsx` | useReducer + types |
| `src/components/shared/aspect-ratio-picker.tsx` | Reusable picker for both modes |

### Frontend — Modified Files
| File | Changes |
|---|---|
| `src/lib/types.ts` | Clipper types, `Lite`/`ProMax` plans, `source_type`, `aspect_ratio` on Short |
| `src/lib/api.ts` | `generateClips()` function |
| `src/components/layout/header.tsx` | "Clipper" nav link |
| `src/app/pricing/page.tsx` | 5-tier pricing table, Lite highlighted |
| `src/app/(home)/page.tsx` or results section | "Or clip it yourself" section with link |
| `src/components/shared/short-card.tsx` | Handle `captions_failed` warning display |

---

## 13. Implementation Order

**Phase 1: Backend Foundation (do first — frontend depends on it)**
1. DB migration (`008_add_manual_clipper_support`)
2. Model changes (Session, Short, CreditBalance)
3. Schemas (`clip.py`, update `shorts.py`, `billing.py`)
4. `short_generator.py` changes (aspect ratio, `hook=None` path, captions toggle, audio toggle)
5. `ffmpeg_commands.py` changes (aspect resolutions, watermark filter)
6. `credit_manager.py` — `deduct_manual_credits()`
7. `billing_service.py` — Lite/ProMax plans, manual minute tracking
8. `clip_service.py` — full service
9. `clip.py` router — endpoint + rate limit
10. `main.py` — register router
11. Backend tests

**Phase 2: Frontend (after backend is stable)**
12. `types.ts` — all new types
13. `api.ts` — `generateClips()` call
14. `aspect-ratio-picker.tsx` — shared component
15. `youtube-player.tsx` — embed wrapper
16. `timeline-scrubber.tsx` — dual-handle slider
17. `clip-queue.tsx` — clip list
18. `clip-settings.tsx` — settings panel
19. `clip-state-machine.tsx` — useReducer
20. `clip/page.tsx` — assemble page
21. `header.tsx` — nav link
22. AI results page — "Or clip it yourself" section
23. `pricing/page.tsx` — 5-tier table

**Phase 3: Polish**
24. Watermark asset (manual creation — not code)
25. Logo watermark FFmpeg integration
26. Admin dashboard — source_type analytics
27. CONTRACTS.md updates
28. Post-generation cross-sell ("Try AI Analysis" for Lite/Free users)

---

## 14. Out of Scope (Explicitly NOT in V1)

- Frame-accurate seeking (YouTube API is ~250ms precision — acceptable)
- Waveform visualization (requires audio download — defeats the purpose)
- Per-clip settings (all clips share aspect ratio / caption style)
- Video trimming preview in the browser (just use YouTube player scrubbing)
- Batch download (download clips individually)
- Auto-reframing / face tracking (future feature — just center-crop for now)
- Custom watermark position (always bottom-right)
