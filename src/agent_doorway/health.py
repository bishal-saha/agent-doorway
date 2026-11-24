"""Readiness probes: can the gateway reach the services it depends on?"""

import asyncio
from collections.abc import Sequence
from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class Probe(Protocol):
    """One dependency check. `check` returns on success and raises on failure."""

    name: str

    async def check(self) -> None: ...


class PostgresProbe:
    name = "postgres"

    def __init__(self, url: str) -> None:
        # A one-connection pool: this engine only ever runs SELECT 1.
        self._engine: AsyncEngine = create_async_engine(url, pool_size=1, max_overflow=0)

    async def check(self) -> None:
        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def close(self) -> None:
        await self._engine.dispose()


class RedisProbe:
    name = "redis"

    def __init__(self, url: str) -> None:
        self._client: Redis = Redis.from_url(url)

    async def check(self) -> None:
        await self._client.ping()

    async def close(self) -> None:
        await self._client.aclose()


async def _run_one(probe: Probe, timeout_seconds: float) -> str:
    try:
        await asyncio.wait_for(probe.check(), timeout=timeout_seconds)
    except Exception as exc:  # any failure means "not ready"
        # Only the exception type: messages can contain DSNs with passwords.
        return f"fail: {type(exc).__name__}"
    return "ok"


async def run_probes(probes: Sequence[Probe], timeout_seconds: float) -> dict[str, str]:
    """Run every probe at the same time; each gets `timeout_seconds` to answer."""
    results = await asyncio.gather(*(_run_one(p, timeout_seconds) for p in probes))
    return {probe.name: result for probe, result in zip(probes, results, strict=True)}
