#!/bin/bash
set -e

echo "=== HookCut Backend Starting ==="
echo "PORT: $PORT"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'NO')"
echo "REDIS_URL set: $([ -n "$REDIS_URL" ] && echo 'yes' || echo 'NO')"
echo "GEMINI_API_KEY set: $([ -n "$GEMINI_API_KEY" ] && echo 'yes' || echo 'NO')"
echo "NEXTAUTH_SECRET set: $([ -n "$NEXTAUTH_SECRET" ] && echo 'yes' || echo 'NO')"

echo "=== Running Alembic migrations ==="
alembic upgrade head 2>&1 || echo "WARNING: Alembic migration failed (continuing anyway)"

echo "=== Starting Uvicorn on port ${PORT:-8000} ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --log-level info
