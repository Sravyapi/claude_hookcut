# Staff SWE Audit #8 — Full-Stack Fix (Nav, Auth, Pricing, Clipper, UI)

## Overview
This spec fixes 21 issues + 5 workflow redesigns found in the Staff SWE full-stack audit (frontend, backend, auth, pricing, navigation, admin). Work is divided into 5 independent agents, each in its own worktree. Agents touch **non-overlapping files** to prevent merge conflicts.

**CRITICAL RULE**: Each agent works ONLY on the files listed in its section. If you discover you need to edit a file assigned to another agent, add a `// TODO(agent-X): description` comment instead. Do NOT edit files outside your scope.

**Build rule**: Do NOT run `next build` or `npm run build` during agent work. Only run `npx tsc --noEmit` for type checking within each agent. The final build is run once after all agents merge.

---

## Agent 1: Navigation, Header & Dashboard-as-Home (worktree: `fix-nav-header`)

### Files you own:
- `hookcut-frontend/src/components/header.tsx`
- `hookcut-frontend/src/app/dashboard/page.tsx` (ONLY: add Header import + render, add "Manual Clip" button, add session type badge)
- `hookcut-frontend/src/app/settings/page.tsx` (ONLY: add Header import + render)
- `hookcut-frontend/src/app/clip/page.tsx` (ONLY: add Header import + render, fix callbackUrl, add back-to-dashboard link, add credit display)
- `hookcut-frontend/src/app/admin/layout.tsx` (ONLY: add Header import + render)
- `hookcut-frontend/src/components/home-state-machine.tsx` (ONLY: redirect auth'd users to /dashboard)
- `hookcut-frontend/src/components/authenticated-home.tsx` (DELETE or repurpose — its content merges into dashboard)

### Tasks:

**1.1 Add global header to all product pages**
These pages currently render NO header:
- `src/app/dashboard/page.tsx` — Add `import Header from "@/components/header"` and render `<Header />` as the first child inside the outermost wrapper div.
- `src/app/settings/page.tsx` — Same pattern.
- `src/app/clip/page.tsx` — Same pattern.
- `src/app/admin/layout.tsx` — Add `<Header />` before the `<main>` tag (line ~110). This gives admin pages global nav.

**1.2 Fix nav links: Features/Pricing should use dedicated pages**
In `header.tsx`, the `NAV_LINKS` array (line ~21-27):
- Change `{ href: "/#features", label: "Features", match: "features" }` → `{ href: "/features", ... }`
- Change `{ href: "/#pricing", label: "Pricing", match: "pricing" }` → `{ href: "/pricing", ... }`

**1.3 Add Admin link to user dropdown (admin only)**
In `header.tsx`, find the user dropdown menu (the `<DropdownMenuContent>` section). Add a new `<DropdownMenuItem>` for "Admin Panel" that links to `/admin`, conditionally rendered only when `session?.user?.isAdmin === true`. Use the `Shield` icon from lucide-react. Place it before the "Settings" item.

**1.4 Fix `/clip` callbackUrl**
In `src/app/clip/page.tsx`, find line 212: `router.push("/auth/login")`. Change to:
```ts
router.push("/auth/login?callbackUrl=/clip");
```

**1.5 Dashboard-as-Home for authenticated users (Redesign F2)**
Currently, authenticated users see `AuthenticatedHome` (a simplified workspace with URL input + 3 recent sessions) on `/`. The real dashboard at `/dashboard` is a separate page with full stats, credit ring, session history with pagination, etc.

**Goal**: When a logged-in user visits `/`, redirect them to `/dashboard` instead of showing `AuthenticatedHome`. This makes the dashboard the true home for authenticated users.

In `src/components/home-state-machine.tsx`:
- In the `state.step === "input"` block (line ~402), when `isAuthenticated` is true, instead of rendering `<AuthenticatedHome />`, use `router.push("/dashboard")` with a loading skeleton as placeholder. Import `useRouter` from `next/navigation`.
- OR simpler approach: Render a `redirect("/dashboard")` component that does the redirect client-side.
- The URL input (HeroUrlInput) that currently lives in AuthenticatedHome needs to be moved to the dashboard page so users can still start new analyses from there.

In `src/app/dashboard/page.tsx`:
- Import `HeroUrlInput` from `@/components/hero-url-input`
- Add the URL input section above the stats grid, styled similarly to how AuthenticatedHome renders it (greeting + URL input + niche selector)
- The existing credit ring, stats, and session history stay as-is
- Add a `handleAnalyze` function that POSTs to the API and redirects to `/` with the session in progress (the HomeStateMachine will pick it up via sessionStorage persistence)

After these changes, `authenticated-home.tsx` can be deleted since all its functionality lives in dashboard/page.tsx now.

**1.6 Add "Manual Clip" action to dashboard**
In `src/app/dashboard/page.tsx`, next to the existing "+ New Video" button (if one exists) or in the top action bar, add a "✂ Manual Clip" button that navigates to `/clip`. Style it as a secondary/outline variant.

**1.7 Add session type badge to dashboard history**
In the session history table on dashboard, add a badge showing session type:
- If `session_type === "manual_clip"` → "Manual" badge (purple)
- Otherwise → "AI" badge (default blue)
Check the session data structure for the correct field name. If `session_type` doesn't exist, add a TODO comment.

**1.8 Add navigation aids to clip page**
In `src/app/clip/page.tsx`:
- Add a "← Back to Dashboard" link at the top-left of the main content area (below header)
- Add a credit balance display using the `useUser` hook from `@/components/providers`

### Verification:
- `npx tsc --noEmit` passes
- Every product page (dashboard, settings, clip, admin) shows the global header
- Features/Pricing nav links go to `/features` and `/pricing` respectively
- Admin link appears in user dropdown for admin users only
- `/clip` redirects to login with callbackUrl
- Authenticated users visiting `/` are redirected to `/dashboard`
- Dashboard shows URL input, credit stats, session history, and Manual Clip button
- Clip page shows credit balance and back-to-dashboard link

---

## Agent 2: Pricing & Metadata Fixes (worktree: `fix-pricing-meta`)

### Files you own:
- `hookcut-frontend/src/components/marketing-home.tsx` (ONLY: pricing section — replace hardcoded pricing with shared data)
- `hookcut-frontend/src/app/dashboard/layout.tsx`
- `hookcut-frontend/src/app/settings/layout.tsx`
- `hookcut-frontend/src/app/pricing/layout.tsx`
- `hookcut-frontend/src/app/pricing/page.tsx` (ONLY: unauthenticated plan loading)
- `hookcut-frontend/src/lib/pricing-data.ts` (NEW: shared pricing constants)
- `hookcut-backend/app/routers/billing.py` (ONLY: plans endpoint auth)

### Tasks:

**2.1 Create shared pricing data (Redesign F5)**
Create `src/lib/pricing-data.ts` with a single source of truth for plan names, prices, and features:
```ts
export const PLANS = [
  {
    key: "free",
    name: "Free",
    priceUSD: 0,
    priceINR: 0,
    period: null,
    minutes: 120,
    features: ["5 hooks per video", "3 Shorts per video", "Watermarked"],
    cta: "Start Free",
    highlighted: false,
  },
  {
    key: "lite",
    name: "Lite",
    priceUSD: 7,
    priceINR: 499,
    period: "mo",
    minutes: 100,
    minutesLabel: "100 watermark-free minutes",
    features: ["5 hooks per video", "3 Shorts per video", "100 watermark-free minutes", "Priority support"],
    cta: "Go Lite",
    highlighted: true,
  },
  {
    key: "pro",
    name: "Pro",
    priceUSD: 13,
    priceINR: 999,
    period: "mo",
    minutes: 500,
    minutesLabel: "500 watermark-free minutes",
    features: ["5 hooks per video", "Unlimited Shorts", "500 watermark-free minutes", "Priority support", "Early access"],
    cta: "Go Pro",
    highlighted: false,
  },
] as const;
```

**2.2 Fix pricing inconsistency — homepage must use shared data**
In `src/components/marketing-home.tsx`, the pricing section (line ~209-340) has hardcoded INR prices with tier name "Starter". Replace the entire hardcoded pricing grid with a component that imports `PLANS` from `@/lib/pricing-data` and renders from that array. This ensures homepage pricing always matches `/pricing`.

Key changes:
- "Starter" → "Lite" (the `PLANS` array uses "Lite")
- Features match exactly
- Keep the annual/monthly toggle — annual = 20% discount applied to the shared prices

**2.3 Fix unauthenticated pricing 401 error**
The `/api/billing/plans` endpoint (in `hookcut-backend/app/routers/billing.py` line 41-46) requires `get_current_user_id` which returns 401 for unauthenticated users. The pricing page should be visible without login.

In `hookcut-backend/app/routers/billing.py`:
- Change the `get_plans` endpoint so `user_id` is an `Optional` dependency (use `Depends(get_optional_user_id)` or make a new optional version)
- If no user is authenticated, return default USD plans
- If authenticated, return plans in the user's preferred currency

In `hookcut-frontend/src/app/pricing/page.tsx`:
- Ensure the API call handles 401 gracefully by falling back to the shared `PLANS` data from `@/lib/pricing-data.ts`

**2.4 Fix page title duplication**
The root layout uses `template: "%s | HookCut"`. Child layouts must NOT include "| HookCut" in their title strings.

- `src/app/dashboard/layout.tsx`: Change `"Dashboard | HookCut"` → `"Dashboard"`
- `src/app/settings/layout.tsx`: Change `"Settings | HookCut"` → `"Settings"`
- `src/app/pricing/layout.tsx`: Change title to just `"Pricing — Start Free, $7/month"`. Update the openGraph and twitter title fields similarly. Also fix "Starter" → "Lite" if present in description.
- `src/app/how-it-works/page.tsx` — title also has `| HookCut` at the end. BUT this file is owned by Agent 4. Add a `// TODO(agent-4): remove "| HookCut" from title metadata` comment in this file.

### Verification:
- Homepage pricing says "Lite" not "Starter", uses shared PLANS data
- `/pricing` loads fully for both authenticated and unauthenticated users (no 401)
- Page titles render as "Dashboard | HookCut" (not "Dashboard | HookCut | HookCut")
- `npx tsc --noEmit` passes

---

## Agent 3: Admin Panel & Auth Fix (worktree: `fix-admin`)

### Files you own:
- `hookcut-frontend/src/lib/auth.ts`
- `hookcut-frontend/src/proxy.ts`
- `hookcut-frontend/next-auth.d.ts`
- `hookcut-backend/app/routers/auth.py` (ONLY: role/isAdmin in login/register response)
- `hookcut-backend/app/services/auth_service.py` (ONLY: ensure role is in response)

### Tasks:

**3.1 Debug and fix `isAdmin` JWT propagation**
The admin panel redirects all users (including admins) to `/` because `token.isAdmin` is falsy.

Trace the full chain:

1. **Backend** (`hookcut-backend/app/routers/auth.py`): The `login` and `register` endpoints return `AuthService.login(...)` / `AuthService.register(...)`. Verify `AuthResponse` schema includes `role` field. Check `auth_service.py` to ensure `role` is populated from `User.role`.

2. **Frontend auth config** (`hookcut-frontend/src/lib/auth.ts`):
   - Line 49-55: The `authorize` function reads `data.role` and returns `{ role: data.role ?? "user" }` — this looks correct.
   - Line 94-101: The `jwt` callback sets `token.role` and `token.isAdmin = token.role === "admin"` — this looks correct.
   - Line 104-112: The `session` callback copies both `role` and `isAdmin` to `session.user` — this looks correct.
   - **Check the Google OAuth flow**: The `GoogleProvider` path does NOT go through `authorize()`. When a user signs in with Google, the `jwt` callback fires with `user` from Google (which has NO `role` field). So `token.role` stays `undefined` and `isAdmin` stays `false`. Fix: In the `jwt` callback, when `user` exists AND `user.role` is missing (Google sign-in), make a backend API call to sync/fetch the user's role. Or: after Google sign-in, call a backend endpoint that returns the user's role and set it.

3. **Type declarations** (`next-auth.d.ts`): Verify it extends `Session`, `JWT`, and `User` interfaces with `role` and `isAdmin` fields. If the file doesn't exist, create it.

4. **Middleware** (`proxy.ts` line 13): `token.isAdmin` — verify this matches the JWT callback field name exactly.

**Common gotchas:**
- Is the JWT encoding/decoding stripping custom fields? NextAuth's default JWT handler should preserve them.
- After fixing, the user must sign out and sign back in (JWT changes require a new session).
- The `jwt` callback's `user` parameter is only present on sign-in, NOT on subsequent requests. So the initial sign-in must correctly set `token.role` and `token.isAdmin`.

### Verification:
- Sign in as admin user → navigate to `/admin` → admin panel loads (not redirect to `/`)
- Sign in as non-admin → navigate to `/admin` → redirects to `/` (correct behavior)
- Google OAuth users get correct role from backend
- `npx tsc --noEmit` passes

---

## Agent 4: Content Pages & How-It-Works (worktree: `fix-content-pages`)

### Files you own:
- `hookcut-frontend/src/app/how-it-works/page.tsx`
- `hookcut-frontend/src/app/youtube-hooks-for/[niche]/page.tsx` (ONLY: thumbnail fallback)
- `hookcut-frontend/src/components/marketing-home.tsx` (ONLY: YouTube thumbnail fallback, social proof — NOT pricing section, that's Agent 2)

### Tasks:

**4.1 Fix YouTube thumbnail 404s**
The current code uses `maxresdefault.jpg` which 404s for many videos. Add an `onError` fallback:
```tsx
<img
  src={`https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`}
  onError={(e) => { e.currentTarget.src = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`; }}
  alt={...}
/>
```

Update in:
- `src/components/marketing-home.tsx` — any hardcoded YouTube thumbnail URLs
- `src/app/youtube-hooks-for/[niche]/page.tsx` — niche page thumbnails

**4.2 Add manual clipper to How It Works page**
In `src/app/how-it-works/page.tsx`, add a new section after the existing steps:
- Title: "Or clip any moment yourself"
- Description: "Know exactly which moment you want? Use the Manual Clipper to set precise start and end points, choose your caption style, and export — no AI needed."
- Link/button to `/clip`

Also fix the title duplication: remove `| HookCut` from the metadata title (currently `"How HookCut Works — URL to Short in 3 Steps | HookCut"` → `"How HookCut Works — URL to Short in 3 Steps"`). Same for openGraph and twitter titles.

**4.3 Fix homepage CTA auth state comment**
In `src/components/marketing-home.tsx`, the CTA buttons link to `/auth/login`. Since `MarketingHome` only renders for unauthenticated users (HomeStateMachine gates this), the links are correct. Add a clarifying comment:
```ts
// MarketingHome only renders for unauthenticated users (see HomeStateMachine),
// so CTA links to /auth/login are intentional.
```

### Verification:
- No YouTube thumbnail 404 errors in browser console
- How It Works page mentions manual clipper
- Title metadata doesn't double "| HookCut"
- `npx tsc --noEmit` passes

---

## Agent 5: Footer & Misc UI (worktree: `fix-misc-ui`)

### Files you own:
- `hookcut-frontend/src/components/footer.tsx`

### Tasks:

**5.1 Fix dead footer links**
In `src/components/footer.tsx`:
- Social links (Twitter, YouTube, LinkedIn) currently render with icons but the hrefs are likely `#`. Change to:
  - Add `aria-disabled="true"` and a `title="Coming soon"` tooltip on each
  - OR use real placeholder URLs if social accounts exist
- `/case-studies` link — this page likely doesn't exist. Change to point to `/blog` with label "Blog & Case Studies". Or keep the link and add a TODO for creating the page.

**5.2 Verify social link markup**
Read `footer.tsx` fully. The social links section (likely near the bottom) should render the Twitter, Youtube, Linkedin icons from lucide-react. Ensure they have proper `aria-label`s ("Follow us on Twitter", etc.) and `target="_blank"` + `rel="noopener noreferrer"` for external links.

### Verification:
- Footer social links are clearly marked as "coming soon" or point to real URLs
- No broken `/case-studies` 404
- `npx tsc --noEmit` passes

---

## Merge Order & Final Verification

After all 5 agents complete:

1. Merge in this order (least conflict risk first):
   - Agent 5 (footer/misc) → main
   - Agent 4 (content pages) → main
   - Agent 2 (pricing/metadata) → main
   - Agent 3 (admin fix) → main
   - Agent 1 (nav/header/dashboard-as-home) → main (last, since it touches the most files and has the architectural change)

2. After all merges, run:
   ```bash
   cd hookcut-frontend && npx tsc --noEmit && npm run build
   ```

3. Manual smoke test checklist:
   - [ ] Unauthenticated: Homepage → marketing page with correct pricing (Lite, not Starter)
   - [ ] Unauthenticated: `/pricing` → all 3 plan cards load (no 401)
   - [ ] Unauthenticated: `/clip` → redirects to login WITH `callbackUrl=/clip`
   - [ ] Authenticated: `/` → redirects to `/dashboard` (not the old AuthenticatedHome)
   - [ ] Authenticated: Dashboard shows URL input, credit ring, stats, session history, Manual Clip button
   - [ ] Authenticated: All pages show global header (dashboard, settings, clip, admin)
   - [ ] Authenticated: Nav "Features" goes to `/features`, "Pricing" goes to `/pricing`
   - [ ] Admin: User dropdown shows "Admin Panel" link
   - [ ] Admin: `/admin` loads the admin dashboard (not redirect to `/`)
   - [ ] Clip page: Shows credit balance, back-to-dashboard link, header
   - [ ] Page titles: "Dashboard | HookCut" (not doubled)
   - [ ] No YouTube thumbnail 404s in console
   - [ ] How It Works: mentions manual clipper
   - [ ] Homepage + /pricing use shared PLANS data (single source of truth)
   - [ ] Footer: social links handled, no broken /case-studies link
