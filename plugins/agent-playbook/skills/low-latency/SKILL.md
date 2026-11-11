---
name: low-latency
description: >
  Low-latency engineering for hot paths: per-message code in market-data feeds,
  network receive loops, order books, matching, and anything else with a
  latency budget. Use when code depends on or the user mentions disruptor, ring
  buffers, lock-free or SPSC queues, crossbeam, rtrb, busy-spin or wait
  strategies, false sharing, CachePadded, CPU pinning, isolcpus, io_uring,
  zero-copy decoding, bytes or zerocopy, back-pressure, tail latency or p99,
  HdrHistogram, coordinated omission, latency benchmarks, or loom. The
  principles hold in any language; the library pages are Rust. Loads alongside
  the language skill, whose rules still apply.
---

# Low-latency skill

Rules for code where a per-message cost shows up in tail latency. A hot path is the code that runs once per message, packet, or order: receive loops, decoders, book updates, and the queues between them. Everything else follows the normal language skill.

## Routing table (mandatory)

Read the matching page BEFORE writing or reviewing hot-path code. Paths are relative to this skill's directory.

| Task touches | Read |
|---|---|
| `disruptor` rings, producers and pollers, wait strategies, batch publish | `references/rust/disruptor.md` |
| `crossbeam` channels or queues, `CachePadded`, `Backoff`, `rtrb` SPSC rings | `references/rust/crossbeam.md` |
| wire decoding, `Bytes`/`BytesMut`, `zerocopy` views, fixed-layout messages | `references/rust/bytes-zerocopy.md` |
| `io-uring` receive paths, registered or provided buffers, SQPOLL | `references/rust/io-uring.md` |
| benchmarks, latency histograms, coordinated omission, `loom`, Miri | `references/rust/measure.md` |
| `core_affinity`, isolated cores, thread placement | `references/rust/pinning.md` |

Multiple matches: read all matched. Every change to a hot path also reads `measure.md`.

## Rule zero: measure

1. No hot-path change without numbers: the same benchmark before and after, on the same machine, build profile, and input (`references/rust/measure.md`).
2. Report percentiles (p50, p99, p99.9, max) and throughput at a fixed rate, never a mean alone.
3. A new project-wide performance rule needs a measured cost delta and an anchor in code. A rule without a measurement is folklore; do not add it.
4. Equal medians with overlapping spread mean no measurable difference. Prefer the simpler code.

## Principles

1. **One writer per structure.** Each piece of mutable hot state has exactly one writing thread. Other threads get messages or snapshots. Shared writes mean locks or contended atomics, and cache lines bouncing between cores.
2. **No allocation per message.** Preallocate and reuse buffers. No `Box`, `Vec`, `String`, or `format!` per message on the hot path. When data must outlive the message, materialize in bulk (arena, slab, preallocated pool), never one allocation per item.
3. **Mind the cache line.** Pad indices and counters written by different threads onto separate cache lines (`CachePadded`). Keep fields a hot loop reads together. A loop that reads one field across many items wants that field in its own array.
4. **Choose the wait strategy per thread.** Busy-spin gives the lowest wake-up latency and burns a full core, so use it only on an isolated core. Yield or back off spends less CPU and adds jitter. Park or block costs the least CPU and adds wake-up latency. Never busy-spin on a core shared with other work.
5. **Every queue has a declared overflow policy.** Block the producer, drop (oldest or newest), or fail fast. Pick it per consumer, count what gets dropped, and never put an unbounded queue on a hot path. A blocking call inside async code stalls every task on that executor thread.
6. **Place threads deliberately.** Pin hot threads to isolated cores, keep interrupts and housekeeping elsewhere, and keep a pipeline's threads on one NUMA node (`references/rust/pinning.md`).
7. **Batch syscalls and I/O.** No syscall per message. Read and submit in batches; reach for io_uring or kernel busy-polling only when a measurement says the syscall path is the cost (`references/rust/io-uring.md`).
8. **Keep logging and metrics off the per-message path.** Log state transitions (gap detected, reconnect, session end), never each message. Count in per-thread or padded atomics with `Relaxed` ordering and aggregate off the hot path.
9. **Async on a receive loop is a measurement question.** Do not refactor `.await` away, or add it, without a per-message latency comparison.
10. **Prove lock-free code.** Model-check custom atomics with `loom`, run unsafe views under Miri where it can run, and fuzz decoders (`references/rust/measure.md`).

## Review checklist

- [ ] Per-message allocation, `clone`, `format!`, or logging on the hot path
- [ ] A queue with no declared overflow policy, or an unbounded queue
- [ ] A blocking call (channel `send`, mutex, file or network I/O) inside async code on the hot path
- [ ] Shared mutable state written by more than one thread
- [ ] Hot atomics or indices from different threads sharing a cache line
- [ ] Busy-spin on a core that is not isolated
- [ ] Hot-path change without before and after numbers from the same benchmark

## Post-write gate

Run the language skill's gate, then the benchmarks for every hot path the change touched, and report before and after numbers with spread. Lock-free or unsafe changes also run their loom and Miri tests.
