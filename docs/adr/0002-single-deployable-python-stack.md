# ADR 0002: One deployable, built on Python 3.12, FastAPI, Postgres and Redis

- **Status:** Accepted
- **Date:** 2026-11-23

## Context

Agent Doorway sits between a company's apps/agents and the LLM providers and MCP tools they call.
It needs an HTTP API (OpenAI- and Anthropic-compatible), durable state (tenants, keys, policies,
usage, audit log), shared fast counters across replicas (rate limits, budgets, circuit breakers),
an admin console and a CLI. It must run locally with one command and no API keys.

## Decision

- **Language and framework:** Python 3.12 with FastAPI on Uvicorn. The AI tooling ecosystem
  (official MCP SDK, provider SDKs, OpenTelemetry) is strongest in Python, and Pydantic gives typed
  validation of requests, policies and config. mypy runs in strict mode on `src/`.
- **One deployable:** the gateway, the admin API and the admin console ship in one process and one
  container image. The admin side is API-first: a JSON admin API over one service layer, used by
  both the server-rendered console (Jinja + HTMX) and the `doorway` CLI. A separate SPA can be added
  later from the OpenAPI spec without touching the gateway.
- **Postgres 16** holds durable state; **Redis 7** holds shared counters and breaker state.
- **Configuration** comes only from `DOORWAY_*` environment variables, validated at startup.
- **Health:** `/healthz` (liveness, no dependencies) and `/readyz` (readiness, probes Postgres and
  Redis concurrently with a timeout, never echoes connection strings).
- **Mock-first:** the default provider is a deterministic mock, so nothing needs an API key.
- **Compose at the repo root** in phase 1, so `docker compose up` works with no flags. Monitoring
  and Helm assets will live under `deploy/` when they arrive.

## Consequences

- One image and one process are simple to run, test and reason about; the admin surface scales
  with the gateway rather than independently, which is acceptable for a control plane.
- Python is slower per request than Go or Rust gateways; the gateway's overhead will be measured
  and published (load test, phase 9) rather than assumed.
- Redis becomes a hard runtime dependency once rate limits and breakers arrive; readiness reports
  it.
