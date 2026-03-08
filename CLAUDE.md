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

## Response Protocol (applies to EVERY query, in ALL Claude interfaces — CLI, browser, desktop, API)
- **Before starting any task**, provide:
  1. **Estimated token usage**: approximate input+output tokens needed (e.g., "~5K tokens" or "~50K tokens")
  2. **Estimated time**: how long the task will likely take (e.g., "~30 seconds" or "~5 minutes")
- Format: a short line at the top of your response, e.g., `**Estimate: ~8K tokens · ~2 min**`
- For simple questions, keep it brief: `**Estimate: ~1K tokens · ~10s**`
- If the task scope grows beyond the original estimate, flag it immediately and re-estimate before continuing

## Cross-Cutting Rules
- **Contract-first**: Every package has a `CONTRACTS.md`. Read it before modifying that package.
- **Never commit `.env`** or files containing secrets
- **Run typecheck after schema changes**: Backend Pydantic changes must sync with frontend types
- **Spec-driven workflow**: For multi-step features, write a spec in `.claude/specs/in-progress/` first
- **One task per session**: Use `/clear` between distinct tasks

## Tool Discipline (prevent runaway sessions)
- **NEVER run concurrent `npm install`, `rm -rf node_modules`, or `mv node_modules`** — concurrent filesystem operations on node_modules corrupt it and create an unrecoverable spiral
- **One package manager operation at a time**: Wait for the previous `npm install` / `npm ci` to fully complete before starting another
- **NEVER run `rm -rf node_modules` in the background** — it takes minutes on macOS and blocks all subsequent npm operations. If node_modules needs to be deleted, ask the user to do it in their terminal
- **Environment issues get 2 attempts max**: If `npm install` or `npm run dev` fails twice, stop and ask the user to fix it manually. Do NOT keep retrying with escalating force — each retry makes it worse
- **Prefer foreground for destructive commands**: `rm -rf`, `mv`, and `npm install` must run in the foreground (not `run_in_background`) so you can see the result before proceeding
- **Hand off to the user early**: If a local environment problem (port conflicts, corrupted deps, build tool hangs) is not resolved in 2 attempts, give the user the exact commands and stop

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
