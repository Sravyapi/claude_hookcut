# Edit Celery Task Module

You are editing files in `hookcut-backend/app/tasks/`.

## Before Making ANY Changes
1. Read `hookcut-backend/app/tasks/CONTRACTS.md` completely
2. Read `hookcut-backend/app/services/CONTRACTS.md` — services you call
3. Read the specific task file you're modifying

## Rules
- Task results MUST match the schema in tasks/CONTRACTS.md
- Never call service methods not listed in services/CONTRACTS.md
- Credit deduction happens AFTER session creation — never reorder
- DB sessions use `get_db_session()` (non-generator), NOT `get_db()` (FastAPI-only)
- Always close DB sessions in `finally` blocks
- `run_analysis` catches ALL exceptions and returns SUCCESS to Celery — never change this pattern
- Status updates go to BOTH the DB column AND Celery meta (`self.update_state`)
- Use `db.get(Model, id)` not `db.query(Model).get(id)` (SQLAlchemy 2.0)
- No bare `except: pass` — always log inner exceptions
- After changes, verify the task's state machine transitions match CONTRACTS.md
