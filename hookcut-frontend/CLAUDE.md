# HookCut Frontend — Claude Code Instructions

## Stack
Next.js 16, React 19, Tailwind CSS 4, TypeScript 5, shadcn/ui, NextAuth.js (Google OAuth)

## Architecture
- Server components by default, `'use client'` only for interactivity
- All API calls go through `src/lib/api.ts` — never call fetch() directly
- Types in `src/lib/types.ts` — single source of truth
- State machine in `page.tsx`: input → analyzing → hooks → shorts
- Constants in `src/lib/constants.ts` — `SESSION_STATUS`, `HOOK_TYPE_DESCRIPTIONS`, `CAPTION_STYLES`

## Type Contract
- `TYPE_AUDIT.md` maps every TS interface to its backend Pydantic model
- **When backend schemas change**: update corresponding types in `types.ts`
- Future: OpenAPI codegen will auto-generate these (see TYPE_AUDIT.md §6)

## Key Patterns
- Polling: `usePollTask` (analysis) and `useShortPoller` (shorts) with exponential backoff
- `POLL_CONFIG`: 1s initial, 1.5x multiplier, 5s max interval
- Score display: `score-bar.tsx` hardcodes 7 dimension keys — must match backend `HookScores`
- Dark glass-morphism theme throughout
- `React.memo()` on list item components (`SessionRow`, `HookCard`) for performance
- `useMemo` / `useCallback` for expensive computations and stable references
- Search debounce (250ms) in dashboard via `useRef` timer
- Admin role guard pattern: layout.tsx fetches `api.getProfile()`, checks `role === "admin"`, redirects non-admins
- Admin sidebar uses `usePathname()` for active link highlighting with `motion.div layoutId`

## V1 Features (Frontend)
- **Caption style picker**: 4 visual preview cards in `hooks-step.tsx` (clean, bold, neon, minimal)
- **Trim controls**: `trim-slider.tsx` — ±10s boundary adjustment per selected hook
- **Hook insights always visible**: `hook-card.tsx` shows platform_dynamics, viewer_psychology, improvement_suggestion without collapsing
- **Hook type descriptions**: `HOOK_TYPE_DESCRIPTIONS` map in `constants.ts` (18 one-line descriptions)
- **Inline video preview**: `shorts-step.tsx` uses HTML5 `<video>` player instead of thumbnail-only
- **Analysis speed badge**: Elapsed timer in `progress-step.tsx`, "Analysis Time" stat in `hooks-step.tsx`
- 7 admin pages under `src/app/admin/` (layout, dashboard, users, sessions, rules, models, audit)
- 13 admin TypeScript types in `src/lib/types.ts`
- 18 admin API methods in `src/lib/api.ts`
- `/admin/:path*` route protection in `proxy.ts`

## Key Components
- `hook-card.tsx` — Hook display with scores, insights, type description
- `hooks-step.tsx` — Hook selection, caption style picker, trim controls
- `shorts-step.tsx` — Short preview with video player, download
- `progress-step.tsx` — Analysis progress with elapsed timer
- `trim-slider.tsx` — Dual time adjuster for hook boundaries
- `score-bar.tsx` — 7-dimension score visualization
- `app/admin/layout.tsx` — Admin layout with sidebar nav + role-based access guard
- `app/admin/page.tsx` — Dashboard: stats cards, recent sessions, NARM insights
- `app/admin/users/page.tsx` — User table with role management
- `app/admin/sessions/page.tsx` — Session browser with expandable detail panels
- `app/admin/rules/page.tsx` — Prompt rule editor with version history + preview
- `app/admin/models/page.tsx` — Provider config cards with primary/fallback switching
- `app/admin/audit/page.tsx` — Audit log table with JSON diff + export

## Known Issues (from TYPE_AUDIT.md)
- `Hook.scores` should be typed `HookScores` not `Record<string, number>` (MEDIUM)
- `SHORT_STATUS` duplicated between frontend const and backend model comment

## Build
```bash
# Must use Node 22 (not 25) for Next.js 16
npm run dev      # development
npm run build    # production build
npm run lint     # eslint
```
