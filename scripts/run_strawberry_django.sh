#!/bin/bash
# Run Strawberry Django GraphQL ASGI benchmark server
# Port: 8009

cd "$(dirname "$0")/.."

echo "Starting Strawberry Django GraphQL (ASGI) on port 8009..."
exec uv run uvicorn strawberry_django_app:application --host 0.0.0.0 --port 8009 --workers 1 --no-access-log
