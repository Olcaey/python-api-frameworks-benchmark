#!/bin/bash
# Run GraphQL benchmark servers and execute GraphQL-only benchmark
# Starts Strawberry, Graphene v3, and Graphene v2 (if available).

set -e

cd "$(dirname "$0")/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# PID file to track servers
PID_FILE=".benchmark_graphql_pids"

cleanup() {
    echo -e "\n${YELLOW}Stopping servers...${NC}"
    if [ -f "$PID_FILE" ]; then
        while read pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    echo -e "${GREEN}Cleanup complete${NC}"
}

trap cleanup EXIT INT TERM

echo -e "${GREEN}=== GraphQL Framework Benchmark ===${NC}"
echo ""

# Check if bombardier is installed
if ! command -v bombardier &> /dev/null; then
    if command -v go &> /dev/null; then
        export PATH="$(go env GOPATH)/bin:$PATH"
    fi
fi

if ! command -v bombardier &> /dev/null; then
    echo -e "${RED}ERROR: bombardier not found${NC}"
    echo "Install with: go install github.com/codesenberg/bombardier@latest"
    exit 1
fi

# Clear old PIDs
rm -f "$PID_FILE"

# Log directory for server output
LOG_DIR=".benchmark_logs"
mkdir -p "$LOG_DIR"

# Start Strawberry Django ASGI
echo -e "${YELLOW}Starting Strawberry Django ASGI on port 8009...${NC}"
uv run uvicorn strawberry_django_app:application --host 0.0.0.0 --port 8009 --workers 1 --no-access-log \
    > "$LOG_DIR/strawberry_django.log" 2>&1 &
echo $! >> "$PID_FILE"

# Start Graphene v2 ASGI (separate venv)
GRAPHENE_V2_VENV=".venv-graphene-v2"
GRAPHENE_V2_UVICORN="$GRAPHENE_V2_VENV/bin/uvicorn"
graphene_v2_expected=false
if [ -x "$GRAPHENE_V2_UVICORN" ]; then
    echo -e "${YELLOW}Starting Graphene v2 ASGI on port 8007...${NC}"
    "$GRAPHENE_V2_UVICORN" graphene_v2_app:application --host 0.0.0.0 --port 8007 --workers 1 --no-access-log \
        > "$LOG_DIR/graphene_v2.log" 2>&1 &
    echo $! >> "$PID_FILE"
    graphene_v2_expected=true
else
    echo -e "${YELLOW}Graphene v2 venv not found at $GRAPHENE_V2_VENV (skipping).${NC}"
    echo -e "${YELLOW}Run ./scripts/setup_graphene_v2.sh to enable Graphene v2 benchmarks.${NC}"
fi

# Start Graphene v3 ASGI
echo -e "${YELLOW}Starting Graphene v3 ASGI on port 8008...${NC}"
uv run uvicorn graphene_app:application --host 0.0.0.0 --port 8008 --workers 1 --no-access-log \
    > "$LOG_DIR/graphene_v3.log" 2>&1 &
echo $! >> "$PID_FILE"

# Wait for servers to start
echo ""
echo -e "${YELLOW}Waiting for servers to start...${NC}"
sleep 5

check_graphql_server() {
    local name=$1
    local port=$2
    local query='{"query":"query { json1k { id name } }"}'
    if curl -s -X POST -H "Content-Type: application/json" -d "$query" "http://127.0.0.1:${port}/graphql" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name (port $port)"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name (port $port) - NOT RESPONDING"
        return 1
    fi
}

echo ""
echo "Checking servers:"
all_ok=true
check_graphql_server "Strawberry Django ASGI" 8009 || all_ok=false
check_graphql_server "Graphene v3 ASGI" 8008 || all_ok=false

graphene_v2_available=false
if check_graphql_server "Graphene v2 ASGI" 8007; then
    graphene_v2_available=true
else
    if [ "$graphene_v2_expected" = true ]; then
        all_ok=false
    else
        echo -e "  ${YELLOW}i${NC} Graphene v2 not detected on port 8007 (skipping)"
    fi
fi

if [ "$all_ok" = false ]; then
    echo ""
    echo -e "${RED}Some servers failed to start. Check the logs above.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All servers running!${NC}"
echo ""

# Run benchmark
echo -e "${YELLOW}Running benchmark...${NC}"
echo ""
frameworks=(graphene-v3 strawberry-django)
if [ "$graphene_v2_available" = true ]; then
    frameworks+=(graphene-v2)
fi
uv run python bench.py --skip-slow --frameworks "${frameworks[@]}" "$@"

echo ""
echo -e "${GREEN}Benchmark complete!${NC}"
