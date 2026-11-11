# Rust Performance

Loaded via `rust` SKILL.md routing table. Sources: The Rust Performance Book (nnethercote), Cargo profiles reference, criterion/divan docs, cargo-flamegraph, samply, cargo-pgo.

## Rule zero

- Readable first. Optimize only with a profile or benchmark showing the hot path.
- Every optimization change carries before/after numbers (criterion report, `divan` table, flamegraph diff). No numbers, no merge.
- Always `--release`. Debug-build numbers are meaningless.
- Hot path definition in this workspace: concrete non-generic per-message function callable across a crate boundary. Those get `#[inline]` at write time (`api-design.md`). Everything else: measure first.

## Measure

```sh
cargo bench -p core -- parse                      # criterion or divan under benches/
cargo flamegraph --release --bin app -- args      # perf/dtrace flame graph (svg)
samply record ./target/release-debug/app args     # Firefox Profiler UI, macOS/Linux
cargo instruments -t time --release --bin app     # macOS Instruments
cargo build --timings                             # compile-time hot spots
cargo llvm-lines -p core                          # monomorphization bloat
cargo bloat --release --crates                    # binary size by crate
```

- Profiling profile keeps symbols: `[profile.release-debug] inherits = "release"; debug = "line-tables-only"; strip = "none"`.
- `criterion`: statistical, detects regressions across runs (`target/criterion`), `BenchmarkId` over input sizes, `black_box` on inputs and outputs. `divan`: lighter syntax, `#[divan::bench(args = [...])]`. Pick one per repo.
- `perf stat -e cache-misses,branch-misses` (Linux) for microarchitecture questions. `valgrind --tool=dhat` or `dhat-rs` for allocation counts and sites.
- `RUSTFLAGS="-C target-cpu=native"` only when comparing on the deploy hardware; never bake into a published crate.
- Async: `tokio-console` for task stalls, `tracing` spans with timings. Blocking on runtime threads shows as idle workers + long poll times.

## Allocation

- `Vec::with_capacity`, `String::with_capacity`, `HashMap::with_capacity` when size known. `reserve` before batch pushes.
- Reuse buffers across iterations: `buf.clear()` then refill; pass `&mut Vec<T>` into hot functions (`_into` variants).
- `&str`/`&[T]` params; `Cow<'_, str>` when sometimes owned. `Box<str>`/`Box<[T]>` for long-lived immutable data (no capacity word).
- `Arc<str>`/`Arc<[T]>` for shared immutable data instead of cloning `String`/`Vec`.
- `SmallVec`/`ArrayVec` for small bounded collections on hot paths, measured. `smallvec` inline size chosen from data, not guessed.
- `format!` in hot loops allocates: `write!(&mut buf, ...)`, `itoa`/`ryu` for number formatting.
- `String` concatenation with `+` in loops: `push_str` into preallocated buffer.
- Iterator chains fuse; `collect` only at the end. `sum`, `fold`, `any` do not allocate.
- `Box<dyn Trait>` per element allocates and indirects; enum dispatch or generics on hot paths.
- Global allocator: `mimalloc` or `jemalloc` (`tikv-jemallocator`) for allocation-heavy services, measured. Default system allocator otherwise.
- `#[derive(Clone)]` on big structs invites accidental clones; audit `.clone()` in hot paths with `clippy::redundant_clone`, `clippy::clone_on_ref_ptr`.

## Data layout

- Field order: largest alignment first, or let the compiler reorder (default for `repr(Rust)`). `#[repr(C)]` only at FFI. Check with `size_of` tests for hot structs (contract pins).
- Enum size = largest variant + tag. Box the rare large variant (`clippy::large_enum_variant`).
- Struct-of-arrays for tight numeric loops. `Vec<T>` of small `Copy` structs over `Vec<Box<T>>`.
- `[T; N]` and `Box<[T]>` when length is fixed. `VecDeque` for queues. `BTreeMap` only for ordered access.
- Hash: `FxHashMap` (`rustc-hash`) or `ahash` for small keys when hashing shows in the profile. Default SipHash for untrusted keys (HashDoS).
- `NonZero*`, `Option<Box<T>>`, `Option<&T>` are niche-optimized: no size cost.

## Compute

- Bounds checks: iterate with `iter()`/`zip` instead of indexing; `chunks_exact`, `as_chunks` (1.88+). `get_unchecked` only with `// SAFETY:` and a benchmark proving the check mattered.
- Branch hints: `#[cold]` on error functions, `std::hint::cold_path()` (1.95+) in the unlikely branch. `likely`/`unlikely` intrinsics are unstable.
- Integer ops: `wrapping_*`/`strict_*` chosen deliberately; `u32` vs `u64` per data range; avoid `as` chains in loops.
- Float: `mul_add` (FMA), `algebraic_*` ops (1.98+) when reassociation is acceptable. `f32` when precision allows.
- SIMD: `std::arch` with `#[target_feature(enable = "...")]` + runtime detection (`is_x86_feature_detected!`); `portable_simd` is nightly. Autovectorization first: simple loops over slices, no early exits.
- Monomorphization: generic hot code is fast but bloats; `cargo llvm-lines`. `dyn` at coarse boundaries, generics in inner loops.
- `#[inline]` policy in `api-design.md`. `#[inline(never)]` to keep cold code out of hot functions' bodies.
- Strings: `bytes()` over `chars()` when ASCII; `memchr` crate for searching; `str::split_once`.
- Regex: `regex` compiles once (`LazyLock`); `regex::bytes` for byte input; `RegexSet` for many patterns; `aho-corasick` for literal sets.

## Concurrency for throughput

- `rayon` `par_iter` for CPU-bound data parallelism; chunk work so per-item overhead is amortized.
- Async I/O: bounded concurrency (`Semaphore`, `buffer_unordered(n)`), batch small writes (`BufWriter`, `writev`), `bytes::Bytes` for zero-copy sharing.
- Lock contention: `parking_lot`, sharding, or per-thread accumulators merged at the end. `mutex` profile via `perf lock` or `tracing`.
- Channels: `crossbeam-channel` bounded; `tokio::sync::mpsc` bounded; batch messages rather than per-item sends.
- False sharing: `crossbeam_utils::CachePadded` on per-thread counters, measured.

## Build configuration

```toml
[profile.release]
lto = "fat"            # or "thin"; measure link time vs speed
codegen-units = 1
panic = "abort"        # binaries only
opt-level = 3
```

- PGO: `cargo pgo build`, run representative workload, `cargo pgo optimize`. 5-15% typical. `cargo pgo bolt` on Linux for layout optimization on top.
- `-C target-cpu=native` for deploy-built binaries; explicit `-C target-feature=+avx2` with runtime detection fallback for distributed ones.
- `opt-level = "s"`/`"z"` + `lto` + `strip` for wasm and embedded size.
- `debug = "line-tables-only"` in release for symbolized production profiles; small cost.

## I/O

- `BufReader`/`BufWriter` around files and sockets; `flush` explicitly. `read_to_end` with capacity hint. `std::io::pipe` (1.87+) for process plumbing.
- `mmap` (`memmap2`) for large read-mostly files; document the unsafety (file may change underneath).
- `tokio::fs` is thread-pool backed: batch file ops or use `spawn_blocking` with std I/O for throughput.
- Serialization: `serde_json` with `to_writer` into a `BufWriter`; `simd-json` or `sonic-rs` when JSON parse is the profile top; `bincode`/`postcard`/`rkyv` for internal binary formats.
- DB: prepared statements, batch inserts, connection pool sized to DB cores.

## Avoid

- Optimizing without a profile. "Obviously faster" changes without a benchmark.
- `unsafe` for speed without a benchmark showing the safe version is the bottleneck and a `// SAFETY:` proof.
- `Arc<Mutex<Vec<T>>>` shared accumulators in parallel loops. Per-thread collect then merge.
- `clone()` to satisfy the borrow checker in hot loops. Restructure ownership.
- `Box<dyn Fn>` callbacks per element. Generics or enum.
- `collect::<Vec<_>>()` between adapters.
- `String` keys in hot maps when `u64`/`Arc<str>`/interned ids fit.
- `#[inline(always)]` without a cited measured delta.
- Global allocator swaps, `lto = "fat"`, `codegen-units = 1` without measuring on the actual workload.
- Micro-benchmarks that the optimizer defeats: missing `black_box`, constant-folded inputs.
