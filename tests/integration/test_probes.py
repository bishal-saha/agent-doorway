"""Probes against real Postgres and Redis containers (needs Docker): `make test-integration`."""

from collections.abc import Iterator

import pytest
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer

from agent_doorway.health import PostgresProbe, RedisProbe, run_probes

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="module")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:16", driver="asyncpg") as container:
        yield container


@pytest.fixture(scope="module")
def redis() -> Iterator[RedisContainer]:
    with RedisContainer("redis:7") as container:
        yield container


def redis_url(container: RedisContainer) -> str:
    host = container.get_container_host_ip()
    port = container.get_exposed_port(6379)
    return f"redis://{host}:{port}/0"


async def test_postgres_probe_ok(postgres: PostgresContainer) -> None:
    probe = PostgresProbe(postgres.get_connection_url())
    try:
        assert await run_probes([probe], timeout_seconds=5) == {"postgres": "ok"}
    finally:
        await probe.close()


async def test_redis_probe_ok(redis: RedisContainer) -> None:
    probe = RedisProbe(redis_url(redis))
    try:
        assert await run_probes([probe], timeout_seconds=5) == {"redis": "ok"}
    finally:
        await probe.close()


async def test_postgres_probe_wrong_password_fails(postgres: PostgresContainer) -> None:
    url = postgres.get_connection_url().replace(f":{postgres.password}@", ":wrong-password@")
    probe = PostgresProbe(url)
    try:
        result = await run_probes([probe], timeout_seconds=5)
        assert result["postgres"].startswith("fail: ")
        assert "wrong-password" not in result["postgres"]
    finally:
        await probe.close()
