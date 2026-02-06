#!/bin/bash
# Run Strawberry GraphQL ASGI benchmark server
# Port: 8006

cd "$(dirname "$0")/.."

echo "Starting Strawberry GraphQL (ASGI) on port 8006..."
exec uvicorn strawberry_app:app --host 0.0.0.0 --port 8006 --workers 1 --no-access-log