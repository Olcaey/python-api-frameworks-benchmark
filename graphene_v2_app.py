"""
Graphene v2 (Django) GraphQL ASGI Benchmark Application

4 GraphQL queries:
1. json1k     - Returns ~1KB JSON response
2. json10k    - Returns ~10KB JSON response
3. users      - 10 reads from SQLite database
4. slow       - Mock API that takes 2 seconds to respond

Uses Django's native ASGI application with Graphene-Django.
"""

from __future__ import annotations

import os
import sys
import django

# Setup Django before imports (use minimal settings for GraphQL benchmarks)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings_graphql")
django.setup()

import graphene
from graphene_django import DjangoObjectType
from django.urls import path
from graphene_django.views import GraphQLView as BaseGraphQLView
from django.http import JsonResponse

from django_project.users.models import BenchmarkUser
from shared import data as test_data
from shared.mutation import create_item_async
from shared.nplus1 import get_users, batch_load_orders_async
from shared.versions import build_versions_payload


class UserType(DjangoObjectType):
    """GraphQL type for BenchmarkUser model."""

    class Meta:
        model = BenchmarkUser
        fields = ("id", "username", "email", "first_name", "last_name", "is_active")


class GenericItemType(graphene.ObjectType):
    """Generic item type for JSON responses."""

    id = graphene.Int()
    name = graphene.String()
    description = graphene.String()
    price = graphene.Float()
    category = graphene.String()
    in_stock = graphene.Boolean()
    tags = graphene.List(graphene.String)


class SlowResponseType(graphene.ObjectType):
    """Response type for slow query."""

    status = graphene.String()
    delay_seconds = graphene.Int()


class OrderType(graphene.ObjectType):
    """Order type for N+1 test."""

    id = graphene.Int()
    total = graphene.Float()
    item_count = graphene.Int()


class UserWithOrdersType(graphene.ObjectType):
    """User type with orders for N+1 test."""

    id = graphene.Int()
    username = graphene.String()
    orders = graphene.List(OrderType)


class Query(graphene.ObjectType):
    """Root GraphQL query."""

    json1k = graphene.List(GenericItemType)
    json10k = graphene.List(GenericItemType)
    users = graphene.List(UserType)
    slow = graphene.Field(SlowResponseType)
    nplus1 = graphene.List(UserWithOrdersType)

    def resolve_json1k(self, info):
        """Return ~1KB JSON response."""
        return [GenericItemType(**item) for item in test_data.JSON_1K]

    def resolve_json10k(self, info):
        """Return ~10KB JSON response."""
        return [GenericItemType(**item) for item in test_data.JSON_10K]

    def resolve_users(self, info):
        """Read 10 users from database."""
        return BenchmarkUser.objects.all()[:10]

    def resolve_slow(self, info):
        """Mock slow API - 2 second delay."""
        import time
        time.sleep(2)
        return SlowResponseType(status="ok", delay_seconds=2)

    async def resolve_nplus1(self, info):
        """Return users with orders using batch loading."""
        users = get_users()
        user_ids = [u["id"] for u in users]
        orders_map = await batch_load_orders_async(user_ids)
        return [
            {
                "id": user["id"],
                "username": user["username"],
                "orders": orders_map.get(user["id"], []),
            }
            for user in users
        ]


class MutateInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    quantity = graphene.Int(required=True)


class CreateItem(graphene.Mutation):
    class Arguments:
        input = MutateInput(required=True)

    id = graphene.Int()
    name = graphene.String()
    quantity = graphene.Int()
    status = graphene.String()

    async def mutate(self, info, input):
        payload = await create_item_async(input.name, input.quantity)
        return CreateItem(**payload)


class Mutation(graphene.ObjectType):
    create_item = CreateItem.Field()


# Create GraphQL schema
schema = graphene.Schema(query=Query, mutation=Mutation)


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
        print("[graphene-asgi] Seeded 10 users")


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "ok"})

def versions(request):
    """Return library versions used by this app."""
    packages = [
        "django",
        "graphene",
        "graphene-django",
        "uvicorn",
    ]
    return JsonResponse(build_versions_payload("graphene-v2", packages))


# Seed database on module load (only when not in async context)
try:
    seed_database()
except Exception:
    # Skip seeding if in async context (will be seeded on first request)
    pass

# Define URL patterns
urlpatterns = [
    path("graphql", BaseGraphQLView.as_view(graphiql=False, schema=schema)),
    path("health", health_check),
    path("versions", versions),
]

# Monkey-patch Django's URL configuration for this standalone app
from django.conf import settings
if not settings.configured or settings.ROOT_URLCONF != __name__:
    settings.ROOT_URLCONF = __name__

# Create ASGI application using Django's native ASGI
from django.core.asgi import get_asgi_application
application = get_asgi_application()


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn
    uvicorn.run("graphene_v2_app:application", host="127.0.0.1", port=8008, log_level="error")
