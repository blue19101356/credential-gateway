#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Credential Gateway..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
