# HookCut Frontend

Next.js 16 frontend for HookCut — extract hook segments from YouTube videos and generate Shorts.

## Stack

- **Next.js 16** with App Router
- **React 19** with server components by default
- **Tailwind CSS 4** — dark glass-morphism theme
- **TypeScript 5** — strict mode
- **shadcn/ui** — component library
- **NextAuth.js** — Google OAuth authentication

## Prerequisites

- Node.js 22 (not 25 — Next.js 16 compatibility)
- npm

## Quick Start

```bash
cd hookcut-frontend
npm install
cp .env.example .env.local
# Edit .env.local — set NEXTAUTH_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, NEXT_PUBLIC_API_URL
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Architecture

```
src/
├── app/                    # Next.js pages
│   ├── page.tsx            # Main flow: input → analyzing → hooks → shorts
│   ├── dashboard/          # Session history + search
│   ├── auth/               # NextAuth sign-in/sign-out
│   └── admin/              # Admin pages (7)
│       ├── layout.tsx      # Sidebar layout + role guard
│       ├── page.tsx        # Dashboard
│       ├── users/page.tsx  # User management
│       ├── sessions/page.tsx # Session browser
│       ├── rules/page.tsx  # Prompt rule editor
│       ├── models/page.tsx # Provider management
│       └── audit/page.tsx  # Audit log viewer
├── components/             # UI components
│   ├── hook-card.tsx        # Hook display (scores, insights, type description)
│   ├── hooks-step.tsx       # Hook selection + caption picker + trim controls
│   ├── shorts-step.tsx      # Short preview (video player) + download
│   ├── progress-step.tsx    # Analysis progress with elapsed timer
│   ├── trim-slider.tsx      # ±10s boundary adjustment per hook
│   ├── score-bar.tsx        # 7-dimension score visualization
│   └── ...
└── lib/
    ├── api.ts              # All backend API calls (never use fetch directly)
    ├── types.ts            # TypeScript interfaces (single source of truth)
    ├── constants.ts        # SESSION_STATUS, HOOK_TYPE_DESCRIPTIONS, CAPTION_STYLES
    └── utils.ts            # Shared utilities
```

## Admin Features

- **Admin Dashboard**: Stats overview, recent sessions, NARM recommendations
- **Rule Engine UI**: Two-column editor with base/custom rules, version history, prompt preview
- **Model Management**: Provider cards with primary/fallback switching, API key updates
- **Audit Log**: Filterable table with expandable JSON diff rows, export to JSON

## Key Patterns

- **State machine**: `page.tsx` drives the flow: `input → analyzing → hooks → shorts`
- **Polling**: `usePollTask` (analysis) and `useShortPoller` (shorts) with exponential backoff
- **Performance**: `React.memo()` on list items, `useMemo`/`useCallback`, search debounce (250ms)
- **API client**: All calls go through `src/lib/api.ts` — never call `fetch()` directly

## Scripts

```bash
npm run dev      # Development server (http://localhost:3000)
npm run build    # Production build
npm run lint     # ESLint
```

## Environment Variables

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API URL (e.g., `http://localhost:8000`) |
| `NEXTAUTH_URL` | NextAuth callback URL (e.g., `http://localhost:3000`) |
| `NEXTAUTH_SECRET` | NextAuth JWT secret |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
