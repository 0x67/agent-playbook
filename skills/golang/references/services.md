# Go Services

Loaded via `golang` SKILL.md routing table. Sources: `net/http` docs, go.dev/blog/routing-enhancements, go.dev/blog/slog, pgx and sqlc docs, connectrpc.com docs, buf docs.

## Entry point

- `cmd/<app>/main.go`: signal ctx, load config, `run(ctx, cfg, ...) error`, print error, exit. Pattern in `errors.md`.
- `run` wires dependencies explicitly: config, logger, DB pool, clients, handlers, server. No DI framework. No globals.
- Constructor per component: `NewServer(cfg, log, store) *Server`. Dependencies as params; interfaces where tests substitute.
- Fail fast at startup: validate config, ping DB, bind port. One log line with version and addr.

## HTTP server

Stdlib first. Router library (`chi`) only when repo already uses one.

```go
mux := http.NewServeMux()
mux.HandleFunc("GET /users/{id}", s.getUser)
mux.HandleFunc("POST /users", s.createUser)
mux.HandleFunc("GET /files/{path...}", s.serveFile)
mux.HandleFunc("GET /{$}", s.index) // exact root only

srv := &http.Server{
	Addr:              cfg.Addr,
	Handler:           chain(mux, recoverer(log), requestID, logging(log)),
	ReadHeaderTimeout: 5 * time.Second,
	ReadTimeout:       15 * time.Second,
	WriteTimeout:      30 * time.Second,
	IdleTimeout:       120 * time.Second,
	BaseContext:       func(net.Listener) context.Context { return ctx },
}
```

- Patterns (1.22+): method prefix, `{id}` wildcard, `{path...}` rest, `{$}` exact. `r.PathValue("id")`. Mux panics on conflicting patterns at registration: test route table.
- Timeouts always set. Zero timeouts = slowloris.
- Handler methods on server struct: `func (s *Server) getUser(w http.ResponseWriter, r *http.Request)`. ctx via `r.Context()`.
- Body cap before decode: `r.Body = http.MaxBytesReader(w, r.Body, 1<<20)`.
- Response: headers, `w.WriteHeader(code)` once, body. `respondJSON(w, code, v)` helper; encode error only loggable after header written.
- Handler: decode, call domain, encode. Domain returns error; one `status(err)` switch maps it (`errors.md`).
- `http.CrossOriginProtection` (1.25+) for cookie-auth browser clients. `http.TimeoutHandler` for per-route deadlines.
- Static: `http.FileServerFS(embedFS)` with `//go:embed`.

## Middleware

```go
type Middleware func(http.Handler) http.Handler

func chain(h http.Handler, m ...Middleware) http.Handler {
	for i := len(m) - 1; i >= 0; i-- {
		h = m[i](h)
	}
	return h
}

func requestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := r.Header.Get("X-Request-ID")
		if id == "" {
			id = uuid.New().String() // stdlib uuid on 1.27+, github.com/google/uuid before
		}
		ctx := context.WithValue(r.Context(), ctxKeyRequestID{}, id)
		w.Header().Set("X-Request-ID", id)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
```

- Order outermost first: recover, request id, logging, auth, rate limit, timeout, handler.
- Recover middleware: log stack, 500, no re-panic. `http.ErrAbortHandler` passes through.
- Status capture wrapper minimal. Preserve `http.Flusher`/`http.Hijacker` via `http.NewResponseController` (1.20+).
- Auth puts principal in ctx via typed key + accessor `PrincipalFrom(ctx) (Principal, bool)`.

## Graceful shutdown

```go
func run(ctx context.Context, cfg Config, log *slog.Logger) error {
	srv := newServer(ctx, cfg, log)

	errc := make(chan error, 1) // buffered: goroutine exits even if nobody reads
	go func() { errc <- srv.ListenAndServe() }()

	select {
	case err := <-errc:
		return fmt.Errorf("listen %s: %w", cfg.Addr, err)
	case <-ctx.Done():
	}

	shutdownCtx, cancel := context.WithTimeout(context.WithoutCancel(ctx), 15*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		_ = srv.Close()
		return fmt.Errorf("shutdown: %w", err)
	}
	return nil
}
```

- `ListenAndServe` returns `http.ErrServerClosed` after `Shutdown`; expected, ignored.
- Readiness flips to 503 before `Shutdown` so load balancer drains. k8s: preStop hook or short sleep only when platform needs it.
- Order: stop ingress, drain, stop workers, flush telemetry, close pools.

## HTTP client

- Never bare `http.Get` or `http.DefaultClient`. `&http.Client{Timeout: d, Transport: t}` built once, injected.
- Every request `http.NewRequestWithContext(ctx, ...)`. `noctx` linter.
- `defer resp.Body.Close()` always, even on error status. Drain small bodies for connection reuse. `bodyclose` linter.
- Check `resp.StatusCode` before decoding. Non-2xx into typed error with status and truncated body.
- Reuse one `http.Transport`. Tune `MaxIdleConnsPerHost` for high fan-out to one host.
- Retries: idempotent methods only, exponential backoff with jitter, honor `Retry-After`, bounded by ctx.
- Client struct wraps base URL, `*http.Client`, auth. Method per endpoint, typed results.

## JSON

- `json.NewDecoder(r).Decode(&v)`. `dec.DisallowUnknownFields()` for strict APIs.
- Tags on every field: `json:"user_id"`. `omitempty` for pointers/slices/maps. `omitzero` (1.24+) for structs and `time.Time`.
- Request/response DTOs separate from domain types. Map explicitly.
- `encoding/json/v2` (stable 1.27; `GOEXPERIMENT=jsonv2` on 1.25/1.26): stricter defaults (rejects duplicate keys, invalid UTF-8), `json.MarshalWrite(w, v)`, `json.UnmarshalRead(r, &v)`, `json.RejectUnknownMembers(true)`. Use when go.mod >= 1.27 and repo opts in. Never mix v1 and v2 in one package.
- IDs and money: `int64`, `string`, or decimal type. Never `float64`.

## Logging

`log/slog` only. No `log.Printf` in libraries. No `fmt.Println` in services.

```go
log := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: cfg.LogLevel}))
slog.SetDefault(log) // only so third-party log.Printf lands in JSON
```

- One logger built in `run`, injected. Scoped: `log = log.With("component", "worker", "queue", q)`.
- Message: constant lowercase phrase. Variables as attributes: `log.InfoContext(ctx, "user created", "user_id", id)`. Never `Sprintf` into message.
- `*Context` variants when ctx available; handlers pull trace id.
- Hot paths: typed `slog.Attr` (`slog.String`, `slog.Int`), `log.LogAttrs(ctx, level, msg, attrs...)` zero-alloc.
- `slog` vet catches odd key/value pairs. `sloglint` enforces style.
- Levels: Debug (dev detail), Info (state change, request summary), Warn (degraded, retried), Error (failed, needs human). Error logged once with `"err", err`, at top of chain.
- Dev: `slog.NewTextHandler`. Prod: JSON. Tests: `slog.New(slog.DiscardHandler)` (1.24+) or `slog.NewTextHandler(t.Output(), nil)` (1.25+).
- `slog.NewMultiHandler(h1, h2)` (1.26+) fans out. `slog.LevelVar` for runtime level change.
- Never log secrets, tokens, full bodies, PII by default. `slog.LogValuer` on sensitive types to redact.

## Config

- Priority: flags > env > file > defaults. One `Config` struct, one `LoadConfig(args, getenv) (Config, error)`.
- Stdlib `flag` sufficient. `cobra` when repo uses it or CLI has subcommands; use `cmd.Context()`.
- `os.LookupEnv` distinguishes unset from empty. `time.ParseDuration` for durations. Validate at load; one error listing all problems via `errors.Join`.
- Secrets from env or files, never flags (visible in `ps`). Never log config with secrets: `LogValuer` redaction.
- No `viper` unless present. No config globals: pass `Config` or sub-structs.

## Database

Postgres: `github.com/jackc/pgx/v5` + `pgxpool`. Queries: `sqlc` generating typed funcs. `database/sql` when driver-agnostic or repo standard. ORMs (`gorm`, `ent`) only when repo already uses.

```go
func (s *Store) WithTx(ctx context.Context, fn func(pgx.Tx) error) (err error) {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return fmt.Errorf("begin tx: %w", err)
	}
	defer func() {
		if p := recover(); p != nil {
			_ = tx.Rollback(ctx)
			panic(p)
		}
		if err != nil {
			_ = tx.Rollback(ctx) // rollback error irrelevant, original err wins
		}
	}()
	if err := fn(tx); err != nil {
		return err
	}
	if err := tx.Commit(ctx); err != nil {
		return fmt.Errorf("commit tx: %w", err)
	}
	return nil
}
```

- `ctx` on every call. Statement timeout via ctx deadline or pool config.
- `defer rows.Close()`, `rows.Err()` after loop. `sqlclosecheck`, `rowserrcheck` linters.
- Map driver errors at store layer: `pgx.ErrNoRows` to `ErrNotFound`; unique violation (`*pgconn.PgError` code `23505`) to `ErrConflict`. Callers never see driver types.
- Parameters bound (`$1`), never string-built SQL. `gosec` G201/G202.
- Pool: `MaxConns` near DB cores times 2-4, not hundreds. One pool per process, injected.
- Migrations: repo's tool (`goose`, `golang-migrate`, `atlas`, `tern`). Versioned files in `migrations/`, applied by separate command or startup flag. Never silent auto-migrate in prod.
- Tests: real Postgres via container or `TEST_DATABASE_URL`; isolate by tx rollback or unique schema. Store interface at consumer for unit tests above store.

## gRPC and Connect

- New services: `connectrpc.com/connect` + `buf`. Handlers mount on `http.ServeMux`, reuse net/http middleware, speak gRPC, gRPC-Web, and Connect (JSON or proto) on one port. `h2c` for HTTP/2 without TLS internally.
- Existing gRPC ecosystem (`grpc-go` interceptors, xDS, grpc-gateway): stay on `google.golang.org/grpc`.
- `buf.yaml` + `buf.gen.yaml`. `buf lint`, `buf format`, `buf breaking --against '.git#branch=main'` in CI. Never hand-run `protoc`.
- Proto style: package `acme.user.v1`, request/response message per RPC (`GetUserRequest`), `snake_case` fields, enums with `_UNSPECIFIED = 0`. `protovalidate` for constraints.
- Generated code committed under `gen/` or produced in CI; one policy, never both.
- Errors: `connect.NewError(connect.CodeNotFound, err)` or `status.Error(codes.NotFound, ...)` mapped in transport layer. Never leak internals on `Internal`.
- Deadlines propagate from ctx. Client-side timeout per call.
- Interceptors mirror HTTP middleware: recover, logging, auth, metrics.

## Ops endpoints

- `GET /healthz` liveness: process up, no dependencies. `GET /readyz` readiness: dependencies pingable, 503 during shutdown.
- `net/http/pprof`, `expvar` on separate admin listener (localhost or internal port). Never on public mux.
- Metrics: `prometheus/client_golang` or OpenTelemetry per repo. `otelhttp.NewHandler` for traces. Request id on every log line.
- Version: `debug.ReadBuildInfo()` for module version and VCS revision (stamped by default via `-buildvcs`).

## Workers and queues

- Worker owns loop: `Run(ctx) error` blocks until ctx done or fatal. Started via `errgroup` in `run`.
- Poll with ticker + ctx, never `time.Sleep`. Backoff on empty or error.
- Bounded in-flight per worker (`SetLimit`). Ack/commit only after durable side effect.
- Idempotent handlers: at-least-once delivery is the norm.
- Shutdown: stop polling, finish in-flight within deadline, nack the rest.

## Layering

```
cmd/<app>            main, run, wiring
internal/<domain>    types, rules, Store/Client interfaces it consumes
internal/store       pgx + sqlc implementation
internal/httpapi     handlers, DTOs, middleware, error-to-status
internal/rpcapi      connect handlers
internal/worker      queue consumers
```

- Dependencies point inward: transport imports domain; domain imports no internal package. Store implements domain's interface.
- Interfaces live in consumer (domain), implemented in store/client packages.
- No `pkg/`. No `models` package holding every struct. Types live with behavior.
- Logger, tracer injected, never global.

## Avoid

- Global `var DB`, `var Log`.
- Framework lock-in (`gin`, `echo`, `fiber`) for new services. Stdlib mux + small middleware suffices.
- `map[string]any` JSON beyond the boundary. Decode into structs.
- Business logic in handlers.
- Panic as flow control caught by recover middleware.
- Unbounded `go` per message in workers.
- `context.Background()` inside request handling. `r.Context()`; `WithoutCancel` when work must outlive request.
