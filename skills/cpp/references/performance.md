# C++ Performance

Loaded via `cpp` SKILL.md routing table. Sources: Google Benchmark user guide, Linux perf and heaptrack docs, Apple Instruments docs, CMake `CheckIPOSupported` docs, Clang and GCC profile-guided optimization docs.

## Rule

- Measure before and after on a release build with debug info (`RelWithDebInfo`, or `-O2 -g`). Report both numbers.
- Algorithm and data layout first, micro-tuning last.
- No `-march=native` in shipped or shared builds; only for binaries built on the machine that runs them.

## Benchmarks

```cpp
#include <benchmark/benchmark.h>

static void BM_ParsePort(benchmark::State& state) {
    for (auto _ : state) {
        benchmark::DoNotOptimize(parse_port("8080"));
    }
}
BENCHMARK(BM_ParsePort);
BENCHMARK_MAIN();
```

- `benchmark::DoNotOptimize` on results and `benchmark::ClobberMemory()` when writes must land; otherwise the optimizer deletes the work.
- Quiet machine, release build, frequency scaling off. `--benchmark_repetitions=10 --benchmark_report_aggregates_only=true`. Compare runs with the library's `tools/compare.py`.
- nanobench is a header-only alternative.

## Profiling

| Platform | Tools |
|---|---|
| Linux | `perf record -g` + `perf report`, flame graphs; heaptrack for allocations; `valgrind --tool=callgrind` for exact counts |
| macOS | Instruments (Time Profiler, Allocations), `xctrace` on the command line, samply |
| Windows | Visual Studio profiler, Windows Performance Analyzer (ETW), Intel VTune |

Build with `-fno-omit-frame-pointer` for usable call stacks.

## Common wins

- Allocation: `reserve`, reuse buffers, pass views instead of copies, avoid `shared_ptr` churn, arenas or `std::pmr` (C++17) for many short-lived objects.
- Copies: `const auto&` in range-for, move sinks, `emplace_back` from arguments. `-Wrange-loop-construct` (in `-Wall`) flags accidental copies.
- Layout: contiguous containers (`vector`, `flat_map`) beat node containers (`list`, `map`) for iteration. Struct of arrays for hot loops over one field. Pad hot per-thread data to a cache line (64 bytes, or `std::hardware_destructive_interference_size` where the library defines it) to stop false sharing.
- Hash maps: `reserve` and a good hash. Open-addressing maps (`absl::flat_hash_map`, `boost::unordered_flat_map`) when profiling points at `std::unordered_map`.
- Virtual calls in hot loops: `final`, templates, or `std::variant` + `std::visit` when the set of types is closed.
- Exceptions cost nothing until thrown. Never throw for control flow on a hot path.
- `std::endl` flushes; write `'\n'`.
- `[[likely]]`/`[[unlikely]]` (C++20) only with profile evidence.

## Compiler and linker

- `-O2` for release; `-O3` only when measured faster.
- LTO: `CMAKE_INTERPROCEDURAL_OPTIMIZATION ON` after `check_ipo_supported()` from `CheckIPOSupported`; on Clang, `-flto=thin`.
- PGO with a representative workload only. Clang: `-fprofile-instr-generate`, run, `llvm-profdata merge -o app.profdata`, then `-fprofile-instr-use=app.profdata`. GCC: `-fprofile-generate`, run, `-fprofile-use`.
- `inline` is about the one-definition rule, not speed. Forced inlining (`[[gnu::always_inline]]`, `__forceinline`) only with a measured delta.
- Check codegen in Compiler Explorer (godbolt.org) or `objdump -d` when a micro-optimization matters.
- Compile time: precompiled headers (`target_precompile_headers`), unity builds (`CMAKE_UNITY_BUILD`), ccache or sccache, fewer includes in headers.
