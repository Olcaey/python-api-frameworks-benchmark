"""Shared N+1/dataloader-style test data and helpers."""

from __future__ import annotations

from typing import Any


NPLUS1_USER_COUNT = 50
NPLUS1_ORDERS_PER_USER = 3


def _build_users() -> list[dict[str, Any]]:
    return [
        {
            "id": i,
            "username": f"user{i:03d}",
        }
        for i in range(1, NPLUS1_USER_COUNT + 1)
    ]


def _build_orders() -> dict[int, list[dict[str, Any]]]:
    orders: dict[int, list[dict[str, Any]]] = {}
    for user_id in range(1, NPLUS1_USER_COUNT + 1):
        user_orders = []
        for j in range(1, NPLUS1_ORDERS_PER_USER + 1):
            order_id = user_id * 1000 + j
            user_orders.append(
                {
                    "id": order_id,
                    "total": round(10.0 + (user_id * 0.1) + j, 2),
                    "item_count": 1 + (order_id % 4),
                }
            )
        orders[user_id] = user_orders
    return orders


NPLUS1_USERS = _build_users()
NPLUS1_ORDERS = _build_orders()


def get_users(limit: int | None = None) -> list[dict[str, Any]]:
    """Return mock users for N+1 tests."""
    if limit is None:
        return list(NPLUS1_USERS)
    return list(NPLUS1_USERS[:limit])


def batch_load_orders(user_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
    """Batch-load orders for the given user ids."""
    return {user_id: NPLUS1_ORDERS.get(user_id, []) for user_id in user_ids}


async def batch_load_orders_async(user_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
    """Async wrapper for batch loading orders."""
    return batch_load_orders(user_ids)
