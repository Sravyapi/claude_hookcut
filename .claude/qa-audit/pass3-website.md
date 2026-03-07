# PASS 3 — Production Website Crawl

**Tested against**: https://hookcut.nyxpath.com/
**Date**: 2026-03-07
**Status**: PARTIAL COMPLETE (no browser/Playwright — used WebFetch + curl)

---

## Pages Tested

| Page | HTTP | Notes |
|------|------|-------|
| `/` | 200 | Loads correctly, all sections present |
| `/ai-hook-finder` | 200 | Content server-rendered, input not visible in SSR |
| `/pricing` | 200 (redirected to login) | Pricing page redirects unauthenticated users to login — BAD UX |
| `/auth/login` | 200 | Google OAuth only, no email/password |
| `/dashboard` | 200 (redirected to login) | Correctly requires auth |

---

## Security Headers — Frontend (Vercel)

| Header | Status |
|--------|--------|
| `x-frame-options: DENY` | GOOD |
| `x-content-type-options: nosniff` | GOOD |
| `strict-transport-security: max-age=63072000` | GOOD |
| `referrer-policy: strict-origin-when-cross-origin` | GOOD |
| `permissions-policy: camera=(), microphone=(), geolocation=()` | GOOD |
| `content-security-policy` | **MISSING** |
| `access-control-allow-origin: *` (wildcard) | **BAD — overly permissive** |

---

## Issues Found

### 1. Pricing Page Requires Login — UX BUG (MEDIUM)
`/pricing` redirects to `/auth/login?callbackUrl=...pricing`. Public pricing pages should be accessible without authentication.
**Fix**: Remove auth middleware guard from `/pricing` route.

### 2. No CSP Header — HIGH
No Content-Security-Policy on either frontend (Vercel) or backend (Railway).
Without CSP, XSS attacks can exfiltrate tokens, session data, etc.
**Fix**: Add CSP headers in `next.config.ts` (headers function) and Railway response headers.

### 3. Wildcard CORS on Frontend Static Assets — LOW
`access-control-allow-origin: *` on frontend static assets is set by Vercel by default.
Low risk for static files but signals no CORS policy review was done.

### 4. No Backend Security Headers — HIGH
Backend at `api.hookcut.nyxpath.com` returns no security headers beyond what Railway adds.
Missing: X-Frame-Options, X-Content-Type-Options, HSTS, CSP.
**Fix**: Add security header middleware to FastAPI app.

### 5. Google OAuth Only — MISSING FEATURE (noted by user)
No email/password signup. All users must use Google.
**Impact**: Blocks users without Google accounts, no B2B use case.
**Recommendation**: Add email/password auth as V2 feature.

### 6. nonce Attribute Undefined — LOW
Login page source shows CSP nonce attributes set to `undefined` in rendered HTML.
This indicates a Next.js CSP nonce setup was attempted but not completed.

### 7. No Robots.txt for API Subdomain — LOW
`api.hookcut.nyxpath.com/robots.txt` not configured.
Search engines may index API endpoint URLs.

### 8. JS Chunks Not Referenced in Manifest Correctly — LOW
One chunk URL probe returned empty — Next.js build artefacts may not match deployed version. Minor.

---

## Page Load Performance (estimated from headers)

- `x-vercel-cache: HIT` on homepage — CDN caching working
- `age: 1168` — page cached for ~19 minutes, good
- No obvious large bundle size issues (chunks are split)
- No third-party analytics scripts visible (PostHog/Sentry not yet configured)

---

## Missing States Observed

- `/ai-hook-finder`: Loading state present (spinner), but no visible error state for API failures in SSR render
- Login page: No error message area visible for failed OAuth attempts
- No visible rate limit exceeded message in UI

---

## TODO (not yet tested due to missing auth)
- [ ] Dashboard page content (requires auth)
- [ ] Settings page
- [ ] Admin pages (requires admin JWT)
- [ ] Shorts generation flow end-to-end
- [ ] Download flow
- [ ] Mobile responsiveness
