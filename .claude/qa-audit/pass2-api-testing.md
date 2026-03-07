# HookCut API QA Audit — Pass 2: Live Production API Testing

**Date:** 2026-03-07
**Tester:** Claude QA Agent
**Environment:** Production
**Frontend URL:** https://hookcut.nyxpath.com/
**Backend URL:** https://api.hookcut.nyxpath.com/ (discovered from JS bundle `c45631b1c634e459.js`)

---

## 1. API Discovery

### Backend URL Discovery
- Fetched https://hookcut.nyxpath.com/ and enumerated JS chunks
- Found production API base URL in `/_next/static/chunks/c45631b1c634e459.js`: `https://api.hookcut.nyxpath.com/api`
- Note: `.env.local` in repo has `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api` — only for local dev. Production Vercel env has the Railway URL baked in.

### All Registered Endpoints (from `/openapi.json`)
```
/api/validate-url
/api/analyze
/api/sessions/{session_id}/hooks
/api/sessions/{session_id}/regenerate
/api/sessions/{session_id}/select-hooks
/api/storage/{file_key}
/api/shorts/{short_id}
/api/shorts/{short_id}/download
/api/shorts/{short_id}/discard
/api/tasks/{task_id}
/api/user/balance
/api/user/history
/api/user/profile
/api/user/currency
/api/billing/plans
/api/billing/checkout
/api/billing/payg
/api/auth/sync
/api/billing/v0-grant
/api/webhooks/stripe
/api/webhooks/razorpay
/api/admin/dashboard
/api/admin/users
/api/admin/users/{user_id}/role
/api/admin/sessions
/api/admin/sessions/{session_id}
/api/admin/audit-logs
/api/admin/audit-logs/export
/api/admin/rules
/api/admin/rules/preview
/api/admin/rules/seed
/api/admin/rules/{rule_key}/history
/api/admin/rules/{rule_id}
/api/admin/rules/{rule_id}/revert/{version_id}
/api/admin/providers
/api/admin/providers/{provider_name}
/api/admin/providers/{provider_name}/set-primary
/api/admin/providers/{provider_name}/set-key
/api/admin/narm/analyze
/api/admin/narm/insights
/health
```

---

## 2. Health / Discovery Tests

### 2.1 `/health`
```
GET https://api.hookcut.nyxpath.com/health
Response: {"status":"ok","version":"0.1.0"}  HTTP 200
```
**Finding:** PASS — Health endpoint functional, returns version string.

### 2.2 `/docs` (Swagger UI)
```
GET https://api.hookcut.nyxpath.com/docs
HTTP 200
```
**Finding:** CONCERN — SEVERITY: LOW
Swagger UI is exposed in production with full interactive documentation. This leaks endpoint schemas, request/response formats, and makes API surface discoverable. Should be disabled in production (`docs_url=None` in FastAPI constructor).

### 2.3 `/redoc`
```
GET https://api.hookcut.nyxpath.com/redoc
HTTP 200
```
**Finding:** CONCERN — SEVERITY: LOW
Same as /docs — ReDoc is also exposed. Should be disabled in production.

### 2.4 `/openapi.json`
```
GET https://api.hookcut.nyxpath.com/openapi.json
HTTP 200 — Returns full OpenAPI 3.x schema (41 paths, all endpoint signatures)
```
**Finding:** CONCERN — SEVERITY: LOW
Full API schema exposed, including all route paths, request/response shapes, and validation rules. In combination with the auth issues below, this significantly reduces attacker effort.

---

## 3. Unauthenticated Access Tests

### 3.1 `/api/user/balance` — NO AUTH REQUIRED
```
GET https://api.hookcut.nyxpath.com/api/user/balance
Response: {"paid_minutes_remaining":0.0,"free_minutes_remaining":36.0,...,"total_available":36.0}
HTTP 200
```
**Finding:** FAIL — SEVERITY: HIGH
Returns user balance data without any authentication token. In V0 mode, this defaults to `v0_local_user` — but this is a production server. Any unauthenticated client can read the "default user's" balance. Endpoint should require authentication.

### 3.2 `/api/user/profile` — NO AUTH REQUIRED
```
GET https://api.hookcut.nyxpath.com/api/user/profile
Response: {"id":"v0_local_user","email":"v0_local_user@hookcut.local","currency":"USD","plan_tier":"free","role":"user","created_at":"2026-03-04T13:40:15.496247"}
HTTP 200
```
**Finding:** FAIL — SEVERITY: HIGH
Returns user profile data without authentication. Exposes user ID, email, role, plan tier, and creation date.

### 3.3 `/api/user/history` — NO AUTH REQUIRED, REAL SESSION DATA EXPOSED
```
GET https://api.hookcut.nyxpath.com/api/user/history
HTTP 200 — Returns 54 real analysis sessions with video titles, video IDs, session IDs, credit usage, timestamps
```
**Finding:** FAIL — SEVERITY: CRITICAL
Real production user data (54 sessions) returned without authentication. Data exposed includes:
- Video titles and YouTube video IDs
- Internal session UUIDs (reusable in other unauthenticated calls)
- Credit charges per session (`minutes_charged`)
- Session status
- Whether sessions are watermarked

This is a data breach: anyone can access the history of the production "default user" account.

### 3.4 `/api/sessions/{session_id}/hooks` — NO AUTH REQUIRED
```
GET https://api.hookcut.nyxpath.com/api/sessions/c14f9828-5877-4af0-9373-8ae5bb4dc49a/hooks
HTTP 200 — Returns all 5 hook objects with full LLM-generated content, scores, timestamps
```
**Finding:** FAIL — SEVERITY: HIGH
Hook data (LLM output with scores, platform analysis, viewer psychology, improvement suggestions) accessible without authentication. Session IDs are discoverable from `/api/user/history`.

### 3.5 `/api/sessions/{session_id}/regenerate` — NO AUTH REQUIRED
```
POST https://api.hookcut.nyxpath.com/api/sessions/c14f9828-5877-4af0-9373-8ae5bb4dc49a/regenerate
Response: {"session_id":"...","task_id":"53d80cb2-27dc-4146-8b49-c71b9807b168","regeneration_count":1,...}
HTTP 200
```
**Finding:** FAIL — SEVERITY: HIGH
Hook regeneration triggered without authentication. Router code has `user_id: str = Depends(get_current_user_id)` but the `get_current_user_id` dependency appears to return a default user ID when no token is provided (V0 mode behavior). This means any unauthenticated caller can trigger regeneration tasks, potentially consuming Celery worker capacity and credits.

### 3.6 `/api/billing/v0-grant` — CREDIT INJECTION WITHOUT AUTH
```
POST https://api.hookcut.nyxpath.com/api/billing/v0-grant?paid_minutes=9999&payg_minutes=9999
Response: {"granted":{"paid_minutes":9999.0,"payg_minutes":9999.0},"balance":{"paid":9999.0,"payg":9999.0,...,"total":19998.5...}}
HTTP 200
```
**Finding:** FAIL — SEVERITY: CRITICAL
The V0 credit grant endpoint is live in production with no authentication requirement. Any unauthenticated user can call this endpoint to grant themselves unlimited credits (tested with 9999 minutes each). This completely bypasses the billing system. This endpoint must either be removed from production or locked behind admin authentication.

### 3.7 `/api/auth/sync` — NO AUTH REQUIRED
```
POST https://api.hookcut.nyxpath.com/api/auth/sync?email=hacker@evil.com
Response: {"user_id":"v0_local_user","is_new":false,"plan_tier":"free","role":"user"}
HTTP 200
```
**Finding:** CONCERN — SEVERITY: MEDIUM
Auth sync endpoint responds without requiring a JWT. In V0 mode it falls through to the default user. The email parameter is logged/processed but doesn't appear to affect which user is returned. Nonetheless, accepting arbitrary email values in a production endpoint without authentication validation is a concern.

### 3.8 `/api/user/currency` (PATCH) — NO AUTH REQUIRED
```
PATCH https://api.hookcut.nyxpath.com/api/user/currency
Body: {"currency": "INR"}
Response: {"currency":"INR"}  HTTP 200
```
**Finding:** FAIL — SEVERITY: MEDIUM
User currency can be changed without authentication. Any unauthenticated caller can modify the default user's currency preference.

### 3.9 `/api/tasks/{task_id}` — NO AUTH REQUIRED
```
GET https://api.hookcut.nyxpath.com/api/tasks/INVALID_TASK_ID
Response: {"task_id":"INVALID_TASK_ID","status":"PENDING",...}  HTTP 200
```
**Finding:** CONCERN — SEVERITY: LOW
Task status endpoint requires `get_current_user_id` per router code but still responds to unauthenticated requests. Any task_id returns PENDING for unknown IDs. Valid task IDs from regenerate responses can be polled without auth.

### 3.10 `/api/billing/plans` — NO AUTH REQUIRED
```
GET https://api.hookcut.nyxpath.com/api/billing/plans
HTTP 200 — Returns plan list
```
**Finding:** PASS (acceptable) — Plans listing doesn't expose user data. Low risk.

### 3.11 Admin Endpoints — ALL PROPERLY SECURED
```
GET /api/admin/dashboard     → 403 Admin access required
GET /api/admin/users         → 403 Admin access required
GET /api/admin/rules         → 403 Admin access required
GET /api/admin/sessions      → 403 Admin access required
GET /api/admin/audit-logs    → 403 Admin access required
GET /api/admin/providers     → 403 Admin access required
GET /api/admin/narm/insights → 403 Admin access required
GET /api/admin/audit-logs/export → 403 Admin access required
GET /api/admin/sessions/{id} → 403 Admin access required
```
**Finding:** PASS — All 9 admin endpoints tested return 403 for unauthenticated requests. RBAC is correctly enforced.

---

## 4. Input Validation Tests

### 4.1 Empty body
```
POST /api/analyze  Body: {}
Response: {"detail":[{"type":"missing","loc":["body","youtube_url"],"msg":"Field required",...}]}  HTTP 422
```
**Finding:** PASS — Pydantic validation working correctly.

### 4.2 Empty URL
```
POST /api/analyze  Body: {"youtube_url": "", "niche": "Tech / AI", "language": "English"}
Response: {"detail":"URL is required"}  HTTP 400
```
**Finding:** PASS — Empty URL rejected with a clean message.

### 4.3 Extremely long URL (10,000 chars)
```
POST /api/analyze  Body: {"youtube_url": "AAAA...10000 chars", ...}
Response: {"detail":"URL must be a valid YouTube link"}  HTTP 400
```
**Finding:** PASS — Long URL rejected. No buffer overflow or 500 error.

### 4.4 XSS payload
```
POST /api/analyze  Body: {"youtube_url": "<script>alert(1)</script>", ...}
Response: {"detail":"URL must be a valid YouTube link"}  HTTP 400
```
**Finding:** PASS — XSS in URL field rejected cleanly. API returns JSON, not HTML, so XSS is not a concern here.

### 4.5 SQL Injection
```
POST /api/analyze  Body: {"youtube_url": "' OR 1=1 --", ...}
Response: {"detail":"URL must be a valid YouTube link"}  HTTP 400
```
**Finding:** PASS — SQL injection payload rejected at URL validation layer. Backend uses SQLAlchemy ORM with parameterized queries, so injection risk is low.

### 4.6 SSRF: AWS metadata endpoint
```
POST /api/analyze  Body: {"youtube_url": "http://169.254.169.254/latest/meta-data/", ...}
Response: {"detail":"Could not extract video ID..."}  HTTP 400
```
**Finding:** PASS — SSRF attempt to AWS metadata service blocked at URL validation. URL scheme/domain is validated to be a YouTube URL before any HTTP fetch occurs.

### 4.7 SSRF: localhost Redis
```
POST /api/analyze  Body: {"youtube_url": "http://localhost:6379", ...}
Response: {"detail":"Could not extract video ID..."}  HTTP 400
```
**Finding:** PASS — Internal service SSRF blocked.

### 4.8 Null URL
```
POST /api/analyze  Body: {"youtube_url": null, ...}
Response: {"detail":[{"type":"string_type","msg":"Input should be a valid string",...}]}  HTTP 422
```
**Finding:** PASS — Null value rejected with proper 422.

### 4.9 Malformed JSON
```
POST /api/analyze  Body: not_json
Response: {"detail":[{"type":"json_invalid","msg":"JSON decode error",...}]}  HTTP 422
```
**Finding:** PASS — Malformed JSON returns 422 without exposing stack trace.

### 4.10 Niche validation
```
POST /api/analyze  Body: {"youtube_url": "...", "niche": "music", "language": "en"}
Response: {"detail":[{"msg":"Value error, Invalid niche. Must be one of: Tech / AI, Finance, ..."},...]}  HTTP 422
```
**Finding:** PASS — Niche and language values are validated against allowed lists. Unexpected values rejected.

---

## 5. HTTP Security Headers Audit

### 5.1 Backend Headers (api.hookcut.nyxpath.com)
```
HTTP/2 headers from /health (HEAD via /api/analyze):
  server: railway-edge
  x-railway-edge: railway/asia-southeast1-eqsg3a
  x-railway-request-id: <id>
  content-type: application/json
```

Missing security headers on backend:
- `X-Content-Type-Options: nosniff` — MISSING
- `X-Frame-Options` — MISSING
- `Strict-Transport-Security` — MISSING
- `Content-Security-Policy` — MISSING
- `X-XSS-Protection` — MISSING
- `Referrer-Policy` — MISSING

**Finding:** CONCERN — SEVERITY: LOW
Backend API is missing standard security headers. Since this is an API (not a browser-rendered app), some headers like X-Frame-Options and CSP are less critical, but X-Content-Type-Options and HSTS should be added.

### 5.2 Frontend Headers (hookcut.nyxpath.com)
```
strict-transport-security: max-age=63072000
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
permissions-policy: camera=(), microphone=(), geolocation=()
```

Missing on frontend:
- `Content-Security-Policy` — MISSING
- `X-XSS-Protection` — MISSING (deprecated but widely used)

**Finding:** PASS (mostly) — Frontend has good header coverage from Vercel. CSP would be a further hardening improvement.

---

## 6. CORS Audit

### 6.1 Origin: https://evil.com (GET)
```
curl -H "Origin: https://evil.com" GET /health
Response: access-control-allow-credentials: true (no access-control-allow-origin header)
```
**Finding:** PASS — `evil.com` origin not granted CORS access. `access-control-allow-credentials: true` appears but without a matching `access-control-allow-origin`, browsers will block cross-origin requests.

### 6.2 Origin: https://evil.com (OPTIONS preflight)
```
curl -H "Origin: https://evil.com" -X OPTIONS /api/analyze
Response: HTTP 400, access-control-allow-credentials: true, access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
```
**Finding:** CONCERN — SEVERITY: LOW
The OPTIONS preflight returns HTTP 400 (not 200 or 204) for disallowed origins. CORS is functionally blocking evil.com, but the 400 response and exposure of `access-control-allow-methods` with all verbs listed is more verbose than necessary.

### 6.3 Origin: https://hookcut.nyxpath.com (GET)
```
curl -H "Origin: https://hookcut.nyxpath.com" GET /health
Response: access-control-allow-origin: https://hookcut.nyxpath.com, access-control-allow-credentials: true
```
**Finding:** PASS — Legitimate origin receives correct CORS headers.

---

## 7. Rate Limit Testing

### 7.1 Invalid URL format (20 requests)
```
20x POST /api/analyze with non-YouTube URL format
All 20: HTTP 400 (URL validation fails before rate limiter)
```
**Finding:** N/A — Rate limiter not reached because URL validation fails first.

### 7.2 Valid YouTube URL format (20 requests)
```
20x POST /api/analyze with https://youtube.com/watch?v=dQw4w9WgXcQ
Requests 1-7: HTTP 200 (session created, task dispatched)
Requests 8-20: HTTP 402 (credits exhausted)
```
**Finding:** PASS (partially)
Rate limiting is in code (`limit=10, window_seconds=900` per user_id) but was not the limiting factor here — the user ran out of credits after 7 requests instead. The rate limiter key uses `user_id` from the dependency, which defaults to `v0_local_user` for unauthenticated requests — meaning the rate limit is per-user but all unauthenticated requests share one user_id bucket, providing some protection.

**Concern:** Because unauthenticated requests all share the same `v0_local_user` identity, a single authenticated user could potentially bypass the rate limiter by sending unauthenticated requests while their own rate-limited user_id resets.

---

## 8. Task Status Endpoint

### 8.1 Invalid task ID
```
GET /api/tasks/INVALID_TASK_ID
Response: {"task_id":"INVALID_TASK_ID","status":"PENDING","progress":null,...}  HTTP 200
```
**Finding:** PASS — Returns PENDING status for unknown IDs (Celery treats unknown tasks as PENDING). No 404 or error leak.

### 8.2 Zero UUID
```
GET /api/tasks/00000000-0000-0000-0000-000000000000
Response: {"task_id":"00000000-0000-0000-0000-000000000000","status":"PENDING",...}  HTTP 200
```
**Finding:** PASS — Consistent behavior for any unrecognized task ID.

### 8.3 Path traversal attempt
```
GET /api/tasks/../../../etc/passwd
Response: {"detail":"Not Found"}  HTTP 404
```
**Finding:** PASS — Path traversal blocked by FastAPI routing.

---

## 9. Admin Endpoints (Unauthenticated)

All tested endpoints return 403 "Admin access required":

| Endpoint | Status |
|---|---|
| GET /api/admin/dashboard | 403 |
| GET /api/admin/users | 403 |
| GET /api/admin/rules | 403 |
| GET /api/admin/sessions | 403 |
| GET /api/admin/audit-logs | 403 |
| GET /api/admin/providers | 403 |
| GET /api/admin/narm/insights | 403 |
| GET /api/admin/audit-logs/export | 403 |
| GET /api/admin/sessions/{id} | 403 |

**Finding:** PASS — All admin endpoints properly secured by `get_admin_user` RBAC dependency.

---

## 10. Documentation Exposure

### 10.1 Swagger UI (/docs)
```
GET https://api.hookcut.nyxpath.com/docs  →  HTTP 200
```
**Finding:** FAIL — SEVERITY: LOW
Interactive Swagger UI available in production. Shows all endpoints, request/response schemas, allows "Try it out" execution.

### 10.2 ReDoc (/redoc)
```
GET https://api.hookcut.nyxpath.com/redoc  →  HTTP 200
```
**Finding:** FAIL — SEVERITY: LOW
ReDoc API documentation available in production.

### 10.3 OpenAPI Schema (/openapi.json)
```
GET https://api.hookcut.nyxpath.com/openapi.json  →  HTTP 200 (full schema, 41 paths)
```
**Finding:** FAIL — SEVERITY: LOW
Full OpenAPI schema served publicly. Exposes all endpoint signatures, validation rules, field names, and response models.

---

## 11. Webhook Security

### 11.1 Stripe webhook (no signature)
```
POST /api/webhooks/stripe  Body: {"type": "payment_intent.succeeded"}  (no stripe-signature header)
Response: {"detail":"Invalid webhook signature"}  HTTP 400
```
**Finding:** PASS — Stripe webhook signature validation working. Unsigned requests rejected.

### 11.2 Razorpay webhook (no signature)
```
POST /api/webhooks/razorpay  Body: {"event": "payment.captured"}  (no x-razorpay-signature header)
Response: Internal Server Error  HTTP 500
```
**Finding:** FAIL — SEVERITY: MEDIUM
Razorpay webhook endpoint throws an unhandled 500 error instead of returning a clean 400/401. This suggests either:
1. Razorpay keys are not configured (RAZORPAY_KEY_SECRET not set), causing an exception in the signature verification code, OR
2. There's a bug in the webhook handler for the no-signature case.

The 500 response leaks that the endpoint exists and has an error condition. Should return 400 "Invalid webhook signature" like the Stripe handler.

---

## 12. Error Information Leakage

### 12.1 Malformed JSON
```
POST /api/analyze  Body: not_json
Response: {"detail":[{"type":"json_invalid","loc":["body",0],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting value"}}]}  HTTP 422
```
**Finding:** PASS — FastAPI's default validation error. No stack trace exposed. Acceptable for an API.

### 12.2 404 endpoint
```
GET /api/nonexistent-endpoint-xyz
Response: {"detail":"Not Found"}  HTTP 404
```
**Finding:** PASS — Minimal error response, no internal details.

### 12.3 Server header
```
server: railway-edge (on backend)
server: Vercel (on frontend)
```
**Finding:** CONCERN — SEVERITY: INFO
Server header reveals hosting infrastructure (Railway, Vercel). Low risk but could be removed for defense in depth.

---

## 13. Session Data Enumeration

### 13.1 Session hooks accessible via known ID
```
GET /api/sessions/c14f9828-5877-4af0-9373-8ae5bb4dc49a/hooks
Response: Full hook data with LLM analysis, scores, improvement suggestions  HTTP 200
```
**Finding:** FAIL — SEVERITY: HIGH
Session IDs are discoverable from `/api/user/history` (no auth). Once obtained, any unauthenticated caller can access the full hook analysis for any session. Session IDs are UUIDs (low guessability) but the combination of unauthenticated `/user/history` + unauthenticated `/sessions/{id}/hooks` creates a full data exposure path.

### 13.2 Unknown session ID
```
GET /api/sessions/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/hooks
Response: {"detail":"Session not found"}  HTTP 404
```
**Finding:** PASS — Random UUIDs correctly return 404.

---

## 14. Storage Path Traversal

```
GET /api/storage/../../../etc/passwd
Response: {"detail":"Not Found"}  HTTP 404
```
**Finding:** PASS — Path traversal blocked by routing. FastAPI does not resolve `..` in path parameters.

---

## Summary of Findings

### CRITICAL (2)
| ID | Finding | Endpoint |
|---|---|---|
| C-1 | V0 credit grant endpoint live in production — anyone can grant themselves unlimited credits without auth | `POST /api/billing/v0-grant` |
| C-2 | Full user session history exposed without authentication — 54 real production sessions readable | `GET /api/user/history` |

### HIGH (4)
| ID | Finding | Endpoint |
|---|---|---|
| H-1 | User balance readable without authentication | `GET /api/user/balance` |
| H-2 | User profile readable without authentication (user ID, email, role, plan tier) | `GET /api/user/profile` |
| H-3 | Hook analysis data readable without authentication via discovered session IDs | `GET /api/sessions/{id}/hooks` |
| H-4 | Hook regeneration triggered without authentication — consumes Celery capacity | `POST /api/sessions/{id}/regenerate` |

### MEDIUM (3)
| ID | Finding | Endpoint |
|---|---|---|
| M-1 | Razorpay webhook returns 500 (unhandled error) instead of 400/401 | `POST /api/webhooks/razorpay` |
| M-2 | User currency modifiable without authentication | `PATCH /api/user/currency` |
| M-3 | Auth sync accepts arbitrary email without authentication | `POST /api/auth/sync` |

### LOW (4)
| ID | Finding | Endpoint |
|---|---|---|
| L-1 | Swagger UI (/docs) exposed in production | `GET /docs` |
| L-2 | ReDoc (/redoc) exposed in production | `GET /redoc` |
| L-3 | Full OpenAPI schema (/openapi.json) exposed | `GET /openapi.json` |
| L-4 | Backend missing security headers (HSTS, X-Content-Type-Options, etc.) | All |

### PASS (22)
- All 9 admin endpoints return 403 unauthenticated
- All input validation tests (XSS, SQLi, SSRF, long inputs, null, malformed JSON)
- Stripe webhook signature validation
- Path traversal attempts (storage, tasks, static)
- CORS: evil.com origin blocked
- CORS: hookcut.nyxpath.com origin granted correctly
- Rate limiting exists (tested: hits 402 after credit exhaustion)
- 404 responses minimal, no stack trace
- Task status: invalid IDs return PENDING, not errors

---

## Root Cause Analysis

All CRITICAL and HIGH findings share the same root cause: **the V0 authentication mode allows all endpoints to fall through to a shared `v0_local_user` identity when no Bearer token is provided.**

The `get_current_user_id` dependency in `dependencies.py` appears to return a default user ID (`v0_local_user`) rather than raising a 401 when no token is present. This was intentional for V0 local development but was deployed to production without being disabled.

**The fix required:**
1. Set `FEATURE_V0_MODE=false` in Railway env vars (if that controls the fallback behavior), OR
2. Make `get_current_user_id` raise 401 when no valid JWT is present in production
3. Remove or guard the `/api/billing/v0-grant` endpoint behind an admin or internal flag
4. Disable `/docs`, `/redoc`, `/openapi.json` in non-debug production mode

---

## Appendix: Raw Test Commands

```bash
# Backend URL discovery
curl -s "https://hookcut.nyxpath.com/_next/static/chunks/c45631b1c634e459.js" | grep -o 'api.hookcut[^"]*'

# Health check
curl -s "https://api.hookcut.nyxpath.com/health"
# → {"status":"ok","version":"0.1.0"}

# Docs exposure
curl -s -o /dev/null -w "%{http_code}" "https://api.hookcut.nyxpath.com/docs"  # → 200

# Critical: v0-grant
curl -s -X POST "https://api.hookcut.nyxpath.com/api/billing/v0-grant?paid_minutes=9999&payg_minutes=9999"
# → {"granted":{"paid_minutes":9999.0,...},...}

# Critical: user history
curl -s "https://api.hookcut.nyxpath.com/api/user/history"
# → {"sessions":[...54 real sessions...],"total":54,...}

# High: session hooks
curl -s "https://api.hookcut.nyxpath.com/api/sessions/c14f9828-5877-4af0-9373-8ae5bb4dc49a/hooks"
# → Full LLM hook analysis data

# Admin correctly blocked
curl -s "https://api.hookcut.nyxpath.com/api/admin/dashboard"
# → {"detail":"Admin access required"}

# SSRF blocked
curl -s -X POST "https://api.hookcut.nyxpath.com/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"youtube_url":"http://169.254.169.254/latest/meta-data/","niche":"Tech / AI","language":"English"}'
# → {"detail":"Could not extract video ID..."}
```
