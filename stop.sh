#!/bin/bash

# HookCut — Stop all services

echo "Stopping app services..."
overmind quit 2>/dev/null || true

echo "Stopping infrastructure..."
brew services stop postgresql@16 2>/dev/null || true
brew services stop redis 2>/dev/null || true

echo "Done."
