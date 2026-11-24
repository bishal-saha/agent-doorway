import pytest
from pydantic import ValidationError

from agent_doorway.config import Settings


def make_settings() -> Settings:
    # _env_file=None: a developer's local .env must never leak into tests.
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DOORWAY_ENV",
        "DOORWAY_DATABASE_URL",
        "DOORWAY_REDIS_URL",
        "DOORWAY_LOG_LEVEL",
        "DOORWAY_PROBE_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_defaults() -> None:
    s = make_settings()
    assert s.env == "dev"
    assert s.database_url == "postgresql+asyncpg://doorway:doorway@localhost:5432/doorway"
    assert s.redis_url == "redis://localhost:6379/0"
    assert s.log_level == "INFO"
    assert s.probe_timeout_seconds == 2.0


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOORWAY_ENV", "prod")
    monkeypatch.setenv("DOORWAY_REDIS_URL", "redis://cache:6379/1")
    s = make_settings()
    assert s.env == "prod"
    assert s.redis_url == "redis://cache:6379/1"


def test_invalid_env_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOORWAY_ENV", "staging")
    with pytest.raises(ValidationError):
        make_settings()


def test_bad_database_scheme_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOORWAY_DATABASE_URL", "mysql://u:p@db/x")
    with pytest.raises(ValidationError):
        make_settings()


def test_bad_redis_scheme_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOORWAY_REDIS_URL", "http://cache:6379")
    with pytest.raises(ValidationError):
        make_settings()


@pytest.mark.parametrize("value", ["0", "-1", "31"])
def test_probe_timeout_bounds(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("DOORWAY_PROBE_TIMEOUT_SECONDS", value)
    with pytest.raises(ValidationError):
        make_settings()


def test_bad_dsn_error_hides_password(monkeypatch: pytest.MonkeyPatch) -> None:
    # The most likely mistake (forgetting +asyncpg) must not print the password at startup.
    monkeypatch.setenv("DOORWAY_DATABASE_URL", "postgresql://admin:Sup3rS3cret@prod-db/app")
    with pytest.raises(ValidationError) as excinfo:
        make_settings()
    assert "Sup3rS3cret" not in str(excinfo.value)
