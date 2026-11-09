# Measuring latency (Rust)

Loaded via the low-latency SKILL.md routing table. Checked against criterion 0.8.2, hdrhistogram 7.6.0, loom 0.7.3 on 2026-11-09. Sources: crate source and doc comments of criterion 0.8.2, hdrhistogram 7.6.0, loom 0.7.2 and iai-callgrind 0.16.1; Miri README (rust-lang/miri master, 2026-11-06); `core::alloc::GlobalAlloc` docs.

## What to measure

- Latency is a distribution. Report p50, p99, p99.9 and max with the sample count `n`. A mean hides the tail, and a latency claim is about the tail.
- Keep service time (one call, back to back) apart from response time (from when a request was due to when it finished). Only response time under a fixed offered rate shows queueing.
- Throughput at a fixed offered rate, with the percentiles measured at that rate. Raise the rate until p99 breaks the budget; that rate is the capacity. Peak throughput alone says nothing about latency.
- Allocations per message on the steady-state hot path. A `#[global_allocator]` wrapper over `std::alloc::System` that counts `alloc` and `realloc` calls (thread-local counter) gives allocs/msg and bytes/msg. Target zero after warm-up.
- Timers cost time. Measure throughput with instrumentation off and latency in a separate instrumented pass.
- Know the clock. Time an empty region many times and publish the median overhead and the tick next to the results; never subtract it silently. A call cheaper than one tick (a 24 MHz counter ticks every ~42 ns) gives a histogram of quantization: time a batch, divide by the batch size, and label it a mean.

## criterion

- Answers "which version is cheaper on average". The `time:` line is the per-iteration slope estimate (the mean when there is no slope) with its confidence interval. There is no per-call distribution, so no p99 and no max: use hdrhistogram for tails.
- One target per file under `benches/`, declared with `[[bench]]`, `name = "decode"`, `harness = false`.
- `std::hint::black_box` on inputs so constants do not fold. `criterion::black_box` is deprecated in 0.8.2. `Bencher::iter` already passes the return value through `black_box`.

```rust
use criterion::{criterion_group, criterion_main, BatchSize, BenchmarkId, Criterion, Throughput};
use std::hint::black_box;

fn decode(c: &mut Criterion) {
    let mut g = c.benchmark_group("decode");
    for msg in fixtures() {
        g.throughput(Throughput::Bytes(msg.len() as u64));
        g.bench_with_input(BenchmarkId::new("view", msg.len()), &msg, |b, m| {
            b.iter(|| parse_view(black_box(m)))
        });
        g.bench_with_input(BenchmarkId::new("owned", msg.len()), &msg, |b, m| {
            b.iter_batched(|| m.clone(), parse_owned, BatchSize::SmallInput)
        });
    }
    g.finish();
}
criterion_group!(benches, decode);
criterion_main!(benches);
```

- `Throughput::Elements(n)` when one iteration handles `n` messages (prints elem/s). Also `Bytes`, `BytesDecimal`, `Bits`, `ElementsAndBytes { elements, bytes }`.
- `iter_batched(setup, routine, size)` keeps setup out of the timed region; the routine takes the input by value. `iter_batched_ref` passes `&mut I`, so dropping the input is untimed too. `iter_custom(|iters| { ...; start.elapsed() })` when the routine must time itself, for example across threads.
- `BatchSize::SmallInput` (iters/10 per batch) unless memory runs out, then `LargeInput` (iters/1000). `PerIteration` costs up to about 350 ns of overhead per call (the crate's rough estimate), so never use it on a ns-scale routine. `NumBatches(n)` and `NumIterations(n)` for manual control.
- Defaults: 100 samples (minimum 10), 3 s warm-up, 5 s measurement, noise threshold 0.01, confidence 0.95, significance 0.05. Override per group (`g.sample_size(..)`, `g.measurement_time(..)`) or per run (`--sample-size`, `--measurement-time`). `g.sampling_mode(SamplingMode::Flat)` for long benches.

```sh
cargo bench --bench decode -- --save-baseline before   # old code
cargo bench --bench decode -- --baseline before        # new code, compared, "before" kept
```

- A plain run compares against `base`, then overwrites it. `--baseline X` fails if any bench lacks `X`; `--baseline-lenient X` skips those benches. Raw numbers sit in `target/criterion/<group>/<id>/new/estimates.json` (mean, median, median_abs_dev, slope, std_dev); `--verbose` prints median and median absolute deviation with their intervals.
- "Performance has regressed" or "improved" appears only when p < significance level and the whole confidence interval of the mean change lies beyond the noise threshold. Otherwise it prints "Change within noise threshold." or "No change in performance detected." `--profile-time 10` iterates each bench for about 10 s with no analysis and nothing saved, for a profiler.
- Instruction counts: `iai-callgrind` 0.16.1 runs each bench once under Valgrind Callgrind and reports instruction counts plus an estimated cycle count. Counts stay steady on noisy VMs. The cycle estimate is a relative metric and does not replace wall-clock. It does not run on Windows or anywhere Valgrind does not; it needs system `valgrind` and `iai-callgrind-runner` installed at the library's version (the library passes `0.16.1` to the runner).

## hdrhistogram

```rust
use hdrhistogram::Histogram;

// ns, 1 ns..60 s, 3 significant figures; fixed range, so recording never reallocates
let template = Histogram::<u64>::new_with_bounds(1, 60_000_000_000, 3)?;
let mut local = Histogram::<u64>::new_from(&template); // one per thread
local.record(ns)?; // Err(RecordError::ValueOutOfRangeResizeDisabled) above 60 s

let mut total = Histogram::<u64>::new_from(&template);
for h in &per_thread { total.add(h)?; } // off the hot path
let v: Vec<u64> = total.value_at_quantiles([0.5, 0.99, 0.999]).collect();
println!("n={} p50={} p99={} p99.9={} max={}", total.len(), v[0], v[1], v[2], total.max());
```

- `new_with_bounds(low, high, sigfig)`: `low >= 1`, `high >= 2 * low`, `sigfig` in 0..=5. Three figures keeps quantization within 0.1% of the value. Memory grows exponentially with `sigfig`.
- `Histogram::new(sigfig)` auto-resizes, so a large value can reallocate mid-run. `new_with_max` and `new_with_bounds` disable resizing; recording into them is constant time with no allocation (the crate docs cite 3 to 6 ns on 2014-era Intel).
- `saturating_record` clamps out-of-range values to the bounds without error and hides extreme outliers. If you use it, check `max()` against `high()` after the run.
- Reported values are bucket equivalents, not raw samples: `max()` returns the highest value equivalent to the largest sample.
- Prefer `value_at_quantile(0.99)` over `value_at_percentile(99.0)`: one less float step. `value_at_quantiles` (new in 7.6.0) answers several in one pass; pass them ascending, since iteration stops at the first quantile lower than its predecessor.
- `add` returns `Err(AdditionError::OtherAddendValueExceedsRange)` when the target cannot resize and the source holds larger values. Build every per-thread histogram from one template with `new_from`.
- `SyncHistogram` (default `sync` feature): `hist.into_sync()`, one `recorder()` per thread, `refresh()` blocks until every recorder has handed off. An idle recorder stalls `refresh()`: call `Recorder::idle()` or use `refresh_timeout`. On hand-off the writer allocates a fresh histogram (`new_from`) and sends the old one over an unbounded channel, so a strict zero-allocation path keeps plain per-thread histograms instead.

## Coordinated omission

- A closed-loop generator sends the next request only after the previous reply. At one request per 100 us, a 10 ms stall records one slow sample and silently drops the 99 requests that were due during it. p99 then looks healthy while callers waited.
- Preferred fix: drive an open-loop schedule. Derive each send time from the start, never from the previous send, and record completion minus intended time.

```rust
let interval = Duration::from_micros(100);
let start = Instant::now();
for i in 0..n {                       // n: u32
    let intended = start + interval * i;
    while Instant::now() < intended { std::hint::spin_loop(); }
    send_and_wait();
    h.record(intended.elapsed().as_nanos() as u64)?; // lateness included
}
```

- When the generator cannot change: `h.record_correct(value, expected_interval)` records `value`, then backfills `value - interval`, `value - 2 * interval`, and so on while the result is at least `interval`. The post-hoc forms are `clone_correct(interval)`, `add_correct(src, interval)` and `set_to_corrected(src, interval)`.
- At-recording and post-recording correction are mutually exclusive per data set, and neither belongs on data already recorded against intended times. Correct once.
- Correction needs an intended rate. A back-to-back microbenchmark has none: report it as service time, uncorrected. When you do correct, publish raw and corrected percentiles side by side.

## loom and Miri

```rust
// Cargo.toml: [target.'cfg(loom)'.dependencies] loom = "0.7"
// src/sync.rs: one switch point for the crate; hint::spin_loop yields under loom
#[cfg(loom)]
pub(crate) use loom::{hint, sync::atomic::{AtomicUsize, Ordering}};
#[cfg(not(loom))]
pub(crate) use std::{hint, sync::atomic::{AtomicUsize, Ordering}};

// tests/loom_spsc.rs
#![cfg(loom)]
#[test]
fn spsc_no_lost_item() {
    loom::model(|| {
        let q = loom::sync::Arc::new(mycrate::Spsc::new(2));
        let p = q.clone();
        let t = loom::thread::spawn(move || p.push(1));
        while q.pop().is_none() { loom::thread::yield_now(); }
        t.join().unwrap();
    });
}
```

- Run: `RUSTFLAGS="--cfg loom" cargo test --test loom_spsc --release`. The model closure runs once per explored interleaving, so build it optimized.
- Everything shared must be a loom type: atomics, `Arc`, `Mutex`, `thread::spawn`, `loom::cell::UnsafeCell`. A `std` type is invisible to loom. Its `UnsafeCell` exposes `with(|ptr| ..)` and `with_mut(|ptr| ..)` and panics on concurrent mutable and shared access, so the non-loom build needs a small wrapper with the same two methods.
- The scheduler is not fair: spin loops must call `loom::thread::yield_now()` or `loom::hint::spin_loop()`, or the model never ends.
- Keep models tiny. A model holds at most `loom::MAX_THREADS` (5) threads. `LOOM_MAX_PREEMPTIONS=2` or `3` bounds large searches. On failure, `LOOM_CHECKPOINT_FILE` (needs the `checkpoint` feature) plus `LOOM_LOG=trace LOOM_LOCATION=1` replay the failing permutation.
- Limits: `SeqCst` loads and stores are modeled as `AcqRel` (false alarms are possible; `fence(SeqCst)` is modeled). Load buffering and same-thread `Relaxed` reordering are not explored, so a pass is not a proof. Inputs must be deterministic: mock RNGs and syscalls.
- Miri: `rustup +nightly component add miri`, then `cargo +nightly miri test`. It flags out-of-bounds access, use-after-free, uninitialized reads, misaligned access, invalid values, data races, leaks, and Stacked Borrows aliasing violations (`MIRIFLAGS="-Zmiri-tree-borrows"` swaps in Tree Borrows).
- Miri cannot run most platform APIs or FFI ("can't call foreign function"), has no networking, and fakes clocks, env and entropy unless `-Zmiri-disable-isolation`. Gate such tests with `#[cfg_attr(miri, ignore)]`; keep the unsafe core testable without them.
- Miri runs one execution per seed. `MIRIFLAGS="-Zmiri-many-seeds=0..16"` varies thread interleavings and allocation addresses. Its weak-memory emulation is incomplete: loom covers the atomics, Miri covers the unsafe memory access. A clean Miri run shows that execution had no UB; it does not prove soundness.

## Reporting a result

- Same machine, same pinned toolchain, same `[profile.release]` (`lto`, `codegen-units`, `panic`), same input bytes, same power and governor state. Record git rev, CPU, OS, `rustc -V` and profile with every number. Never compare debug builds.
- Report a center and a spread: criterion median with median absolute deviation (or the mean interval), and p50/p99/p99.9/max with `n` from the histogram. Note batch size whenever a number is a batch mean divided per message.
- Run the same config at least twice. The run-to-run swing on that host is its noise floor: a VM that swings 12% cannot show a 5% win.
- A difference counts when criterion reports a regression or improvement, the delta clears the host's noise floor, and it repeats on a rerun. For a tail claim the shift must hold at the percentile claimed across reruns, with `n` large enough to populate it (p99.9 needs well over 1,000 samples).
- Cross-check a narrow win with a deterministic count (instructions per message, allocs per message) or a second host. Across hosts compare rankings, never absolute ns.
- A performance rule or merge claim cites the measured delta (ns/msg or allocs/msg), the bench id, the host and the date. No measured delta, no rule.
