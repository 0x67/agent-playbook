# Resilience

Loaded via `services` SKILL.md routing table. Sources: Release It! (2nd edition), Michael Nygard; Site Reliability Engineering (Google), chapters Handling Overload and Addressing Cascading Failures; Timeouts, retries, and backoff with jitter, Marc Brooker, and Making retries safe with idempotent APIs, Malcolm Featonby, Amazon Builders' Library; Exponential Backoff and Jitter, Marc Brooker, AWS Architecture Blog; RFC 9110 (idempotent methods, `Retry-After`); RFC 6585 (`429`); The Idempotency-Key HTTP Header Field, IETF httpapi draft; Stripe API docs, idempotent requests; Transactional outbox and Saga patterns, Chris Richardson, microservices.io.

## Timeouts

- Give each outbound call a timeout: HTTP, gRPC, database, cache, queue publish. Many clients default to none: Go's `http.Client{}`, Java's `HttpClient` without a request `timeout`, Python `requests` without `timeout=`.
- Set connect and total timeouts separately where the client allows it.
- Base the value on the dependency's measured latency, a little above its p99.9, and keep it under the caller's own deadline.
- Pass the deadline down. A request with 2 s left does not start a call with a 5 s timeout. Use the stack's carrier (Go `context`, gRPC deadlines, a deadline header between services) and stop work once it expires.
- A timeout means the outcome is unknown: the other side may have done the work. For a call that changes state, look up the result by your reference or retry with the same idempotency key.

## Retries

- Retry transient failures only: connection errors, timeouts, `408`, `429`, `502`, `503`, `504`, gRPC `UNAVAILABLE`. Any other `4xx` means the request itself is wrong, and a retry repeats it.
- Retry only operations that are safe to repeat. `GET`, `PUT`, and `DELETE` are idempotent by HTTP's definition (RFC 9110), when the server implements them that way. Anything else needs an idempotency key.
- Exponential backoff with full jitter: sleep a random time between 0 and `min(cap, base * 2^attempt)` (Brooker).
- Cap the attempts, and keep the total time inside the caller's deadline.
- Honor `Retry-After` on `429` and `503`.
- Retry at one layer. Retries multiply across layers: 3 attempts at each of 3 layers send 27 calls for one failure.
- When many calls fail, stop retrying: a retry budget (the SRE book's example keeps retries under 10% of requests) or a circuit breaker.
- Use the client's built-in retry where it has one (cloud SDKs, gRPC retry policy), and then add none of your own.

## Idempotency

| Operation | Technique |
|---|---|
| set a value (`PUT /users/7/email`) | idempotent by nature: write the value, never a delta |
| create, charge, or send (`POST /payments`) | idempotency key |
| change a status (`pay`, `ship`, `cancel`) | guarded transition (below) |
| consume a message, webhook, or job | deduplicate on the message or event id |

Idempotency keys:

- The client generates one key per logical operation and stores it before the first attempt, so a crash and restart retries with the same key.
- The server keeps a unique constraint on the key (scoped by client or account), a fingerprint of the request, and the response it sent.
- For a request with a known key, the server returns the stored response when the payload matches, rejects the request when it differs (the IETF draft answers `422`; Stripe returns an error), and answers `409` while the first request is still running.
- After an unknown outcome, resend under the same key or look the operation up. A new key for the same operation is how duplicates happen.
- When the outcome cannot be settled (the key mismatches, the provider has no record), stop and hand the operation to a person through an ops queue or alert. Do not resend it.
- Keys expire after a window the provider documents (Stripe may drop a key once it is 24 hours old). A retry after that window counts as a new request, so retries finish well inside it.

Consumers:

- Treat delivery as at least once. Brokers redeliver, webhook senders retry until they get a `2xx`, and job runners rescue jobs that look stuck.
- Record the processed message or event id under a unique constraint in the same transaction as the effect. A duplicate hits the constraint and is acknowledged with no second effect.
- Arrival order is not guaranteed across partitions or retries. Check the entity's current status or version before applying a message.

## Status changes in storage

Levels 0 to 2 (a plain field, a status enum with one transition function, one type per state) are in skill `software-design`, `references/types.md`. These two levels add storage and time.

| Level | Shape | Use when |
|---|---|---|
| 3 | status stored with a guarded transition; optionally a history table of transitions | several writers, retries, or redelivered messages can attempt the same transition |
| 4 | workflow engine, saga, or durable execution (Temporal, AWS Step Functions, a saga of steps with compensations) | the process runs for hours or days, spans services, needs timers, or must undo earlier steps when a later one fails |

```sql
UPDATE orders
SET status = 'paid', version = version + 1
WHERE id = $1 AND status = 'pending';
```

- Check the rows affected. Zero means another writer moved the order first, or it is in a state that does not allow the transition: reload and decide.
- A transition requested again into the status the entity already has returns the current result instead of an error, so retries and redelivered messages do nothing.
- Load, check, then save races under concurrency. Use the conditional update above, a row lock (`SELECT ... FOR UPDATE`), or an optimistic version check.
- Level 4 only where the repo already runs the engine, or with the user's agreement: it adds infrastructure and its own programming model.
- In a saga, every step has a compensating step that undoes it, and compensations are idempotent too.

## Side effects and transactions

- No network call inside a database transaction. It holds locks and connections while it waits, and a rollback cannot take back a request that was already sent.
- A side effect that must follow a commit (publish an event, call a provider, send an email) is recorded in the same transaction:
  1. Transactional outbox: insert the message into an outbox table in the business transaction. A relay sends it and marks it sent. Delivery is at least once, and the receiver deduplicates.
  2. Pending status: commit the business change with a status such as `PAYOUT_PENDING`. A job or sweeper finds rows in that status and completes them.
- Either way, a crash between commit and send leaves a row that something retries. A side effect fired right after commit with nothing recorded is lost when the process stops in between.
- When the external call has to happen first (the provider must accept before you can commit), store the idempotency key before calling. A commit that fails after the call succeeded becomes a typed error that a retry with the same key resolves.
- Every path that sends the same side effect (the normal path, resume after restart, a rescued job, a fallback) builds the request with one shared function. A fallback that rebuilds it differently sends the wrong thing while the system is already recovering from a failure.

## Overload and failing dependencies

- Circuit breaker: after a run of failures, fail calls at once for a cool-off period, then let a few through to test recovery (Nygard). Use the stack's library (resilience4j, Polly, `sony/gobreaker`) where the repo has one.
- Bulkheads: separate connection pools, worker pools, or semaphores per dependency, so one slow dependency cannot use up every connection.
- Rate limits: stay under the provider's documented quota with a client-side limiter, and back off on `429`. When the service limits its own callers, it answers `429` with `Retry-After`.
- Load shedding: bound every queue, and reject new work early when it is full. Queued work that will time out anyway only delays the failure.

## Testing

- Drive the failure paths with a fake or test server that times out, answers `503` and then `200`, answers success after the client has given up, and delivers the same message twice. Assert on the outcome: one charge, one row, the stored response returned.
- Test a crash between commit and side effect: run the recovery path (the sweeper, the rescued job) and assert it sends exactly what the normal path would have sent.
