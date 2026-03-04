# Edit Service Module

You are editing files in `hookcut-backend/app/services/`.

## Before Making ANY Changes
1. Read `hookcut-backend/app/services/CONTRACTS.md` completely
2. Read `hookcut-backend/app/llm/CONTRACTS.md` — if the service calls LLM providers
3. Read `hookcut-backend/app/schemas/` — Pydantic models you consume/return
4. Read the specific service file you're modifying

## Rules
- Do NOT change public method signatures without updating services/CONTRACTS.md
- All public methods must have return type annotations
- Raise only exceptions defined in `app/exceptions.py`
- Services own all business logic — routers must NOT contain business logic
- CreditManager deduction order: paid → PAYG → free (never change)
- HookEngine must return exactly 5 hooks — this is an invariant
- Score values must be clamped to [0, 10]
- TranscriptService cascade: youtube-transcript-api → yt-dlp → Whisper (never reorder)
- Use `db.get(Model, id)` not `db.query(Model).get(id)` (SQLAlchemy 2.0)
- No bare `except: pass` — always log inner exceptions
- After changes, update services/CONTRACTS.md if any public interface changed
