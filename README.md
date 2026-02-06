# Python API Framework Benchmark (REST + GraphQL)

> **Extended from:** [fastapi-vs-litestar-vs-django-bolt-vs-django-ninja-benchmarks](https://github.com/FarhanAliRaza/fastapi-vs-litestar-vs-django-bolt-vs-django-ninja-benchmarks)
> **Additions:** Django REST Framework + GraphQL (Graphene v3, Graphene v2, Strawberry)

![Framework Benchmark](graphs/benchmark_combined.png)

> **Disclaimer:** This is an informal benchmark run on a local development machine without proper isolation. It does not follow benchmarking best practices such as Docker containerization, CPU pinning, or elimination of background process interference. Results may vary significantly in production environments. Take these numbers as a rough indicator, not absolute truth.

---

## What’s Included

REST frameworks:
- **[FastAPI](https://github.com/fastapi/fastapi)** - ASGI framework with Pydantic
- **[Litestar](https://github.com/litestar-org/litestar)** - High-performance ASGI framework
- **[Django Ninja](https://github.com/vitalik/django-ninja)** - Django + Pydantic API framework
- **[Django Bolt](https://github.com/FarhanAliRaza/django-bolt)** - Rust-powered Django API framework
- **[Django REST Framework](https://github.com/encode/django-rest-framework)** - Traditional Django REST API framework

GraphQL frameworks:
- **[Graphene v3](https://github.com/graphql-python/graphene-django)** - Django + Graphene (v3)
- **[Graphene v2](https://github.com/graphql-python/graphene-django)** - Django + Graphene (v2, separate venv)
- **[Strawberry FastAPI](https://github.com/strawberry-graphql/strawberry)** - ASGI GraphQL (FastAPI)
- **[Strawberry Django](https://github.com/strawberry-graphql/strawberry)** - Django + Strawberry (Django integration)

Infrastructure notes:
- Graphene v2 and v3 both use the same minimal Django settings (`django_project/settings_graphql.py`) for a fair comparison.
- Strawberry reads/writes the same SQLite DB file (`django_benchmark.db`) and uses a table that mirrors Django’s `benchmark_users`.

---

## Endpoints

REST:

| Endpoint    | Description                   |
| ----------- | ----------------------------- |
| `/json-1k`  | Returns ~1KB JSON response    |
| `/json-10k` | Returns ~10KB JSON response   |
| `/db`       | 10 reads from SQLite database |
| `/slow`     | Mock API with 2 second delay  |
| `/nplus1`   | Batch-loaded related data     |
| `/mutate`   | Mutation (write) test         |

GraphQL (POST `/graphql`):

| Query    | Description                          |
| -------- | ------------------------------------ |
| `json1k` | Returns ~1KB JSON response           |
| `json10k`| Returns ~10KB JSON response          |
| `users`  | 10 reads from SQLite database        |
| `slow`   | Mock API with 2 second delay         |
| `nplus1` | N+1 style test with batched resolving|

---

## Requirements

- Python 3.12+ for the main environment
- Python 3.10 (or lower) for Graphene v2 venv
- [uv](https://github.com/astral-sh/uv) package manager
- [bombardier](https://github.com/codesenberg/bombardier) HTTP benchmarking tool

Install bombardier:

```bash
go install github.com/codesenberg/bombardier@latest
```

If `bombardier` is installed but not found, add Go's bin to your PATH:

```bash
export PATH="$(go env GOPATH)/bin:$PATH"
```

---

## Quick Start

```bash
# Setup (run once)
./scripts/setup.sh

# Optional: set up Graphene v2 venv (runs on port 8007)
PYTHON_BIN=python3.10 ./scripts/setup_graphene_v2.sh

# Run all benchmarks (will include Graphene v2 if venv exists)
./scripts/run_all.sh

# Run GraphQL-only benchmarks (Graphene v2/v3 + Strawberry Django)
./scripts/run_graphql.sh

# Short run (no long tests, fewer warmups)
./scripts/run_all.sh -d 5 -w 200 -r 1

# Or with custom options
./scripts/run_all.sh -c 200 -d 15 -r 5
```

Notes:
- Server logs are written to `.benchmark_logs/` to reduce console noise.
- Graphene v2 runs in a separate venv at `.venv-graphene-v2`.
- Graphene v2 and v3 use the same minimal Django settings module for GraphQL benchmarks.
- Graphene v3 runs on port 8008. Graphene v2 runs on port 8007. Strawberry FastAPI runs on port 8006. Strawberry Django runs on port 8009.
- A GraphQL-only combined graph is generated as `graphs/benchmark_combined_graphql.png` when `./scripts/run_all.sh` is used.

---

## Manual Usage

### 1. Setup

```bash
./scripts/setup.sh
```

### 2. Start Servers (in separate terminals)

```bash
./scripts/run_fastapi.sh   # Port 8001
./scripts/run_litestar.sh  # Port 8002
./scripts/run_ninja.sh     # Port 8003
./scripts/run_bolt.sh      # Port 8004
./scripts/run_drf.sh       # Port 8005
./scripts/run_strawberry.sh        # Port 8006 (Strawberry FastAPI)
./scripts/run_graphene_v2.sh       # Port 8007 (requires .venv-graphene-v2)
./scripts/run_graphene_v3.sh       # Port 8008
./scripts/run_strawberry_django.sh # Port 8009
```

### 3. Run Benchmark

```bash
uv run python bench.py
```

---

## Benchmark Options

```
-c, --connections  Concurrent connections (default: 100)
-d, --duration     Duration per endpoint in seconds (default: 10)
-w, --warmup       Warmup requests (default: 1000)
-r, --runs         Runs per endpoint (default: 3)
-o, --output       Output file (default: BENCHMARK_RESULTS.md)
--frameworks       Frameworks to benchmark (default: all)
--skip-slow        Skip the /slow endpoint
--graphql-combined-graph  Generate graphs/benchmark_combined_graphql.png
```

---

## Server Ports

| Framework     | Port |
| ------------- | ---- |
| FastAPI       | 8001 |
| Litestar      | 8002 |
| Django Ninja  | 8003 |
| Django Bolt   | 8004 |
| Django DRF    | 8005 |
| Strawberry FastAPI | 8006 |
| Graphene v2   | 8007 |
| Graphene v3   | 8008 |
| Strawberry Django | 8009 |

---

## Results & Graphs

Generated artifacts:
- `BENCHMARK_RESULTS.md` for the latest run summary.
- `graphs/benchmark_combined.png` for all frameworks.
- `graphs/benchmark_combined_graphql.png` for GraphQL-only comparisons (graphene v2/v3 + strawberry-django).
- Per-endpoint graphs like `graphs/benchmark_json_1k.png`, `graphs/benchmark_db.png`, etc.

---

## How It Works

High-level flow:
1. Start the selected framework servers.
2. Warm up each endpoint/query to avoid cold-start bias.
3. Run `bombardier` against each endpoint/query for a fixed duration.
4. Capture best-of-N runs, then emit `BENCHMARK_RESULTS.md`.
5. Generate per-endpoint graphs plus combined summaries.

The benchmark runner lives in `bench.py`, and `scripts/run_all.sh` / `scripts/run_graphql.sh` orchestrate server startup and teardown.
