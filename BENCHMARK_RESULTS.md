# Framework Benchmark Results

**Date:** 2026-02-06 01:34:16

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
| `/nplus1` | Batch-loaded related data |
| `/mutate` | Mutation (write) test |

## Results

## Library Versions (Runtime by Framework)

| Framework | Package | Version |
|-----------|---------|---------|
| django-bolt | django | 6.0 |
| django-bolt | django-bolt | 0.4.7 |
| django-bolt | msgspec | 0.20.0 |
| django-bolt | python | 3.13.6 |
| django-bolt | uvicorn | 0.40.0 |
| django-drf | django | 6.0 |
| django-drf | djangorestframework | 3.16.1 |
| django-drf | python | 3.13.6 |
| django-drf | uvicorn | 0.40.0 |
| django-ninja | django | 6.0 |
| django-ninja | django-ninja | 1.5.1 |
| django-ninja | pydantic | 2.12.5 |
| django-ninja | python | 3.13.6 |
| django-ninja | uvicorn | 0.40.0 |
| fastapi | aiosqlite | 0.22.1 |
| fastapi | fastapi | 0.127.0 |
| fastapi | msgspec | 0.20.0 |
| fastapi | orjson | 3.11.5 |
| fastapi | pydantic | 2.12.5 |
| fastapi | python | 3.13.6 |
| fastapi | sqlalchemy | 2.0.45 |
| fastapi | starlette | 0.50.0 |
| fastapi | uvicorn | 0.40.0 |
| graphene-v2 | django | 3.2.25 |
| graphene-v2 | graphene | 2.1.9 |
| graphene-v2 | graphene-django | 2.16.0 |
| graphene-v2 | python | 3.10.6 |
| graphene-v2 | uvicorn | 0.40.0 |
| graphene-v3 | django | 6.0 |
| graphene-v3 | graphene | 3.4.3 |
| graphene-v3 | graphene-django | 3.2.3 |
| graphene-v3 | python | 3.13.6 |
| graphene-v3 | uvicorn | 0.40.0 |
| litestar | aiosqlite | 0.22.1 |
| litestar | litestar | 2.19.0 |
| litestar | msgspec | 0.20.0 |
| litestar | orjson | 3.11.5 |
| litestar | python | 3.13.6 |
| litestar | sqlalchemy | 2.0.45 |
| litestar | uvicorn | 0.40.0 |
| strawberry-fastapi | aiosqlite | 0.22.1 |
| strawberry-fastapi | fastapi | 0.127.0 |
| strawberry-fastapi | python | 3.13.6 |
| strawberry-fastapi | sqlalchemy | 2.0.45 |
| strawberry-fastapi | starlette | 0.50.0 |
| strawberry-fastapi | strawberry-graphql | 0.287.3 |
| strawberry-fastapi | uvicorn | 0.40.0 |
| strawberry-django | django | 6.0 |
| strawberry-django | python | 3.13.6 |
| strawberry-django | strawberry-graphql | 0.287.3 |
| strawberry-django | uvicorn | 0.40.0 |

## Library Versions (Project Dependencies)

| Package | Version |
|---------|---------|
| aiosqlite | 0.22.1 |
| django | 6.0 |
| django-bolt | 0.4.7 |
| django-ninja | 1.5.1 |
| djangorestframework | 3.16.1 |
| fastapi | 0.127.0 |
| graphene-django | 3.2.3 |
| httpx | 0.28.1 |
| litestar | 2.19.0 |
| matplotlib | 3.10.8 |
| msgspec | 0.20.0 |
| orjson | 3.11.5 |
| pytest | unknown |
| sqlalchemy | 2.0.45 |
| starlette | 0.50.0 |
| strawberry-graphql | 0.287.3 |
| strawberry-graphql-django | 0.71.0 |
| uvicorn | 0.40.0 |

### /json-1k

| Framework | RPS | Latency (avg) | Latency (p99) | Errors |
|-----------|----:|-------------:|-------------:|-------:|
| litestar | 32,850 | 0.00ms | 0.00ms | 0 |
| django-bolt | 28,684 | 0.00ms | 0.00ms | 0 |
| fastapi | 12,984 | 0.01ms | 0.00ms | 0 |
| django-ninja | 4,037 | 0.02ms | 0.00ms | 0 |
| django-drf | 2,566 | 0.04ms | 0.00ms | 0 |
| strawberry-fastapi | 1,260 | 0.08ms | 0.00ms | 0 |
| graphene-v2 | 972 | 0.10ms | 0.00ms | 0 |
| strawberry-django | 933 | 0.11ms | 0.00ms | 0 |
| graphene-v3 | 629 | 0.16ms | 0.00ms | 0 |

### /json-10k

| Framework | RPS | Latency (avg) | Latency (p99) | Errors |
|-----------|----:|-------------:|-------------:|-------:|
| litestar | 25,703 | 0.00ms | 0.00ms | 0 |
| django-bolt | 22,150 | 0.00ms | 0.00ms | 0 |
| django-ninja | 3,421 | 0.03ms | 0.00ms | 0 |
| fastapi | 2,331 | 0.04ms | 0.00ms | 0 |
| django-drf | 2,263 | 0.04ms | 0.00ms | 0 |
| strawberry-fastapi | 597 | 0.17ms | 0.00ms | 0 |
| strawberry-django | 506 | 0.20ms | 0.00ms | 0 |
| graphene-v2 | 432 | 0.23ms | 0.00ms | 0 |
| graphene-v3 | 402 | 0.25ms | 0.00ms | 0 |

### /db

| Framework | RPS | Latency (avg) | Latency (p99) | Errors |
|-----------|----:|-------------:|-------------:|-------:|
| django-bolt | 5,604 | 0.02ms | 0.00ms | 0 |
| litestar | 1,345 | 0.07ms | 0.00ms | 0 |
| fastapi | 1,322 | 0.08ms | 0.00ms | 0 |
| graphene-v2 | 795 | 0.13ms | 0.00ms | 0 |
| django-ninja | 625 | 0.16ms | 0.00ms | 0 |
| strawberry-fastapi | 558 | 0.18ms | 0.00ms | 0 |
| django-drf | 521 | 0.19ms | 0.00ms | 0 |
| strawberry-django | 395 | 0.25ms | 0.00ms | 0 |
| graphene-v3 | 341 | 0.29ms | 0.00ms | 0 |

### /nplus1

| Framework | RPS | Latency (avg) | Latency (p99) | Errors |
|-----------|----:|-------------:|-------------:|-------:|
| litestar | 18,211 | 0.01ms | 0.00ms | 0 |
| django-bolt | 15,545 | 0.01ms | 0.00ms | 0 |
| django-ninja | 2,976 | 0.03ms | 0.00ms | 0 |
| django-drf | 1,813 | 0.06ms | 0.00ms | 0 |
| fastapi | 1,182 | 0.09ms | 0.00ms | 0 |
| strawberry-django | 1,025 | 0.10ms | 0.00ms | 0 |
| graphene-v2 | 960 | 0.10ms | 0.00ms | 0 |
| graphene-v3 | 597 | 0.17ms | 0.00ms | 0 |
| strawberry-fastapi | 443 | 0.22ms | 0.00ms | 0 |

### /mutate

| Framework | RPS | Latency (avg) | Latency (p99) | Errors |
|-----------|----:|-------------:|-------------:|-------:|
| django-bolt | 28,105 | 0.00ms | 0.00ms | 0 |
| litestar | 24,804 | 0.00ms | 0.00ms | 0 |
| fastapi | 17,430 | 0.01ms | 0.00ms | 0 |
| django-ninja | 3,582 | 0.03ms | 0.00ms | 0 |
| django-drf | 1,765 | 0.06ms | 0.00ms | 0 |
| strawberry-fastapi | 1,080 | 0.09ms | 0.00ms | 0 |
| strawberry-django | 845 | 0.12ms | 0.00ms | 0 |
| graphene-v2 | 744 | 0.13ms | 0.00ms | 0 |
| graphene-v3 | 504 | 0.20ms | 0.00ms | 0 |

## Summary (RPS by Endpoint)

| Framework | /json-1k | /json-10k | /db | /nplus1 | /mutate |
|-----------|--------:|--------:|--------:|--------:|--------:|
| django-bolt | 28,684 | 22,150 | 5,604 | 15,545 | 28,105 |
| graphene-v2 | 972 | 432 | 795 | 960 | 744 |
| django-drf | 2,566 | 2,263 | 521 | 1,813 | 1,765 |
| strawberry-django | 933 | 506 | 395 | 1,025 | 845 |
| litestar | 32,850 | 25,703 | 1,345 | 18,211 | 24,804 |
| strawberry-fastapi | 1,260 | 597 | 558 | 443 | 1,080 |
| django-ninja | 4,037 | 3,421 | 625 | 2,976 | 3,582 |
| graphene-v3 | 629 | 402 | 341 | 597 | 504 |
| fastapi | 12,984 | 2,331 | 1,322 | 1,182 | 17,430 |
