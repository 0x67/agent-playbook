# Operability

Loaded via `services` SKILL.md routing table. Sources: The Twelve-Factor App (config, logs, disposability); Site Reliability Engineering (Google), chapter Monitoring Distributed Systems; the RED method, Tom Wilkie; the USE method, Brendan Gregg; Prometheus metric and label naming docs; OpenTelemetry docs; W3C Trace Context; Kubernetes docs on probes and pod termination.

The language skill's services page names the libraries (Go `slog`, SLF4J and Micrometer on the JVM). This page sets what they have to do.

## Configuration

- Load config once at startup into one typed value, validate all of it (required keys, ranges, URLs, durations), and refuse to start with one error that lists every bad key. Code reads that value; it never calls `getenv` deep inside a function.
- Values come from the environment or files the platform provides (Twelve-Factor). A default in code is for a value that is safe in every environment. Production endpoints and credentials have none.
- Secrets come from the secret store or the environment at runtime, never from a committed file, a command-line flag (visible in `ps`), or a log line. Redact them in the config summary logged at startup.
- A key with a unit names it: `HTTP_TIMEOUT_MS`, `MAX_BODY_BYTES` (`software-design` `references/naming.md`).
- A feature flag has an owner and a removal date. Tests run both sides of it, and the code behind the old side is deleted once the rollout finishes.
- Config changes at runtime only where the repo already supports reloading; otherwise a change means a restart.

## Logging

- Structured logs (JSON or key-value) through the repo's logger. The message is a constant phrase; values go in fields.
- Every line written while handling a request or message includes its request id or trace id.
- Levels:
  1. `ERROR`: the operation failed for a reason that is not the caller's, and a person may need to act.
  2. `WARN`: degraded but handled, such as a retry that succeeded or a fallback that was used.
  3. `INFO`: lifecycle (start, stop, config summary) and business events at a volume someone can read.
  4. `DEBUG`: detail that is off in production.
- A caller's mistake (`4xx`, a validation failure) is `INFO` or `WARN`. Logged as `ERROR`, it hides the errors that need a person among ones that do not.
- Log an error once, where it is handled, with its context. Logging it and returning it logs it again at every layer.
- No secrets, tokens, passwords, full card numbers, or personal data beyond what policy allows. Redact in the logger or in the type (an allowlist of fields, a redacting `String()` or `toString`), so one forgetful call site cannot leak it.
- No log line per item in a hot loop. Count items in a metric.

## Metrics

- Request-driven services get the RED metrics: rate, errors, and duration per route or operation. Resources (pools, queues, disks) get the USE metrics: utilization, saturation, errors. Together they cover the SRE book's four golden signals: latency, traffic, errors, and saturation.
- Durations are histograms. Alert on percentiles or on an error budget, never on an average.
- Keep label values bounded: a route template (`/orders/{id}`), a status class, an outcome. A user id, order id, or raw URL path as a label creates one time series per value.
- Names include the unit, in base units: `http_request_duration_seconds`, `payload_size_bytes`. Counters end in `_total` (Prometheus naming).
- Money flows get counts and sums per outcome (payouts sent, failed, held). A problem then shows on a dashboard before it shows in a reconciliation report.

## Tracing

- Propagate W3C Trace Context (`traceparent`) on outbound HTTP calls and in message headers, through the repo's OpenTelemetry setup or the framework's instrumented clients.
- One span per inbound request, outbound call, and consumed message. Record errors on the span, and follow the OpenTelemetry semantic conventions for attribute names.

## Health and shutdown

- Liveness checks only that the process can answer. Readiness checks what the service needs before it takes traffic, and fails during shutdown. A liveness probe that calls the database restarts every instance when the database has a short outage.
- On `SIGTERM`: stop accepting new work, finish in-flight requests and jobs within a timeout shorter than the platform's grace period (Kubernetes defaults to 30 s), flush telemetry, then exit.
- A job still running at shutdown may be killed and later rescued by the job runner. That rescue path has to be idempotent and must send what the normal path would have sent (`resilience.md`).
