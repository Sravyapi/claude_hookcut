# HookCut Routers Layer — Contracts

> All endpoints, request/response schemas, auth requirements, error mappings, and service delegation.
> Generated from `app/routers/`, `app/schemas/`, `app/middleware/`, and `app/main.py`.

---

## Global Configuration

**App mount:** All routers prefixed with `/api`
**CORS:** `settings.FRONTEND_URL` + `http://localhost:3000`, credentials allowed
**Sentry:** Initialized if `SENTRY_DSN` is set (non-fatal on failure)

```python
# main.py router registration
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(shorts.router,   prefix="/api", tags=["shorts"])
app.include_router(tasks.router,    prefix="/api", tags=["tasks"])
app.include_router(user.router,     prefix="/api", tags=["user"])
app.include_router(billing.router,  prefix="/api", tags=["billing"])
app.include_router(admin.router,    prefix="/api", tags=["admin"])
```

---

## Authentication

**Mechanism:** `get_current_user_id` → `get_authenticated_user_id` (FastAPI `Depends`)

```python
# V0 mode: returns "v0_local_user" (no auth check)
# V1 mode: verifies NextAuth JWT from Authorization header
#   - Algorithm: HS256
#   - Secret: settings.NEXTAUTH_SECRET
#   - User ID: payload["sub"]
```

**Auth errors:**
| Status | Condition | Detail |
|--------|-----------|--------|
| 401 | Missing/malformed Authorization header | "Missing or invalid Authorization header" |
| 401 | Token expired | "Token expired" |
| 401 | Invalid token | "Invalid token" |
| 401 | Token missing `sub` claim | "Invalid token: missing sub claim" |
| 500 | NEXTAUTH_SECRET not configured | "Auth not configured" |

---

## Master Endpoint Table

| Method | Path | Auth | Request Body | Response | Router |
|--------|------|:----:|-------------|----------|--------|
| GET | `/health` | No | — | `{status, version}` | main.py |
| POST | `/api/validate-url` | No | `VideoValidateRequest` | `VideoValidateResponse` | analysis |
| POST | `/api/analyze` | Yes | `AnalyzeRequest` | `AnalyzeResponse` | analysis |
| GET | `/api/sessions/{session_id}/hooks` | No | — | `HooksListResponse` | analysis |
| POST | `/api/sessions/{session_id}/regenerate` | Yes | — | `RegenerateResponse` | analysis |
| POST | `/api/sessions/{session_id}/select-hooks` | Yes | `SelectHooksRequest` | `SelectHooksResponse` | analysis |
| GET | `/api/shorts/{short_id}` | No | — | `ShortResponse` | shorts |
| POST | `/api/shorts/{short_id}/download` | No | — | `ShortDownloadResponse` | shorts |
| POST | `/api/shorts/{short_id}/discard` | No | — | `{status: "discarded"}` | shorts |
| GET | `/api/tasks/{task_id}` | Yes | — | `TaskStatusResponse` | tasks |
| GET | `/api/user/balance` | Yes | — | `BalanceResponse` | user |
| GET | `/api/user/history` | Yes | `?page=1&per_page=20` | `{sessions, total, page, per_page}` | user |
| GET | `/api/user/profile` | Yes | — | `{id, email, currency, plan_tier, created_at}` | user |
| PATCH | `/api/user/currency` | Yes | `CurrencyUpdateRequest` | `{currency}` | user |
| GET | `/api/billing/plans` | Yes | — | `PlansResponse` | billing |
| POST | `/api/billing/checkout` | Yes | `?plan_tier=lite\|pro` | `{checkout_url, session_id}` | billing |
| POST | `/api/billing/payg` | Yes | `?minutes=100` | `{checkout_url, session_id}` | billing |
| POST | `/api/auth/sync` | Yes | `?email=<str>` | `{user_id, is_new, plan_tier}` | billing |
| POST | `/api/billing/v0-grant` | Yes | `?paid_minutes=0&payg_minutes=0` | `{granted, balance}` | billing |
| POST | `/api/webhooks/stripe` | No | Raw body | `{status: "ok"\|"ignored"}` | billing |
| POST | `/api/webhooks/razorpay` | No | Raw body | `{status: "ok"}` | billing |

---

## Analysis Router (`analysis.py`)

> **Architecture:** Thin HTTP adapter. All business logic lives in `AnalyzeService`. This module only extracts request data, calls `AnalyzeService`, and returns the response schema. All endpoints catch `HookCutError` and convert to `HTTPException`.

### Rate Limiting

All mutating analysis endpoints are rate-limited via `get_rate_limiter()`:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /api/analyze` | 10 requests | 15 min |
| `POST .../regenerate` | 5 requests | 15 min |
| `POST .../select-hooks` | 10 requests | 15 min |

### Centralized Exception Handling

`HookCutError` exceptions from services are caught and converted to `HTTPException`:
```python
except HookCutError as e:
    raise HTTPException(status_code=e.status_code, detail=e.detail)
```

Additionally, a global `hookcut_exception_handler` is registered in `main.py` for any uncaught `HookCutError`.

### POST `/api/validate-url`
- **Auth:** None
- **Request:** `VideoValidateRequest { youtube_url: str }`
- **Response:** `VideoValidateResponse { valid: bool, video_id?: str, title?: str, duration_seconds?: float, error?: str }`
- **Delegates to:** `AnalyzeService.validate_url(req)` (static method)
- **Errors:** None raised — failures encoded in response (`valid: false, error: "..."`)

### POST `/api/analyze`
- **Auth:** Required
- **Rate limit:** 10 / 15 min
- **Request:** `AnalyzeRequest { youtube_url: str, niche: str = "Generic", language: str = "English" }`
- **Validators:**
  - `niche` must be in `NICHES` dict (8 values)
  - `language` must be in `LANGUAGES` dict (13 values)
- **Response:** `AnalyzeResponse { session_id, task_id, video_title, video_duration_seconds: float, minutes_charged: float, is_watermarked: bool }`
- **Delegates to:** `AnalyzeService.start_analysis(db, user_id, youtube_url, niche, language)` (static method)
- **Service delegation chain** (inside AnalyzeService):
  1. `_ensure_user(db, user_id)` — auto-creates User + CreditBalance if missing
  2. `validate_youtube_url(req.youtube_url)` — URL parsing
  3. `VideoMetadataService().fetch(video_id)` — yt-dlp metadata
  4. `VideoMetadataService().validate_accessibility(metadata)` — live/private/age checks
  5. `CreditManager(db).check_balance(user_id, minutes_needed)` — balance check
  6. Creates `AnalysisSession` row (status="pending"), `db.flush()`
  7. `CreditManager(db).deduct(user_id, minutes_needed, session_id=session.id)` — credit deduction
  8. `db.commit()`
  9. `run_analysis.delay(session.id)` — Celery dispatch
  10. `track(user_id, "analysis_started", {...})` — analytics
- **Errors:**
  | Status | Condition | Detail |
  |--------|-----------|--------|
  | 400 | Invalid YouTube URL | `validate_youtube_url` error string |
  | 400 | Metadata fetch failed | "Could not fetch video metadata" |
  | 400 | Accessibility check failed | `validate_accessibility` error string |
  | 402 | Insufficient credits | "Insufficient minutes. Available: X, needed: Y. Please top up your account." |
  | 422 | Invalid niche | "Invalid niche. Must be one of: ..." |
  | 422 | Invalid language | "Invalid language. Must be one of: ..." |
- **Side effects:** Creates AnalysisSession, Transaction, dispatches Celery task
- **Critical invariant:** Session created → credits deducted → task dispatched (this order)

### GET `/api/sessions/{session_id}/hooks`
- **Auth:** None
- **Response:** `HooksListResponse { session_id, status, regeneration_count: int, hooks: HookResponse[] }`
- **HookResponse fields:** `{ id, rank: int, hook_text, start_time, end_time, hook_type, funnel_role, scores: HookScores, attention_score: float, platform_dynamics, viewer_psychology, improvement_suggestion: str = "", is_composite: bool, is_selected: bool }`
- **HookScores:** 7 named float fields, each clamped [0, 10]: `scroll_stop, curiosity_gap, stakes_intensity, emotional_voltage, standalone_clarity, thematic_focus, thought_completeness`
- **Delegates to:** `AnalyzeService.get_hooks(db, session_id)` (static method)
- **Errors:** 404 "Session not found"

### POST `/api/sessions/{session_id}/regenerate`
- **Auth:** Required
- **Rate limit:** 5 / 15 min
- **Response:** `RegenerateResponse { session_id, task_id, regeneration_count: int, fee_charged?: int, currency?: str }`
- **Validator:** `fee_charged` set → `currency` must also be set
- **Delegates to:** `AnalyzeService.regenerate_hooks(db, session_id)` (static method)
- **Logic:**
  - 1st regeneration: free (regeneration_count goes from 0→1)
  - 2nd+: charges fee via `get_regen_fee(video_duration_seconds, currency)`
  - Creates `Transaction(type="regeneration_fee")` for paid regens
  - Creates `LearningLog(event_type="regeneration_triggered")`
  - Resets session status to "pending"
  - Dispatches new `run_analysis.delay(session.id)`
- **Errors:**
  | Status | Condition | Detail |
  |--------|-----------|--------|
  | 404 | Session not found | "Session not found" |
  | 400 | Status not in ("hooks_ready", "completed") | "Session is not in a state that allows regeneration" |

### POST `/api/sessions/{session_id}/select-hooks`
- **Auth:** Required
- **Rate limit:** 10 / 15 min
- **Request:** `SelectHooksRequest { hook_ids: list[str], caption_style: str = "clean", time_overrides: dict[str, TimeOverride] = {} }`
- **TimeOverride:** `{ start_seconds: float, end_seconds: float }`
- **Validators:** 1-3 hooks, no duplicates, `caption_style` must be in `VALID_CAPTION_STYLES` (clean, bold, neon, minimal), time overrides validated for ±10s bounds and min 5s duration
- **Response:** `SelectHooksResponse { short_ids: list[str], task_ids: list[str] }`
- **Delegates to:** `AnalyzeService.select_hooks(db, session_id, hook_ids, caption_style, time_overrides)` (static method)
- **Logic:**
  1. Validates all `hook_ids` belong to this session
  2. Validates `caption_style` against `VALID_CAPTION_STYLES` from `ffmpeg_commands.py`
  3. Validates `time_overrides` (±10s from original, min 5s duration)
  4. Marks hooks as `is_selected=True/False`
  5. Creates `LearningLog` for each hook (selected or not) with `hook_type` in metadata
  6. Creates `Short` records (status="queued") with `caption_style`, `start_seconds_override`, `end_seconds_override`
  7. Dispatches `generate_short.delay(short.id)` for each
  8. Sets session status to "generating_shorts"
- **Errors:**
  | Status | Condition | Detail |
  |--------|-----------|--------|
  | 404 | Session not found | "Session not found" |
  | 400 | Status ≠ "hooks_ready" | "Hooks are not ready for selection" |
  | 400 | Hook ID not in session | "Hook {hook_id} not found in this session" |
  | 400 | Time override for unknown hook | "Time override for unknown hook {hook_id}" |
  | 400 | Trimmed hook < 5s | "Trimmed hook must be at least 5 seconds" |
  | 400 | Start > 10s before original | "Start time cannot be more than 10s before original" |
  | 400 | End > 10s after original | "End time cannot be more than 10s after original" |
  | 422 | <1 or >3 hooks | "Must select between 1 and 3 hooks" |
  | 422 | Duplicate hook IDs | "hook_ids must not contain duplicates" |
  | 422 | Invalid caption style | "Invalid caption style. Must be one of: ..." |

---

## Shorts Router (`shorts.py`)

### GET `/api/shorts/{short_id}`
- **Auth:** None
- **Response:** `ShortResponse { id, hook_id, status, is_watermarked: bool, title?, cleaned_captions?, duration_seconds?: float, file_size_bytes?: int, download_url?, download_url_expires_at?: datetime, thumbnail_url?, error_message? }`
- **Logic:** If `thumbnail_file_key` exists, generates presigned URL via `StorageService().get_download_url(key, expires_in=DOWNLOAD_URL_EXPIRES_SECONDS)`
- **Errors:** 404 "Short not found"

### POST `/api/shorts/{short_id}/download`
- **Auth:** None
- **Response:** `ShortDownloadResponse { download_url: str, expires_at: datetime }`
- **Logic:**
  1. Generates presigned URL via `StorageService().get_download_url(video_file_key, expires_in=DOWNLOAD_URL_EXPIRES_SECONDS)`
  2. Updates `short.download_url` and `short.download_url_expires_at`
  3. Creates `LearningLog(event_type="short_downloaded")` — uses `short.session` relationship (no separate DB query)
- **Errors:**
  | Status | Condition | Detail |
  |--------|-----------|--------|
  | 404 | Short not found | "Short not found" |
  | 400 | Status ≠ "ready" | "Short is not ready (status: {status})" |
  | 400 | No video file | "No video file available" |

### POST `/api/shorts/{short_id}/discard`
- **Auth:** None
- **Response:** `{ status: "discarded" }` (inline dict, no Pydantic model)
- **Logic:** Creates `LearningLog(event_type="short_discarded")`
- **Errors:** 404 "Short not found"

---

## Tasks Router (`tasks.py`)

### GET `/api/tasks/{task_id}`
- **Auth:** Required
- **Response:** `TaskStatusResponse { task_id, status: str, progress?: int, stage?: str, result?: dict, error?: str }`
- **Status values:** `"PENDING"`, `"STARTED"`, `"PROGRESS"`, `"SUCCESS"`, `"FAILURE"`
- **Logic:** Reads from Celery `AsyncResult(task_id)` directly
- **Critical note:** `run_analysis` task catches all exceptions internally and always returns SUCCESS to Celery. Check `result.error` field for actual failures.

**Frontend polling behavior:**
| Celery Status | `progress` | `stage` | `result` | `error` |
|---------------|-----------|---------|----------|---------|
| PENDING | null | null | null | null |
| STARTED | null | null | null | null |
| PROGRESS | int (0-100) | string | null | null |
| SUCCESS | 100 | null | dict | null |
| FAILURE | null | null | null | string |

---

## User Router (`user.py`)

### GET `/api/user/balance`
- **Auth:** Required
- **Response:** `BalanceResponse { paid_minutes_remaining: float, paid_minutes_total: float, free_minutes_remaining: float, free_minutes_total: float, payg_minutes_remaining: float, total_available: float }`
- **Delegates to:** `CreditManager(db).get_balance(user_id)`

### GET `/api/user/history`
- **Auth:** Required
- **Query params:** `page: int = 1`, `per_page: int = 20`
- **Response:** Inline dict (no Pydantic `response_model`):
  ```json
  {
    "sessions": [
      {
        "id": "str", "video_title": "str", "video_id": "str",
        "niche": "str", "language": "str", "status": "str",
        "minutes_charged": "float", "is_watermarked": "bool",
        "regeneration_count": "int", "created_at": "str (ISO 8601)"
      }
    ],
    "total": "int",
    "page": "int",
    "per_page": "int"
  }
  ```
- **Note:** `created_at` is manually `.isoformat()`'d. No formal schema — drift risk.

### GET `/api/user/profile`
- **Auth:** Required
- **Response:** Inline dict: `{ id, email, currency, plan_tier, role, created_at (ISO 8601) }`
- **Errors:** 404 "User not found"

### PATCH `/api/user/currency`
- **Auth:** Required
- **Request body:** `CurrencyUpdateRequest { currency: str }` (JSON body, not query param)
- **Response:** `{ currency: str }`
- **Errors:**
  | Status | Condition | Detail |
  |--------|-----------|--------|
  | 400 | Currency ∉ ("INR", "USD") | "Currency must be INR or USD" |
  | 404 | User not found | "User not found" |

---

## Billing Router (`billing.py`)

### GET `/api/billing/plans`
- **Auth:** Required
- **Response:** `PlansResponse { current_tier: str, currency: Literal["USD","INR"], plans: PlanInfo[] }`
- **PlanInfo:** `{ tier: Literal["free","lite","pro"], price_display: str, watermark_free_minutes: int, currency: Literal["USD","INR"] }`
- **Plan data:** Hardcoded in `PLANS_INR` and `PLANS_USD` constants

### POST `/api/billing/checkout`
- **Auth:** Required
- **Query param:** `plan_tier: str`
- **Response:** `{ checkout_url: str, session_id: str }` (inline dict)
- **Delegates to:** `PaymentService().create_subscription_checkout(user_id, email, plan_tier, currency)`
- **Errors:**
  | Status | Condition | Detail |
  |--------|-----------|--------|
  | 501 | V0 mode | "Payment processing not available in V0 mode..." |
  | 400 | plan_tier ∉ ("lite", "pro") | "Invalid plan tier. Must be 'lite' or 'pro'" |
  | 404 | User not found | "User not found" |
  | 500 | Checkout creation fails | "Failed to create checkout session" |

### POST `/api/billing/payg`
- **Auth:** Required
- **Query param:** `minutes: int = 100`
- **Response:** `{ checkout_url: str, session_id: str }` (inline dict)
- **Delegates to:** `PaymentService().create_payg_checkout(user_id, email, minutes, currency)`
- **Errors:**
  | Status | Condition | Detail |
  |--------|-----------|--------|
  | 501 | V0 mode | Same as checkout |
  | 400 | minutes < 100 or not multiple of 100 | "Minutes must be a multiple of 100 (minimum 100)" |
  | 404 | User not found | "User not found" |
  | 500 | Checkout creation fails | "Failed to create checkout session" |

### POST `/api/auth/sync`
- **Auth:** Required
- **Query param:** `email: str`
- **Response:** `{ user_id: str, is_new: bool, plan_tier: str }`
- **Logic:** Creates User + CreditBalance if not exists. Fires `identify` and `track("user_signed_up")` for new users.

### POST `/api/billing/v0-grant`
- **Auth:** Required
- **Query params:** `paid_minutes: float = 0`, `payg_minutes: float = 0`
- **Response:** `{ granted: {paid_minutes, payg_minutes}, balance: {paid, payg, free, total} }`
- **Errors:** 403 "Only available in V0 mode"

### POST `/api/webhooks/stripe`
- **Auth:** None (signature verification in router, business logic delegated to `WebhookService`)
- **Events handled:**
  - `checkout.session.completed` → `WebhookService.handle_stripe_checkout_completed(db, data)` — PAYG credit grant or subscription activation
  - `invoice.paid` → `WebhookService.handle_stripe_invoice_paid(db, data)` — Subscription renewal credit grant
  - `customer.subscription.deleted` → `WebhookService.handle_stripe_subscription_deleted(db, data)` — Cancel subscription, revert to free
- **Errors:** 400 "Invalid webhook signature"

### POST `/api/webhooks/razorpay`
- **Auth:** None (signature verification in router, business logic delegated to `WebhookService`)
- **Events handled:**
  - `subscription.charged` → `WebhookService.handle_razorpay_subscription_charged(db, entity, notes)` — Subscription activation
  - `order.paid` (purchase_type=payg) → `WebhookService.handle_razorpay_order_paid(db, entity, notes)` — PAYG credit grant
  - `subscription.cancelled` → `WebhookService.handle_razorpay_subscription_cancelled(db, entity, notes)` — Cancel subscription
- **Errors:** 400 "Invalid webhook signature"

---

## State Machines (Reference)

### Session Status
```
pending → fetching_transcript → analyzing → hooks_ready → generating_shorts → completed
                                          ↘ failed
hooks_ready → pending (on regenerate)
```

### Short Status
```
queued → processing → ready
                   ↘ failed
ready → expired (via cleanup task)
```

### Celery Task Status (what frontend sees)
```
PENDING → STARTED → PROGRESS → SUCCESS
                             ↘ FAILURE
```
**Important:** `run_analysis` always returns SUCCESS to Celery. Check `result.error` for actual failures.

---

## LearningLog Event Types

| Event Type | Trigger Endpoint | Metadata |
|------------|-----------------|----------|
| `regeneration_triggered` | `POST .../regenerate` | `{regeneration_count, previous_hook_ids}` |
| `hook_selected` | `POST .../select-hooks` | `{selection_order, hook_type}` |
| `hook_not_selected` | `POST .../select-hooks` | `{hook_type}` |
| `short_downloaded` | `POST .../download` | `{is_watermarked}` |
| `short_discarded` | `POST .../discard` | — |

---

## Shared Constants (imported from `app/tasks/celery_app`)

| Constant | Value | Used by |
|---|---|---|
| `DOWNLOAD_URL_EXPIRES_SECONDS` | `3600` | `shorts.py` — presigned URL TTL |

---

## Admin Router (`admin.py`)

**Prefix:** `/admin`
**Auth:** All endpoints require `Depends(get_admin_user)` — returns 403 for non-admin users.

### Endpoints (21 routes)

| Method | Path | Request | Response | Purpose |
|--------|------|---------|----------|---------|
| GET | `/admin/dashboard` | — | `AdminDashboardResponse` | Stats + recent sessions |
| GET | `/admin/users` | `?page=1&per_page=20` | `AdminUserListResponse` | Paginated user list |
| PATCH | `/admin/users/{user_id}/role` | `RoleUpdateRequest` | `AdminUserResponse` | Change user role |
| GET | `/admin/sessions` | `?page=1&per_page=20&status=` | `AdminSessionListResponse` | All sessions (filterable) |
| GET | `/admin/sessions/{session_id}` | — | `AdminSessionDetailResponse` | Session detail + hooks + shorts |
| GET | `/admin/audit-logs` | `?page=1&per_page=20&action=` | `AuditLogListResponse` | Paginated audit log |
| GET | `/admin/audit-logs/export` | `?start_date=&end_date=` | `list[dict]` | Export audit logs as JSON |
| GET | `/admin/rules` | — | `PromptRuleListResponse` | List active rules (latest version per key) |
| POST | `/admin/rules` | `PromptRuleCreateRequest` | `PromptRuleResponse` | Create custom rule |
| POST | `/admin/rules/preview` | `PromptPreviewRequest` | `PromptPreviewResponse` | Preview assembled prompt |
| POST | `/admin/rules/seed` | — | `PromptRuleListResponse` | Bootstrap 17 base rules from hardcoded prompt |
| GET | `/admin/rules/{rule_key}/history` | — | `PromptRuleHistoryResponse` | Version history for a rule key |
| PATCH | `/admin/rules/{rule_id}` | `PromptRuleUpdateRequest` | `PromptRuleResponse` | Update rule (creates new version) |
| POST | `/admin/rules/{rule_id}/revert/{version_id}` | — | `PromptRuleResponse` | Revert to a specific version |
| DELETE | `/admin/rules/{rule_id}` | — | `{"status": "deleted"}` | Delete custom rule (deactivate) |
| GET | `/admin/providers` | — | `ProviderListResponse` | List provider configs |
| PATCH | `/admin/providers/{provider_name}` | `ProviderUpdateRequest` | `ProviderConfigResponse` | Update provider settings |
| POST | `/admin/providers/{provider_name}/set-primary` | — | `ProviderConfigResponse` | Set as primary provider |
| POST | `/admin/providers/{provider_name}/set-key` | `SetApiKeyRequest` | `ProviderConfigResponse` | Update provider API key |
| POST | `/admin/narm/analyze` | `NarmAnalyzeRequest` | `NarmInsightsListResponse` | Trigger NARM analysis |
| GET | `/admin/narm/insights` | — | `NarmInsightsListResponse` | Get latest NARM insights |

**Route ordering note:** `/rules/preview` and `/rules/seed` are defined BEFORE `/rules/{rule_key}/history` to avoid path parameter conflicts.

### Admin Schemas (23 models in `schemas/admin.py`)

**Response models** (with `from_attributes=True`):
AdminDashboardResponse, AdminSessionSummary, AdminUserResponse, AdminUserListResponse, AdminSessionListResponse, AdminSessionDetailResponse, AuditLogResponse, AuditLogListResponse, PromptRuleResponse, PromptRuleListResponse, PromptRuleHistoryResponse, PromptPreviewResponse, ProviderConfigResponse, ProviderListResponse, NarmInsightResponse, NarmInsightsListResponse

**Request models:**
RoleUpdateRequest (role: Literal["user", "admin"]), PromptRuleCreateRequest, PromptRuleUpdateRequest, PromptPreviewRequest, ProviderUpdateRequest, SetApiKeyRequest, NarmAnalyzeRequest
