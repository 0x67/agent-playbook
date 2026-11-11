# crossbeam and rtrb (Rust)

Loaded via the low-latency SKILL.md routing table. Checked against crossbeam-channel 0.5.17, crossbeam-utils 0.8.23, crossbeam-queue 0.3.14, rtrb 0.4.1 on 2026-11-06. Sources: crate source of each (lib docs, `flavors/`, `waker.rs`, `backoff.rs`, `cache_padded.rs`, CHANGELOG), crossbeam 0.8.5 source for the umbrella crate, tokio 1.54.1 source for the async boundary, disruptor 4.4.0 README for the comparison.

## When to use which

- `bounded(n)` with `n > 0`: preallocated array (Vyukov bounded MPMC). Default for thread-to-thread handoff. `Full` is the backpressure signal. Size `n` from peak burst rate times worst consumer stall, then measure.
- `unbounded()`: linked list of 31-slot blocks; the send path allocates a new block as it fills. `try_send` never returns `Full` and `is_full()` is always `false`. Only for streams whose rate is bounded by construction (control, lifecycle events).
- `bounded(0)`: rendezvous. Each send waits for a matching receive. For handoff or acknowledgement, never for throughput.
- `after`, `at`, `tick`, `never`: receive-only timer channels, generated lazily on receive, meant for `select!` arms.
- `crossbeam_queue::ArrayQueue`: bounded MPMC with no blocking, no disconnection, no select. `force_push` overwrites the oldest element (latest value wins). Bring your own wait strategy.
- `crossbeam_queue::SegQueue`: unbounded MPMC built from segments. Same growth risk as `unbounded()`.
- `rtrb::RingBuffer`: strict SPSC, wait-free push and pop, no allocation after `new`. The types enforce one producer and one consumer. There is no way to wait: the consumer polls.
- `disruptor` crate: when every handler must see every event (a crossbeam MPMC channel gives each message to exactly one receiver), with preallocated event slots, handler dependency chains, and busy-spin wait strategies that trade CPU for latency.
- Either side async: `tokio::sync::mpsc`. crossbeam-channel has no async API.

## Core API

- `bounded<T>(cap: usize) -> (Sender<T>, Receiver<T>)` (panics if `cap` is too large) and `unbounded<T>()`. Handles are `Clone`, and `Send + Sync` for `T: Send`. Clones share one stream; they do not fan out.
- `Sender::try_send(&self, T) -> Result<(), TrySendError<T>>`: `Full(T)` or `Disconnected(T)`, the message comes back.
- `Sender::send(&self, T) -> Result<(), SendError<T>>`: spins with `Backoff`, then parks the OS thread while full. `send_timeout(T, Duration)` and `send_deadline(T, Instant)` return `SendTimeoutError::{Timeout(T), Disconnected(T)}`, and still send if there is room after the deadline has passed.
- `Receiver::try_recv() -> Result<T, TryRecvError>` (`Empty`, `Disconnected`), `recv() -> Result<T, RecvError>`, `recv_timeout(Duration)` and `recv_deadline(Instant)` (`RecvTimeoutError::{Timeout, Disconnected}`). `try_iter()` drains what is buffered without blocking; `iter()` blocks.
- `len()`, `is_empty()`, `is_full()`, `capacity() -> Option<usize>` on both handles. A zero-capacity channel reports empty and full at once.
- `select!` picks a random ready arm; `select_biased!` picks the first ready arm. Arms: `recv(r) -> msg =>`, `send(s, m) -> res =>`, `default =>`, `default(Duration) =>`. `Select::new()` and `Select::new_biased()` build a set at runtime; the returned `SelectedOperation` must be finished with `.recv(&r)` or `.send(&s, m)`, and dropping it unfinished panics.
- `crossbeam_utils::CachePadded<T>`: `CachePadded::new(t)` (const), `Deref`/`DerefMut`, `into_inner()`. Aligns to 128 bytes on x86-64, aarch64, and powerpc64, 64 on most other targets. `repr(C)` since 0.8.22.
- `crossbeam_utils::Backoff`: `new()`, `spin()`, `snooze()`, `is_completed()`, `reset()`. It holds a `Cell<u32>`, so it is not `Sync`: one per wait loop.
- `crossbeam_utils::thread::scope` is soft-deprecated since Rust 1.63 in favor of `std::thread::scope`. Its spawn closure takes the scope (`s.spawn(|_| ...)`) and the call returns `thread::Result<R>` holding child panics.
- crossbeam-queue: `ArrayQueue::new(cap)` (panics on 0), `push(&self, T) -> Result<(), T>`, `force_push(&self, T) -> Option<T>`, `pop(&self) -> Option<T>`. `SegQueue::new()` (const), `push`, `pop`. `push_mut`/`pop_mut` skip the atomics when you hold `&mut`.
- rtrb: `RingBuffer::<T>::new(cap) -> (Producer<T>, Consumer<T>)`. `Producer::push(&mut self, T) -> Result<(), PushError<T>>` (`Full(T)`), `Consumer::pop(&mut self) -> Result<T, PopError>` (`Empty`), plus `peek`, `slots`, `is_abandoned`. Batches: `write_chunk(n)` (needs `T: Default`) or `write_chunk_uninit(n)` then `fill_from_iter`, `read_chunk(n)` then `commit_all()`, `push_entire_slice`/`pop_entire_slice` for `T: Copy`. Both handles are `Send`, not `Sync`.
- `crossbeam` 0.8.5 umbrella re-exports `channel`, `select`, `queue`, `deque`, `epoch`, `utils::{Backoff, CachePadded}`, and `scope`. Its default `std` feature already enables every subcrate, so `features = ["crossbeam-channel"]` adds nothing. Workspaces that declare both the umbrella and `crossbeam-channel` should pick one: depend on the subcrates actually used.

## Idioms

```rust
use crossbeam_channel::{select_biased, Receiver};

fn run(ctl: Receiver<Ctl>, data: Receiver<Msg>) {
    loop {
        select_biased! {
            recv(ctl) -> c => match c { Ok(c) => apply(c), Err(_) => return },
            recv(data) -> m => match m {
                Ok(m) => { handle(m); data.try_iter().for_each(handle) } // drain the burst
                Err(_) => return,
            },
        }
    }
}
```

- Control arm first in `select_biased!` so shutdown never waits behind a busy data arm. Control is rare, so it cannot starve data. Use `select!` when arms are peers.
- After a wake, `try_iter()` handles everything already buffered without another select round.

```rust
use crossbeam_channel::TrySendError;

match tx.try_send(msg) {
    Ok(()) => {}
    Err(TrySendError::Full(_msg)) => {
        stats.dropped.fetch_add(1, Relaxed); // policy: drop newest, count it
    }
    Err(TrySendError::Disconnected(_)) => return Err(Closed),
}
```

- Every bounded channel gets a written overflow policy next to its capacity: drop newest and count, drop oldest (`ArrayQueue::force_push`), fail fast and resync from a sequence number, or block on a dedicated thread with `send_timeout` so a stuck consumer surfaces as an error.

```rust
use crossbeam_utils::CachePadded;
use std::sync::atomic::{AtomicU64, Ordering::Relaxed};

let per_worker: Box<[CachePadded<AtomicU64>]> =
    (0..n).map(|_| CachePadded::new(AtomicU64::new(0))).collect();
per_worker[id].fetch_add(1, Relaxed); // each writer touches only its own line
let total: u64 = per_worker.iter().map(|c| c.load(Relaxed)).sum();
```

- Same rule for hand-rolled queues: head and tail indexes in separate `CachePadded` fields, as crossbeam and rtrb do internally.

```rust
use crossbeam_utils::Backoff;

let backoff = Backoff::new();
loop {
    let done = consumer.is_abandoned(); // read before pop so the last pushes are seen
    match consumer.pop() {
        Ok(ev) => { handle(ev); backoff.reset(); }
        Err(_) if done => break,
        Err(_) => backoff.snooze(),
    }
}
```

- `reset()` after progress so the next miss starts with short spins. On a pinned core reserved for this loop, call `spin()` instead of `snooze()`.
- A consumer that must react in microseconds polls `try_recv` or `pop` like this instead of parking in `recv`.

## Sharp edges

- Blocking calls in async code. `send`, `recv`, their timeout forms, and `iter()` park the OS thread, which on a tokio worker stalls every task scheduled there. A pattern seen in socket-reader tasks: `try_send` inside an `async fn`, then on `TrySendError::Full` a fallback to blocking `send` for backpressure. The reader stops polling its socket, and if the same task sends heartbeats, the session can time out. Fixes: run the reader on a dedicated OS thread where blocking is fine; or use `tokio::sync::mpsc` (`send(..).await` yields, the sync consumer calls `blocking_recv()`); or keep `try_send` with an explicit overflow policy.
- `tokio::task::block_in_place` is only a stopgap: it panics on a `current_thread` runtime and suspends other futures in the same task. tokio's `blocking_send` panics inside an async context; crossbeam gives no such warning.
- Unbounded growth. `unbounded()` and `SegQueue` never push back. A consumer that falls behind becomes queueing latency, then memory growth, then OOM, and the send path keeps allocating blocks. Overflow stays invisible because `try_send` never returns `Full`.
- Fairness. `select!` gives a hot data arm and a rare control arm equal odds each round. `select_biased!` starves later arms while the first stays ready. A disconnected receiver counts as ready forever, so a loop that ignores its `Err` spins at full CPU: return, or swap the handle for `never()`.
- Disconnection. After every `Sender` drops, receivers drain the buffer, then `recv` returns `Err(RecvError)` without blocking. Dropping every `Receiver` of an unbounded channel discards its buffered messages at once. A stray `Sender` clone kept on the consumer side holds the channel open, so `recv()` never ends and shutdown hangs. Timer channels never disconnect.
- Wake cost. While a receiver is parked, each send takes the waker lock and unparks it on the sender's thread. With no waiter the check is one atomic load.
- `bounded(0)` is not a capacity-1 channel: `try_send` returns `Full` unless a receiver is blocked at that instant.
- False sharing. Per-thread counters in a plain `[AtomicU64; N]` or adjacent struct fields share a cache line, so each increment invalidates the neighbors' copies. Intel's spatial prefetcher pulls 64-byte line pairs, hence 128-byte padding on x86-64. The cost is `N * 128` bytes; fields one thread reads together stay unpadded.
- `Backoff::spin()` caps at 64 `spin_loop` hints per call and never makes `is_completed()` true, so a `spin` plus `is_completed` loop never reaches its park branch. `snooze()` switches to `thread::yield_now()` after 7 calls and reports completed after 11.
- rtrb has no blocking and no wakeup. `is_abandoned()` turning `true` does not mean empty: keep popping until `Empty`. `PushError::Full` hands the value back; nothing is dropped.
- crossbeam-channel 0.5.12 to 0.5.14 can double free when dropping an unbounded channel (0.5.14 was yanked; fixed in 0.5.15). 0.5.17 fixes UB in bounded channels when a `SelectedOperation` is leaked.

## Verify

```sh
cargo tree -i crossbeam-channel                          # one version, 0.5.15 or newer
cargo tree -e features -i crossbeam                      # umbrella present, and what it pulls in
rg -n --type rust 'crossbeam_channel|crossbeam::channel' # every owner of a handle
```

- For each `send`, `recv`, `iter`, or timeout call on a crossbeam handle, the enclosing function and its callers are not `async` and not inside a spawned future. In tokio-console, a producer task with long poll times is blocking its worker.
- Overflow test: fill `bounded(cap)`, then assert the next `try_send` returns `Full`, the drop counter moved, and the call returned without blocking.
- Layout pin: `assert_eq!(size_of::<CachePadded<AtomicU64>>(), 128)` under `#[cfg(any(target_arch = "x86_64", target_arch = "aarch64"))]`.
- Latency: record enqueue-to-dequeue time per message into a histogram under burst load, `--release`, producer and consumer pinned. Compare p99 and p99.9 for the bounded channel, `ArrayQueue`, and rtrb with the real message type.
- Export `len()` as a gauge. A rising floor means the consumer cannot keep up.
