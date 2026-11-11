# Go Performance

Loaded via `golang` SKILL.md routing table. Sources: go.dev/doc/pgo, go.dev/doc/diagnostics, runtime docs, `testing` docs, Uber Go Style (performance).

## Rule zero

- Readable first. Optimize only with profile or benchmark showing hot path.
- Every optimization change carries `benchstat` before/after or pprof evidence. No numbers, no merge.
- Micro-optimization in cold path is negative value: more code, same speed.

## Measure

```sh
go test -bench=. -benchmem -count=10 -run=^$ ./pkg > old.txt   # baseline
# change
go test -bench=. -benchmem -count=10 -run=^$ ./pkg > new.txt
benchstat old.txt new.txt                                       # p-value, delta

go test -cpuprofile=cpu.out -memprofile=mem.out -bench=BenchmarkX -run=^$ ./pkg
go tool pprof -http=:0 cpu.out                      # flame graph, top, list
go tool pprof -sample_index=alloc_space mem.out
go build -gcflags='-m -m' ./pkg 2>&1 | grep escapes  # escape analysis
go test -trace=trace.out ./pkg && go tool trace trace.out
```

- `-count=10` minimum for benchstat. Quiet machine. `-cpu=1,4` when parallelism matters.
- Benchmarks: `for b.Loop()` (1.24+), `b.ReportAllocs()`. Realistic inputs, sub-benchmarks by size.
- Production: `net/http/pprof` on admin port. Profiles: `cpu`, `heap` (`inuse_space` for leaks, `alloc_space` for churn), `goroutine`, `block` (`runtime.SetBlockProfileRate`), `mutex` (`runtime.SetMutexProfileFraction`), `goroutineleak` (1.27).
- `runtime/trace.FlightRecorder` (1.25+): ring buffer, dump on rare event. Continuous profiler (Pyroscope, Parca, vendor) when available.
- `runtime/metrics` for GC pause, heap, goroutine counts; scheduler metrics added 1.26.
- `testing.AllocsPerRun` to pin zero-alloc only where zero-alloc is contract.

## Allocations

Heap allocation is the usual cost. GC work scales with allocation rate.

- Preallocate when size known: `make([]T, 0, n)`, `make(map[K]V, n)`. `prealloc` linter.
- `strings.Builder` with `Grow(n)` over `+=` in loops. `stringsbuilder` modernizer.
- `strconv.Itoa`, `strconv.AppendInt` over `fmt.Sprintf` for scalars. `perfsprint` linter.
- One `[]byte(s)` / `string(b)` conversion; hold result. Compiler elides some (map lookup `m[string(b)]`, comparisons).
- Append APIs into reused buffer: `strconv.AppendInt`, `time.AppendFormat`, `encoding.TextAppender` (1.24+).
- `sync.Pool` for large short-lived buffers in hot loops (encoders, compressors). Reset on Put. Pooling small objects is slower than allocating.
- Return small structs by value. Pointer forces heap when escaping.
- Closures and method values capturing variables escape. Hot loops: explicit args.
- Non-pointer value into interface allocates (except small ints, zero-size). Hot path: concrete types or generics.
- `fmt` with `any` args allocates per arg. `slog.LogAttrs` with typed attrs does not.
- `unique.Make` (1.23+) interns repeated strings. `weak.Pointer` (1.24+) for caches that must not pin memory.
- Compiler stack-allocates more slice backing stores since 1.25/1.26. Keep sizes small and non-escaping to benefit.

## Data layout

- Struct fields largest-alignment first to cut padding. `fieldalignment` analyzer for many instances.
- Slice of structs over slice of pointers for locality when elements small and unshared.
- `[N]T` arrays for fixed small sizes in hot structs.
- Maps fast but iteration allocates and order random. Sorted slice + `slices.BinarySearch` for read-heavy small sets. Swiss tables (1.24+) improved large maps.
- No `map[string]any` in hot paths. Typed structs.

## Strings and bytes

- `strings.Cut`, `CutPrefix`, `CutSuffix`, `CutLast` (1.27) over `Index` + slicing.
- `strings.SplitSeq`, `Lines`, `FieldsSeq` (1.24+) iterate without slice allocation.
- `bytes.Buffer.Peek` (1.26+) inspects without copy.
- Regex compiled once (`regexp.MustCompile` at package level is the accepted global). No regex for plain prefix/contains.
- `strings.EqualFold` over lowering both sides.

## Interfaces, generics, reflection

- Interface method call: indirect, blocks inlining. Fine everywhere except tightest loops.
- Generics use GC-shape stenciling; pointer-heavy type params share code via dictionaries. Measure; generics are not free speed.
- Reflection (`encoding/json` v1, `reflect`) slow. Codegen (`sqlc`, protobuf) or `encoding/json/v2` (1.27) when JSON is hot.
- `reflect.TypeFor[T]()` over `TypeOf`. `reflecttypefor` modernizer.

## Compiler

- Inlining automatic for small funcs. `-gcflags=-m` shows `can inline`. No manual inline directive; `//go:noinline` only in benchmarks/tests.
- Bounds-check elimination: `_ = s[n-1]` hint before loop, or `for i := range s`. `-gcflags=-d=ssa/check_bce` lists remaining checks.
- PGO: CPU profile at `cmd/<app>/default.pgo`; `go build` picks it up (`-pgo=auto` default since 1.21). Collect from prod at 1-5% sampling, merge via `go tool pprof -proto a.pprof b.pprof > default.pgo`. Expect 2-14%. Refresh per release; stale profile still safe.
- `-trimpath -ldflags="-s -w"` shrinks binary, not runtime.

## Runtime and GC

- `GOGC` (default 100): raise to trade memory for less GC CPU. `GOMEMLIMIT` (1.19+): soft heap cap at ~80-90% of container limit; `GOGC=off` + `GOMEMLIMIT` only for memory-bound batch jobs.
- Green Tea GC default 1.26: 10-40% less GC overhead, no code change.
- `GOMAXPROCS` container-aware 1.25+ (cgroup CPU quota). Older: `uber-go/automaxprocs`.
- `runtime.AddCleanup` (1.24+) over `SetFinalizer`. Neither for correctness; resources need explicit `Close`.
- `debug.SetGCPercent`, `debug.SetMemoryLimit` when env not controllable.
- Goroutine cost ~2-8KB stack. Millions fine; unbounded not.

## I/O

- `bufio.Reader`/`Writer` around files and sockets. Flush writers.
- `io.Copy` uses `ReaderFrom`/`WriterTo` and `sendfile`. Prefer over manual loop.
- `io.ReadAll` 2x faster in 1.26 but unbounded: `io.LimitReader` for untrusted input.
- `os.ReadFile` for small whole files. Stream large.
- Batch DB writes (`CopyFrom` in pgx, multi-row insert). Pipeline round trips.
- HTTP: shared Transport keep-alive, HTTP/2 for many small requests to one host.

## Concurrency for throughput

- Parallelize only CPU-bound or I/O-latency-bound work with independent units. Batch tiny units first; coordination overhead exceeds gain.
- Bound with `errgroup.SetLimit`. Limit: `GOMAXPROCS` for CPU, higher for I/O until downstream saturates.
- Contention: `mutex` profile. Shard by key hash or per-goroutine accumulators merged at end, before lock-free.
- `atomic` counters over mutex for simple stats. Cache-line padding (`[64]byte`) only with measured false sharing.
- Channel op ~50-100ns under contention. Not for per-byte or per-element handoff; batch.

## Avoid

- Optimizing without profile.
- `sync.Pool` of small objects.
- `unsafe` for speed without benchmark and invariant comment.
- Premature `RWMutex`, lock-free structures, custom allocators.
- `runtime.GC()` in production.
- Global `sync.Map` as "faster map".
- `simd/archsimd` (experimental 1.26+) unless task is explicitly SIMD kernel.
- cgo for speed: call overhead (tens of ns, 30% cheaper on 1.26) plus thread handoff loses for small ops.
