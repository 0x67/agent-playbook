# Rust Concurrency

Loaded via `rust` SKILL.md routing table. Sources: Rustonomicon, `std::sync` docs, tokio docs and tutorial (shutdown), tokio-util docs (`CancellationToken`, `TaskTracker`), parking_lot, crossbeam, DashMap, "Cancelling async Rust" (sunshowers).

## Ownership, borrowing, lifetimes

- One clear owner, then borrowing, then shared ownership. In that order.
- `&T` over clone unless ownership transfer is needed. `&mut T` when borrowed data must change.
- Clone intentionally: cheap clones fine; no allocation or refcount churn in hot paths.
- Lifetimes annotated only when the compiler cannot infer or the signature reads clearer.
- Owned values at task and thread boundaries when borrowed lifetimes make ownership unclear. `std::thread::scope` (1.63+) when borrowing across threads is the point.
- No self-referential structs without a proven abstraction that documents pinning.
- `Arc::unwrap_or_clone`, `Arc::make_mut` for copy-on-write. `Arc<str>`, `Arc<[T]>` for shared immutable data.

## Shared ownership

- `Rc<T>` single-threaded, `Arc<T>` across threads or tasks.
- `&T` for ordinary read-only calls. `Arc<T>` by value when callee stores it, spawns, or needs shared ownership. `&Arc<T>` only when callee must clone, downgrade, or inspect refcount.
- Struct-level ownership design over widespread `Arc`. `Arc<Mutex<T>>` everywhere means the ownership model is unclear.
- `Weak<T>` to break cycles (parent pointers, caches).

## Interior mutability

- `Cell<T>` for `Copy` values, `RefCell<T>` single-threaded. `Cell::update` (1.88+).
- `Mutex<T>` / `RwLock<T>` for multi-threaded. Zero-value ready: `Mutex::new(T)` in constructors, never `Option<Mutex>`.
- Lock scope minimal and explicit. Copy or clone needed data out, drop the guard, then work.
- No lock across `.await`. No lock across I/O, channel ops, callbacks.
- `Mutex` over `RwLock` unless read-heavy contention is measured. `RwLockWriteGuard::downgrade` (1.92+) when write-then-read.
- Poisoning: `lock().unwrap_or_else(PoisonError::into_inner)` when the protected data stays valid after a panic; propagate otherwise. Comment the choice.
- Message passing over shared mutable state when ownership can move.

## One-time init and atomics

- `std::sync::LazyLock` / `OnceLock` (1.80+) for lazy statics. `lazy_static!`, `once_cell::sync::Lazy` only in code already using them. `LazyCell` / `OnceCell` single-threaded.
- `Once::wait` (1.86+) to block until init done.
- Atomics for counters, flags, config swaps (`AtomicPtr`, `arc-swap`). Multi-field invariants: mutex.
- `fetch_update` / `update` (1.95+) for read-modify-write loops.
- Ordering: `Relaxed` for independent counters; `Acquire`/`Release` for publish-subscribe of other memory; `SeqCst` only with a documented reason. Comment non-obvious choices.
- `loom` tests for any hand-rolled lock-free structure.

## `parking_lot`

- Ergonomic alternative to `std::sync` locks: no poisoning, smaller, fair unlock, `try_lock_for`.
- Use when measured contention, timed acquisition, or repo standard. Caveat: invariants after panic are on you. Not async-aware.

## `DashMap`

- High-concurrency map when one `Mutex<HashMap>` is a measured bottleneck and access is per independent key.
- No guard across `.await`. No re-entry into the same map while holding a guard. Iteration is not a snapshot. Not for multi-key transactions or small low-contention maps.

## `crossbeam` and `rayon`

- `crossbeam-channel` for blocking MPMC, `select!` over sync channels, `crossbeam::scope` when `std::thread::scope` lacks a feature.
- `rayon` for CPU-bound data parallelism (`par_iter`). Never inside a tokio worker thread without `spawn_blocking`.
- `std::sync::mpsc` fine for simple single-consumer sync channels.

## Async: tokio

- Runtime threads never block: file I/O, DNS, CPU-heavy work, sync locks with contention, `std::thread::sleep` go to `tokio::task::spawn_blocking` or `rayon`.
- Async fn in traits native (1.75+). Public traits needing `Send` futures: `trait_variant::make(Send)` or explicit `-> impl Future<Output = T> + Send`. `#[async_trait]` only when `dyn Trait` with async methods is required and repo already uses it.
- Async closures (1.85+): `async |x| { ... }` with `AsyncFn`, `AsyncFnMut`, `AsyncFnOnce` bounds. Replaces `|x| async move { ... }` when borrowing the closure's captures matters.
- `tokio::sync::{Mutex, RwLock}` only when a guard must be held across `.await`. `std::sync` or `parking_lot` for short non-await critical sections is faster.
- `Semaphore` for bounded concurrency (`acquire_owned` for spawned tasks). `mpsc` bounded for backpressure; unbounded only with a documented bound elsewhere. `oneshot` for single reply. `watch` for latest-value config. `broadcast` for fan-out with lag policy. `Notify` for wakeups.
- `tokio::time::timeout` around every external await. `tokio::time::sleep` never in loops for polling; `interval` with `MissedTickBehavior` set.
- `Pin`: `std::pin::pin!` for stack pinning in `select!` loops. `Box::pin` for stored futures. `pin-project-lite` for manual `Future` impls.

## Task lifecycle

- Every `tokio::spawn` has an owner that awaits, aborts, or tracks it. No fire-and-forget.
- `JoinSet` when results are collected or tasks must abort on drop. `JoinSet::join_all`, `join_next`, `abort_all`.
- `tokio_util::task::TaskTracker` when tasks are many, long-lived, and results are not collected: memory freed at exit, cloneable, `close()` then `wait()`. Does not abort on drop.
- `JoinError::is_panic()` handled at the owner: log with task name, decide restart or shutdown.
- `tokio::task::Builder::name` (unstable) or a name field in the task's struct for diagnostics. `tokio-console` when repo has it.

## Cancellation

- Cancellation is dropping the future. Happens only at `.await` points. CPU loops must check `token.is_cancelled()` or yield.
- `tokio_util::sync::CancellationToken`: clone into tasks, `child_token()` for subtrees, `cancelled()` in `select!`. `drop_guard()` to cancel when the owner drops.
- `select!` cancel safety: a branch that loses drops its future. Safe: `mpsc::Receiver::recv`, `sleep`, `Notify::notified`, `TcpListener::accept`, `AsyncReadExt::read`. Unsafe (loses data on drop): `read_exact`, `write_all`, `Mutex::lock` mid-critical-section, any future holding partial state. Wrap unsafe ones in a task or store the future outside the loop with `pin!`.
- `biased;` in `select!` when priority matters (shutdown branch first).
- `tokio::task::yield_now().await` in long CPU sections that must stay cancellable; better to `spawn_blocking` them.

## Shutdown pattern

```rust
let token = CancellationToken::new();
let tracker = TaskTracker::new();

for conn in listener { // pseudo
    let token = token.child_token();
    tracker.spawn(async move {
        tokio::select! {
            biased;
            _ = token.cancelled() => { /* flush, close */ }
            res = handle(conn) => { if let Err(e) = res { tracing::warn!(error = %e, "conn failed") } }
        }
    });
}

tokio::signal::ctrl_c().await?;
token.cancel();
tracker.close();
tokio::time::timeout(Duration::from_secs(15), tracker.wait()).await?;
```

- Order: stop accepting, cancel token, drain with deadline, flush telemetry, close pools, return from `main`.
- `Drop` impls cannot await. Explicit `async fn shutdown(&self)` on components; `Drop` only as last-resort abort.
- Unix: `tokio::signal::unix::signal(SignalKind::terminate())` alongside `ctrl_c`.

## Choosing primitive

| Need | Use |
|---|---|
| Single owner | plain ownership, borrowing |
| Single-thread shared | `Rc<T>`, `Rc<RefCell<T>>` only when runtime checks are worth it |
| Shared immutable across threads | `Arc<T>`, `Arc<str>` |
| Shared mutable, low contention | `Arc<Mutex<T>>` |
| Shared mutable, read-heavy measured | `Arc<RwLock<T>>` |
| High contention or timed locks | `parking_lot` |
| Concurrent map, independent keys | `DashMap` |
| Config hot-swap | `arc_swap::ArcSwap`, `watch` |
| Lazy static | `LazyLock`, `OnceLock` |
| Counters, flags | atomics with ordering rationale |
| Borrow across threads | `std::thread::scope` |
| CPU parallel iteration | `rayon` |
| Async communication | `tokio::sync::{mpsc, oneshot, watch, broadcast}` |
| Bounded async concurrency | `Semaphore`, bounded `mpsc` |
| Collect task results / abort on drop | `JoinSet` |
| Track many long tasks, graceful drain | `TaskTracker` + `CancellationToken` |
| Blocking work in async | `spawn_blocking`, `rayon` bridge via `oneshot` |
| Sync threaded channel | `crossbeam-channel`, `std::sync::mpsc` |
| Verify lock-free code | `loom` |

## Avoid

- `Arc<Mutex<T>>` as default design.
- Holding `std::sync`, `parking_lot`, or `DashMap` guards across `.await`.
- Nested locks without documented order. Upgrading read to write while holding read.
- `RwLock` without measured read-heavy access.
- Premature lock-free structures.
- `tokio::spawn` without join, abort, or tracker. Spawning in `Drop`.
- Unbounded channels on externally-driven traffic.
- `block_on` inside a runtime thread. `Handle::block_on` from `spawn_blocking` only.
- `std::sync::Mutex` in async code when the critical section awaits.
- `#[async_trait]` on new traits when native async fn works.
- `tokio::select!` over non-cancel-safe futures in a loop.
- `static mut`. Atomics or `OnceLock`.
