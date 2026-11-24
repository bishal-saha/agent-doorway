from typing import Any

import pytest
from typer.testing import CliRunner

from agent_doorway.cli import main as cli

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == "agent-doorway 0.1.0"


def capture_uvicorn(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    calls: dict[str, Any] = {}

    def fake_run(target: str, **kwargs: Any) -> None:
        calls["target"] = target
        calls.update(kwargs)

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)
    return calls


def test_serve_calls_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = capture_uvicorn(monkeypatch)
    result = runner.invoke(cli.app, ["serve"])
    assert result.exit_code == 0
    assert calls["target"] == "agent_doorway.api.app:create_app"
    assert calls["factory"] is True
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 8080
    assert calls["reload"] is False


def test_serve_custom_port(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = capture_uvicorn(monkeypatch)
    result = runner.invoke(cli.app, ["serve", "--port", "9000"])
    assert result.exit_code == 0
    assert calls["port"] == 9000


def test_serve_bad_config_exits_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = capture_uvicorn(monkeypatch)
    monkeypatch.setenv("DOORWAY_ENV", "staging")
    monkeypatch.setenv("DOORWAY_DATABASE_URL", "postgresql://admin:Sup3rS3cret@db/app")
    cli.get_settings.cache_clear()
    result = runner.invoke(cli.app, ["serve"])
    cli.get_settings.cache_clear()
    assert result.exit_code == 2
    assert calls == {}  # the server never starts
    assert "Invalid configuration" in result.output
    assert "DOORWAY_ENV" in result.output
    assert "DOORWAY_DATABASE_URL" in result.output
    assert "Sup3rS3cret" not in result.output
    assert "Traceback" not in result.output
