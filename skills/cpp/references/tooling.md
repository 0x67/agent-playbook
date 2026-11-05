# C/C++ Tooling

Loaded via `cpp` SKILL.md routing table. Sources: CMake docs (cmake-buildsystem, cmake-presets), OpenSSF Compiler Options Hardening Guide for C and C++ (2026-08 revision), libc++ hardening docs, clang-tidy and clang-format docs, Clang sanitizer docs.

## Gate (run in order, after every change)

```sh
clang-format --dry-run --Werror <changed files>
cmake --build --preset dev
ctest --preset dev
clang-tidy -p build/dev <changed .cpp/.cc files>
cmake --build --preset asan && ctest --preset asan
```

- Red: fix, rerun the whole gate. Report failures verbatim.
- Code under `#if` for another platform, compiler, or feature compiles only in that configuration. Build that preset too, or say which configurations were not built. Green without compiling the target is false green.
- No presets in the repo: `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON && cmake --build build && ctest --test-dir build --output-on-failure`.

## CMake

Targets carry their own requirements. No global flags in `CMakeLists.txt`.

```cmake
cmake_minimum_required(VERSION 3.28)
project(app LANGUAGES CXX)

set(CMAKE_CXX_EXTENSIONS OFF)

add_library(app_warnings INTERFACE)
target_compile_options(app_warnings INTERFACE
  $<$<CXX_COMPILER_ID:GNU,Clang,AppleClang>:-Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Wshadow
    -Wnon-virtual-dtor -Wold-style-cast -Woverloaded-virtual -Wnull-dereference -Wdouble-promotion
    -Wformat -Wformat=2 -Wimplicit-fallthrough>
  $<$<CXX_COMPILER_ID:MSVC>:/W4 /permissive- /utf-8 /Zc:__cplusplus>)

add_library(app_core src/parser.cpp)
target_include_directories(app_core PUBLIC include)
target_compile_features(app_core PUBLIC cxx_std_23)
target_link_libraries(app_core PRIVATE app_warnings)

add_executable(app src/main.cpp)
target_link_libraries(app PRIVATE app_core app_warnings)

if(PROJECT_IS_TOP_LEVEL)
  include(CTest)
  if(BUILD_TESTING)
    add_subdirectory(tests)
  endif()
endif()
```

- `target_*` commands with `PRIVATE`/`PUBLIC`/`INTERFACE`. No `include_directories`, `add_definitions`, `link_libraries`, or `CMAKE_CXX_FLAGS` edits in `CMakeLists.txt`. Warnings link in `PRIVATE` so consumers do not inherit them; sanitizers and hardening come from presets.
- Standard: `target_compile_features(<lib> PUBLIC cxx_std_NN)`, or `CMAKE_CXX_STANDARD` plus `CMAKE_CXX_STANDARD_REQUIRED ON`. `CMAKE_CXX_EXTENSIONS OFF` keeps `-std=c++NN` instead of `gnu++NN`.
- Warnings as errors: `CMAKE_COMPILE_WARNING_AS_ERROR` (CMake 3.24) in the CI preset, not hard-coded `-Werror`, so new compilers do not break users' builds.
- Dependencies: `find_package(X CONFIG REQUIRED)` fed by vcpkg (manifest `vcpkg.json`, `CMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake`) or Conan 2 (`conan install . --build=missing`, `CMakeDeps` + `CMakeToolchain`), or `FetchContent` pinned to a tag or commit (`FIND_PACKAGE_ARGS` to prefer an installed copy). Follow the repo. No copied-in sources without a reason.
- Generator: Ninja. Build through `cmake --build`, never by calling make or ninja inside the build dir in scripts.

## Presets

`CMakePresets.json` is committed; `CMakeUserPresets.json` stays local and ignored.

```json
{
  "version": 6,
  "configurePresets": [
    {
      "name": "dev",
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build/${presetName}",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "Debug", "CMAKE_EXPORT_COMPILE_COMMANDS": "ON" }
    },
    { "name": "ci", "inherits": "dev", "cacheVariables": { "CMAKE_COMPILE_WARNING_AS_ERROR": "ON" } },
    {
      "name": "asan",
      "inherits": "dev",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "RelWithDebInfo",
        "CMAKE_CXX_FLAGS": "-fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=all"
      }
    },
    {
      "name": "tsan",
      "inherits": "dev",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "RelWithDebInfo", "CMAKE_CXX_FLAGS": "-fsanitize=thread" }
    }
  ],
  "buildPresets": [
    { "name": "dev", "configurePreset": "dev" },
    { "name": "ci", "configurePreset": "ci" },
    { "name": "asan", "configurePreset": "asan" },
    { "name": "tsan", "configurePreset": "tsan" }
  ],
  "testPresets": [
    { "name": "dev", "configurePreset": "dev", "output": { "outputOnFailure": true } },
    { "name": "ci", "configurePreset": "ci", "output": { "outputOnFailure": true } },
    {
      "name": "asan",
      "configurePreset": "asan",
      "output": { "outputOnFailure": true },
      "environment": { "ASAN_OPTIONS": "abort_on_error=1", "UBSAN_OPTIONS": "print_stacktrace=1" }
    },
    { "name": "tsan", "configurePreset": "tsan", "output": { "outputOnFailure": true } }
  ]
}
```

- `CMAKE_CXX_FLAGS` also reaches the link line when the C++ driver links, so `-fsanitize` needs no separate linker flag.
- clangd and clang-tidy: symlink `build/dev/compile_commands.json` to the repo root, or point `.clangd` at `build/dev`.

## Warnings

| Compiler | Baseline | Worth adding |
|---|---|---|
| GCC, Clang | `-Wall -Wextra -Wpedantic` | `-Wconversion -Wsign-conversion -Wshadow -Wnon-virtual-dtor -Wold-style-cast -Woverloaded-virtual -Wnull-dereference -Wdouble-promotion -Wformat -Wformat=2 -Wimplicit-fallthrough` |
| GCC only | | `-Wduplicated-cond -Wduplicated-branches -Wlogical-op -Wuseless-cast` |
| Clang only | | `-Wthread-safety` (with annotations) |
| MSVC | `/W4 /permissive-` | `/utf-8`, `/Zc:__cplusplus`, `/analyze` in a CI job |

Clang's `-Wformat=2` does not include `-Wformat`; list both.

## Hardening (release builds)

The OpenSSF guide's baseline, for GCC and Clang on ELF platforms:

```sh
-O2 -Wall -Wformat -Wformat=2 -Wconversion -Wimplicit-fallthrough -Werror=format-security
-U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3                     # needs -O1 or higher
-D_GLIBCXX_ASSERTIONS                                     # libstdc++
-D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_FAST      # libc++ 18+
-fstrict-flex-arrays=3
-fstack-clash-protection -fstack-protector-strong
-Wl,-z,nodlopen -Wl,-z,noexecstack -Wl,-z,relro -Wl,-z,now
-Wl,--as-needed -Wl,--no-copy-dt-needed-entries
```

- Add per target: executables `-fPIE -pie`, shared libraries `-fPIC -shared`; x86_64 `-fcf-protection=full`; AArch64 `-mbranch-protection=standard`.
- Production extras from the guide: `-ftrivial-auto-var-init=zero -fno-delete-null-pointer-checks -fno-strict-overflow -fno-strict-aliasing`.
- GCC 14+: `-fhardened` turns on most of this in one flag. GCC-only extras: `-Wtrampolines`, `-fzero-init-padding-bits=all` (GCC 15).
- The `-Wl,-z,...` and `--as-needed` options are GNU ld spellings; LLD, gold, and Apple ld differ. `-z,nodlopen` breaks shared objects meant to be loaded with `dlopen` (plugins).
- libc++ modes: `none`, `fast` (recommended for production), `extensive`, `debug` (non-production). Define the macro before any include, on the command line. No ABI impact.

## clang-tidy

Starting `.clang-tidy`; the repo's file wins:

```yaml
Checks: >
  -*,
  bugprone-*,
  clang-analyzer-*,
  concurrency-*,
  cppcoreguidelines-*,
  misc-*,
  modernize-*,
  performance-*,
  portability-*,
  readability-*,
  -bugprone-easily-swappable-parameters,
  -portability-avoid-pragma-once,
  -cppcoreguidelines-owning-memory,
  -performance-enum-size,
  -cppcoreguidelines-avoid-magic-numbers,
  -readability-magic-numbers,
  -modernize-use-trailing-return-type,
  -readability-identifier-length,
  -misc-non-private-member-variables-in-classes
WarningsAsErrors: '*'
HeaderFilterRegex: '(src|include)/'
```

- `clang-tidy -p build/dev <files>` on changed files; `run-clang-tidy -p build/dev` for the whole tree.
- Each disabled check gets a reason in review. Above: `portability-avoid-pragma-once` contradicts the header rule in `style.md`, `cppcoreguidelines-owning-memory` needs GSL's `gsl::owner`, the rest are style noise for most codebases.
- `misc-include-cleaner` wants each `.cpp` to include what it uses directly, even when its own header already includes it.
- `clang-tidy --fix` for mechanical modernization in its own commit; review the diff.
- `clang-tidy --verify-config` after editing the file.

## clang-format

Starting `.clang-format`:

```yaml
BasedOnStyle: Google
ColumnLimit: 100
IncludeBlocks: Regroup
DerivePointerAlignment: false
PointerAlignment: Left
InsertBraces: true
```

- Pin the clang-format major version in CI; output changes between versions.
- `git clang-format` formats only changed lines in existing code.

## Other build systems

| System | Build and test | Notes |
|---|---|---|
| Meson | `meson setup build -Dwarning_level=3 -Dwerror=true`, `meson compile -C build`, `meson test -C build` | `-Db_sanitize=address,undefined`; writes `compile_commands.json` itself |
| Bazel | `bazel build //...`, `bazel test //...` | sanitizers via `--config=asan` in `.bazelrc`; compile commands via `hedronvision/bazel-compile-commands-extractor` |
| Make | the repo's targets | `bear -- make` for `compile_commands.json` |

## CI skeleton

1. `clang-format --dry-run --Werror` on changed files.
2. Configure and build the `ci` preset on each supported compiler (GCC, Clang, MSVC as the repo needs) and the minimum supported versions.
3. `ctest --preset ci`.
4. `asan` and `tsan` presets with tests.
5. `clang-tidy` on changed files.
6. Release build with the hardening flags; fuzz targets on a schedule.

## Install missing tools

```sh
brew install llvm cmake ninja                 # macOS; Homebrew llvm is keg-only: add $(brew --prefix llvm)/bin to PATH
sudo apt install clang clangd clang-tidy clang-format cmake ninja-build   # Debian/Ubuntu
```

Windows: Visual Studio Build Tools (MSVC), LLVM, CMake, and Ninja from winget or their installers. Run CMake from a Developer PowerShell so MSVC is on `PATH`.
