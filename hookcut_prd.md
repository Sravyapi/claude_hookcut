## 15 Admin Features (V1)

> **STATUS: IMPLEMENTED (March 2026).** All admin features below are functional. Backend: `get_admin_user` RBAC dependency, 4 new models (`AdminAuditLog`, `PromptRule`, `ProviderConfig`, `NarmInsight`), `AdminService` with 22 methods, 20 endpoints under `/api/admin/`. Frontend: 7 admin pages under `/admin/` (layout, dashboard, users, sessions, rules, models, audit). Database: Alembic migration 007.

### Admin Login & Role Management
- Admin access controlled via `User.role` field ("user" or "admin"), set during V1 migration 003.
- `get_admin_user` FastAPI dependency enforces role check on all `/api/admin/*` endpoints (returns 403 for non-admins).
- Frontend `proxy.ts` middleware protects `/admin/:path*` routes (redirects unauthenticated users to login).
- Admin layout (`src/app/admin/layout.tsx`) checks role client-side and redirects non-admins to "/".
- Role changes: PATCH `/api/admin/users/{user_id}/role` with audit logging.

### Admin Dashboard: NARM Recommendations & Rule Engine
- **Dashboard** (`GET /api/admin/dashboard`): 4 stat cards (total users, sessions, shorts, active subscriptions) + last 10 sessions table.
- **NARM (Natural Adaptive Rule Mining)**: `POST /api/admin/narm/analyze` feeds LearningLog aggregates (hook selection rates, niche trends, regeneration patterns) to the primary LLM provider. Returns natural language insights stored as `NarmInsight` records.
- **Rule Engine**: 17 base rules (A-Q) seeded from the hardcoded prompt via `POST /api/admin/rules/seed`. Admin can:
  - View and edit all rules (base + custom) with full content editing
  - Create custom rules (auto-assigned keys R, S, T...)
  - Toggle rules active/inactive
  - View version history per rule and revert to any previous version
  - Preview the full assembled prompt with any niche/language combination
- Rule changes are versioned (never edited in place). `build_hook_prompt_from_rules()` accepts admin rules as plain dicts at analysis time (LLM layer is DB-isolated).
- All rule changes tracked in `AdminAuditLog` with before/after state for revertability.

### Model Management
- 3 provider configs (Gemini, Anthropic, OpenAI) stored in `ProviderConfig` table.
- Admin can toggle providers enabled/disabled, change model IDs, and set primary/fallback roles.
- API key updates write to `.env` file (keys never stored in DB -- only `api_key_last4` and `api_key_set` boolean).
- `POST /api/admin/providers/{name}/set-primary` atomically switches the primary provider.
- All provider changes tracked in audit log.

### Audit Log
- All admin actions logged in `AdminAuditLog` with: admin_user_id, action type, resource_type, resource_id, before/after state (JSON), human-readable description, timestamp.
- Action types: role_changed, prompt_rule_created, prompt_rule_updated, prompt_rule_reverted, prompt_rule_deleted, provider_updated, provider_primary_changed, api_key_updated, narm_triggered.
- Audit log page: paginated, filterable by action type, expandable rows showing JSON diff of before/after state.
- Export: JSON download of filtered audit logs.

### Session & Data Management
- `GET /api/admin/sessions`: Paginated view of ALL sessions across all users (filterable by status).
- `GET /api/admin/sessions/{id}`: Full session detail with hooks, shorts, transcript, and user email.
- Admin can browse any user's session data for debugging and support.

### User vs. Admin Views
- Regular users see: hook text, scores, "why it works" education, improvement suggestions, and video preview.
- Admin dashboard shows: all user sessions, full scoring breakdowns, prompt rule editor, provider management, NARM insights, and complete audit trail.
- Admin layout uses sidebar navigation (Dashboard, Users, Sessions, Rules, Models, Audit Log).

### Revertability
- Rule changes: Each edit creates a new version. Admin can revert to any previous version via `POST /api/admin/rules/{id}/revert/{version_id}`.
- Provider changes: Tracked in audit log with before/after state snapshots.
- Role changes: Tracked in audit log. Can be undone by changing role back.
- All revert operations themselves create new audit log entries.

---

# Staff SWE Audit & Codebase Sync (March 2026)

**This PRD is synchronized with the current codebase as of March 2026.**

## Staff SWE Audit Summary (March 2026)
- **Dead Code Elimination:** Removed unused imports (logging in LLM providers), unused Pydantic schemas (`schemas/user.py`, `SetPrimaryRequest`), obsolete files and bytecode caches. Deleted unused `animated-section.tsx` component.
- **Bug Fixes:** Added missing `POST /providers/{name}/set-key` admin route. Fixed `PATCH /user/currency` from query param to JSON body. Added `hook_type` to LearningLog metadata for hook_selected/hook_not_selected events. Removed insecure `/billing/admin-grant` endpoint (superseded by RBAC).
- **Structural Refactor:** Added `SESSION_STATUS` constants with Set-based lookups in dashboard. Added `is_selected` to frontend Hook interface. Fixed pre-existing TypeScript errors.
- **Architecture Refactors (Phase 6):**
  - Extracted business logic from `routers/analysis.py` → `services/analyze_service.py` (5 static methods). Router is now a thin HTTP adapter.
  - Extracted webhook logic from `routers/billing.py` → `services/webhook_service.py` (6 static methods). Signature verification stays in router.
  - Refactored `build_hook_prompt_from_db()` → `build_hook_prompt_from_rules()` — LLM layer accepts plain dicts, never DB sessions.
  - `HookEngine.analyze()` accepts optional `rules: list[dict]` parameter for admin-defined rules.
  - Registered centralized `hookcut_exception_handler` in `main.py`. Removed local exception class shadows from `hook_engine.py` and `short_generator.py` — all exceptions now from `app.exceptions`.
  - Added rate limiting to analysis endpoints: analyze (10/15min), regenerate (5/15min), select-hooks (10/15min).
  - Added auth requirement to `regenerate` and `select-hooks` endpoints (previously unauthenticated).
- **Performance Improvements:** `HooksStep`, `HookCard`, and `SessionRow` wrapped with `React.memo`. Score calculations memoized with `useMemo`. Dashboard search debounced (250ms). Celery `worker_prefetch_multiplier` reduced from 4 to 1. History endpoint uses single base query. Shorts router uses relationship navigation. Timer cleanup with `useRef`. Callback stabilization with refs. Unbounded `export_audit_logs` query capped at 10,000.
- **Maintainability Pass:** Extracted shared constants (`ERROR_MSG_MAX_LEN`, `FREE_MONTHLY_MINUTES`, `DOWNLOAD_URL_EXPIRES_SECONDS`). Standardized error message truncation. Fixed CONTRACTS.md retry delay mismatch. Shared `getStatusConfig()` function in frontend constants. `NICHES` imported from constants (not duplicated). Error toasts added to all admin pages.
- **Competitive Features (March 2026):** Caption style presets (4 styles), hook boundary trimming (±10s), video preview before download, enhanced "Why It Works" education, analysis speed badge + timer.
- **Test Count:** 120 backend tests passing (up from 105 pre-audit).

---

## 01 Product Overview

**One-Line Description**
HookCut extracts high-performing hook segments from long-form YouTube videos and converts them into polished YouTube Shorts — explaining why each hook works and estimating its virality potential.

**Core Value Proposition**
- Identify the most scroll-stopping moments using LLM-based reasoning tuned per audience niche
- Convert selected hook segments into ready-to-post YouTube Shorts
- Explain hook effectiveness to educate creators, not just automate them — platform dynamics, viewer psychology, and actionable creator tips
- Minimise editing effort and cognitive load for solo creators
- 4 caption style presets and ±10s hook trimming for quick customisation

---

## 02 Non-Negotiable Principles

**Cumulative Feature Model**
All features introduced in V1 are available in V2 and V3 by default. Later versions only add — never remove.

**LLM Minimalism**
LLMs are used only where human-like editorial reasoning is required: hook identification, hook scoring, hook reasoning, title generation, caption cleanup, and improvement suggestions. Everything else uses deterministic, open-source, low-cost tooling (FFmpeg, OpenAI Whisper API, yt-dlp).

**No Full Video Download — Ever (V1)**
HookCut never downloads or stores a full video in V1. Only the transcript is fetched. After the user selects hook segments, `yt-dlp --download-sections` extracts only those timestamp ranges.
> V2 note: When users upload a video file directly, it may be cached temporarily for the session duration only, then deleted.

**Source Video Duration Billing**
Users are billed based on the duration of the source video processed, not the duration of the Short generated.

**Global Launch (V1)**
V1 is a global launch. HookCut supports creators worldwide, with particularly strong support for Indian English and Indian-language creators as a key differentiator. INR and USD pricing are both active from day one. Language is selected by the creator at analysis time. Indian English filler phrases ("hello dosto", "subscribe karo", "namaskar dosto") are still penalised in the LLM prompt regardless of niche.

**Hook Engine: LLM-Only (Final Decision)**
Hook identification is LLM-only. Deterministic heuristics-based approaches and hybrid approaches were both evaluated and abandoned due to unacceptably low accuracy. There is no deterministic pre-filtering stage, no keyword scoring, and no rule-based hook detection. The LLM is the only hook identification mechanism.

---

## 03 Hook Engine

**Architecture: Pure LLM, No Pre-Filtering**
The hook engine sends the full transcript to the LLM in one pass. There is no deterministic pre-filtering, no keyword scoring, and no rule-based hook detection. Deterministic and hybrid approaches were both evaluated and abandoned due to unacceptably low accuracy.

The V1 implementation uses Gemini 2.5 Flash as the primary LLM provider with Claude Sonnet 4 as the fallback. The user has no option to choose the provider. Provider selection was based on cost-per-analysis vs. accuracy benchmarks.

**What the LLM Does**
- Reads the full transcript in one pass
- Identifies exactly 5 hook candidates per video
- Scores each candidate on 7 dimensions (see scoring model below)
- Classifies each hook by type (18 types) and funnel role (6 roles)
- Explains the hook's psychological mechanism (platform dynamics + viewer psychology)
- Provides an actionable improvement suggestion per hook
- Adjusts selection criteria based on the user's chosen audience niche

**Scoring Model (7 Dimensions)**

| Dimension | Weight | What It Measures |
|---|---|---|
| scroll_stop | 35% | Pattern interrupt power — would a casual scroller pause? |
| curiosity_gap | 25% | Strength of the unresolved question created |
| stakes_intensity | 20% | Perceived consequence magnitude for the viewer |
| emotional_voltage | 12% | Speaker's emotional energy and conviction |
| standalone_clarity | 8% | Makes complete sense without prior context |
| thematic_focus | — | Thematic focus and relevance to the niche (gating: < 5 means hook cannot rank top 3) |
| thought_completeness | — | Completeness of the hook's dramatic thought (cuts early = ≤4, goes past landing = ≤5, delivers while withholding = 8+) |

`Attention Score` is a separate editorial judgment (0-10) by the LLM, explicitly not a formula over the 7 dimensions.

**Hook Duration**
No fixed minimum or maximum. Duration is determined by the content and the niche. Practical floor: hooks shorter than 10 seconds rarely contain enough context to be compelling. The correct duration is however long it takes to complete the hook's dramatic thought — no shorter, no longer.

**Niche / Audience Selector**

| Niche | Soft Duration Range | Primary Stakes | Tone | Preferred Types |
|---|---|---|---|---|
| Tech / AI | 12–30s | Disruption, obsolescence, breakthrough capability, competitive advantage, AI replacing humans, paradigm shifts | Bold, precise, forward-looking. Clear insight or surprising claim about technology impact. | Zero-Second Claim, Curiosity Gap, Counterintuitive, High Stakes Warning, Live Proof |
| Finance | 15–35s | Money lost/gained, hidden risk, wealth gap, market timing, financial ruin, generational wealth | Risk/reward framing. Concrete numbers, specific dollar figures, market-moving events. | Fear-Based, High Stakes Warning, Direct Benefit, Contrarian, FOMO Setup |
| Fitness | 10–25s | Wasted effort, transformation, body image | Transformation, motivation, before/after, emotional journey. | Contrarian, Direct Benefit, Personal Transformation, Counterintuitive |
| Relationships | 10–25s | Emotional pain, betrayal, connection | Vulnerable, relatable, emotionally charged. | Story-Based, Pattern Interrupt, Curiosity Gap, Personal Transformation |
| Drama / Commentary | 12–30s | Conflict, controversy, social consequence | Opinionated, provocative, high-energy. | Pattern Interrupt, High Stakes Warning, Zero-Second Claim, Fear-Based |
| Entrepreneurship | 15–30s | Costly mistakes, hard lessons, status | Candid, hard-won lessons, status signals. | Story-Based, High Stakes Warning, Contrarian, Personal Transformation, Curiosity Gap |
| Podcast | 15–40s | Insight reveal, surprising reframe, expert credibility | Insightful, expert-driven, surprising. | Curiosity Gap, Counterintuitive, Authority, Story-Based, Contrarian |
| Generic (default) | 12–30s | Broad curiosity gap, universal emotion | Universal, broad appeal, curiosity-driven. | Curiosity Gap, Counterintuitive, Direct Benefit, Story-Based |

**Encoded Rules (A–Q)**
hook_engine_v4 encodes 17 learned rules (A through Q) in the system prompt. These rules govern boundary quality, filler rejection, demo sequence handling, standalone clarity, and other editorial patterns derived from iterative feedback sessions.

**Hook Types (18)**
Curiosity Gap, Direct Benefit, Fear-Based, Authority, Contrarian, Counterintuitive, Story-Based, Pattern Interrupt, High Stakes Warning, Social Proof, Elimination, Objection Handler, Pain Escalation, Personal Transformation, Live Proof, FOMO Setup, Zero-Second Claim, Extended Demo.

**Funnel Roles (6)**
curiosity_opener, pain_escalation, solution_reveal, proof_authority, retention_hook, extended_demo.

---

## 04 Language Support (V1)

HookCut supports multi-language content from V1 launch. Language is selected by the creator at analysis time. The hook engine outputs `hook_text` in the **original language — never translated**.

| Language | Notes |
|---|---|
| English | Indian English + Global English. Hinglish code-switching accepted. |
| Hinglish | Hindi + English mix. Output in original mixed form. |
| Hindi | Devanagari or romanized. English tech terms allowed. |
| Tamil | Tamil or Tanglish (Tamil + English). |
| Telugu | Telugu or Telugu + English mix. |
| Kannada | Kannada or Kannada + English mix. |
| Malayalam | Malayalam or Manglish. |
| Marathi | Marathi or Marathi + Hindi/English mix. |
| Gujarati | Gujarati or Gujarati + English/Hindi mix. |
| Punjabi | Punjabi (Gurmukhi or romanized) or mixed. |
| Bengali | Bengali or Banglish (Bengali + English). |
| Odia | Odia or Odia + English/Hindi mix. |
| Other | Auto-detect from transcript. Code-switching to English or Hindi is normal for Indian creators. Apply all hook rules identically. Output hook_text in the ORIGINAL language — NEVER translate. |

> **Source of truth for per-language LLM prompt injection:** `hookcut-backend/app/llm/prompts/constants.py` → `LANGUAGES` dict.

---

## 05 User Workflow (V1)

**Step 0: Authentication and Quota Setup**
1. User signs up via Google OAuth (NextAuth.js)
2. Plan assigned. Minute quota initialised: 120 free watermarked minutes + paid plan minutes if applicable

**Step 1: Video Input**
1. User pastes a YouTube URL
2. System validates URL format (watch, youtu.be, shorts, embed)
3. System fetches source video duration via yt-dlp metadata (no video download)
4. System checks if user has sufficient minutes
5. User selects audience niche from pill chips (or leaves as Generic)

**Step 2: Transcript Acquisition**
1. youtube-transcript-api (primary)
2. yt-dlp subtitle extraction (fallback 1)
3. OpenAI Whisper API (fallback 2)
4. Failure → error shown, no credits deducted

> Transcripts are not cached. Each analysis fetches fresh.

**Step 3: Hook Generation**
Credits deducted when user clicks "Analyze". Analysis dispatched as async Celery task.
- Full transcript sent to LLM with niche system prompt
- LLM returns exactly 5 hooks with scores, explanations, and improvement suggestions
- On failure: retry up to 2 times (3 total, backoff 0s/5s/30s). All fail → credits refunded
- Frontend shows live elapsed timer during analysis

**Step 4: Hook Review and Selection**
- User reviews 5 hook cards with:
  - Hook text, timestamp range, attention score, hook type tag, funnel role
  - Platform dynamics and viewer psychology (always visible, not collapsed)
  - Hook type description (18 one-line explanations)
  - Top 2 strongest score highlights
  - Actionable "Creator Tip" (improvement suggestion from LLM)
  - Full 7-dimension score breakdown (expandable)
- Analysis time badge shows "Hooks found in X seconds"
- User selects 1–3 hooks to generate Shorts from
- User picks caption style (Clean, Bold, Neon, or Minimal)
- User can adjust hook boundaries ±10s with trim controls
- If unhappy: Regenerate (first free, 2nd+ charged ₹10–25)

**Step 5: Short Generation Pipeline**
For each selected hook:
1. `yt-dlp --download-sections` — extract segment only (respects time overrides if trimmed)
2. Aspect ratio: 16:9 → 9:16 (letterbox/crop, FFmpeg)
3. Audio: silence removal, padding, normalisation (FFmpeg)
4. Captions: LLM-cleaned transcript, burned in with selected caption style (FFmpeg + LLM)
5. Title: LLM-generated, Short-optimised
6. Thumbnail: middle frame extracted (FFmpeg)
7. Watermark if free tier

**Step 6: Output and Download**
- Inline video preview with play/pause controls (HTML5 player, not just thumbnail)
- MP4 + thumbnail + suggested title + hook explanation recap
- Minutes deducted (paid first, then free watermarked)
- Temp files deleted after download or session expiry

---

## 06 Short Generation Specification

**Caption Style Presets (V1)**

| Style | Font | Size | Color | Effect | Vibe |
|---|---|---|---|---|---|
| **Clean** (default) | Arial | 64px | White | 4px black outline | Professional, readable |
| **Bold** | Impact | 72px | White | 5px black outline, bold weight | High-energy, YouTube-native |
| **Neon** | Arial Black | 64px | Cyan (#00FFFF) | 3px dark blue outline, glow shadow | Trendy, gaming/tech |
| **Minimal** | Helvetica | 52px | White @ 90% | 2px dark gray outline, subtle shadow | Elegant, understated |

Caption style is selected by the user before Short generation and stored on the Short record.

**Hook Segment Analysis**
Each identified hook segment is accompanied by an analysis explaining why it is likely to work, scoring it on 7 dimensions, and assigning an overall attention score. This analysis is always visible to the user and includes an actionable improvement suggestion — turning HookCut from a clip tool into a content strategy coach.

| Element | Action | Tool |
|---|---|---|
| Aspect ratio | 16:9 → 9:16 (letterbox/crop) | FFmpeg |
| Audio | Silence removal, padding, normalisation | FFmpeg |
| Captions | LLM-cleaned text, burned in with selected style | FFmpeg + LLM |
| Title | LLM-generated, Short-optimised | LLM |
| Thumbnail | Middle frame as static image | FFmpeg |
| Watermark | Applied if free tier | FFmpeg |

**Hook Boundary Trimming (V1)**
Users can adjust hook start/end times by ±10 seconds using trim controls before generating Shorts. Constraints:
- Minimum hook duration: 5 seconds
- Start cannot be more than 10s before original
- End cannot be more than 10s after original
- Overrides stored on the Short record, original timestamps preserved on Hook

**What Does NOT Change in V1**
- No face-aware cropping or face tracking
- No visual content modifications beyond aspect ratio
- No B-roll, overlays, or visual effects
- No re-encoding beyond required operations
- Single-pass FFmpeg rendering only

> V3 will introduce meme overlays, emoji reactions, dynamic zoom cuts, animated subtitles.

**Output Format:** MP4, 9:16, normalised audio, burned-in captions (user-selected style), JPG thumbnail.

---

## 07 Transcript Acquisition

**Provider Cascade**
1. youtube-transcript-api (primary) — fast, free, YouTube's own caption data
2. yt-dlp subtitle extraction (fallback 1) — broader format support (json3, VTT)
3. OpenAI Whisper API (fallback 2, only if FEATURE_WHISPER_FALLBACK is enabled) — audio transcription when no captions exist
4. Failure — user informed, no credits deducted
The Whisper fallback is controlled by a feature flag and may be disabled in some deployments.

**Why OpenAI Whisper API (Not Local Whisper.cpp)**
More accurate, no local GPU, simpler deployment. Per-minute cost absorbed into margin at launch. Local Whisper reconsidered in V2 if cost becomes material.

**Input Format (V1):** YouTube URLs only. No file upload. Transcripts not cached.

---

## 08 Regeneration Policy

- First regeneration per video: **free**
- Each subsequent regeneration: **₹10–25** depending on source video duration
- Fees are flat (LLM tokens, not video processing capacity)
- No cooldown — paid service, user can regenerate immediately
- Credits for Short generation deducted at "Analyze" click
- Regeneration fees charged at point of clicking Regenerate (2nd+ only)

---

## 09 Billing and Plans

**Universal Free Tier:** 120 minutes watermarked/month for all users including paid subscribers.

**Credit Consumption Order:**
1. Paid watermark-free credits (from subscription)
2. Free watermarked tier (auto-activates when paid exhausted)
3. Prompt to top up via PAYG

**Subscription Plans (V1) — INR**

| Plan | Price | Watermark-Free Minutes | Free Watermarked | Notes |
|---|---|---|---|---|
| Free | ₹0/month | 0 | 120 min/month | Watermark on all Shorts |
| Lite | ₹499/month | 100 min/month | 120 min/month | |
| Pro | ₹999/month | 500 min/month | 120 min/month | |
| PAYG Add-On | ₹100 per 100 min | As purchased | — | No expiry |

**Subscription Plans (V1) — USD**

| Plan | Price | Watermark-Free Minutes | Free Watermarked | Notes |
|---|---|---|---|---|
| Free | $0/month | 0 | 120 min/month | Watermark on all Shorts |
| Lite | $7/month | 100 min/month | 120 min/month | |
| Pro | $13/month | 500 min/month | 120 min/month | |
| PAYG Add-On | $2 per 100 min | As purchased | — | No expiry |

> Currency is detected from user locale at signup and can be changed in settings.

**Payment Methods (V1)**

| Method | Provider | Currency | Use Case |
|---|---|---|---|
| UPI | Razorpay | INR | Indian users — primary |
| Indian debit/credit cards | Razorpay | INR | Indian users |
| International cards | Stripe | USD | Global users |

**Billing Notes**
- Billing on source video duration, not Short duration
- No charge for failed analyses
- No charge for reviewing hooks before confirming Short generation
- Regeneration fees separate from minute credits
- Regeneration fee (2nd+ attempt): ₹10–25 / ~$0.30

---

## 10 Data Learning Loop
**Editorial Feedback Approval**
Feedback analysis and proposed rule updates are not applied automatically. All feedback analysis and rule changes must be manually reviewed and approved by an admin before being incorporated into the rule engine.

**Purpose:** Capture user behaviour signals to inform periodic manual improvements to the hook engine system prompt. No real-time auto-modification.

**What Is Logged Per Session**

| Event | Data Captured |
|---|---|
| Hook presented | video_id, hook_text, start_time, end_time, hook_type, attention_score, niche, session_id |
| Hook selected for Short | hook_id, selection_order, session_id |
| Hook not selected | hook_id, session_id |
| Regeneration triggered | video_id, session_id, which hooks shown previously |
| Short downloaded | hook_id, watermarked (bool), session_id |
| Short discarded | hook_id, session_id |

**How It Is Used**
- Accepted vs. rejected hooks reveal systematic engine biases
- Regeneration triggers indicate engine missed the mark
- Patterns across users inform prompt refinements (not individual personalisation)
- Manual review cadence: weekly or monthly

**Important Constraints**
- User feedback = signal, not ground truth
- No real-time prompt modification in V1
- No personalisation per user in V1
- Logging is read-only from user perspective

---

## 11 Error Handling

| Error | When | User Message | Credits Deducted? |
|---|---|---|---|
| Invalid URL | URL validation | Format guidance shown | No |
| Insufficient minutes | Before transcript fetch | Show balance + top-up | No |
| Transcript unavailable | All 3 providers fail | "No transcript found. Try a video with captions." | No |
| Video private/age-restricted | Fetch | "Video not accessible." | No |
| LLM failure (all 3 retries) | Hook generation | "Analysis unavailable. Credits not deducted. Try again." | No (refunded) |
| FFmpeg failure | Short generation | "Short generation failed. Credits refunded." | No (refunded) |
| yt-dlp segment failure | Short generation | "Could not extract segment. Try different hook." | No (refunded) |
| Wallet insufficient | Regeneration 2+ | Show balance + top-up | No |

**LLM Retry Policy:** 3 total attempts with backoff (0s, 5s, 30s). Attempts 1-2 use primary provider (Gemini). Attempt 3 uses fallback provider (Anthropic). All fail → error shown + credits refunded.

---

## 12 Version Roadmap

**V0 — Local Development (Complete)**
- Transcript cascade — production-ready
- LLM hook identification — 17 rules, niche-aware, multi-language
- Short generation pipeline — FFmpeg-based
- Orchestration layer — FastAPI + Celery

**V1 — Web Application (Current — March 2026)**
- Global launch — INR + USD pricing, Razorpay + Stripe
- YouTube URL input only (no file upload)
- 13 languages: English, Hinglish, Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Gujarati, Punjabi, Bengali, Odia, Other
- Google OAuth via NextAuth.js
- Supabase PostgreSQL
- Gemini 2.5 Flash (primary) + Claude Sonnet 4 (fallback) + GPT-4o (tertiary)
- 18 hook types, 7-dimension holistic scoring, 6 funnel roles
- 4 caption style presets (Clean, Bold, Neon, Minimal)
- Hook boundary trimming (±10s)
- Inline video preview before download
- Enhanced "Why It Works" education (platform dynamics, viewer psychology, creator tips)
- Analysis speed badge + elapsed timer
- Free watermarked tier (120 min/mo) + Lite + Pro + PAYG
- Data learning loop (LearningLog)
- Dashboard with session history, credit balance, and search
- Admin dashboard with NARM recommendations, rule engine, model management, and audit log

**V1.1 — Post-Launch Improvements**
- A/B hook variants (multiple FFmpeg renders per hook)
- Per-creator learning (LearningLog analysis pipeline + enhanced admin analytics)
- Accent/multi-speaker robustness improvements
- Stripe integration (pending invite approval for India)

**V2 — Input and Market Expansion**
- Direct video file upload (MP4, session-cached then deleted)
- Face-aware reframing with face tracking (OpenCV/ML)
- Multi-platform publishing (YouTube Data API)
- Template library & brand kits
- In-tool timeline editor
- Cloud infrastructure, dashboards, persistent hook libraries
- Local Whisper.cpp reconsidered if API cost becomes material at scale

**V3 — Creative Augmentation**
- Word-by-word animated captions (word-level Whisper timestamps + custom renderer)
- Meme overlays, emoji reactions, sound effects
- Dynamic zoom cuts, loop-friendly endings
- Transcript-based video editing (Gling-level UX)
- Beyond talking heads (content-type detection ML)
- Hook identification logic identical to V1

---

## 13 Tech Stack (V1)

**Backend**

| Component | Technology | Notes |
|---|---|---|
| Language | Python 3.10+ | |
| Framework | FastAPI | Async, automatic OpenAPI docs |
| Transcript — primary | youtube-transcript-api 1.2.4+ | |
| Transcript — fallback 1 | yt-dlp | Subtitle extraction |
| Transcript — fallback 2 | OpenAI Whisper API | Audio transcription only when needed |
| Video segment extraction | yt-dlp --download-sections | Never downloads full video |
| Video/audio processing | FFmpeg | Single-pass rendering only |
| LLM — primary | Gemini 2.5 Flash (Google AI API) | Raw HTTP via httpx, JSON mode |
| LLM — fallback | Claude Sonnet 4 (Anthropic API) | Official SDK |
| LLM — tertiary | GPT-4o (OpenAI API) | Official SDK |
| Database | PostgreSQL (Supabase, ap-south-1) | SQLAlchemy 2.0 ORM |
| Auth | NextAuth.js (JWT) | Google OAuth, HS256 tokens |
| Payments | Razorpay + Stripe | Razorpay: UPI + Indian cards. Stripe: international cards + USD |
| Background jobs | Celery + Redis | Async analysis + Short generation |

**Frontend**

| Component | Technology |
|---|---|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript 5 |
| UI | Tailwind CSS 4 + shadcn/ui |
| Animations | Framer Motion |
| Auth | NextAuth.js (next-auth v5) |
| State | React hooks (useState, useMemo, useCallback) — no external state library |
| Hosting | Vercel |

**Infrastructure**

| Component | Technology |
|---|---|
| Backend hosting | Railway or Render |
| Database | Supabase PostgreSQL (ap-south-1) |
| File storage | Cloudflare R2 (temp Short files, auto-deleted) |
| Monitoring | Sentry + PostHog |
| Email | Resend.com |

---

## 14 Legal and Operational Considerations

- User must confirm rights/permission before generating Shorts
- Temp files deleted after download or session expiry
- Rate limiting on transcript fetch and LLM calls
- Virality scores are LLM estimates, not guarantees — disclaimer shown in UI
- GDPR and Indian IT Act compliance: user data deletion on request
- YouTube Terms of Service: users responsible for compliance with original creator's terms

---

## 15 Todo / Roadmap Tracker

### Pre-Launch Blockers

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Stripe setup (India invite pending) | BLOCKED | Invitation submitted. Once approved: create products/prices/webhook, set `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` in .env |
| 2 | Razorpay setup | BLOCKED | Fill `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, plan IDs in .env |
| 3 | Node.js 22 for production | TODO | Must use Node 22 (not 25) for Next.js 16 |
| 4 | Sentry DSN + PostHog keys | TODO | Code ready, DSN/keys blank until projects created |
| 5 | Run Alembic migrations (004-006) | TODO | Caption style, improvement_suggestion, time overrides columns |
| 6 | Production deploy config | TODO | Railway/Render backend, Vercel frontend |
| 7 | R2 storage CORS configuration | TODO | Verify `Accept-Ranges` headers for video streaming/preview |
| 8 | End-to-end testing (full flow) | TODO | URL → hooks → select → generate → preview → download |

### V1.1 — Post-Launch

| # | Feature | Effort | Notes |
|---|---|---|---|
| 1 | A/B hook variants | High | Multiple FFmpeg renders per hook |
| 2 | Per-creator learning pipeline | High | LearningLog analysis + admin dashboard |
| 3 | Accent/multi-speaker robustness | Medium | Whisper fallback handles most cases |

### V2 — Features

| # | Feature | Effort | Notes |
|---|---|---|---|
| 1 | Face-aware reframing | High | OpenCV/ML model, center crop handles 80% |
| 2 | Direct video file upload | Medium | MP4 session-cached, then deleted |
| 3 | Multi-platform publishing | Medium | YouTube Data API + OAuth scope |
| 4 | Template library & brand kits | Medium | Agency feature |
| 5 | In-tool timeline editor | High | Trim controls handle 80% of the need |
| 6 | Transcript-based video editing | Very High | Gling-level UX |
| 7 | Beyond talking heads | High | Content-type detection ML |

### V3 — Features

| # | Feature | Effort | Notes |
|---|---|---|---|
| 1 | Word-by-word animated captions | Very High | Word-level Whisper timestamps + custom renderer |
| 2 | Meme overlays + emoji reactions | High | |
| 3 | Dynamic zoom cuts | High | |
| 4 | Loop-friendly endings | Medium | |

---

*HookCut • NyxPath • Confidential • Version 4.0 • March 2026*
