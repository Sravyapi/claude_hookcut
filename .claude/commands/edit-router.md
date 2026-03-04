# Edit Router Module

You are editing files in `hookcut-backend/app/routers/`.

## Before Making ANY Changes
1. Read `hookcut-backend/app/routers/CONTRACTS.md` completely
2. Read `hookcut-backend/app/services/CONTRACTS.md` — services you delegate to
3. Read the relevant `hookcut-backend/app/schemas/` files for request/response models
4. Read the specific router file you're modifying

## Rules
- Routers handle HTTP only — NO business logic in routers
- Always delegate to services for business logic
- Never import models directly for business operations — go through services
- Use Pydantic `response_model` on all endpoints (no bare `dict` returns)
- All errors must use `HTTPException` with status codes from routers/CONTRACTS.md
- Auth: use `Depends(get_current_user_id)` — never roll your own auth
- DB: use `Depends(get_db)` — never create sessions manually in routers
- Use `db.get(Model, id)` not `db.query(Model).get(id)` (SQLAlchemy 2.0)
- Webhooks verify signatures — never add auth middleware to webhook endpoints
- After changes, update routers/CONTRACTS.md if any endpoint interface changed
- If adding a new endpoint, add it to the Master Endpoint Table in CONTRACTS.md
