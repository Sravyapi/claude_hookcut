# Staff SWE Audit #8 — Full-Stack Fix

## Audit Findings (Playwright-verified, March 10 2026)

### Page-by-Page Current State

**Unauthenticated pages:**
- `/` (homepage): Marketing page renders correctly. Issues: pricing section hardcodes ₹ (INR) with no currency toggle tied to user preference; YouTube thumbnail 404 for `maxresdefault.jpg`; social footer links are `href="#"` (dead); CTA "Start Analyzing Free" links to `/auth/login` (correct for unauth).
- `/pricing`: Shows PAYG slider + FAQ but **plan cards are MISSING** — the API call to `/api/billing/plans` likely 401s since it requires auth. Only the PAYG section and FAQ render.
- `/auth/login`: Works correctly, redirects to `/dashboard` on success.
- `/clip` (unauth): Not in proxy matcher — no auth redirect. Renders with header but user gets stuck if unauthenticated (no callbackUrl).

**Authenticated pages (verified with fresh user):**
- `/dashboard` (immediately after login redirect): Shows correctly — auth'd header with Dashboard link, credit badge (120 min), user avatar, credit ring, 4 stat cards (Subscription 0/0, PAYG 0, Free 120/120, Manual Clips 0/0), session history, "Manual Clip" button, "New Video" button.
- `/` (auth'd, navigating back): Shows FULL MARKETING PAGE with unauthenticated header — no user avatar, no credit badge, no Dashboard link. The `router.push("/dashboard")` redirect on line 237 of home-state-machine.tsx is NOT firing. `authStatus` appears to be "loading" or "unauthenticated" when navigating to `/` after initial login.
- `/settings` (auth'd): Shows unauthenticated header + **EMPTY main content**. The settings form doesn't render.
- `/pricing` (auth'd): Shows unauthenticated header. Plan cards still missing. Only PAYG + FAQ visible.
- `/clip` (auth'd): Shows auth'd header (Dashboard link, user avatar) + "Back to Dashboard" + clipper form. But NO credit badge in header (unlike dashboard), no footer.
- `/admin` (auth'd, non-admin user): Redirects to `/` → shows marketing page (correct behavior for non-admin, but should show a "not authorized" message instead of silently redirecting).

### Critical Bugs (Ship-blockers)

**B1: Session persistence broken across client-side navigation**
After login, only the initial redirect target (`/dashboard`) has a working session. Navigating to ANY other page (`/`, `/settings`, `/pricing`) loses the authenticated state — pages render with unauthenticated header and empty/broken content. This means `useSession()` returns `unauthenticated` on those pages.

Root cause candidates:
- NextAuth session cookie may not be setting correctly (check `NEXTAUTH_URL`, cookie domain/path)
- The session provider may not be wrapping all pages correctly
- The JWT callback may be failing silently on subsequent requests

**B2: Settings page renders empty**
`/settings` shows an empty `<main>` tag even when authenticated (when session briefly works). The component may be waiting for an API response that fails silently.

**B3: Pricing plan cards not rendering**
Both auth'd and unauth'd pricing page show no plan cards. The `/api/billing/plans` endpoint requires auth (`get_current_user_id`). The frontend component may be failing to render the cards when the API returns 401 or when the session is missing.

**B4: Homepage shows marketing page for authenticated users**
The redirect in `home-state-machine.tsx` line 237 (`router.push("/dashboard")`) doesn't fire because `authStatus` is not "authenticated" (related to B1).

### UX/Workflow Issues

**W1: No unified entry point for AI analysis vs Manual Clip**
Dashboard has both "New Video" and "Manual Clip" buttons, but they go to completely different pages with different UIs. Users should see both options with clear credit buckets — how many AI minutes vs manual clip minutes they have.

**W2: Credit display doesn't show both buckets prominently**
Dashboard stat cards show 4 separate buckets, but the header credit badge only shows `total_available` as a single number. Users can't tell at a glance how much AI credit vs manual clip credit they have. The clipper page shows NO credit info at all.

**W3: Header inconsistency across pages**
- Dashboard: auth'd header with Dashboard link, credit badge, user avatar ✓
- Clip: auth'd header with Dashboard link, user avatar, but NO credit badge ✗
- Settings, Pricing, Homepage: unauthenticated header (broken due to B1)

**W4: Pricing data duplication**
Homepage pricing section hardcodes INR (₹499, ₹999) with tier names matching the API. The `/pricing` page tries to fetch from API but fails. Two sources of truth.

**W5: Homepage pricing always shows INR**
The marketing homepage hardcodes ₹ symbols. For international users this is confusing. Should use shared pricing data with currency awareness.

**W6: Footer social links are dead (`href="#"`)**
Twitter, YouTube, LinkedIn links in footer go nowhere.

**W7: YouTube thumbnail 404**
`maxresdefault.jpg` returns 404 for many videos. No fallback to `hqdefault.jpg`.

### Security Issues

**S1: `/clip` not in proxy middleware matcher**
`proxy.ts` matcher is `["/dashboard/:path*", "/settings/:path*", "/admin/:path*"]`. The `/clip` route is NOT protected — unauthenticated users can access it without redirect to login with callbackUrl.

---

## Implementation Plan — 4 Agents

### Agent 1: Fix Session & Auth (worktree: `fix-session-auth`)
**Priority: CRITICAL — all other agents depend on this working**

Files:
- `hookcut-frontend/src/lib/auth.ts`
- `hookcut-frontend/src/proxy.ts`
- `hookcut-frontend/src/app/layout.tsx` (session provider wrapping)
- `hookcut-frontend/src/components/providers.tsx` (session provider)
- `hookcut-frontend/next-auth.d.ts`
- `hookcut-backend/app/routers/auth.py`
- `hookcut-backend/app/routers/billing.py` (ONLY: make plans endpoint work without auth)

Tasks:

1. **Debug and fix session persistence (B1)** — This is the #1 ship-blocker. After login, navigating to `/`, `/settings`, `/pricing` loses the session.
   - Check that `SessionProvider` from `next-auth/react` wraps ALL pages in `layout.tsx` or `providers.tsx`.
   - Check `NEXTAUTH_URL` environment variable — must match `http://localhost:3000` for dev. If missing, NextAuth may not set cookies correctly.
   - Check cookie settings in `auth.ts` — the `sameSite`, `secure`, and `path` settings may be wrong for dev.
   - Check if the JWT callback is throwing on subsequent token refreshes (not just initial sign-in).
   - After fix: verify `useSession()` returns `authenticated` on ALL pages after login.

2. **Add `/clip` to proxy middleware matcher (S1)** — In `proxy.ts`, add `/clip/:path*` to the matcher array. This ensures unauthenticated users get redirected to `/auth/login?callbackUrl=/clip`.

3. **Make pricing plans work without auth (B3 partial)** — In `hookcut-backend/app/routers/billing.py`, change `get_plans` to use an optional user dependency. If no user, return USD plans. If user exists, return plans in their preferred currency.

4. **Verify admin auth flow** — After B1 is fixed, admin auth should work since the JWT `isAdmin` field is already being set in the `jwt` callback (line 99 of auth.ts). If it still doesn't work after B1 fix, debug the `token.isAdmin` check in proxy.ts.

Verification:
- Login → navigate to `/` → redirects to `/dashboard` (not marketing page)
- Login → navigate to `/settings` → shows auth'd header + settings form
- Login → navigate to `/pricing` → shows auth'd header + plan cards
- Login → navigate to `/clip` → shows auth'd header + credit badge + clipper
- Unauth → `/clip` → redirects to `/auth/login?callbackUrl=/clip`
- Unauth → `/pricing` → shows plan cards (USD default)

---

### Agent 2: Dashboard & Credit Display Redesign (worktree: `fix-dashboard-credits`)

Files:
- `hookcut-frontend/src/app/dashboard/page.tsx`
- `hookcut-frontend/src/components/header.tsx`
- `hookcut-frontend/src/app/clip/page.tsx` (ONLY: add credit display)

Tasks:

1. **Restructure nav links** — In `header.tsx`, replace the `NAV_LINKS` array. Remove "Clipper" (accessed from dashboard only). Combine "Use Cases" into "Blog". Add "How It Works":
   - Unauth nav: `Features` (`/features`) · `How It Works` (`/how-it-works`) · `Pricing` (`/pricing`) · `Blog` (`/blog`)
   - Auth'd nav: `Dashboard` (`/dashboard`) · `Features` (`/features`) · `How It Works` (`/how-it-works`) · `Pricing` (`/pricing`) · `Blog` (`/blog`)
   - The "Dashboard" link already conditionally renders for auth'd users — keep that logic.

2. **Show dual credit buckets in header** — The credit badge in `header.tsx` currently shows just `total_available` as one number. Change it to show two numbers:
   - "AI: X min" (subscription + free + PAYG minutes)
   - "Clip: Y min" (manual_clip_minutes_remaining)
   - Keep the combined total as the primary number, with a tooltip or dropdown showing the breakdown.

2. **Add credit display to clipper page** — In `clip/page.tsx`, show the manual clip minutes remaining prominently near the top (e.g., "✂ 0.0 clip minutes remaining" with a link to pricing/top-up).

3. **Dashboard: clearer dual-mode entry** — The dashboard already has "New Video" and "Manual Clip" buttons. Enhance them:
   - "New Video" button: show "AI Analysis" label with remaining AI minutes below (e.g., "120 min available")
   - "Manual Clip" button: show remaining clip minutes below (e.g., "0 min available")
   - If a bucket is empty, show the button as disabled with "Top up" link instead.

4. **Fix "New Video" button destination** — Currently links to `/` which shows marketing page (broken). After Agent 1 fixes the session, `/` should redirect to `/dashboard`. So "New Video" should instead trigger the analysis workflow directly — either open a modal with the URL input, or navigate to a `/analyze` route that hosts the HomeStateMachine in analyzing mode.
   - Simplest fix: Change the "New Video" href from `/` to `/dashboard?action=analyze` and add URL input handling on dashboard. OR just open the HeroUrlInput inline on dashboard.

Verification:
- Header credit badge shows AI vs Clip breakdown
- Clipper page shows clip minutes remaining
- Dashboard entry points show per-bucket availability
- Users can start AI analysis from dashboard

---

### Agent 3: Pricing Single Source of Truth (worktree: `fix-pricing`)

Files:
- `hookcut-frontend/src/lib/pricing-data.ts` (NEW)
- `hookcut-frontend/src/components/marketing-home.tsx` (ONLY: pricing section)
- `hookcut-frontend/src/app/pricing/page.tsx`

Tasks:

1. **Create shared pricing constants** — New file `src/lib/pricing-data.ts`:
   ```ts
   export const PLANS = [
     { key: "free", name: "Free", priceUSD: 0, priceINR: 0, minutes: 120, features: [...], highlighted: false },
     { key: "lite", name: "Lite", priceUSD: 7, priceINR: 499, minutes: 100, features: [...], highlighted: true },
     { key: "pro", name: "Pro", priceUSD: 13, priceINR: 999, minutes: 500, features: [...], highlighted: false },
   ];
   ```

2. **Marketing homepage: use shared data** — Replace hardcoded pricing grid in `marketing-home.tsx` (lines ~209-340) with a component that maps over `PLANS`. Keep the annual/monthly toggle (annual = 20% off). Use `PLANS` as the source.

3. **Pricing page: fallback to shared data** — In `pricing/page.tsx`, if the API call to `/api/billing/plans` fails (401 or network error), fall back to rendering from `PLANS` in USD. When the API succeeds, use the API response (which has the user's preferred currency).

4. **Fix plan card rendering** — The pricing page currently shows only PAYG + FAQ. The plan cards section may be conditionally rendered based on API response. Ensure cards render from either API or fallback data.

Verification:
- Homepage pricing: "Lite" (not "Starter"), prices from shared data
- `/pricing` unauth: shows all 3 plan cards in USD (fallback)
- `/pricing` auth'd: shows plan cards in user's preferred currency
- Changing currency in settings updates pricing page

---

### Agent 4: Misc UI & Cleanup (worktree: `fix-misc-ui`)

Files:
- `hookcut-frontend/src/components/footer.tsx`
- `hookcut-frontend/src/app/dashboard/layout.tsx`
- `hookcut-frontend/src/app/how-it-works/page.tsx`
- `hookcut-frontend/src/components/marketing-home.tsx` (ONLY: YouTube thumbnail fallback — NOT pricing section, that's Agent 3)

Tasks:

1. **Fix YouTube thumbnail 404** — Add `onError` fallback from `maxresdefault.jpg` to `hqdefault.jpg` in any `<img>` tag using YouTube thumbnail URLs. Check `marketing-home.tsx` and any other components rendering thumbnails.

2. **Fix dead footer social links** — In `footer.tsx`, the Twitter/YouTube/LinkedIn links use `href="#"`. Add `aria-disabled="true"`, `title="Coming soon"`, and change the styling to show they're inactive (reduced opacity).

3. **Fix page title duplication** — `dashboard/layout.tsx` has `title: "Dashboard | HookCut"` which becomes "Dashboard | HookCut | HookCut" via root template. Change to just `"Dashboard"`. Same for `how-it-works/page.tsx` (remove trailing `| HookCut`).

4. **Add manual clipper mention to How It Works** — Add a section after the 3 steps: "Or clip any moment yourself" with description and link to `/clip`.

Verification:
- No thumbnail 404 errors in console
- Footer social links show "Coming soon" tooltip
- Page title: "Dashboard | HookCut" (not doubled)
- How It Works mentions manual clipper

---

## Merge Order

1. **Agent 1 (session/auth) FIRST** — all other agents need working sessions
2. Agent 4 (misc UI) — independent
3. Agent 3 (pricing) — needs Agent 1 for auth'd pricing to work
4. Agent 2 (dashboard/credits) — needs Agent 1 for session, needs pages to render

After all merges: `cd hookcut-frontend && npx tsc --noEmit && npm run build`

## Smoke Test Checklist

- [ ] Login → all pages show authenticated header (Dashboard link, credit badge, user avatar)
- [ ] `/` auth'd → redirects to `/dashboard`
- [ ] Dashboard shows dual-mode entry (AI Analysis + Manual Clip) with per-bucket credits
- [ ] Header credit badge shows AI vs Clip breakdown
- [ ] Clipper page shows clip minutes remaining
- [ ] `/pricing` unauth → shows 3 plan cards (USD fallback)
- [ ] `/pricing` auth'd → shows plan cards in user's currency
- [ ] Homepage pricing uses shared data ("Lite" not "Starter")
- [ ] `/clip` unauth → redirects to login with callbackUrl
- [ ] `/settings` auth'd → renders settings form
- [ ] `/admin` admin user → loads admin panel
- [ ] No YouTube thumbnail 404s
- [ ] Page titles not doubled
- [ ] Footer social links show "Coming soon"
