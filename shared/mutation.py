"""Shared mutation helper for benchmarks."""

from __future__ import annotations

from typing import Any
import asyncio


_counter = 0
_lock = asyncio.Lock()


def create_item(name: str, quantity: int) -> dict[str, Any]:
    """Create a mock item and return its payload."""
    global _counter
    _counter += 1
    return {
        "id": _counter,
        "name": name,
        "quantity": quantity,
        "status": "ok",
    }


async def create_item_async(name: str, quantity: int) -> dict[str, Any]:
    """Async wrapper to create a mock item."""
    global _counter
    async with _lock:
        _counter += 1
        item_id = _counter
    return {
        "id": item_id,
        "name": name,
        "quantity": quantity,
        "status": "ok",
    }
