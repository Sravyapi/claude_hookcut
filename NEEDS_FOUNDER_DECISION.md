# Needs Founder Decision

Items flagged during Staff SWE Audit #6 that require product decisions before fixing.

---

[DECISION-1] — Duplicate Video Submission While Analysis Running

File: app/services/analyze_service.py:66
Issue: If a user submits the same YouTube URL while an analysis for that URL is already running,
a second session is created and credits are charged twice. No deduplication exists.
Options:
  A) Block duplicate submissions by checking for active sessions with the same video_id + user_id
  B) Allow duplicates (current behavior) — user may want fresh analysis
  C) Show a warning but allow the user to proceed
Recommendation: A — Check for existing pending/analyzing sessions with same video_id for the
same user and return the existing session_id instead of creating a new one.

---

[DECISION-2] — No Confirmation Before Paid Regeneration

File: app/services/analyze_service.py:219
Issue: The 2nd+ regeneration charges a fee, but there is no server-side confirmation step.
The fee is deducted immediately on POST. If the frontend doesn't show a confirmation dialog,
users are charged without warning.
Options:
  A) Add a 2-step flow: POST /regenerate/preview returns the fee, POST /regenerate/confirm executes
  B) Frontend-only fix: show confirmation dialog before calling the endpoint (current API stays)
  C) Keep current behavior — the fee is small and disclosed in the UI
Recommendation: B — Frontend should show "This will cost X. Continue?" before calling the endpoint.
Server-side API change not strictly necessary.

---

[DECISION-3] — Admin LLM Prompt Injection Surface

File: app/routers/admin.py:115-122, app/services/admin_service.py
Issue: Admin-created prompt rules are inserted directly into the LLM prompt via
build_hook_prompt_from_rules(). A malicious admin could craft rules that manipulate LLM behavior
(e.g., "ignore all previous instructions").
Options:
  A) Add rule content sanitization/validation (block known injection patterns)
  B) Accept the risk — admins are trusted and the blast radius is limited to hook quality
  C) Add a "review & approve" workflow for rule changes
Recommendation: B for now — admin-only access, low blast radius, and rule versioning provides
audit trail. Revisit if admin access is shared with external partners.

---

[DECISION-4] — Webhook Rate Limiting

File: app/routers/billing.py:100-150
Issue: POST /api/webhooks/stripe and /api/webhooks/razorpay have no rate limiting. A flood of
fake webhooks (even with invalid signatures) could cause CPU load from signature verification
and DB lookups.
Options:
  A) Add rate limiting (e.g., 100 req/min per IP) to webhook endpoints
  B) Rely on Stripe/Razorpay to not flood + signature verification as protection
  C) Add IP allowlisting for known Stripe/Razorpay IPs
Recommendation: A — Simple rate limit prevents abuse without breaking legitimate webhooks.

---

[DECISION-5] — Health Check Missing Celery Worker Status

File: app/main.py:152-181
Issue: GET /api/health checks DB and Redis but NOT Celery worker availability. If all workers
are down, analyses queue indefinitely with no alert from the health endpoint.
Options:
  A) Add celery_app.control.inspect() check (adds ~200ms latency to health endpoint)
  B) Separate endpoint GET /api/health/workers for monitoring only
  C) Keep current health check simple; rely on Celery monitoring tools (Flower, etc.)
Recommendation: B — Separate endpoint avoids slowing down the primary health check used by
load balancers.

---

[DECISION-6] — Content-Security-Policy May Break Frontend

File: app/main.py:52
Issue: SecurityHeadersMiddleware sets `X-Content-Security-Policy: default-src 'self'`. This is
the backend API, so it mainly affects API responses. However, if the frontend ever loads API
responses in iframes or uses inline scripts for API-related pages, this header will block them.
Options:
  A) Keep as-is (API-only, low risk)
  B) Relax to allow specific CDN origins
  C) Remove CSP from backend (frontend sets its own via Next.js headers)
Recommendation: A — Backend API responses don't serve HTML, so CSP is informational only.

---

[DECISION-7] — Fixed-Window Rate Limiting Boundary Issue

File: app/middleware/rate_limit.py
Issue: Fixed-window rate limiting allows up to 2x the limit at window boundaries (e.g., 10 requests
at end of window + 10 at start of next = 20 in 30 seconds). This is a known limitation.
Options:
  A) Switch to sliding window (more complex Lua script)
  B) Accept fixed-window limitation (current behavior)
  C) Use token bucket algorithm
Recommendation: B for MVP — The current limits are generous enough that 2x burst is acceptable.

---

[DECISION-8] — Missing OG Image

File: hookcut-frontend/src/app/layout.tsx:42
Issue: Root layout references `/og-image.png` for social sharing, but the file does not exist
in `public/`. Every social share (Twitter, LinkedIn, Slack) will show a broken/missing preview.
Options:
  A) Create a branded 1200x630px image (requires design work)
  B) Use a text-based auto-generated OG image via Next.js ImageResponse
  C) Remove the OG image reference until one is created
Recommendation: A — This is a launch blocker for social sharing. Create the image before launch.
