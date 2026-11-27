# Rust Services

Loaded via `rust` SKILL.md routing table. Checked against axum 0.8.9, tower 0.5.3, tower-http 0.7.1, tokio 1.54.1, tokio-util 0.7.20, reqwest 0.13.5, sqlx 0.9.1, tracing 0.1.44, and tracing-subscriber 0.3.23 on 2026-11-27. Sources: the CHANGELOG.md files of axum, tower-http, reqwest, and sqlx; docs.rs for `tower_http::timeout` and `reqwest::retry`. Cross-language rules for timeouts, retries, idempotency, logging, and security: skill `services`.

## Versions

- axum 0.8: path parameters are `/{id}` and `/{*rest}` (`/:id` and `/*rest` are 0.7 syntax). Handlers and services added to a `Router` must be `Sync`. The `Host` extractor moved to `axum-extra`. Breaking changes for the next release (merged nested fallbacks, a new `serve` output type) are on the main branch and unreleased as of this check.
- tower-http 0.7: `TimeoutLayer::new` is deprecated since 0.6.7; use `TimeoutLayer::with_status_code(status, timeout)`. 0.7 adds `CsrfLayer` (checks `Sec-Fetch-Site` and `Origin`) and drops the no-op `tokio` and `async-compression` features.
- reqwest 0.13: rustls is the default TLS backend, with the aws-lc crypto provider. The `rustls-tls` feature is now `rustls`, and `query` and `form` are opt-in features. A built-in retry policy exists since 0.12.23.
- sqlx 0.9: MSRV 1.94. `query*()` functions take `impl SqlSafeStr`, implemented only for `&'static str` and `AssertSqlSafe`. `offline` is its own feature, and the combined runtime-plus-TLS features are gone.

## Entry point

- `main` only wires things together: load config, set up tracing, build the pool, clients, and `AppState`, serve, then shut down. A binary returns `anyhow::Result<()>`.
- `AppState` holds handles that are cheap to clone (`PgPool` and `reqwest::Client` already are) and goes to the router with `with_state`.

## HTTP server (axum)

```rust
fn router(state: AppState) -> Router {
    Router::new()
        .route("/orders/{id}", get(get_order))
        .route("/healthz", get(|| async { StatusCode::OK }))
        .layer(
            ServiceBuilder::new()
                .layer(SetRequestIdLayer::x_request_id(MakeRequestUuid))
                .layer(TraceLayer::new_for_http())
                .layer(PropagateRequestIdLayer::x_request_id())
                .layer(TimeoutLayer::with_status_code(
                    StatusCode::SERVICE_UNAVAILABLE,
                    Duration::from_secs(10),
                ))
                .layer(RequestBodyLimitLayer::new(1024 * 1024)),
        )
        .with_state(state)
}

async fn get_order(
    State(state): State<AppState>,
    Path(id): Path<OrderId>,
) -> Result<Json<OrderView>, ApiError> {
    let order = state.orders.get(id).await?;
    Ok(Json(OrderView::from(order)))
}
```

- `ServiceBuilder` applies layers top to bottom, outermost first. Here the request id is set before `TraceLayer` opens its span.
- Extractors parse into typed values: `Path<OrderId>` with a validating `Deserialize` on the newtype, `Json<CreateOrder>` with only the fields a caller may set.
- axum's `DefaultBodyLimit` caps the `Json` and `Bytes` extractors at 2 MB by default. Set it per route, or put `RequestBodyLimitLayer` in front of everything.
- tower middleware that can fail (`ConcurrencyLimitLayer`, `LoadShedLayer`, tower's own timeout) needs `HandleErrorLayer` in front of it, because axum only accepts services whose error type is `Infallible`.
- CORS through `CorsLayer` with an explicit origin list; `CsrfLayer` for browser endpoints that authenticate with cookies.

## Errors to responses

One `ApiError` enum implements `IntoResponse` and maps domain errors to a status in one `match` (`errors.md`). Callers get a code; the error chain goes to the log.

```rust
impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, code) = match &self {
            ApiError::NotFound => (StatusCode::NOT_FOUND, "not_found"),
            ApiError::Conflict => (StatusCode::CONFLICT, "conflict"),
            ApiError::Internal(err) => {
                tracing::error!(error = ?err, "request failed");
                (StatusCode::INTERNAL_SERVER_ERROR, "internal")
            }
        };
        (status, Json(serde_json::json!({ "code": code }))).into_response()
    }
}
```

## Graceful shutdown

```rust
let token = CancellationToken::new();
let tracker = TaskTracker::new();
tracker.spawn(cancel_on_signal(token.clone())); // ctrl_c and SIGTERM, then token.cancel()

let listener = tokio::net::TcpListener::bind(cfg.listen_addr).await?;
axum::serve(listener, router(state))
    .with_graceful_shutdown(token.clone().cancelled_owned())
    .await?;

tracker.close();
tokio::time::timeout(cfg.drain_timeout, tracker.wait()).await?;
pool.close().await;
```

- `with_graceful_shutdown` stops accepting connections and waits for open ones, with no deadline of its own. The request `TimeoutLayer` limits how long an in-flight request can hold shutdown open; keep it, plus the drain timeout, under the platform's grace period.
- Signal handling, `CancellationToken`, and `TaskTracker`: `concurrency.md`.

## HTTP client (reqwest)

- Build one `reqwest::Client` at startup and clone it; clones share the connection pool. `reqwest::get` builds a new client on every call.
- reqwest does not set a total timeout by default. Set `connect_timeout` and `timeout` on the builder, and `RequestBuilder::timeout` for a slower endpoint.
- Check the status before decoding (`error_for_status()` or a `match` on `status()`), and map non-2xx answers to a typed error that holds the status and a truncated body.
- Retries: `ClientBuilder::retry` with a policy from `reqwest::retry::for_host`. A policy comes with a retry budget (20% extra requests by default), and your classifier decides what is safe to resend. A `POST` that creates or charges is retried only with an idempotency key (skill `services`, `references/resilience.md`).

```rust
let retry = reqwest::retry::for_host("api.provider.test")
    .max_retries_per_request(2)
    .classify_fn(|rr| {
        let transient = rr.error().is_some()
            || matches!(rr.status().map(|s| s.as_u16()), Some(429 | 502 | 503 | 504));
        if transient && rr.method().is_idempotent() {
            rr.retryable()
        } else {
            rr.success()
        }
    });

let client = reqwest::Client::builder()
    .connect_timeout(Duration::from_secs(2))
    .timeout(Duration::from_secs(10))
    .retry(retry)
    .build()?;
```

## Database (sqlx)

- One `PgPool` built at startup with `PgPoolOptions` (`max_connections`, `acquire_timeout`) and a server-side `statement_timeout` through `PgConnectOptions::options([("statement_timeout", "5s")])`.
- `query!` and `query_as!` check SQL against the schema at compile time. Commit the `.sqlx/` directory from `cargo sqlx prepare`, and enable the `offline` feature when CI builds without a database.
- Dynamic SQL goes through `QueryBuilder` with `push_bind`. A `format!` string has to be wrapped in `AssertSqlSafe` to compile, so every `AssertSqlSafe` in a diff gets checked for caller input inside the string.
- Transactions: `let mut tx = pool.begin().await?`, queries on `&mut *tx`, then `tx.commit().await?`. Dropping `tx` without a commit rolls back. No outbound HTTP call while `tx` is open.
- A guarded status change checks `rows_affected()` on `UPDATE orders SET status = 'paid' WHERE id = $1 AND status = 'pending'`.
- Migrations: `sqlx::migrate!()` embeds `./migrations`. Whether it runs at startup or as a separate job follows the repo; changes others depend on go through skill `migrations`.
- Money columns are `NUMERIC`, read as `rust_decimal::Decimal` (feature `rust_decimal`) or `bigdecimal`, never `f64` (skill `money`).

## Logging and tracing

- `tracing` for events and spans. In production, `tracing-subscriber` with `fmt().json()` (feature `json`) and `EnvFilter` (feature `env-filter`).
- `#[tracing::instrument(skip_all, fields(order_id = %id))]` on handlers and outbound calls. `skip_all` keeps arguments, which may hold secrets or large bodies, out of the span.
- Values go in fields: `tracing::info!(order_id = %id, "order placed")`.
- Secrets are `secrecy::SecretString`, whose `Debug` output is redacted. Call `expose_secret()` only where the value is sent.
- `TraceLayer::new_for_http()` opens one span per request. Export to OpenTelemetry through `tracing-opentelemetry`, on the release that matches the `opentelemetry` crate version.

## Config

- One `Config` struct loaded once in `main` (`Config::from_env() -> Result<Config, ConfigError>`), with typed fields (`Duration`, `SocketAddr`, `Url`, `SecretString`) and every missing or bad key collected into one error.
- Use the repo's config crate if it has one, and `std::env::var` in that one function otherwise. Components get the sub-struct they need; no global config.

## Ops endpoints

- `/healthz` answers 200 without touching dependencies. `/readyz` checks the pool with a short timeout and answers 503 once shutdown starts.
- Metrics through the repo's choice (`metrics` with an exporter, or OpenTelemetry). Label by the `MatchedPath` extractor (`/orders/{id}`), never the raw path.

## Testing

- Router tests run without a socket: `router(state).oneshot(request).await` with `tower::ServiceExt`.
- Outbound calls run against `wiremock`: a delayed response (`ResponseTemplate::set_delay`) for timeouts, and `503` followed by `200` for retries.
- `#[sqlx::test]` gives each test its own database with migrations applied.

## Avoid

- `reqwest::get`, a client built per request, or a client with no timeouts.
- `/:id` routes in axum 0.8 code; `TimeoutLayer::new`.
- `AssertSqlSafe(format!(...))` with caller input in the string.
- `f64` for money columns.
- Request work spawned outside the tracker, or blocking calls inside handlers (`concurrency.md`).
