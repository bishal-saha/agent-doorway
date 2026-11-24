# ADR 0003: Translate every API to one canonical chat model

- **Status:** Accepted
- **Date:** 2026-11-23

## Context

Clients speak two wire formats: the OpenAI Chat Completions API and the Anthropic Messages API.
Upstreams also speak several: Anthropic, OpenAI and the many servers that copy OpenAI's format
(vLLM, Ollama, LM Studio), plus a mock for tests. Policy, metering and audit (phases 4 and 6) must
work the same whatever the client and provider are.

Translating each client format straight into each provider format would need one translator per
pair (2 × 3 today, more with every addition), and every cross-cutting feature would have to
understand every format.

## Decision

- Inside the gateway there is one **canonical chat model** (`providers/base.py`): `ChatRequest`,
  `ChatResponse`, and a stream of `TextDelta` events ending in one `StreamEnd` with usage.
- Each **endpoint** translates its wire format to and from the canonical model
  (`api/openai_compat.py`, `api/anthropic_compat.py`). Each **provider adapter** translates the
  canonical model to and from one upstream (`providers/anthropic.py`, `providers/openai_compat.py`,
  `providers/mock.py`). N formats and M providers need N + M translators.
- Providers implement one `Provider` protocol (`complete`, `stream`) and raise one `ProviderError`
  carrying the upstream status and whether a retry could help, so phase 3's retries and fallbacks
  are written once.
- The gateway assigns its own response ids and reports the requested model name, so ids are
  stable for audit whichever upstream answered.
- Phase 2 is **text only**. Requests using tools or non-text content are refused with a 400, not
  silently simplified; the canonical model grows when tool calls arrive.
- A stream waits for its first upstream event before sending the HTTP status, so an upstream that
  fails at once becomes a normal error response. A failure after that is reported in the stream
  (an `error` event, or an OpenAI error chunk without `[DONE]`), never as a silently cut answer.

## Consequences

- Adding a client format or a provider is one translator, and policy, metering and audit see a
  single shape.
- The canonical model only carries what every side supports. Provider-specific features (prompt
  caching controls, extended thinking, logprobs) are dropped or refused until the model grows to
  carry them; each addition is a deliberate change here, not a pass-through.
- Usage arrives at the end of a canonical stream, so the Anthropic-compatible stream reports input
  tokens in `message_delta` rather than `message_start`. The official SDK's final message has the
  right totals (covered by a contract test).
- Contract tests run the official OpenAI and Anthropic SDKs against the gateway in-process, so a
  drift in either SDK's expectations shows up in CI.
