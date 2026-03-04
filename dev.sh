#!/bin/bash
set -e

# HookCut — One-command development startup
# Starts Postgres + Redis via Homebrew, app services via Overmind

# Check dependencies
if ! command -v overmind &> /dev/null; then
    echo "overmind not found. Install with: brew install overmind tmux"
    exit 1
fi

# Install Postgres if missing
if ! brew list postgresql@16 &>/dev/null; then
    echo "Installing PostgreSQL 16..."
    brew install postgresql@16
fi

# Install Redis if missing
if ! brew list redis &>/dev/null; then
    echo "Installing Redis..."
    brew install redis
fi

# Kill stale processes on required ports
for port in 8000 3000; do
    pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo "Killing stale process on port $port (pid $pid)..."
        kill $pid 2>/dev/null || true
        sleep 1
    fi
done

# Clean up stale overmind socket
rm -f .overmind.sock

# Start infrastructure via Homebrew services
echo "Starting infrastructure..."
brew services start postgresql@16 2>/dev/null || true
brew services start redis 2>/dev/null || true

# Wait for Redis to be ready
for i in $(seq 1 10); do
    if redis-cli ping &>/dev/null; then
        break
    fi
    sleep 1
done

echo "Starting app services (backend + worker + beat + frontend)..."
echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "  Useful commands:"
echo "    overmind connect backend   — attach to backend (for debugging)"
echo "    overmind restart worker    — restart just the worker"
echo "    ./stop.sh                  — stop everything"
echo ""

overmind start -f Procfile.dev -N
