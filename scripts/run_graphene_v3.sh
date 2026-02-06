#!/bin/bash
# Run Graphene v3 (Django GraphQL) ASGI benchmark server
# Port: 8008

cd "$(dirname "$0")/.."

echo "Starting Graphene v3 GraphQL (ASGI) on port 8008..."
exec uvicorn graphene_app:application --host 0.0.0.0 --port 8008 --workers 1 --no-access-log
