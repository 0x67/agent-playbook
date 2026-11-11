# Go Concurrency

Loaded via `golang` SKILL.md routing table. Sources: Go Code Review Comments, Go Memory Model, Uber Go Style, `golang.org/x/sync` docs, go.dev/blog/context, `testing/synctest` docs.

## Goroutine contract

Before `go f()` answer three questions, in code or comment:

1. Who starts it, and does caller expect that?
2. What stops it? ctx cancel, channel close, done signal.
3. Where does its error or panic go?

- No fire-and-forget. Every goroutine joined via `errgroup`, `sync.WaitGroup`, or owner's `Close()`.
- No goroutines in `init()`, package-level vars, or constructors that return before goroutine is owned.
- Library functions synchronous. Caller adds `go`.
- Long-lived goroutines belong to struct with `Run(ctx) error` or `Start(ctx)` / `Close()`.
- Panic in goroutine kills process. Worker goroutines recover and convert to error, or provably cannot panic.

## Context

- `ctx context.Context` first param. Never struct field. Never nil: `context.TODO()` while wiring.
- Derive, do not replace: `ctx, cancel := context.WithTimeout(ctx, d); defer cancel()`. `lostcancel` vet enforces.
- `signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)` in `main`.
- Every blocking op selects on `ctx.Done()`: channel send/recv, sleep, dial, queue pop.
- `context.WithoutCancel(ctx)` (1.21+) for work that must outlive request (audit log, cache fill). Comment why.
- `context.AfterFunc(ctx, f)` (1.21+) for cleanup on cancel without goroutine.
- `context.WithCancelCause` / `context.Cause` when callers must know why.
- Context values: request-scoped metadata only (trace id, principal). Never dependencies, never options. Typed unexported key, accessor func.

## Fan-out

Default: `golang.org/x/sync/errgroup`.

```go
g, ctx := errgroup.WithContext(ctx)
g.SetLimit(runtime.GOMAXPROCS(0))
results := make([]Result, len(items)) // disjoint indexes, no mutex
for i, item := range items {
	g.Go(func() error {
		r, err := process(ctx, item) // ctx cancels siblings on first error
		if err != nil {
			return fmt.Errorf("item %d: %w", i, err)
		}
		results[i] = r
		return nil
	})
}
if err := g.Wait(); err != nil {
	return nil, err
}
```

- `SetLimit` always for unbounded input. Unbounded goroutines = OOM under load.
- No errors to collect: `sync.WaitGroup` with `wg.Go(func())` (1.25+). Before 1.25: `wg.Add(1)` before `go`, `defer wg.Done()` inside. `waitgroup` vet catches misplaced Add.
- Bounded worker pool only when workers hold expensive state (connection, buffer). Otherwise `SetLimit` is the pool.
- Weighted limits: `golang.org/x/sync/semaphore`. Buffered channel as semaphore acceptable in small scope.
- Dedupe concurrent identical calls: `golang.org/x/sync/singleflight`.

## Channels

- Size 0 (sync handoff) or 1 (single-slot signal). Larger needs comment stating why and what bounds it.
- Direction in signatures: `func producer(out chan<- T)`, `func consumer(in <-chan T)`.
- Sender closes. Receiver never closes. Multiple senders: nobody closes directly; `WaitGroup` then one closer.
- Close means "no more values". Never close to send data. Never close twice.
- `for v := range ch` until closed. `v, ok := <-ch` when close matters.
- nil channel blocks forever: set case channel to nil in `select` to disable it.
- `select` with `ctx.Done()` in every loop. `default` only for non-blocking try.
- Pipeline stage owns its output channel, closes when input drains. `errgroup` around stages.
- `chan struct{}` for signals. `chan error` size 1 for single result from goroutine.
- `sigchanyzer` vet: `signal.Notify` needs buffered channel. Prefer `NotifyContext`.

## Locks

- `sync.Mutex` zero value ready. Named field `mu` directly above guarded fields, comment lists them.
- Never copy struct holding mutex (`copylocks` vet). Pointer receiver.
- Critical section minimal. No I/O, channel ops, callbacks, or `.Wait()` while locked. Copy data out, unlock, then work.
- `defer mu.Unlock()` right after `Lock()` unless early unlock is essential and obvious.
- `RWMutex` only when profile shows read-heavy contention. `RLock` not free.
- Lock ordering documented when two locks may nest. Prefer one lock.
- Never embed `sync.Mutex` in exported struct: exports `Lock`/`Unlock`.
- Channels model ownership transfer and pipelines. Mutexes protect shared in-memory state. Do not force one onto the other's job.

## Once, atomics, sync.Map, Pool

- `sync.Once`, `sync.OnceFunc`, `sync.OnceValue`, `sync.OnceValues` (1.21+) for lazy init. Not double-checked locking.
- Atomics: typed `atomic.Int64`, `atomic.Bool`, `atomic.Pointer[T]` (1.19+). Not `atomic.AddInt64(&x, 1)`. `atomictypes` modernizer rewrites.
- Atomics for counters, flags, config swap. Multi-field invariants: mutex.
- `sync.Map` only for append-mostly caches or disjoint key sets per goroutine. Otherwise `map` + `Mutex`.
- `sync.Pool` for hot large temporary buffers. Reset before Put. Never pool small or long-lived objects.

## Timers

- go.mod >= 1.23: unreferenced `time.Timer`/`Ticker` are GC-safe without `Stop`. Timer channels unbuffered; `Reset`/`Stop` never leave stale value.
- Still `defer ticker.Stop()` for clarity and older modules.
- `time.After` in `select` inside loop: fine >= 1.23, leak before. `time.NewTimer` + `Reset` in hot loops either way.
- `time.Sleep` never for polling in production. Ticker + ctx.
- Tests: inject clock or use `testing/synctest`.

## Shutdown

Order: stop accepting, drain in-flight with deadline, stop workers, flush telemetry, close pools, exit.

1. `signal.NotifyContext` cancels root ctx.
2. Servers: `srv.Shutdown(ctxWithTimeout)`. Workers: close input, `g.Wait()`.
3. Flush logs, traces. Close DB pools last.
4. Deadline exceeded: force close, exit non-zero.

- Shutdown funcs idempotent. `Close()` twice must not panic.
- Never `os.Exit` from goroutines. Return error to `main`.

## Leaks and races

- `go test -race ./...` on every concurrency change. Non-negotiable.
- Goroutine leak profile (GA 1.27; `GOEXPERIMENT=goroutineleakprofile` on 1.26): `/debug/pprof/goroutineleak`. Run in long tests or staging.
- `runtime.NumGoroutine()` delta in tests, or `go.uber.org/goleak` when repo has it.
- Common leaks: goroutine blocked on send to abandoned channel, missing `ctx.Done()` case, HTTP body not closed, ticker in abandoned loop before 1.23.
- Data race is undefined behavior, not eventual consistency. Fix, never tolerate.
- Memory model: `chan`, `sync`, `atomic` ops establish happens-before. Plain reads of shared vars need one of them.

## Testing concurrency

- `testing/synctest` (1.25+): `synctest.Test(t, func(t *testing.T) { ... })`. Fake time inside bubble, `synctest.Wait()` blocks until all bubble goroutines idle, `synctest.Sleep` (1.27+). Deterministic timeouts, tickers, debouncers.
- Before 1.25: inject clock, use channels as rendezvous. Never `time.Sleep` to wait for goroutine.
- `t.Parallel()` on tests without shared state. Surfaces races between tests.
- Assert via channels/WaitGroup outcomes, never `runtime.Gosched()` luck.

## Chooser

| Need | Use |
|---|---|
| N tasks, first error cancels rest | `errgroup.WithContext` + `SetLimit` |
| N tasks, no errors | `sync.WaitGroup.Go` |
| Bound concurrency | `errgroup.SetLimit`, `semaphore.Weighted` |
| Cancel, timeout, deadline | `context` |
| Hand value between goroutines | unbuffered channel |
| Signal done | close `chan struct{}` or ctx cancel |
| Protect shared map/struct | `sync.Mutex` |
| Counter, flag, pointer swap | `atomic.Int64`, `atomic.Bool`, `atomic.Pointer` |
| Lazy singleton | `sync.OnceValue` |
| Collapse duplicate calls | `singleflight.Group` |
| Periodic work | `time.Ticker` + `select` on ctx |
| Deterministic time in tests | `testing/synctest` |
| Buffer reuse | `sync.Pool` |

## Avoid

- `go func()` without join or ctx.
- Channels as mutexes, mutexes as channels.
- Buffered channel "for performance" without measurement.
- `select {}` to block main. Wait on ctx or errgroup.
- `runtime.Gosched()`, `time.Sleep` for synchronization.
- Holding lock across `http.Do`, DB call, channel op, callback.
- `sync.Mutex` by value in map or passed by value.
- Global `sync.Map` cache without eviction.
- Unbounded goroutine per message in workers.
- Retry loops ignoring `ctx.Done()`.
