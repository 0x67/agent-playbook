---
name: cpp
description: >
  Idiomatic modern C and C++ engineering: writing, reading, reviewing,
  refactoring, testing, and profiling C/C++ code (.c, .h, .cc, .cpp, .cxx,
  .hpp, .hh, .ixx, .cppm, CMakeLists.txt, *.cmake, CMakePresets.json).
  Use whenever the user works in a C or C++ codebase or asks anything
  involving ownership, RAII, templates, concepts, undefined behavior,
  sanitizers, CMake, clang-tidy, clang-format, clangd, GoogleTest, Catch2,
  or a C/C++ standard version (C++17/20/23/26, C11/C23). Trigger even when
  "C++" is not said but files or commands are clearly C/C++, and on any task
  that needs every usage of a C++ symbol. Core rules inline; specialist rules
  live in references/ and load through the routing table below.
---

# C/C++ engineering skill

Write C++ a careful maintainer would merge without comment: value semantics, ownership in the type system, RAII for every resource, no undefined behavior, zero warnings, and tools that prove it (sanitizers, clang-tidy). The project's language standard is the ceiling, the way `go.mod` and `rust-version` are.

## Routing table (mandatory)

Read matching reference BEFORE writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| finding definitions, references, callers; rename; signature change; unfamiliar code | `references/navigation.md` |
| naming, headers, includes, namespaces, classes, special members, parameters, initialization, casts, comments, formatting | `references/style.md` |
| ownership, RAII, smart pointers, moves, `span`/`string_view` lifetimes, containers, undefined behavior | `references/memory.md` |
| exceptions, `std::expected`, error codes, `noexcept`, assertions, contracts, `main` exit | `references/errors.md` |
| threads, `jthread`, stop tokens, mutexes, condition variables, atomics, coroutines, shutdown | `references/concurrency.md` |
| any test file, GoogleTest, Catch2, doctest, CTest, fuzzing, sanitizer runs, coverage | `references/testing.md` |
| CMake, presets, warnings, hardening flags, sanitizers, clang-tidy, clang-format, packages, CI | `references/tooling.md` |
| choosing features for a given `-std` / `CMAKE_CXX_STANDARD` or oldest compiler, fallbacks on older standards, migrating old idioms | `references/modern.md` |
| benchmarks, profiling, allocation, data layout, inlining, LTO, PGO | `references/performance.md` |
| plain C (`.c`, C-only headers, `CMAKE_C_STANDARD`, C ABI boundaries) | `references/c.md` |

Multiple matches: read all matched. Unsure: read `style.md` and `memory.md`.

## Before writing

1. Find the standard: `CMAKE_CXX_STANDARD`, `target_compile_features(... cxx_std_NN)`, `-std=` in `compile_commands.json`, Meson `cpp_std`, or Bazel `--cxxopt`. Never use a feature above it; `references/modern.md` lists what each standard unlocks. Note the compilers and standard library (libstdc++, libc++, MSVC STL) the repo builds with: feature support differs.
2. Check repo conventions: `.clang-format`, `.clang-tidy`, `CMakePresets.json`, exceptions on or off (`-fno-exceptions`), RTTI, error type in use, test framework, logging, existing helpers. Repo convention beats these defaults.
3. Make sure `compile_commands.json` exists for clangd and clang-tidy (`references/tooling.md`). Without it, symbol tools guess.
4. Find the existing file and target for the change. New file only for a new concern; new library target only for a new component.

## Non-negotiables

- Zero warnings at the repo's warning level (`-Wall -Wextra -Wpedantic` minimum, `/W4` on MSVC). Fix, never silence with a pragma or a cast.
- No undefined behavior: signed overflow, out-of-bounds, use-after-free, data races, uninitialized reads, aliasing violations, null dereference. Sanitizer runs prove it.
- Ownership in types: `std::unique_ptr` by default, `std::shared_ptr` only for real shared ownership, raw `T*`/`T&` never own. No `new`/`delete` outside a resource class; `std::make_unique`/`std::make_shared`.
- RAII for every resource: memory, files, sockets, locks, handles. Rule of zero; a class that owns a raw resource follows the rule of five.
- `const` by default: locals, member functions, reference parameters. Sink parameters by value, then `std::move`.
- Non-owning views (`std::span`, `std::string_view`) as parameters and short-lived locals only. Never store or return one that can outlive its source.
- Containers over raw arrays: `std::vector`, `std::array`, `std::string`. Algorithms and ranges where they read better than a loop.
- `enum class`, `nullptr`, `override` (`final` when meant), `= default`/`= delete`, `explicit` single-argument constructors, `[[nodiscard]]` on results that must be used.
- No C-style casts. `static_cast`; `reinterpret_cast`/`const_cast` only with a comment saying why it is sound; `std::bit_cast` (C++20) or `std::memcpy` for type punning.
- Headers: `#pragma once` or guard, self-contained, include what you use, no `using namespace`.
- No mutable globals; no non-trivial static initialization across translation units. `constexpr`/`constinit` for constants.
- Errors the repo's way (exceptions or `std::expected`/error codes), handled at the boundary that can act. Destructors, moves, and swaps `noexcept`.
- Comments: plain humanizer prose, why not what, no plan/task ids, no em dash. Doc comment on every public declaration in a header, including ownership and lifetime of pointer and view parameters.
- Tests must fail from a project bug. No restating compiler-generated members, no getter echo, no mock-call-count-only.

## After writing (gate, in order)

```sh
clang-format --dry-run --Werror <changed files>
cmake --build --preset dev                          # or: cmake --build build
ctest --preset dev                                  # or: ctest --test-dir build --output-on-failure
clang-tidy -p build/dev <changed .cpp/.cc files>    # when .clang-tidy present
cmake --build --preset asan && ctest --preset asan  # when tests exist
```

Use the repo's presets and build system (Meson: `meson compile -C build && meson test -C build`; Bazel: `bazel test //...`; Make: its targets). Code behind `#if` for another platform or feature compiles only in that configuration: build it or say it was not built. Not done until gate green. Report failures verbatim. `references/tooling.md` has the presets, warning sets, hardening, and sanitizer flags.

## Tool preference

- Definitions, references, call hierarchy, hover: `LSP` tool backed by clangd (`clangd-lsp` plugin in Claude Code) when exposed. Needs `compile_commands.json`. Rules in `references/navigation.md`.
- Exact text search: `mcp__fff__grep`/`rg` for strings, macros, build files. Semantic: Semble.
- Library API and which standard added it: cppreference.com or the header. Never guess a signature.
- Global rules still apply: Code Growth Discipline, Code Simplicity Discipline, Useless Test Ban, terminology guard (`snapshot`/`expected`, never `golden`). Cross-language naming, function size, and architecture: skill `software-design`.
