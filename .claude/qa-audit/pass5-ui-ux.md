# HookCut UI/UX Audit — Pass 5

**Date**: 2026-03-07
**Scope**: Direct code review of all key frontend pages and components
**Files Read**: `page.tsx` (home), `pricing/page.tsx`, `auth/login/page.tsx`, `dashboard/page.tsx` (via pass1b), `header.tsx`, `proxy.ts`, frontend CLAUDE.md, all app routes enumerated

---

## Summary: 14 UX Issues Found

| # | Severity | Location | Issue |
|---|----------|----------|-------|
| UX-01 | CRITICAL | `dashboard/page.tsx` | React hooks crash on auth state change |
| UX-02 | HIGH | `short-card.tsx` | Silent short generation failures |
| UX-03 | HIGH | `header.tsx` | Dashboard link missing for non-admin users |
| UX-04 | MEDIUM | `/pricing` route | Requires login to view public pricing |
| UX-05 | MEDIUM | Marketing/demo sections | Mock/placeholder thumbnails look unfinished |
| UX-06 | MEDIUM | `auth/login/page.tsx` | Fake testimonials on login page |
| UX-07 | MEDIUM | `pricing/page.tsx` | Checkout errors silently swallowed |
| UX-08 | MEDIUM | `auth/login/page.tsx` | callbackUrl hardcoded to "/" |
| UX-09 | MEDIUM | Admin pages | Generic "Failed to load data" toast for all errors |
| UX-10 | LOW | `progress-step.tsx` | Elapsed timer never stops after completion |
| UX-11 | LOW | `ai-hook-finder/error.tsx` | Light theme on dark app |
| UX-12 | LOW | `header.tsx` | Mobile menu close animation missing |
| UX-13 | LOW | `layout.tsx` | nonce="undefined" in HTML |
| UX-14 | LOW | `auth/login/page.tsx` | Terms/Privacy are span not a |

---

## UX-05 — Mock/Placeholder Thumbnails (User-Flagged)

**Files**: Marketing home component, hooks-step demo areas
**Issue**: The product demo sections use static placeholder or mock YouTube thumbnails. On a product whose core value is "we analyze YouTube videos", fake thumbnails directly undermine credibility and conversion.
**Fix**: Use real YouTube thumbnails via `https://img.youtube.com/vi/{videoId}/maxresdefault.jpg`. Choose a well-known creator video. Add a looping screen recording or real analysis screenshot.

---

## UX-06 — Fake Testimonials on Login Page

**Files**: `hookcut-frontend/src/app/auth/login/page.tsx:9-25`
**Evidence**: Three hardcoded testimonials from "Alex M.", "Sarah K.", "James T." with specific quantified claims — but per audit briefing, there are no customers yet (pre-launch).
**Legal Risk**: Fabricated testimonials violate FTC Guides on Endorsements (US) and Consumer Protection Act 2019 Section 2(1)(r) (India).
**Fix**: Replace with factual product benefit statements, or remove until real user quotes exist.

---

## Design Observations

**What Works Well**:
- Dark glass-morphism theme consistent and polished across all public pages
- Pricing page gradient card borders are visually strong
- Login page card is clean with good spacing
- Google OAuth button uses official colored "G" mark
- FAQ accordion with AnimatePresence is well-implemented
- SEO comparison pages (5 alternative pages) add good discovery surface

**Needs Attention**:
- Login page orbs use brand red (#E84A2F) but main app uses violet/purple — minor inconsistency
- Pricing: 120 free minutes vs 100 paid Lite minutes — confusing value proposition
- callbackUrl hardcoded to "/" loses user upgrade intent (clicking Upgrade -> Login -> Home)

---

## Accessibility Summary

| Issue | Location | WCAG |
|-------|----------|------|
| Terms/Privacy `<span>` not `<a>` | login/page.tsx | A |
| Admin modals missing `role="dialog"` | admin pages | A |
| No focus trap in admin modals | admin pages | AA |
| Testimonial carousel dots no aria-label | login/page.tsx | AA |

---

## Route Audit

| Route | Public? | Status |
|-------|---------|--------|
| `/` | YES | OK |
| `/pricing` | NO — redirects to login | BUG (should be public) |
| `/ai-hook-finder` | YES | OK |
| `/auth/login` | YES | OK |
| `/dashboard` | NO — requires auth | Correct |
| `/admin/*` | NO — auth + role | Role check client-side only (HIGH-04) |
| `/features`, `/how-it-works`, `/blog` | YES | OK |
| `/*-alternative` (5 SEO pages) | YES | OK |
