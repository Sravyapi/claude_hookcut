# HookCut Frontend/Backend Type Audit

## Summary

| Metric | Count |
|--------|-------|
| **Matched** (TS interface has a backend counterpart) | **12** |
| **Field-level mismatches** | **6** |
| **Frontend-only types** (no backend schema needed) | **3** |
| **Backend models missing from frontend** | **7** |
| **Duplicated constants** | **1** |

---

## 1. Complete Mapping Table

| # | TypeScript Interface | Pydantic / Backend Model | Backend File | Field-Level Mismatches |
|---|---------------------|--------------------------|--------------|----------------------|
| 1 | `VideoValidation` | `VideoValidateResponse` | `schemas/analysis.py` | Name difference only. Fields match. Backend `duration_seconds` is `Optional[float]`, TS uses `number \| null` — equivalent. |
| 2 | `VideoMeta` | `VideoMetadata` (dataclass) | `services/video_metadata.py` | Partial match. TS has 3 fields, backend has 6 (adds `is_live`, `age_limit`, `availability`). TS is intentional subset. |
| 3 | `AnalyzeResponse` | `AnalyzeResponse` | `schemas/analysis.py` | Backend `video_duration_seconds: float`, `minutes_charged: float`. TS uses `number` — compatible. |
| 4 | `TaskStatus` | `TaskStatusResponse` | `schemas/tasks.py` | Name difference. `progress`: Backend `Optional[int]`, TS `number \| null` — compatible. `result`: Backend `Optional[dict]`, TS `Record<string, unknown> \| null` — equivalent. TS status field uses string literal union (stricter). |
| 5 | `Hook` | `HookResponse` | `schemas/hooks.py` | **HIGH: TS missing `is_selected: bool` field.** `scores`: Backend typed `HookScores` (7 named fields), TS `Record<string, number>` (untyped). |
| 6 | `HooksResponse` | `HooksListResponse` | `schemas/hooks.py` | Name difference. Structure matches (but inherits `Hook.is_selected` omission). |
| 7 | `SelectHooksResponse` | `SelectHooksResponse` | `schemas/analysis.py` | **Exact match.** |
| 8 | `RegenerateResponse` | `RegenerateResponse` | `schemas/analysis.py` | `fee_charged`: Backend `Optional[int]`, TS `number \| null`. Functionally compatible. |
| 9 | `Short` | `ShortResponse` | `schemas/shorts.py` | Name difference. `download_url_expires_at`: Backend `Optional[datetime]`, TS `string \| null` (JSON serialization). `file_size_bytes`: Backend `Optional[int]`, TS `number \| null`. Compatible. |
| 10 | `DownloadResponse` | `ShortDownloadResponse` | `schemas/shorts.py` | Name difference. `expires_at`: Backend `datetime`, TS `string`. JSON serialization compatible. |
| 11 | `CreditBalance` | `BalanceResponse` | `schemas/billing.py` | Name difference. All 6 backend fields are `float`, TS uses `number`. Equivalent. |
| 12 | `UserProfile` | `UserOut` (partial) | `schemas/user.py` + `routers/user.py` | Backend `UserOut` has `updated_at`, `role` — TS omits both. The actual `/user/profile` endpoint returns a subset that matches TS exactly. |
| 13 | `SessionSummary` | Inline dict in `get_history()` | `routers/user.py:51-63` | **No Pydantic model.** Endpoint builds dict inline. Fields match TS. |
| 14 | `HistoryResponse` | Inline dict in `get_history()` | `routers/user.py:50-68` | **No Pydantic model.** Returns raw dict. Fields match TS. |
| 15 | `PlansResponse` | `PlansResponse` | `schemas/billing.py` | **Exact match.** Backend `currency` is `Literal["USD", "INR"]`, TS is `string` (looser). |
| 16 | `PlanInfo` | `PlanInfo` | `schemas/billing.py` | Backend `tier` is `Literal["free", "lite", "pro"]`, `currency` is `Literal["USD", "INR"]`. TS types both as plain `string`. |
| 17 | `CheckoutResponse` | `CheckoutSession` (dataclass) | `services/payment_service.py` + `routers/billing.py` | Partial. Endpoint returns `{checkout_url, session_id}` — matches TS. Backend dataclass has extra `provider` field not exposed. |

---

## 2. Backend Models With NO TypeScript Equivalent

| # | Backend Model | File | Action |
|---|--------------|------|--------|
| 1 | `AnalyzeRequest` | `schemas/analysis.py` | Low priority — request body sent inline. |
| 2 | `VideoValidateRequest` | `schemas/analysis.py` | Low priority — request body sent inline. |
| 3 | `SelectHooksRequest` | `schemas/analysis.py` | Low priority — `{hook_ids: string[]}` sent inline. |
| 4 | `HookScores` | `schemas/hooks.py` | **Should have TS equivalent.** Frontend `score-bar.tsx` hardcodes the same 7 keys — fragile. |
| 5 | `UserBase` / `UserCreate` / `UserUpdate` | `schemas/user.py` | Internal/admin. Not needed. |
| 6 | `UserOut` | `schemas/user.py` | Low priority unless profile shows `role`/`updated_at`. |
| 7 | `LLMResponse` (dataclass) | `llm/provider.py` | Internal. Never surfaces to frontend. |

---

## 3. Frontend-Only Types

| # | TypeScript Type | Purpose |
|---|----------------|---------|
| 1 | `Step` | UI wizard state machine. Purely frontend. |
| 2 | `POLL_CONFIG` | Frontend polling backoff config. |
| 3 | `DEFAULT_LANGUAGE` / `DEFAULT_NICHE` | Default form values. Backend has corresponding defaults but not shared. |

---

## 4. Duplicated Constants

| Constant | Frontend | Backend | Risk |
|----------|----------|---------|------|
| `SHORT_STATUS` values | `types.ts:112-119` (const object) | `models/session.py:91` (comment only) | **Fragile.** Backend change silently breaks frontend. |
| Score dimension keys | `score-bar.tsx:8-14` (hardcoded map) | `schemas/hooks.py` `HookScores` fields | **Fragile.** No shared contract. |
| Default niche `"Generic"` | `types.ts:110` | `schemas/analysis.py:8` | Duplicated. |
| Default language `"English"` | `types.ts:109` | `schemas/analysis.py:9` | Duplicated. |

---

## 5. Critical Fixes Required

| Severity | Issue | Fix |
|----------|-------|-----|
| **HIGH** | `Hook` missing `is_selected` | Add `is_selected: boolean` to `Hook` interface |
| **MEDIUM** | `Hook.scores` untyped | Create typed `HookScores` interface with 7 named fields |
| **MEDIUM** | `PlanInfo.tier` and `currency` too loose | Use `"free" \| "lite" \| "pro"` and `"USD" \| "INR"` |
| **LOW** | `HistoryResponse` / `SessionSummary` have no Pydantic model | Create response schemas for OpenAPI docs |
| **LOW** | `SHORT_STATUS` duplicated without shared contract | Extract to backend constant (not just comment) |

---

## 6. Codegen Readiness

When OpenAPI → TypeScript codegen is wired up, these 12 matched interfaces will be auto-generated. The 3 frontend-only types (`Step`, `POLL_CONFIG`, defaults) will remain hand-maintained. The codegen will expose the `is_selected` field and typed `HookScores` automatically, fixing the two highest-severity issues.

**Pre-codegen checklist:**
- [ ] Fix `HistoryResponse` / `SessionSummary` — add Pydantic `response_model` to the endpoint so OpenAPI spec includes them
- [ ] Extract `SHORT_STATUS` to a backend constant/enum
- [ ] Verify all 12 matched schemas generate correct TS (compare field-by-field after first codegen run)
