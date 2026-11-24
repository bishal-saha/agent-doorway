import pytest
from fastapi.testclient import TestClient

from agent_doorway.api.app import create_app
from agent_doorway.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture
def client(settings: Settings) -> TestClient:
    # probes=[]: unit tests never touch real Postgres/Redis.
    return TestClient(create_app(settings, probes=[]))
