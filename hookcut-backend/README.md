# HookCut Backend

FastAPI backend for HookCut — extract hook segments from YouTube videos and generate Shorts.

## Prerequisites

- Python 3.10+
- Redis (for Celery task queue)
- FFmpeg (for video processing)
- yt-dlp (for YouTube segment extraction)

### Install system dependencies

```bash
# macOS
brew install ffmpeg yt-dlp redis

# Ubuntu/Debian
sudo apt install ffmpeg
pip install yt-dlp
sudo apt install redis-server
```

## Quick Start (V0 Local Dev)

### 1. Clone and install

```bash
cd hookcut-backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set at least GEMINI_API_KEY (primary) or ANTHROPIC_API_KEY (fallback)
# For V1: also set DATABASE_URL, NEXTAUTH_SECRET, R2 credentials
```

### 3. Start Redis

```bash
docker compose up -d
# Or: redis-server (if installed natively)
```

### 4. Start the API server

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Start Celery worker (separate terminal)

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### 6. (Optional) Start Celery Beat for scheduled tasks

```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

## API Usage

### Grant test credits (V0 only)

```bash
curl -X POST "http://localhost:8000/api/billing/v0-grant?paid_minutes=500"
```

### Validate a YouTube URL

```bash
curl -X POST http://localhost:8000/api/validate-url \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### Start hook analysis

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "niche": "Tech / AI",
    "language": "English"
  }'
# Returns: {session_id, task_id, ...}
```

### Poll task status

```bash
curl http://localhost:8000/api/tasks/{task_id}
```

### Get hooks (after task completes)

```bash
curl http://localhost:8000/api/sessions/{session_id}/hooks
```

### Select hooks and generate Shorts

```bash
curl -X POST http://localhost:8000/api/sessions/{session_id}/select-hooks \
  -H "Content-Type: application/json" \
  -d '{
    "hook_ids": ["hook-id-1", "hook-id-2"],
    "caption_style": "bold",
    "time_overrides": {
      "hook-id-1": {"start_seconds": 12.0, "end_seconds": 42.0}
    }
  }'
# Returns: {short_ids, task_ids}
# caption_style: "clean" (default), "bold", "neon", "minimal"
# time_overrides: optional ±10s boundary adjustments per hook
```

### Get Short details

```bash
curl http://localhost:8000/api/shorts/{short_id}
```

### Regenerate hooks

```bash
curl -X POST http://localhost:8000/api/sessions/{session_id}/regenerate
```

### Check balance

```bash
curl http://localhost:8000/api/user/balance
```

### Admin API

All admin endpoints require the user to have `role="admin"`.

#### Get admin dashboard
```bash
curl http://localhost:8000/api/admin/dashboard \
  -H "Authorization: Bearer TOKEN"
```

#### Seed base rules (one-time bootstrap)
```bash
curl -X POST http://localhost:8000/api/admin/rules/seed \
  -H "Authorization: Bearer TOKEN"
```

#### List prompt rules
```bash
curl http://localhost:8000/api/admin/rules \
  -H "Authorization: Bearer TOKEN"
```

## API Docs

With the server running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

```
YouTube URL → validate → fetch metadata → check credits → deduct
  → [Celery] transcript cascade (3 providers) → LLM hook identification (5 hooks)
  → user selects 1-3 hooks
  → [Celery] yt-dlp segment extraction → FFmpeg render (9:16, audio, captions)
  → upload to storage → download
```

### Key Design Decisions

- **LLM-only hook identification** — no deterministic pre-filtering
- **Never downloads full video** — `yt-dlp --download-sections` only
- **Single-pass FFmpeg** — one encode operation
- **Credits billed on source video duration**, not Short duration
- **18 hook types** (union of PRD + engine reference)
- **7-dimension holistic scoring** — attention_score is editorial judgment
- **3-provider transcript cascade** — youtube-transcript-api → yt-dlp subs → Whisper API
- **LLM retry**: 3 attempts with [0s, 5s, 30s] backoff, fallback provider on 3rd attempt
- **4 caption style presets** — clean, bold, neon, minimal (via FFmpeg ASS subtitles)
- **Hook boundary trimming** — ±10s adjustment via time_overrides
- **Improvement suggestions** — LLM-generated creator tips per hook
- **Admin RBAC** — `get_admin_user` dependency, returns 403 for non-admin users
- **Rule versioning** — each edit creates new version, old versions preserved for revert
- **API keys in .env** — ProviderConfig stores only `api_key_last4` + `api_key_set`, actual keys in .env file
- **NARM insights** — LLM-powered analysis of LearningLog aggregates
- **Audit trail** — all admin actions logged with before/after JSON state snapshots

## Project Structure

```
app/
├── main.py              # FastAPI app
├── config.py            # Settings + feature flags
├── dependencies.py      # DB session, auth helpers
├── middleware/           # Auth (NextAuth JWT), rate limiting
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic request/response
├── routers/             # API endpoints
├── services/            # Business logic
├── llm/                 # LLM providers + prompts
│   └── prompts/         # Hook identification, caption cleanup, title gen
├── tasks/               # Celery async tasks
├── utils/               # YouTube URL, timestamps, FFmpeg commands
├── models/admin.py          # Admin models (4: AuditLog, PromptRule, ProviderConfig, NarmInsight)
├── schemas/admin.py         # Admin Pydantic schemas (24 models)
├── services/admin_service.py # AdminService (22 methods)
└── routers/admin.py         # Admin endpoints (20 routes under /api/admin/)
```

## V0 vs V1

| Feature | V0 (Local Dev) | V1 (Production) |
|---------|---------------|-----------------|
| Database | SQLite | Supabase PostgreSQL |
| Storage | Local filesystem | Cloudflare R2 |
| Auth | Bypassed (default user) | NextAuth.js JWT (Google OAuth) |
| LLM | Gemini 2.5 Flash | Gemini → Claude Sonnet 4 → GPT-4o |
| Payments | Grant via API | Stripe + Razorpay |
| Rate Limiting | None | Redis-based |
| Monitoring | Console logs | Sentry + PostHog |
| Admin UI | None | 7 admin pages under /admin/ |
| Rule Engine | Hardcoded prompt | DB-backed versioned rules (A-Q + custom) |
| Audit Log | None | AdminAuditLog with before/after state |
