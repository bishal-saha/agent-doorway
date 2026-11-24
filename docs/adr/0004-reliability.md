# ADR 0004: Retries, fallback chains, Redis-backed breakers and rate limits, failing open

- **Status:** Accepted
- **Date:** 2026-11-23

## Context

Upstream providers time out, rate-limit and have outages. Callers of the gateway should not each
reinvent retries, and a provider that is down should not cost every request a full timeout. The
gateway also needs to protect itself and its upstreams from a runaway client. It runs as several
replicas, so any state about "is this provider healthy?" or "how many requests has this key made?"
must be shared.

## Decision

- **One dispatcher** (`reliability/dispatch.py`) wraps every provider call. The router turns a
  model name into an ordered list of targets: one for a plain model, several for an **alias**
  configured in `DOORWAY_MODEL_ROUTES` (e.g. `smart → claude-sonnet-5-5, gpt-5, mock`).
- **Retries** only for errors the provider marks retryable (408, 409, 429, 5xx, 529, network
  errors), up to `retry_max_attempts` per target, with **full-jitter** exponential backoff so
  clients that failed together don't retry together. Request errors (400, 413, 422) are raised at
  once: they would fail on every provider.
- **Fallback** to the next target after a target's retries run out or it fails non-retryably.
- **Streams** can be retried or fall back only before their first event; afterwards a failure is
  reported in the stream (ADR 0003).
- **Circuit breaker per target** (`provider/model`): open after N failures within a window (one per
  failed request, only for errors that mean the provider is unhealthy), skip it for a cooldown,
  then let exactly one trial through (half-open). State is in Redis, changed only by Lua scripts
  (atomic across replicas), and timed by Redis key expiry (the server's clock).
- **Rate limits**: a token bucket per API key and per tenant, one atomic Lua script per hit using
  Redis `TIME`. Refusals are 429 with `Retry-After`. Authentication runs first, so bad keys can't
  drain a real tenant's budget.
- **Fail open**: if Redis is unreachable, requests are allowed and providers treated as healthy,
  with a warning at most once a minute. Redis calls have 1-second timeouts.
- Responses carry `X-Doorway-Model`, `X-Doorway-Provider` and `X-Doorway-Attempts`.
- In-memory implementations of the breaker and limiter exist for single-process use and unit
  tests; one behaviour suite runs against both implementations.

## Consequences

- Clients get higher availability for free, and can see which model answered from the headers.
- A Redis outage removes rate limiting and breaker protection for its duration (a deliberate
  trade: availability over enforcement). Phase 7's metrics make this visible.
- A 429 from an upstream counts as a breaker failure; a provider that rate-limits hard is skipped
  for a cooldown, which is usually what a caller wants.
- Retries multiply upstream load in an outage, bounded by `retry_max_attempts` × chain length,
  and the breaker stops that quickly.
- Per-tenant limits from policy files arrive in phase 4; these settings are the defaults.
