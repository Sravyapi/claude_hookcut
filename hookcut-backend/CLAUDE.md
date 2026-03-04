# HookCut Backend — Claude Code Instructions

## Layer Architecture
```
routers/ → tasks/ (Celery) → services/ → models/
                            → llm/ (providers + prompts)
```
Routers handle HTTP only. Services own business logic. Tasks orchestrate async work.

## Contract Files (READ BEFORE EDITING)
- `app/tasks/CONTRACTS.md` — Celery task signatures, state machines, Redis serialization, polling
- `app/services/CONTRACTS.md` — Service class APIs, return types, exceptions, dependencies
- `app/routers/CONTRACTS.md` — All endpoints, auth, request/response schemas, error mappings
- `app/llm/CONTRACTS.md` — Provider ABC, prompt system, constants registry, checklists

## Dependency Rules
- Routers import from: services, schemas, models, tasks (for .delay())
- Tasks import from: services, models, dependencies (get_db_session), celery_app (for shared constants)
- Services import from: models, llm, utils, other services
- LLM imports from: config only
- **Never**: router → model (for business logic), task → router, llm → services
- `AdminService` methods are all `@staticmethod` — call as `AdminService.method_name(db, ...)`
- Admin models import: `from app.models.admin import AdminAuditLog, PromptRule, ProviderConfig, NarmInsight`
- Admin RBAC: `from app.dependencies import get_admin_user`

## Shared Constants
`app/tasks/celery_app.py` exports shared constants used across task modules and routers:
- `ERROR_MSG_MAX_LEN = 500` — truncation limit for error messages stored in DB
- `FREE_MONTHLY_MINUTES = 120.0` — monthly free watermarked minutes per user
- `DOWNLOAD_URL_EXPIRES_SECONDS = 3600` — presigned URL TTL (1 hour)

Import pattern: `from app.tasks.celery_app import celery_app, ERROR_MSG_MAX_LEN`

## DB Session Patterns
- **Routers**: `db: Session = Depends(get_db)` (generator, auto-closed)
- **Tasks**: `db = get_db_session()` then `finally: db.close()` (manual lifecycle)
- **Never** mix these patterns
- Prefer relationship navigation (`short.session`) over separate `db.get()` calls

## V1 Features
- **Caption style presets**: 4 styles (clean, bold, neon, minimal) — `caption_style` on Short model
- **Hook boundary trimming**: ±10s adjustment via `time_overrides` on SelectHooksRequest
- **Improvement suggestions**: LLM-generated creator tips — `improvement_suggestion` on Hook model
- **Inline video preview**: Frontend uses presigned URLs for HTML5 video playback
- **Analysis speed badge**: Frontend-only elapsed timer
- Admin RBAC via `get_admin_user` dependency (returns 403 for non-admins)
- Rule engine: versioned prompt rules (A-Q base + custom), revertable
- Model management: provider switching, API key updates (keys in .env, not DB)
- NARM: LLM-powered insights from LearningLog aggregates
- Audit log: all admin actions with before/after JSON state
- 7 frontend admin pages under /admin/

## Testing
```bash
cd hookcut-backend
python -m pytest tests/ -q --tb=short          # all tests
python -m pytest tests/test_analysis.py -q      # one file
python -m ruff check app/                       # lint
```

## Key Files
- `app/exceptions.py` — Centralized exception hierarchy (all error types)
- `app/llm/prompts/constants.py` — NICHES, LANGUAGES, HOOK_TYPES, SCORE_DIMENSIONS, FUNNEL_ROLES
- `app/config.py` — Settings from environment variables
- `app/tasks/celery_app.py` — Celery config + shared constants (ERROR_MSG_MAX_LEN, FREE_MONTHLY_MINUTES, DOWNLOAD_URL_EXPIRES_SECONDS)
- `app/utils/ffmpeg_commands.py` — CAPTION_STYLES dict, VALID_CAPTION_STYLES, ASS subtitle generation
- `app/models/admin.py` — AdminAuditLog, PromptRule, ProviderConfig, NarmInsight
- `app/schemas/admin.py` — 24 Pydantic admin schemas
- `app/services/admin_service.py` — AdminService (22 static methods)
- `app/routers/admin.py` — 20 admin endpoints, prefix="/admin"
- `alembic/versions/007_add_admin_tables.py` — 4 new tables
