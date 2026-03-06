#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
PYTHON="$(pwd)/.venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
  echo "Error: .venv not found. Run: python3 -m venv .venv && pip install -e ."
  exit 1
fi

# Kill all background jobs on Ctrl+C or exit
cleanup() {
  echo ""
  echo "Shutting down..."
  kill 0
}
trap cleanup EXIT INT TERM

# Start Redis if not already running
if ! redis-cli ping &>/dev/null; then
  echo "[redis] Starting..."
  redis-server --daemonize yes --logfile /tmp/hookcut-redis.log
  echo "[redis] Started"
else
  echo "[redis] Already running"
fi

# Start Celery worker in background
echo "[celery] Starting worker..."
"$PYTHON" -m celery -A app.tasks.celery_app worker --loglevel=info 2>&1 | sed 's/^/[celery] /' &

# Start Celery beat in background
echo "[beat] Starting scheduler..."
"$PYTHON" -m celery -A app.tasks.celery_app beat --loglevel=info 2>&1 | sed 's/^/[beat]   /' &

# Give workers a moment to boot
sleep 1

# Start FastAPI in foreground (blocking)
echo "[api] Starting uvicorn on http://127.0.0.1:8000 ..."
"$PYTHON" -m uvicorn app.main:app --reload --port 8000 --reload-exclude ".venv" 2>&1 | sed 's/^/[api]    /'
