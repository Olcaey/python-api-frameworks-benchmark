"""
Strawberry GraphQL (Django) ASGI Benchmark Application

4 GraphQL queries:
1. json1k     - Returns ~1KB JSON response
2. json10k    - Returns ~10KB JSON response
3. users      - 10 reads from SQLite database
4. slow       - Mock API that takes 2 seconds to respond

Uses Django's native ASGI application with Strawberry-Django.
"""

from __future__ import annotations

import os
import django

# Setup Django before imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings_graphql")
django.setup()

import asyncio
import strawberry
import strawberry_django
from strawberry.django.views import GraphQLView
from django.urls import path
from django.http import JsonResponse

from django_project.users.models import BenchmarkUser
from shared import data as test_data
from shared.mutation import create_item_async
from shared.nplus1 import get_users, batch_load_orders_async
from shared.versions import build_versions_payload


@strawberry.type
class GenericItemType:
    id: int
    name: str
    description: str
    price: float
    category: str
    in_stock: bool
    tags: list[str]


@strawberry_django.type(BenchmarkUser)
class UserType:
    id: strawberry.auto
    username: strawberry.auto
    email: strawberry.auto
    first_name: strawberry.auto
    last_name: strawberry.auto
    is_active: strawberry.auto


@strawberry.type
class SlowResponseType:
    status: str
    delay_seconds: int


@strawberry.type
class OrderType:
    id: int
    total: float
    item_count: int


@strawberry.type
class UserWithOrdersType:
    id: int
    username: str
    orders: list[OrderType]


@strawberry.type
class Query:
    @strawberry.field
    def json1k(self) -> list[GenericItemType]:
        return [GenericItemType(**item) for item in test_data.JSON_1K]

    @strawberry.field
    def json10k(self) -> list[GenericItemType]:
        return [GenericItemType(**item) for item in test_data.JSON_10K]

    @strawberry.field
    def users(self) -> list[UserType]:
        return list(BenchmarkUser.objects.all()[:10])

    @strawberry.field
    async def slow(self) -> SlowResponseType:
        await asyncio.sleep(2)
        return SlowResponseType(status="ok", delay_seconds=2)

    @strawberry.field
    async def nplus1(self) -> list[UserWithOrdersType]:
        users = get_users()
        user_ids = [u["id"] for u in users]
        orders_map = await batch_load_orders_async(user_ids)
        return [
            UserWithOrdersType(
                id=user["id"],
                username=user["username"],
                orders=[OrderType(**order) for order in orders_map.get(user["id"], [])],
            )
            for user in users
        ]


@strawberry.input
class MutateInput:
    name: str
    quantity: int


@strawberry.type
class MutationPayload:
    id: int
    name: str
    quantity: int
    status: str


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_item(self, input: MutateInput) -> MutationPayload:
        payload = await create_item_async(input.name, input.quantity)
        return MutationPayload(**payload)


schema = strawberry.Schema(query=Query, mutation=Mutation)


def seed_database():
    """Seed database with 10 users if empty."""
    if not BenchmarkUser.objects.exists():
        users = [
            BenchmarkUser(
                username=f"user{i:02d}",
                email=f"user{i:02d}@example.com",
                first_name=f"First{i}",
                last_name=f"Last{i}",
            )
            for i in range(10)
        ]
        BenchmarkUser.objects.bulk_create(users)
        print("[strawberry-django] Seeded 10 users")


def health_check(request):
    return JsonResponse({"status": "ok"})


def versions(request):
    packages = [
        "django",
        "strawberry-graphql",
        "uvicorn",
    ]
    return JsonResponse(build_versions_payload("strawberry-django", packages))


try:
    seed_database()
except Exception:
    pass

urlpatterns = [
    path("graphql", GraphQLView.as_view(schema=schema)),
    path("health", health_check),
    path("versions", versions),
]

from django.conf import settings
if not settings.configured or settings.ROOT_URLCONF != __name__:
    settings.ROOT_URLCONF = __name__

from django.core.asgi import get_asgi_application
application = get_asgi_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("strawberry_django_app:application", host="127.0.0.1", port=8009, log_level="error")
