from fastapi.testclient import TestClient


def test_healthz_ok(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


# ---- readiness --------------------------------------------------------------

import asyncio  # noqa: E402
import time  # noqa: E402

from agent_doorway.api.app import create_app  # noqa: E402
from agent_doorway.config import Settings  # noqa: E402
from agent_doorway.health import Probe  # noqa: E402


class OkProbe:
    def __init__(self, name: str) -> None:
        self.name = name

    async def check(self) -> None:
        return None


class FailProbe:
    name = "postgres"

    async def check(self) -> None:
        # The message contains a DSN with a password: it must never reach the response.
        raise ConnectionError("could not connect to postgresql://doorway:secret@db/x")


class SlowProbe:
    name = "redis"

    async def check(self) -> None:
        await asyncio.sleep(5)


def ready_client(settings: Settings, probes: list[Probe]) -> TestClient:
    return TestClient(create_app(settings, probes=probes))


def test_readyz_all_ok(settings: Settings) -> None:
    client = ready_client(settings, [OkProbe("postgres"), OkProbe("redis")])
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"postgres": "ok", "redis": "ok"}}


def test_readyz_one_failing(settings: Settings) -> None:
    client = ready_client(settings, [FailProbe(), OkProbe("redis")])
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"postgres": "fail: ConnectionError", "redis": "ok"},
    }


def test_readyz_failure_hides_dsn(settings: Settings) -> None:
    client = ready_client(settings, [FailProbe()])
    response = client.get("/readyz")
    assert "secret" not in response.text
    assert "postgresql://" not in response.text


def test_readyz_times_out_slow_probe() -> None:
    settings = Settings(_env_file=None, probe_timeout_seconds=0.1)  # type: ignore[call-arg]
    client = ready_client(settings, [SlowProbe(), OkProbe("postgres")])
    started = time.monotonic()
    response = client.get("/readyz")
    elapsed = time.monotonic() - started
    assert response.status_code == 503
    assert response.json()["checks"] == {"redis": "fail: TimeoutError", "postgres": "ok"}
    assert elapsed < 1.0


def test_readyz_no_probes(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {}}
