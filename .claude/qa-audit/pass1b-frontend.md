# HookCut Frontend — Production Readiness Audit (Pass 1B)

**Auditor:** Claude Code (Principal Frontend Engineer perspective)
**Date:** 2026-03-07
**Scope:** All files under `hookcut-frontend/src/` plus config files
**Methodology:** Full file-by-file read; React/Next.js best practices, security, performance, type safety, accessibility, and async correctness

---

## Summary Table

| # | File | Line | Severity | Category | Description |
|---|------|------|----------|----------|-------------|
| 1 | `app/dashboard/page.tsx` | 247 | CRITICAL | React Rules | `useMemo` called after conditional early return — Rules of Hooks violation |
| 2 | `components/url-step.tsx` | ~104 | CRITICAL | React Rules | `useTransform` called inside JSX attribute (inline hook call) — Rules of Hooks violation |
| 3 | `hooks/useShortPoller.ts` | — | HIGH | Async/Memory | No `MAX_POLLS` cap — stuck shorts poll forever (memory leak, infinite requests) |
| 4 | `lib/auth.ts` | ~35 | HIGH | Security | `secure: false` hardcoded on OAuth cookies — PKCE/state cookies sent over HTTP in production |
| 5 | `app/admin/layout.tsx` | — | HIGH | Security | Middleware (`proxy.ts`) only checks auth token, NOT admin role — `/admin/*` accessible to any authenticated user until client-side guard runs |
| 6 | `components/header.tsx` | ~146 | HIGH | Logic Bug | Dashboard link shown only when `isAdmin === true` — all authenticated non-admin users lose the Dashboard navigation link |
| 7 | `components/short-card.tsx` | — | HIGH | UX/Silent Failure | `useShortPoller` error state never read — short generation failures are silently discarded, user sees spinner forever |
| 8 | `app/auth/login/page.tsx` | ~80 | MEDIUM | Accessibility | Terms/Privacy links are `<span>` elements, not `<a>` — not keyboard navigable, no href |
| 9 | `app/admin/users/page.tsx` | ~130 | MEDIUM | Accessibility | `ConfirmDialog` modal has no focus trap, no `role="dialog"`, no `aria-modal="true"` |
| 10 | `app/admin/users/page.tsx` | ~160 | MEDIUM | UI/Logic | `motion.div` exit animation inside `ConfirmDialog` not wrapped in `AnimatePresence` — exit animation never fires |
| 11 | `components/header.tsx` | ~75 | MEDIUM | UI/Logic | Mobile menu `motion.div` with `exit` prop not wrapped in `AnimatePresence` — close animation never fires |
| 12 | `app/pricing/page.tsx` | ~90 | MEDIUM | UX/Error Handling | `handleUpgrade` and `handlePaygPurchase` catch blocks only `console.warn` — no user-facing error feedback |
| 13 | `app/settings/page.tsx` | ~110 | MEDIUM | UX/Error Handling | Currency save failure only `console.warn` — no user-visible feedback |
| 14 | `next.config.ts` | — | MEDIUM | Security | Missing `Content-Security-Policy` and `Strict-Transport-Security` (HSTS) headers |
| 15 | `app/api/auth/token/route.ts` | ~18 | MEDIUM | Security | No rate limiting on `/api/auth/token` — any authenticated user can call it in a tight loop for fresh tokens |
| 16 | `app/admin/audit/page.tsx` | ~95 | MEDIUM | Performance | `handleExport` fetches ALL audit logs without pagination — could produce a very large payload |
| 17 | `hooks/useShortPoller.ts` | — | MEDIUM | Type Safety | `error` state returned from hook but `ShortCard` never reads it — error contract is broken by caller |
| 18 | `proxy.ts` | — | MEDIUM | Security | `/pricing/:path*` protected by auth middleware — anonymous users cannot view pricing page without signing in |
| 19 | `app/auth/login/page.tsx` | ~45 | MEDIUM | UX | `callbackUrl` hardcoded to `"/"` in `signIn()` — loses original redirect intent if user followed a deep link to login |
| 20 | `app/admin/audit/page.tsx` | ~100 | LOW | Browser Compat | `URL.revokeObjectURL` called synchronously after `.click()` — download may not initiate in some browsers before revocation |
| 21 | `components/progress-step.tsx` | — | LOW | Dead Code | `isPending` prop passed to `StageCard` but never used inside `StageCard` |
| 22 | `components/shorts-step.tsx` | — | LOW | UX | Elapsed timer `setInterval` runs forever — never stops even after all shorts reach terminal state |
| 23 | `lib/api.ts` | — | LOW | Reliability | No `AbortController` or request timeout — fetch calls can hang indefinitely |
| 24 | `components/error-boundary.tsx` | — | LOW | UX | `handleReset` re-renders the same subtree without fixing the root cause — may loop on persistent errors; raw `error.message` exposed to users |
| 25 | `app/ai-hook-finder/error.tsx` | — | LOW | Design | Uses light theme colors (`bg-[#FAFAF8]`, `text-[#0A0A0A]`) while entire app is dark glass-morphism |
| 26 | `app/ai-hook-finder/loading.tsx` | — | LOW | Design | Same light theme inconsistency as error.tsx |
| 27 | `app/admin/rules/page.tsx` | — | LOW | UX | All admin error toasts say "Failed to load data. Please try again." regardless of the actual failed operation |
| 28 | `app/admin/users/page.tsx` | ~200 | LOW | UX | Role update failure toast says "Failed to load data" — wrong message for an update operation |
| 29 | `marketing-home.tsx` | ~457 | LOW | Consistency | Feature section lists "12 languages supported" but comparison table and ticker also say 12; ai-hook-finder page says "12 languages" — consistent, but language counts are hardcoded copy (not from constants) |
| 30 | `hook-timeline.tsx` | — | LOW | Accessibility | Outer `<div>` has `role="img"` but inner SVG has `aria-hidden="true"` — the accessible label is on the div but SVG content (with interactive buttons) is hidden from AT |

---

## Detailed Findings

### 1. CRITICAL — Rules of Hooks: `useMemo` After Conditional Return

**File:** `src/app/dashboard/page.tsx`
**Line:** ~247 (after line ~232 early return, ~243 null return)

**Problem:** React's Rules of Hooks require hooks to be called unconditionally, at the top level of the component, before any `return` statement. `dashboard/page.tsx` has:

```
if (authStatus === "loading") return (<LoadingSkeleton />); // ~line 232
if (authStatus === "unauthenticated") return null;           // ~line 243
const filteredSessions = useMemo(...)                        // ~line 247 — VIOLATION
```

The `useMemo` call appears after two early `return` statements. React will throw "Rendered more hooks than during the previous render" in production when `authStatus` transitions between `"loading"` and `"authenticated"`. This is a silent bug in development (React strict mode catches it as a hook order violation) but causes a component crash in production.

**Why it matters:** This is a hard crash — the entire dashboard unmounts on first auth state transition, forcing a page reload. Every user who navigates to the dashboard will see this on first load.

**Fix:** Move ALL hook calls to the top of the component, before any conditional returns. Use the loaded/authenticated checks to gate what is rendered in the return statement, not to early-return:

```tsx
// All hooks at top:
const filteredSessions = useMemo(...);
// ...

// Then at render:
if (authStatus === "loading") return <LoadingSkeleton />;
if (authStatus === "unauthenticated") return null;
return <ActualDashboard filteredSessions={filteredSessions} />;
```

---

### 2. CRITICAL — Rules of Hooks: `useTransform` Called Inside JSX

**File:** `src/components/url-step.tsx`
**Line:** ~104

**Problem:** `useTransform` from `framer-motion` is a hook. The code calls it directly inside a JSX attribute expression:

```tsx
style={{
  x: useTransform(orbX, (v) => -v * 0.7),  // hook call inside JSX — VIOLATION
  y: useTransform(orbY, (v) => -v * 0.7),
}}
```

Hooks must be called at the top level of a component, never inside expressions, callbacks, or JSX attributes. React does not guarantee consistent call order when hooks are embedded in JSX. This triggers the `react-hooks/rules-of-hooks` ESLint rule.

**Why it matters:** This can cause subtle render bugs and hook state corruption. React's reconciler assumes hooks are called in the same order every render. Calling them inside JSX expressions makes this dependent on how JSX is evaluated, which can vary.

**Fix:** Extract to component-level variables:

```tsx
const orbXTransformed = useTransform(orbX, (v) => -v * 0.7);
const orbYTransformed = useTransform(orbY, (v) => -v * 0.7);
// ...
style={{ x: orbXTransformed, y: orbYTransformed }}
```

MEMORY.md (Staff SWE Audit #4) notes this was supposedly fixed in `header.tsx` but `url-step.tsx` still has the violation.

---

### 3. HIGH — No Poll Timeout in `useShortPoller`

**File:** `src/hooks/useShortPoller.ts`
**Line:** Entire hook

**Problem:** `usePollTask` (for analysis) has `MAX_POLLS = 120` (~10 minutes), but `useShortPoller` (for short generation) has NO maximum poll count. The polling loop continues indefinitely as long as the short is in a non-terminal state (`"pending"` or `"processing"`).

**Why it matters:** If a Celery worker crashes mid-short, the short status in the database remains `"pending"` forever. Every open `ShortCard` that displays this short will poll the API forever — once per exponential backoff cycle. With 3 shorts selected and one crashed worker, this is 3 infinite polling loops per session, per open tab. This is a resource leak on both the client and the server.

**Fix:** Add a `MAX_POLLS` constant (e.g., 240 = ~20 minutes with backoff) and transition to an error state when exceeded:

```tsx
const MAX_POLLS = 240;
// ...
if (pollCountRef.current >= MAX_POLLS) {
  setError("Short generation timed out. Please try again.");
  return;
}
```

---

### 4. HIGH — Insecure OAuth Cookies (`secure: false`)

**File:** `src/lib/auth.ts`
**Line:** ~35

**Problem:** The NextAuth configuration hardcodes `secure: false` for PKCE code verifier and OAuth state cookies:

```ts
cookies: {
  pkceCodeVerifier: { options: { secure: false, ... } },
  state: { options: { secure: false, ... } },
}
```

In production on HTTPS (Railway, Vercel), these cookies must be `secure: true` or they will be transmitted over HTTP — exposing OAuth PKCE verifiers and state tokens to network interception.

**Why it matters:** PKCE is specifically designed to prevent authorization code interception attacks. Sending the code verifier cookie over HTTP defeats the entire protection. An attacker on the same network can intercept the cookie and complete the OAuth flow themselves.

**Fix:**
```ts
secure: process.env.NODE_ENV === "production"
```

---

### 5. HIGH — Admin Role Not Verified at Middleware Level

**File:** `src/proxy.ts` (middleware), `src/app/admin/layout.tsx`
**Lines:** All

**Problem:** `proxy.ts` (Next.js middleware) protects `/admin/:path*` by checking only that a valid auth token exists — it does NOT check `role === "admin"`. The admin role check is performed client-side in `admin/layout.tsx` via an API call to `api.getProfile()`.

This means:
1. Any authenticated user (e.g., a free tier user) can make direct API requests to `/admin/*` routes without the client-side guard running.
2. Between auth status check and the `api.getProfile()` response, the admin layout skeleton is rendered (not admin content — but Next.js page data fetching for admin sub-pages may still execute).
3. Direct navigation to `/admin/users` by an authenticated non-admin user will briefly render the admin layout structure while the profile fetch completes.

**Why it matters:** Defense in depth for admin access should be enforced at the middleware level. Client-side guards can be bypassed by disabling JavaScript or by direct API calls from authenticated sessions.

**Fix:** In `proxy.ts`, decode the JWT and check the `role` claim for `/admin/*` paths:

```ts
if (request.nextUrl.pathname.startsWith("/admin")) {
  const token = await getToken({ req: request });
  if (!token || token.role !== "admin") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }
}
```

This requires the `role` field to be added to the JWT via the NextAuth `callbacks.jwt` handler in `auth.ts`.

---

### 6. HIGH — Dashboard Link Missing for Non-Admin Authenticated Users

**File:** `src/components/header.tsx`
**Line:** ~146

**Problem:** The header's navigation logic renders the "Dashboard" link conditionally on `isAdmin`. Regular authenticated users (non-admin) do not see the Dashboard link in the header.

The code appears to check something like:
```tsx
{isAdmin && <Link href="/dashboard">Dashboard</Link>}
```

This means every paying user who is not an admin has no header navigation to reach their dashboard — they would need to type the URL manually or use browser history.

**Why it matters:** This is a core navigation bug that degrades the experience for all non-admin users. The dashboard is the primary authenticated user destination.

**Fix:** Show the Dashboard link for all authenticated users:
```tsx
{session && <Link href="/dashboard">Dashboard</Link>}
{isAdmin && <Link href="/admin">Admin</Link>}
```

---

### 7. HIGH — Short Generation Errors Silently Discarded

**File:** `src/components/short-card.tsx`, `src/hooks/useShortPoller.ts`
**Lines:** `ShortCard` render, `useShortPoller` return

**Problem:** `useShortPoller` returns `{ data, isLoading, error }`. `ShortCard` destructures the return but never reads `error`:

```tsx
const { data } = useShortPoller(shortId, index);
// isLoading and error are never used
```

When a short fails (e.g., FFmpeg error, worker crash), the backend sets the short status to `"failed"` with an error message. `useShortPoller` transitions to `error` state. But `ShortCard` never checks this — the user sees an indefinite spinner (because `data?.status` is never `"complete"` and the error branch never renders).

**Why it matters:** Short generation failures are invisible to users. They wait indefinitely with no indication of what went wrong and no path to recovery.

**Fix:** Read and render the error state in `ShortCard`:
```tsx
const { data, error } = useShortPoller(shortId, index);
if (error) return <ErrorCard message={error} />;
```

---

### 8. MEDIUM — Terms/Privacy Links Not Keyboard Navigable

**File:** `src/app/auth/login/page.tsx`
**Line:** ~80

**Problem:** The Terms of Service and Privacy Policy "links" in the login page are `<span>` elements with `onClick` handlers and `cursor-pointer` class. They have no `href`, are not `<a>` elements, and are not included in the tab order.

**Why it matters:** Keyboard users and screen reader users cannot reach or activate these links. WCAG 2.1 SC 4.1.2 requires interactive elements to be operable via keyboard.

**Fix:** Use `<Link href="/terms">` and `<Link href="/privacy">` with proper routes, or at minimum `<a href="/terms">` elements.

---

### 9. MEDIUM — Admin ConfirmDialog Lacks Accessibility

**File:** `src/app/admin/users/page.tsx`
**Line:** ~130

**Problem:** The `ConfirmDialog` modal component:
- Has no `role="dialog"` attribute
- Has no `aria-modal="true"`
- Has no focus trap — keyboard focus can leave the modal
- Has no `aria-labelledby` connecting to the dialog title

**Why it matters:** Screen reader users receive no indication that a modal has opened. Keyboard users can tab to content behind the modal. WCAG 2.1 SC 4.1.2 and ARIA spec require proper modal semantics.

**Fix:** Use `@radix-ui/react-dialog` (already installed per `package.json`) which provides all ARIA semantics and focus trap out of the box.

---

### 10. MEDIUM — `ConfirmDialog` Exit Animation Broken

**File:** `src/app/admin/users/page.tsx`
**Line:** ~160

**Problem:** The `ConfirmDialog` uses a `motion.div` with an `exit` animation prop, but the component is not wrapped in `AnimatePresence`. Without `AnimatePresence`, Framer Motion cannot intercept the unmount and run the exit animation — the modal disappears instantly.

**Why it matters:** Jarring UX; the designed exit animation is never seen. The same issue exists in `header.tsx` for the mobile menu.

**Fix:** Wrap the conditional rendering of `ConfirmDialog` (and the mobile menu in `header.tsx`) in `<AnimatePresence>`:

```tsx
<AnimatePresence>
  {showConfirm && <ConfirmDialog ... />}
</AnimatePresence>
```

---

### 11. MEDIUM — Mobile Menu Exit Animation Broken

**File:** `src/components/header.tsx`
**Line:** ~75

**Problem:** Same as issue #10 — the mobile menu is a `motion.div` with `exit` animation but rendered conditionally without `AnimatePresence`. The menu snaps closed without animating.

**Fix:** Identical to issue #10 — wrap the conditional mobile menu in `<AnimatePresence>`.

---

### 12. MEDIUM — Pricing Errors Not Surfaced to Users

**File:** `src/app/pricing/page.tsx`
**Line:** ~90

**Problem:** Both `handleUpgrade` and `handlePaygPurchase` catch errors and `console.warn` them, with no toast notification, error banner, or user-visible feedback. If Razorpay fails to initialize (network error, missing key), the user clicks a button and nothing happens — no error, no retry prompt.

**Why it matters:** Payment flow failures are critical moments. Silent failures lose revenue and leave users confused.

**Fix:** Add `toast({ variant: "destructive", title: "Payment failed", description: ... })` in the catch block, consistent with other error handling patterns in the codebase.

---

### 13. MEDIUM — Currency Save Failure Silent

**File:** `src/app/settings/page.tsx`
**Line:** ~110

**Problem:** `handleCurrencyChange` only `console.warn` on API failure — no user-visible feedback that the preference was not saved.

**Fix:** Add a destructive toast on failure, matching the pattern used elsewhere.

---

### 14. MEDIUM — Missing CSP and HSTS Headers

**File:** `next.config.ts`
**Line:** `headers()` function

**Problem:** The security headers include X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and Permissions-Policy — but are missing:

- `Content-Security-Policy` — no XSS protection via CSP
- `Strict-Transport-Security` — no HSTS enforcement to prevent HTTP downgrade attacks

**Why it matters:** Without CSP, any injected script (e.g., via an XSS vector in video titles rendered in the UI) executes without browser restriction. Without HSTS, users can be redirected to HTTP on the first visit.

**Fix (starter CSP for Next.js):**
```ts
{
  key: "Content-Security-Policy",
  value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; connect-src 'self' https://api.hookcut.nyxpath.com; img-src 'self' data: https:; style-src 'self' 'unsafe-inline';"
}
{
  key: "Strict-Transport-Security",
  value: "max-age=63072000; includeSubDomains; preload"
}
```

---

### 15. MEDIUM — No Rate Limiting on `/api/auth/token`

**File:** `src/app/api/auth/token/route.ts`
**Line:** ~18

**Problem:** This endpoint re-signs the NextAuth session as an HS256 JWT for backend consumption. It is callable by any authenticated user without rate limiting. An authenticated attacker could call it in a tight loop to generate many valid backend JWT tokens (each valid for 1 hour).

**Why it matters:** While tokens expire, unlimited token generation could be used in token-stuffing attacks or to maintain persistent backend access after a session should have been revoked.

**Fix:** Add rate limiting via the same Redis rate limiter pattern used on the backend analysis endpoints, or use Next.js middleware to limit `/api/auth/token` calls per user per minute.

---

### 16. MEDIUM — Audit Log Export Fetches Unbounded Data

**File:** `src/app/admin/audit/page.tsx`
**Line:** ~95

**Problem:** `handleExport` calls the audit log API without a `page` parameter to fetch all logs for export. For production systems with thousands of audit entries, this is an unbounded query that could time out, exhaust server memory, or produce a response too large for the browser to handle.

**Why it matters:** The audit log table grows with every admin action. At scale (months of data), this will fail or degrade.

**Fix:** Either add server-side CSV streaming export, or add a date range parameter to export (e.g., last 30 days only) with a warning if the range is large.

---

### 17. MEDIUM — Pricing Protected by Auth (Likely Unintentional)

**File:** `src/proxy.ts`
**Line:** `matcher` array

**Problem:** The middleware matcher includes `/pricing/:path*`, meaning unauthenticated visitors are redirected to login when they navigate to `/pricing`. Pricing pages are standard marketing content that should be publicly accessible to convert anonymous visitors.

**Why it matters:** Potential customers who want to see pricing before signing up are forced to create an account first. This adds friction to the top of the conversion funnel.

**Fix:** Remove `/pricing/:path*` from the matcher, or make pricing publicly accessible with the pricing page fetching plan data without requiring authentication.

---

### 18. MEDIUM — Login callbackUrl Hardcoded

**File:** `src/app/auth/login/page.tsx`
**Line:** ~45

**Problem:**
```ts
signIn("google", { callbackUrl: "/" })
```

The `callbackUrl` is hardcoded to `"/"` rather than reading from the URL's `?callbackUrl` query parameter that the middleware sets when redirecting to login. A user who navigates to `/dashboard`, gets redirected to login, and signs in is sent to `/` instead of back to `/dashboard`.

**Why it matters:** Standard UX expectation: after login, return to where the user was trying to go. The middleware correctly adds the `callbackUrl` param — but the login page ignores it.

**Fix:**
```ts
const searchParams = useSearchParams();
const callbackUrl = searchParams.get("callbackUrl") ?? "/dashboard";
signIn("google", { callbackUrl });
```

---

### 19. LOW — `revokeObjectURL` May Fire Before Download

**File:** `src/app/admin/audit/page.tsx`
**Line:** ~100

**Problem:**
```ts
a.click();
URL.revokeObjectURL(url); // immediately after click
```

In Safari and some Chromium versions, programmatic `.click()` on an anchor for a blob URL is asynchronous. Revoking the object URL immediately after `.click()` may cause the download to reference an already-revoked URL.

**Fix:** Use `setTimeout(() => URL.revokeObjectURL(url), 100)` to allow the browser to initiate the download before cleanup.

---

### 20. LOW — Dead `isPending` Prop in `StageCard`

**File:** `src/components/progress-step.tsx`
**Lines:** `StageCard` props and body

**Problem:** `isPending` is declared in `StageCard`'s props interface and passed from the parent, but the prop is never read or used inside `StageCard`'s render output.

**Fix:** Remove `isPending` from `StageCard`'s props interface and all call sites, or use it to add a visual indicator.

---

### 21. LOW — Shorts Elapsed Timer Never Stops

**File:** `src/components/shorts-step.tsx`
**Line:** 17-21

**Problem:** The `setInterval` that drives the elapsed timer in `ShortsStep` runs from component mount until unmount — it never stops when all shorts are complete. The timer ticks up even when the user is looking at 3 fully downloaded shorts.

**Fix:** Accept a `allComplete` signal from parent or derive it from `shortIds` states, then `clearInterval` when complete:

```tsx
useEffect(() => {
  if (allComplete) return; // stop if already done
  const timer = setInterval(...);
  return () => clearInterval(timer);
}, [allComplete]);
```

---

### 22. LOW — No Request Timeout in `api.ts`

**File:** `src/lib/api.ts`
**Lines:** All `fetch()` calls

**Problem:** No `AbortController` timeout or `signal` is passed to any `fetch()` call. If the backend is slow or a network request stalls, the browser will wait indefinitely (no browser fetch timeout for normal requests).

**Fix:** Add a timeout utility:
```ts
function fetchWithTimeout(url: string, opts: RequestInit, ms = 30000) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), ms);
  return fetch(url, { ...opts, signal: ctrl.signal }).finally(() => clearTimeout(id));
}
```

---

### 23. LOW — Error Boundary May Loop on Persistent Errors

**File:** `src/components/error-boundary.tsx`
**Lines:** `handleReset`

**Problem:** `handleReset` sets `this.setState({ hasError: false, error: null })`, which triggers a re-render of the same subtree that just threw. If the error is caused by a prop value (e.g., malformed data from the API), the reset will immediately throw again, producing an error → reset → error loop.

Additionally, `error.message` is rendered directly in the UI — internal error messages may expose stack traces, class names, or API response details to end users.

**Fix:**
1. Pass a `fallback` prop or `onReset` callback to `ErrorBoundary` so callers can navigate away or refetch.
2. Sanitize the displayed error: show a generic "Something went wrong" by default, with a `showDetails` flag for development only.

---

### 24. LOW — Light Theme in Error/Loading Pages for AI Hook Finder

**File:** `src/app/ai-hook-finder/error.tsx`, `src/app/ai-hook-finder/loading.tsx`

**Problem:** Both files use light theme colors (`bg-[#FAFAF8]`, `text-[#0A0A0A]`) while the rest of the application uses a dark glass-morphism theme. This creates a jarring visual discontinuity if these states are reached.

**Fix:** Replace light theme colors with the standard dark theme token values used across the app (`bg-[#0A0A0A]`, `text-white/70`, etc.).

---

### 25. LOW — Generic Admin Error Toast Messages

**Files:** `src/app/admin/rules/page.tsx`, `src/app/admin/users/page.tsx`, `src/app/admin/sessions/page.tsx`

**Problem:** Multiple admin pages use a single generic error message ("Failed to load data. Please try again.") for all API failures regardless of the actual operation — including updates, deletes, and saves — not just loads. The users page shows "Failed to load data" when a role update fails.

**Fix:** Use operation-specific messages:
- Fetch failures: "Failed to load [rules/users/sessions]. Please try again."
- Update failures: "Failed to update [role/rule]. Please try again."
- Save failures: "Failed to save [rule]. Please try again."

---

### 26. LOW — HookTimeline Accessibility Role Conflict

**File:** `src/components/hook-timeline.tsx`
**Line:** 54

**Problem:** The outer `<div>` has `role="img" aria-label="Hook timeline"`, which tells screen readers this is a non-interactive image. But the inner `<svg>` has interactive `<g>` elements with `role="button"` and `tabIndex={0}` when `onMarkerClick` is provided. The `aria-hidden="true"` on the SVG hides these interactive elements from the accessibility tree.

This means: the interactive timeline markers are inaccessible to screen reader users when `onMarkerClick` is provided.

**Fix:** Remove `role="img"` from the outer div when the timeline is interactive. When `onMarkerClick` is provided, the SVG should NOT be `aria-hidden` and should instead use a proper `aria-label` on the SVG itself. When read-only, keep `role="img"` + `aria-hidden` on SVG.

---

## File-Level Summary by Area

### Authentication & Security
| File | Status | Key Issues |
|------|--------|-----------|
| `lib/auth.ts` | FAIL | `secure: false` on OAuth cookies |
| `proxy.ts` | PARTIAL | Auth check only — no admin role check; pricing wrongly protected |
| `app/api/auth/token/route.ts` | WARN | No rate limiting |
| `next.config.ts` | WARN | Missing CSP and HSTS headers |

### React Correctness
| File | Status | Key Issues |
|------|--------|-----------|
| `app/dashboard/page.tsx` | FAIL | `useMemo` after early return — Rules of Hooks |
| `components/url-step.tsx` | FAIL | `useTransform` inline in JSX — Rules of Hooks |
| `hooks/useShortPoller.ts` | FAIL | Infinite polling, error state unused by consumer |
| `components/header.tsx` | WARN | Mobile menu exit animation broken; Dashboard link logic bug |
| `app/admin/users/page.tsx` | WARN | ConfirmDialog exit animation broken |

### Error Handling & UX
| File | Status | Key Issues |
|------|--------|-----------|
| `components/short-card.tsx` | FAIL | Silent short failure — user sees infinite spinner |
| `app/pricing/page.tsx` | WARN | Payment errors silently discarded |
| `app/settings/page.tsx` | WARN | Currency save errors silently discarded |
| `app/admin/rules/page.tsx` | WARN | Generic error messages |
| `components/error-boundary.tsx` | WARN | May loop; exposes raw error message |

### Accessibility
| File | Status | Key Issues |
|------|--------|-----------|
| `app/auth/login/page.tsx` | FAIL | Terms/Privacy not keyboard accessible; callbackUrl ignored |
| `app/admin/users/page.tsx` | FAIL | ConfirmDialog missing ARIA modal semantics and focus trap |
| `hook-timeline.tsx` | WARN | Interactive markers hidden from AT when `role="img"` used |

### Performance
| File | Status | Key Issues |
|------|--------|-----------|
| `app/admin/audit/page.tsx` | WARN | Unbounded export query |
| `lib/api.ts` | WARN | No request timeouts |
| `components/shorts-step.tsx` | INFO | Timer runs after completion |

---

## Dependency Notes (`package.json`)

- `next-auth` 4.24.13 — v4 is in maintenance mode; v5 (Auth.js) is the active branch. Not an immediate issue but plan for migration.
- `remotion` 4.0.434 — present as a dependency for marketing video rendering. Remotion is a heavy dependency (~500ms import cost); confirm it is not imported in any Next.js page that runs in the browser.
- `typescript` 5.9.3 — latest stable. Good.
- Node 22 constraint is documented in `package.json` dev script paths — consider adding `"engines": { "node": ">=22 <23" }` to make this constraint explicit.
- `babel-plugin-react-compiler` present in devDeps — React Compiler is experimental. Confirm it is not enabled in `next.config.ts` without thorough testing, as it rewrites component code and may interact unexpectedly with the Rules of Hooks violations already present.

---

## Priority Fix Order

1. **CRITICAL** (fix before next deploy):
   - Issue #1: `useMemo` after early return in `dashboard/page.tsx`
   - Issue #2: `useTransform` inside JSX in `url-step.tsx`

2. **HIGH** (fix this sprint):
   - Issue #3: Add `MAX_POLLS` to `useShortPoller`
   - Issue #4: `secure: false` in `auth.ts`
   - Issue #5: Add admin role check to `proxy.ts`
   - Issue #6: Dashboard link visible to all authenticated users
   - Issue #7: Read and render `error` state in `ShortCard`

3. **MEDIUM** (fix before public launch):
   - Issues #8-#18: Accessibility, missing headers, error handling, pricing auth gate

4. **LOW** (backlog):
   - Issues #19-#26: Polish, consistency, minor reliability improvements
