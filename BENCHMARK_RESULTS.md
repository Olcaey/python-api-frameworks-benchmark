# Framework Benchmark Results

**Date:** 2025-12-25 20:05:52

## Configuration

- Connections: 100
- Duration: 10s per endpoint
- Warmup: 1000 requests
- Runs: 3 (best result taken)

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/json-1k` | ~1KB JSON response |
| `/json-10k` | ~10KB JSON response |
| `/db` | 10 database reads |
| `/slow` | 2 second mock delay |

## Results

### /json-1k

| Framework | RPS | Latency (avg) | Latency (p99) | Errors |
|-----------|----:|-------------:|-------------:|-------:|
| django-bolt | 39,157 | 0.00ms | 0.00ms | 0 |
| litestar | 35,398 | 0.00ms | 0.00ms | 0 |
| fastapi | 13,726 | 0.01ms | 0.00ms | 0 |
| django-ninja | 3,037 | 0.03ms | 0.00ms | 0 |
| django-drf | 1,951 | 0.05ms | 0.00ms | 0 |

### /json-10k

| Framework | RPS | Latency (avg) | Latency (p99) | Errors |
|-----------|----:|-------------:|-------------:|-------:|
| django-bolt | 29,857 | 0.00ms | 0.00ms | 0 |
| litestar | 27,820 | 0.00ms | 0.00ms | 0 |
| django-ninja | 2,652 | 0.04ms | 0.00ms | 0 |
| fastapi | 2,565 | 0.04ms | 0.00ms | 0 |
| django-drf | 1,702 | 0.06ms | 0.00ms | 0 |

### /db

| Framework | RPS | Latency (avg) | Latency (p99) | Errors |
|-----------|----:|-------------:|-------------:|-------:|
| django-bolt | 5,263 | 0.02ms | 0.00ms | 0 |
| django-drf | 1,489 | 0.07ms | 0.00ms | 0 |
| fastapi | 1,465 | 0.07ms | 0.00ms | 0 |
| litestar | 1,456 | 0.07ms | 0.00ms | 0 |
| django-ninja | 982 | 0.10ms | 0.00ms | 0 |

## Summary (RPS by Endpoint)

| Framework | /json-1k | /json-10k | /db |
|-----------|--------:|--------:|--------:|
| fastapi | 13,726 | 2,565 | 1,465 |
| litestar | 35,398 | 27,820 | 1,456 |
| django-bolt | 39,157 | 29,857 | 5,263 |
| django-ninja | 3,037 | 2,652 | 982 |
| django-drf | 1,951 | 1,702 | 1,489 |
