# HookCut — Claude Code Project Instructions

## Project Overview
HookCut extracts hook segments from YouTube videos → generates YouTube Shorts.
- **Backend**: FastAPI + Celery + Redis + Supabase PostgreSQL → `hookcut-backend/`
- **Frontend**: Next.js 16 + Tailwind 4 + TypeScript → `hookcut-frontend/`
- See `hookcut-backend/CLAUDE.md` and `hookcut-frontend/CLAUDE.md` for layer-specific rules.

## Architecture (high-level)
```
URL → validate → analyze (Celery) → transcript cascade → LLM hook identification → 5 hooks
→ user selects 1-3 (with caption style + optional trim) → Short generation (Celery per hook)
→ yt-dlp + FFmpeg → inline video preview → download
```

## Admin System
- RBAC: `get_admin_user` dependency in `dependencies.py` → requires `User.role == "admin"`
- 21 endpoints under `/api/admin/` (routers/admin.py)
- AdminService (22 methods) in services/admin_service.py
- Rule engine: 17 base rules (A-Q) + custom, versioned, revertable
- NARM: LLM-powered insights from LearningLog data
- Audit: All admin actions tracked with before/after state

## Cross-Cutting Rules
- **Contract-first**: Every package has a `CONTRACTS.md`. Read it before modifying that package.
- **Never commit `.env`** or files containing secrets
- **Run typecheck after schema changes**: Backend Pydantic changes must sync with frontend types
- **Spec-driven workflow**: For multi-step features, write a spec in `.claude/specs/in-progress/` first
- **One task per session**: Use `/clear` between distinct tasks

## Critical Invariants (never violate)
- SQLite path must be absolute for Celery: `sqlite:////absolute/path/hookcut.db`
- Never use `shlex.quote()` with list-mode `subprocess.run()`
- Credits deducted AFTER session creation (Transaction needs real session_id)
- Gemini `maxOutputTokens` needs 2x buffer (thinking tokens consume budget)
- FFmpeg concat filelist paths must be quoted: `file '{path}'`

## Code Conventions
- SQLAlchemy 2.0: `db.get(Model, id)` not `db.query(Model).get(id)`
- No bare `except: pass` — always log inner exceptions
- Raise only exceptions from `app/exceptions.py`
- `APP_VERSION` constant in main.py (no duplicate strings)
- Shared task constants in `celery_app.py`: `ERROR_MSG_MAX_LEN`, `FREE_MONTHLY_MINUTES`, `DOWNLOAD_URL_EXPIRES_SECONDS`
- React components: use `memo()` for list items, `useMemo` for derived values, `useCallback` for handlers
- Frontend types single source of truth: `src/lib/types.ts`

## V1 Features (March 2026)
- 4 caption style presets (Clean, Bold, Neon, Minimal)
- Hook boundary trimming (±10s)
- Inline video preview before download
- Enhanced "Why It Works" (platform dynamics, viewer psychology, creator tips — always visible)
- Analysis speed badge + elapsed timer
- 18 hook types, 7-dimension scoring, 6 funnel roles
- Gemini 2.5 Flash (primary) → Claude Sonnet 4 (fallback) → GPT-4o (tertiary)

## Slash Commands
- `/edit-task` — context-loaded editing for Celery tasks
- `/edit-service` — context-loaded editing for services
- `/edit-router` — context-loaded editing for routers
- `/edit-llm` — context-loaded editing for LLM layer
- `/staff-swe` — full Staff SWE audit

## Slash Command Loader
When a slash command `/X` is used:
1. Look for `.claude/commands/X.md`
2. If found: read completely, follow strictly
3. If not found: inform user it's undefined
