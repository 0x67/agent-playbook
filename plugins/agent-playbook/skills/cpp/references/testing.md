# C++ Testing

Loaded via `cpp` SKILL.md routing table. Sources: GoogleTest docs, Catch2 v3 docs, CMake GoogleTest and CTest docs, libFuzzer docs, Clang sanitizer and source-based coverage docs.

## Framework

Use what the repo has. New project: GoogleTest (with GoogleMock) or Catch2 v3; doctest when compile time matters most.

| | GoogleTest | Catch2 v3 |
|---|---|---|
| test | `TEST(Suite, Name)` | `TEST_CASE("name", "[tag]")` |
| fixture | `TEST_F(Fixture, Name)` | `SECTION`s in one test case, or `TEST_CASE_METHOD(Fixture, ...)` |
| table-driven | `TEST_P` + `INSTANTIATE_TEST_SUITE_P` | `GENERATE(...)` |
| stop / continue on failure | `ASSERT_*` / `EXPECT_*` | `REQUIRE` / `CHECK` |
| register with CTest | `include(GoogleTest)` + `gtest_discover_tests(t)` | `include(Catch)` + `catch_discover_tests(t)` |
| main | link `GTest::gtest_main` | link `Catch2::Catch2WithMain` |

## Layout

- Tests beside the component (`net/parser_test.cpp`) or in `tests/` mirroring `src/`: follow the repo.
- One test executable per library target, registered with CTest, so `ctest` runs everything.
- Shared fakes and builders live in one test support library, not copied between files.

## Writing tests

- Test behavior through the public interface. Name scenario and expectation: `TEST(PortParser, RejectsValuesAbove65535)`.
- Arrange, act, assert. One behavior per test; several asserts on one result are fine.
- `EXPECT_*`/`CHECK` by default so one run reports every failure; `ASSERT_*`/`REQUIRE` when continuing would crash.
- Floating point: `EXPECT_DOUBLE_EQ`, `EXPECT_NEAR`, Catch2 `WithinRel`/`WithinAbs`. Never `==`.
- Death tests (`EXPECT_DEATH`) only for assertion and contract checks.
- Fakes over mocks. GoogleMock when the dependency is an interface and the interaction is the contract; assert on outcomes too, never only call counts.
- Inject time, randomness, filesystem, and network: a clock interface or template parameter, a seeded engine, a temp dir per test.
- No sleeps to synchronize. Latches, futures, fake clocks.
- Tests must fail from a project bug. Skip: compiler-generated copy, move, or `==` working; getter echo; restating `std::` behavior; mock call counts with no observable result.
- Expected-output files are `snapshot` or `expected`, never `golden`.

## Sanitizer runs

The suite runs under sanitizers in CI, one build preset each (`tooling.md` has the presets):

| Preset | Flags | Finds |
|---|---|---|
| asan | `-fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=all` | out-of-bounds, use-after-free, leaks (Linux), UB |
| tsan | `-fsanitize=thread` | data races, lock-order inversions |
| msan | `-fsanitize=memory -fsanitize-memory-track-origins` (Clang, Linux, all code instrumented) | uninitialized reads |

- `-fno-sanitize-recover=all` makes UBSan fail the test instead of printing and continuing.
- Run with `ASAN_OPTIONS=abort_on_error=1` and `UBSAN_OPTIONS=print_stacktrace=1`.
- Sanitizer builds use `-O1` or `-O2` with `-g` (`RelWithDebInfo`).

## Fuzzing

Parsers, decoders, and anything reading untrusted bytes get a libFuzzer target:

```cpp
extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
    (void)parse_message(std::span(data, size));
    return 0;
}
```

Build with Clang `-fsanitize=fuzzer,address,undefined`. Keep a seed corpus in the repo. Every crash input becomes a regression test.

## Coverage

Clang: `-fprofile-instr-generate -fcoverage-mapping`, run tests, `llvm-profdata merge`, `llvm-cov report`/`show`. GCC: `--coverage` with gcovr. Coverage shows untested code; it is not a target.

## Gate

```sh
cmake --build --preset dev && ctest --preset dev
cmake --build --preset asan && ctest --preset asan
```
