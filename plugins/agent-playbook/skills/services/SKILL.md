---
name: services
description: >
  Language-agnostic rules for code that talks to other systems or keeps state
  across requests: outbound HTTP and gRPC calls, request handlers, webhooks,
  message consumers, background jobs, and status changes stored in a
  database. Use when adding or reviewing timeouts, deadlines, retries,
  backoff, jitter, Retry-After, idempotency keys, duplicate requests or
  messages, at-least-once delivery, deduplication, circuit breakers,
  bulkheads, rate limits, load shedding, the transactional outbox, sagas,
  workflow engines, durable execution, optimistic locking, version columns,
  or a status change that concurrent requests or retries can repeat; and
  for config loading, secrets at runtime, feature flags, log levels and
  redaction, metrics and label cardinality, tracing, health checks, and
  graceful shutdown. Loads alongside the language skill and its services
  page, whose idioms win where they differ.
---

# Services skill

Code that calls over a network or keeps state across restarts fails in ways unit tests rarely show: a call that hangs, a retry that charges twice, a crash between a commit and the request that should follow it. This skill contains the cross-language rules. The language skill's services page (`golang`, `jvm`) holds the libraries and idioms.

## Routing table (mandatory)

Read matching reference BEFORE designing or writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| config loading and validation, secrets at runtime, feature flags, log levels and fields, redaction, metrics, histograms, label cardinality, tracing, liveness and readiness, graceful shutdown | `references/operability.md` |
| outbound calls, timeouts, deadlines, retries, backoff, idempotency keys, duplicate requests or messages, webhooks, consumers, persisted status changes, optimistic locking, outbox, sagas, workflow engines, circuit breakers, bulkheads, rate limits, load shedding | `references/resilience.md` |

## Before writing

1. Load the language skill and its services page where it has one.
2. Read how the repo already does this: its HTTP client wrapper, retry helper, job queue, outbox table, idempotency table. Follow it. A new library, queue, broker, or workflow engine needs the user's agreement first.
3. List every external call and every write in the change, and what each one does on a timeout, on an error response, and when it succeeds but the reply is lost.

## Core rules

- Give each outbound call a timeout, and pass the request's remaining deadline down to the calls it makes.
- A timeout leaves the outcome unknown. For a call that changes state, check the result or retry with the same idempotency key; never assume it failed.
- Retry transient failures of operations that are safe to repeat. Use exponential backoff with jitter and a cap, honor `Retry-After`, and retry at one layer.
- A handler that can see the same request or message twice produces the same result the second time.
- A status change stored in a database is guarded where it is stored: a conditional update on the current status or a version column. No read-then-write.
- No network call inside a database transaction. Work that must follow a commit is recorded in the same transaction (an outbox row, or a pending status a job picks up).
- Every path that sends the same side effect (normal, resume, rescue) builds it with the same function.
- A dependency that keeps failing gets a circuit breaker or load shedding, so waiting calls do not pile up.
- Config is loaded and validated once at startup; a bad value stops the service from starting.
- Logs are structured, include the request or trace id, and never contain secrets or personal data beyond policy.

## Review checklist

Flag in a diff:

- An outbound call without a timeout.
- A downstream timeout longer than the caller's remaining deadline.
- Treating a timeout on a state-changing call as a failure and resending it without the original idempotency key.
- A retry loop that sleeps a fixed time, lacks jitter or an attempt cap, or retries `4xx` responses besides `408` and `429`.
- A non-idempotent call (`POST` that creates, charges, or sends) retried without an idempotency key.
- Retries in both the client library and the caller's own loop.
- A webhook, consumer, or job that does not deduplicate by event or message id.
- Read-then-write on a status, balance, or counter with no conditional update, lock, or version check.
- A remote call or message publish inside a database transaction; a side effect after commit with nothing recorded to retry it after a crash.
- A fallback or recovery path that rebuilds a request differently from the normal path.
- An idempotency key reused with a different payload and sent anyway.
- A new queue, broker, or workflow engine the user did not agree to.
- An environment variable read deep in the code; a secret in a log line, a flag, or a committed file.
- `ERROR` logged for a caller's mistake; an error logged at every layer it passes through.
- A metric label holding a user id, an order id, or a raw path; a duration recorded as an average.
- A liveness probe that checks dependencies; shutdown that exits without draining in-flight work.

## Tool preference

- Every call site of the HTTP client, queue publisher, or job enqueue: the `codebase-memory` graph or `LSP` references where connected; fff MCP tools for exact text.
- Global rules still apply: Code Growth Discipline, Code Simplicity Discipline, Useless Test Ban, Bugs and Design Friction. Types, construction, and in-memory state machines: skill `software-design`. Amounts, ledgers, and audit trails: skill `money`.
