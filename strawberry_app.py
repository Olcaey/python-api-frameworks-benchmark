"""
Strawberry GraphQL ASGI Benchmark Application

4 GraphQL queries:
1. json1k     - Returns ~1KB JSON response
2. json10k    - Returns ~10KB JSON response
3. users      - 10 reads from SQLite database
4. slow       - Mock API that takes 2 seconds to respond

Uses FastAPI for ASGI asynchronous server.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import List

import strawberry
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from strawberry.fastapi import GraphQLRouter

from shared.django_models import DjangoBase, BenchmarkUser
from shared import data as test_data
from shared.mutation import create_item_async
from shared.nplus1 import get_users, batch_load_orders_async
from shared.versions import build_versions_payload


# Database setup (align with Django/Graphene DB schema)
DATABASE_URL = "sqlite+aiosqlite:///./django_benchmark.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_database():
    """Seed database with 10 users if empty."""
    async with engine.begin() as conn:
        await conn.run_sync(DjangoBase.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(BenchmarkUser).limit(1))
        if result.scalar_one_or_none() is None:
            users = [
                BenchmarkUser(
                    username=f"user{i:02d}",
                    email=f"user{i:02d}@example.com",
                    first_name=f"First{i}",
                    last_name=f"Last{i}",
                )
                for i in range(10)
            ]
            session.add_all(users)
            await session.commit()
            print("[strawberry] Seeded 10 users")


# Strawberry types
@strawberry.type
class GenericItemType:
    """Generic item type for JSON responses."""

    id: int
    name: str
    description: str
    price: float
    category: str
    in_stock: bool
    tags: List[str]


@strawberry.type
class UserType:
    """User type for database queries."""

    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool


@strawberry.type
class SlowResponseType:
    """Response type for slow query."""

    status: str
    delay_seconds: int


@strawberry.type
class OrderType:
    """Order type for N+1 test."""

    id: int
    total: float
    item_count: int


@strawberry.type
class UserWithOrdersType:
    """User type with orders for N+1 test."""

    id: int
    username: str
    orders: List[OrderType]


@strawberry.type
class Query:
    """Root GraphQL query."""

    @strawberry.field
    def json1k(self) -> List[GenericItemType]:
        """Return ~1KB JSON response."""
        return [
            GenericItemType(
                id=item["id"],
                name=item["name"],
                description=item["description"],
                price=item["price"],
                category=item["category"],
                in_stock=item["in_stock"],
                tags=item["tags"],
            )
            for item in test_data.JSON_1K
        ]

    @strawberry.field
    def json10k(self) -> List[GenericItemType]:
        """Return ~10KB JSON response."""
        return [
            GenericItemType(
                id=item["id"],
                name=item["name"],
                description=item["description"],
                price=item["price"],
                category=item["category"],
                in_stock=item["in_stock"],
                tags=item["tags"],
            )
            for item in test_data.JSON_10K
        ]

    @strawberry.field
    async def users(self) -> List[UserType]:
        """Read 10 users from database."""
        async with async_session() as session:
            stmt = select(BenchmarkUser).limit(10)
            result = await session.execute(stmt)
            users = result.scalars().all()
            return [
                UserType(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_active=user.is_active,
                )
                for user in users
            ]

    @strawberry.field
    async def slow(self) -> SlowResponseType:
        """Mock slow API - 2 second delay."""
        await asyncio.sleep(2)
        return SlowResponseType(status="ok", delay_seconds=2)

    @strawberry.field
    async def nplus1(self) -> List[UserWithOrdersType]:
        """Return users with orders using batch loading."""
        users = get_users()
        user_ids = [u["id"] for u in users]
        orders_map = await batch_load_orders_async(user_ids)
        return [
            UserWithOrdersType(
                id=user["id"],
                username=user["username"],
                orders=[
                    OrderType(**order)
                    for order in orders_map.get(user["id"], [])
                ],
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


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)


# FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - seed database on startup."""
    await seed_database()
    yield


app = FastAPI(lifespan=lifespan)

# Add GraphQL router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/versions")
async def versions():
    """Return library versions used by this app."""
    packages = [
        "strawberry-graphql",
        "fastapi",
        "starlette",
        "uvicorn",
        "sqlalchemy",
        "aiosqlite",
    ]
    return JSONResponse(build_versions_payload("strawberry", packages))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8006, log_level="error")
