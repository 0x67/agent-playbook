# disruptor (Rust)

Loaded via the low-latency SKILL.md routing table. Checked against disruptor 4.4.0 on 2026-11-06. Sources: disruptor 4.4.0 crate source from crates.io (`src/`, in-crate tests, `benches/`, `README.md`), usage in a market-data pipeline.

## When to use it

- Fixed topology known at startup: one or more producers, a set of consumers, optional stage dependencies (pipeline or DAG). Every consumer sees every event (broadcast); there is no work-queue mode.
- Hot path where you can spend a core per consumer on spinning to cut handoff latency, and events can be preallocated and overwritten in place instead of moved.
- Bursty input that can be published in batches. The crate's own benches show the largest gain over crossbeam at bursts of 10 and 100.
- `crossbeam-channel` fits better when consumers come and go, idle threads should park (blocking `recv`, `select!`, timeouts), each message should go to one of several workers, or owned values must move between threads (`crossbeam.md`).
- `rtrb` fits better for one producer and one consumer that already own their threads: a plain SPSC ring of owned values, no spawned threads, no stage graph.
- No async API. `publish` spins and producer drop joins threads, so keep both on dedicated OS threads.

## Core API

```rust
use disruptor::*; // also brings the Producer and ProcessorSettings traits into scope

let mut producer = build_single_producer(1024, Event::default, BusySpin)
    .pin_at_core(2).thread_name("book")
    .handle_events_with(|e: &Event, seq: Sequence, end_of_batch: bool| { /* stage 1 */ })
    .and_then()
    .handle_events_and_state_with(|s: &mut Stats, e: &Event, _, _| { /* stage 2 */ }, Stats::default)
    .build();
producer.publish(|e| e.px = 42);
producer.batch_publish(3, |iter| { for e in iter { e.px = 0; } });
drop(producer); // joins both processor threads after they drain
```

- Entry points: `build_single_producer(size, factory, wait)` returns `builder::single::SPBuilder`, `build_multi_producer(..)` returns `builder::multi::MPBuilder`. Bounds: `F: FnMut() -> E`, `E: 'static + Send + Sync`, `W: 'static + WaitStrategy`. The factory runs `size` times at build to fill every slot.
- Managed handlers get one spawned thread each: `handle_events_with(FnMut(&E, Sequence, bool))`, `handle_events_and_state_with(FnMut(&mut S, &E, Sequence, bool), FnOnce() -> S)`, plus `handle_events_with_wait_strategy` and `handle_events_and_state_with_wait_strategy` taking a per-handler strategy. `Sequence` is `i64`; the `bool` is `end_of_batch`.
- Handlers added back to back read in parallel. `and_then()` starts a stage that reads a slot only after every handler of the previous stage is done with it.
- `ProcessorSettings::pin_at_core(id)` and `thread_name(&'static str)` apply to the next managed handler only. Unnamed threads get `processor-N`.
- Pollers, where the caller owns the thread: `new_event_poller()` returns `(EventPoller<E, B>, builder)`. Pollers take part in `and_then()` ordering like handlers.
- `poll()` (all available) or `take(limit: u64)` returns `Result<EventGuard, Polling>` without blocking. Iterate `for e in &mut guard`, size via `(&mut guard).len()`; dropping the guard releases the slots.
- `Polling::NoEvents`: nothing new yet. `Polling::Shutdown`: producers are gone and this poller has read everything. `has_available()` peeks without consuming and does not check shutdown.
- Runtime consumer count: `with_multi_consumer()` (on a builder whose current stage is empty), then loop `new_event_poller()`.
- Out-of-band branch: `let b = builder.new_branch();` then, after more stages, `let (poller, builder) = builder.join(b);`. The branch poller runs parallel to those stages; later `and_then()` stages wait on it too.
- `build()` compiles only when the current stage has a consumer or after `with_multi_consumer()` (typestate). It returns `SingleProducer<E, SingleConsumerBarrier>` or `SingleProducer<E, MultiConsumerBarrier>` (likewise `MultiProducer`). `MultiProducer` is `Clone`, one clone per publishing thread; `SingleProducer` is not.
- `Producer<E>` trait: `publish(FnOnce(&mut E))`, `try_publish(..) -> Result<Sequence, RingBufferFull>`, `batch_publish(n, FnOnce(MutBatchIter<E>))`, `try_batch_publish(n, ..) -> Result<Sequence, MissingFreeSlots>`. The batch iterator yields exactly `n` `&mut E`; `Ok` carries the highest sequence published.
- Wait strategies (managed handlers only): `BusySpin` (empty loop), `BusySpinWithSpinLoopHint` (`std::hint::spin_loop`), `Sleep::new(Duration)` (`thread::sleep`). Custom: implement `disruptor::wait_strategies::WaitStrategy` (`Copy + Send`, `fn wait_for(&self, sequence: Sequence)`); the trait is not re-exported at the crate root.
- Shutdown: drop the producer (for `MultiProducer`, the last clone). Drop stores the shutdown sequence and joins every managed thread once it has handled all published events. Pollers are not joined; they drain, then get `Polling::Shutdown`. A Disruptor cannot be restarted.

```rust
let (mut poller, builder) = build_single_producer(1024, Event::default, BusySpin).new_event_poller();
let mut producer = builder.build();
// consumer thread
loop {
    match poller.take(256) {
        Ok(mut guard) => for e in &mut guard { /* read e in place */ }, // guard drop frees the slots
        Err(Polling::NoEvents) => std::hint::spin_loop(),
        Err(Polling::Shutdown) => break,
    }
}
```

## Idioms

- Prefer `try_publish` on threads that must never stall (socket readers, transport loops); the crate docs recommend the `try_` variants. Map `RingBufferFull` to a drop counter plus a rate-limited log, or to a deliberate halt: the crate docs read a full ring as consumers falling behind.
- Validate capacity before calling the builder and return a typed error, since the crate only asserts.
- Runtime fan-out: `with_multi_consumer()`, loop `new_event_poller()`, and reject a zero count first.
- Bound each poll with `take(limit)` so the cursor advances in steps and producers see freed slots sooner. Read events in place inside the guard; cloning heap payloads out allocates per event.
- Publish bursts with `batch_publish(n, ..)`: one release store per batch (single producer) or per 64-slot word (multi producer) instead of one per event.
- Use `end_of_batch` to amortize: accumulate in handler state and flush (write, syscall, metric) when it is `true`.
- Keep non-`Send` per-thread state (`Rc`, `RefCell`) in `handle_events_and_state_with`: the init closure runs on the processor thread and `S` has no `Send` bound.
- Reuse heap capacity in slots: allocate buffers in the factory and refill with `clear()` plus `extend_from_slice`. `*slot = value` drops the previous occupant on the producer thread. For large fan-out payloads, put an `Arc<T>` in the slot.
- Several message kinds on one ring: make `E` an enum with a cheap variant for the factory (`|| Event::Heartbeat`), as the crate README shows.
- Split load across N handlers by filtering `sequence % n == id` in each; every handler still visits every slot.
- Mix strategies per handler: `BusySpin` on the hot stage, `Sleep::new(..)` on a journal or metrics stage via `handle_events_with_wait_strategy`. `Sleep` ships, so a custom sleeping `WaitStrategy` adds nothing.
- Pin each busy-spin handler with `.pin_at_core(id)` to an isolated core (`pinning.md`) and name it with `.thread_name(..)` so profilers and `top -H` show it.

## Sharp edges

- Capacity must be a power of two: the build panics with "Size must be a power of 2" (0 fails too). `build_multi_producer` also panics below 64 slots: "MultiProducerBarrier must have a size of minimum 64 slots".
- Full ring: `publish` and `batch_publish` spin in an empty loop (no wait strategy, no `spin_loop` hint, no timeout) until the slowest consumer frees space. `try_publish` returns `Err(RingBufferFull)`. `try_batch_publish` returns `Err(MissingFreeSlots(k))` with the shortfall and publishes nothing.
- `batch_publish(n)` with `n` above capacity never returns; `try_batch_publish` reports the shortfall. `n == 0` is a no-op.
- `BusySpin` holds a core at 100% per managed handler, idle or not; `BusySpinWithSpinLoopHint` still spins. `Sleep` adds up to its duration to latency and to shutdown. The crate has no blocking or condvar strategy.
- Handler panic: the thread dies and its cursor freezes. Producers block (or get `RingBufferFull`) once the ring wraps, later stages stall, and producer drop panics with "Consumer should not panic." from the join (abort if already unwinding).
- Panic inside a `MultiProducer` publish closure: the slot was claimed but never published. Consumers stop at that sequence for good and the last producer's drop waits forever in join. Keep publish closures infallible.
- The consumer set is fixed at `build()`; nothing can be added, removed, or detached later. `with_multi_consumer().build()` with no consumer panics: "MultiConsumerBarrier must have at least one cursor".
- The slowest consumer gates every producer. A poller that stops polling, or is dropped (there is no unregister), freezes the ring; a managed stage behind it never reaches the shutdown sequence, so producer drop hangs.
- Producer drop blocks the dropping thread until managed handlers drain. Do not drop it on a latency-critical thread or inside an async task.
- Slots are reused: the update closure sees the previous occupant, and any field it skips keeps stale data. Write every field the consumers read.
- Consumers get `&E`. Moving data out of a slot needs interior mutability inside `E`, which must also be `Sync`.
- `EventGuard` drop releases its whole range, read or not: breaking out of the loop early skips the rest for that consumer.
- Managed handlers store their cursor only after the whole available batch, so with a deep backlog producers and later stages see no progress until that batch ends.
- `pin_at_core` panics at build if `core_affinity` does not list the core id, on every OS. Pinning is a no-op on macOS; elsewhere a failed pin panics inside the processor thread.
- `MutBatchIter` is not re-exported. Helpers that fill a batch take `impl Iterator<Item = &mut E>`.
- Publish methods live on the `Producer` trait; without `use disruptor::Producer` (or the glob import) the calls do not resolve.
- Sequences are `i64` with no overflow guard; the docs call more than 2^63 - 1 publications undefined behavior.

## Verify

- Unit-test pollers on one thread: publish, poll, assert `Polling::NoEvents`, then `drop(producer)` and assert `Polling::Shutdown`. No threads, deterministic; the crate's own tests work this way.
- Managed handlers: send from the handler into `std::sync::mpsc`, `drop(producer)` (joins after drain), then `rx.iter().collect()`. The iterator ends because the handler and its `Sender` die with the thread.
- Full-ring tests: block the first handler call on a channel with `recv_timeout`, fill with `try_publish`, assert `RingBufferFull` or `MissingFreeSlots(k)`, then release. Release from a `Drop` guard so a failed assert cannot leave producer drop joining a stuck handler.
- Use `recv_timeout`, never bare `recv`, in tests so a stalled consumer fails instead of hanging CI.
- The crate runs its own tests under Miri. Poller tests fit there; mark pinned and stress tests `#[cfg_attr(miri, ignore)]` as the crate does.
- Benchmark end to end: the handler stores the last value in an `AtomicI64` sink and the bench spins until it sees it (criterion `iter_custom`, crate `benches/spsc.rs`). Add a baseline that measures the sink alone, and vary burst size (1, 10, 100) and pause between bursts (0, 1, 10 ms).
- Timing only `publish()` measures enqueue cost until the ring fills, then consumer throughput. It says nothing about handoff latency.
- The crate benches report criterion means. For p99 and max, stamp a send time into the event and record per-event latency in the handler (`measure.md`).
- Benchmark on Linux with pinned threads on isolated cores; macOS ignores pinning, so its numbers carry scheduler noise.
- In production, export the `RingBufferFull` drop count and alert on a non-zero rate.
