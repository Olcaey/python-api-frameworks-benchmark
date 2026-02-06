#!/bin/bash
# Run Graphene v2 (Django GraphQL) ASGI benchmark server
# Port: 8007
#
# NOTE: Ensure Graphene v2-compatible dependencies are installed in this env.

cd "$(dirname "$0")/.."

VENV_DIR=".venv-graphene-v2"
UVICORN_BIN="$VENV_DIR/bin/uvicorn"

if [ ! -x "$UVICORN_BIN" ]; then
    echo "ERROR: Graphene v2 venv not found at $VENV_DIR"
    echo "Run: ./setup_graphene_v2.sh"
    exit 1
fi

echo "Starting Graphene v2 GraphQL (ASGI) on port 8007..."
exec "$UVICORN_BIN" graphene_v2_app:application --host 0.0.0.0 --port 8007 --workers 1 --no-access-log
