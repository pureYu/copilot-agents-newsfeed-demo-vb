#!/bin/sh
# Docker entrypoint: seed the database then start the application.
# seed_sources.py is idempotent - safe to run on every startup.
set -e

echo "[entrypoint] Seeding database sources (idempotent)..."
python seed_sources.py

echo "[entrypoint] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
