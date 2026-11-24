.PHONY: check fmt test test-integration

## Run every quality gate: lint, format check, types, unit tests.
check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	uv run pytest

## Auto-fix lint issues and format the code.
fmt:
	uv run ruff check --fix .
	uv run ruff format .

## Unit tests only (fast, no Docker).
test:
	uv run pytest

## Integration tests (need Docker for Postgres/Redis containers).
test-integration:
	uv run pytest -m integration
