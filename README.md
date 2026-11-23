# Agent Doorway

[![CI](https://github.com/bishal-saha/agent-doorway/actions/workflows/ci.yml/badge.svg)](https://github.com/bishal-saha/agent-doorway/actions/workflows/ci.yml)

**Every AI call comes through one door: checked, metered and on the record.**

Companies now have many apps and agents calling LLM providers and MCP tools directly, each with its
own keys, no shared spending limits, no consistent safety checks and no reliable record of who did
what. Agent Doorway is a self-hostable control plane that sits in front of those calls and enforces
identity, policy, budgets, reliability and audit on every one of them.

It is a **reference implementation**, not a product competitor: every design decision is written
down (see [`docs/adr/`](docs/adr/)) and, where possible, backed by a published measurement.

> **Status:** phase 3 of 10 (reliability). Tenants, hashed API keys, OpenAI- and
> Anthropic-compatible endpoints (streaming), retries, fallback chains, circuit breakers and rate
> limits, in front of Anthropic, any OpenAI-compatible server or a built-in mock. Policies,
> budgets and audit come next; see the roadmap below.

## Quick start

Requires Docker. No provider API key needed: the built-in `mock` model answers every request.

```bash
docker compose up -d --build --wait     # Postgres, Redis, migrations, gateway
docker compose exec gateway doorway tenants create acme --name "Acme Ltd"
docker compose exec gateway doorway teams create acme support
# -T: no terminal, so only the key (stdout) is captured, not the messages (stderr)
KEY=$(docker compose exec -T gateway doorway keys create acme support --name demo)

curl localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model": "mock", "messages": [{"role": "user", "content": "Where is my order?"}]}'

docker compose down -v
```

The key is printed once and only its sha256 hash is stored. `doorway keys list acme` shows
prefixes; `doorway keys revoke <prefix>` stops a key on its next request.

## Use it from the official SDKs

Change the base URL and the key; nothing else.

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8080/v1", api_key=KEY)
client.chat.completions.create(model="mock", messages=[{"role": "user", "content": "hi"}])
```

```python
from anthropic import Anthropic

client = Anthropic(base_url="http://localhost:8080", api_key=KEY)
client.messages.create(model="mock", max_tokens=100, messages=[{"role": "user", "content": "hi"}])
```

Both support `stream=True`. Models named `claude-*` go to Anthropic when `ANTHROPIC_API_KEY` is
set; other names go to an OpenAI-compatible server when `OPENAI_API_KEY` or
`DOORWAY_OPENAI_BASE_URL` is set, in your shell or a `.env` file; Compose passes them to the
gateway (see [`.env.example`](.env.example)). Phase 2 is text only:
requests with tools or images are refused with a clear 400.

## Reliability

Every request goes through retries (full-jitter backoff), an ordered fallback chain and a
circuit breaker per target (provider and model); keys and tenants have token-bucket rate limits (429 with
`Retry-After`). Breaker and rate-limit state live in Redis, shared by all replicas; if Redis is
down the gateway fails open. See [ADR 0004](docs/adr/0004-reliability.md).

Try a provider outage with no keys at all: the mock fails on purpose for `mock-error-<status>`.

```bash
# in .env: DOORWAY_MODEL_ROUTES={"smart": ["mock-error-503", "mock"]}
docker compose up -d --build --wait
curl -si localhost:8080/v1/chat/completions -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "smart", "messages": [{"role": "user", "content": "hi"}]}' | grep -i x-doorway
# x-doorway-model: mock
# x-doorway-provider: mock
# x-doorway-attempts: 4
```

After a few such requests the breaker for the failing target opens, and it is skipped at once.

## Development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
uv sync                 # install dependencies
make check              # lint, format check, mypy (strict), unit tests
make test-integration   # tests against real Postgres and Redis containers (needs Docker)
uv run doorway db upgrade   # create the tables (needs a reachable Postgres)
uv run doorway serve    # run the gateway locally on :8080
```

Configuration is read from `DOORWAY_*` environment variables; see [`.env.example`](.env.example).
Design decisions are recorded in [`docs/adr/`](docs/adr/) (0003 explains the canonical chat model).

## Roadmap

1. **Skeleton:** package, config, health checks, Compose, hardened CI, ADRs
2. **Core proxy:** tenants, hashed API keys, OpenAI- and Anthropic-compatible endpoints, streaming
3. **Reliability:** retries, fallback chains, circuit breakers, rate limiting
4. **Policy and guardrails:** per-tenant YAML policies, injection and PII checks, tool allowlists
5. **MCP tool proxy:** allowlists, argument validation, timeouts, idempotency
6. **Metering and audit:** budgets, cost per task, hash-chained audit log, body capture levels
7. **Observability:** OpenTelemetry traces, Prometheus metrics, Grafana dashboards
8. **Admin API and console:** JSON admin API plus a server-rendered HTMX console
9. **Demo and proof:** Kestrel Outfitters demo agent, scenario scripts, load test, Helm chart
10. **Write-up**

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability and the supply-chain measures.

## Licence

[MIT](LICENSE) © 2026 Bishal Saha
