# Rust Testing

Loaded via `rust` SKILL.md routing table. Sources: `cargo test` docs, nexte.st docs, rstest, insta, proptest, mockall 0.14, cargo-llvm-cov, cargo-mutants, Rust Style Guide.

## Runner

- `cargo nextest run --workspace --all-features` is the gate when `cargo-nextest` installed. Per-test process isolation, parallel by default, retries, timeouts, JUnit.
- nextest skips doctests: always follow with `cargo test --doc --workspace`.
- `cargo test` only when nextest unavailable, for doctests, or when a target cannot run under nextest. State fallback reason.
- Config `.config/nextest.toml` at workspace root:

```toml
[profile.default]
slow-timeout = { period = "30s", terminate-after = 3 }
leak-timeout = "500ms"

[profile.ci]
retries = 1
fail-fast = false
status-level = "fail"
final-status-level = "slow"

[profile.ci.junit]
path = "junit.xml"

[[profile.default.overrides]]
filter = "test(/integration/)"
test-threads = 1
```

- Flags: `-P ci`, `--no-fail-fast`, `--retries N`, `-j N`, `--run-ignored all`, `--partition hash:1/2` for sharding. Filter expressions: `-E 'test(parse) & package(core)'`, `kind(lib)`.
- `cargo nextest archive --archive-file t.tar.zst` then `run --archive-file` to test a prebuilt tree in another job.

## Behavior-focused tests

- Test project behavior: invariants, edge cases, error paths, data mapping, retry and backpressure, persistence contracts, regressions (name the issue).
- Every test has a failure mode tied to project logic. None: do not write it.
- Deleting a useless test: no replacement unless coverage is lost.

## Useless tests to reject

Do not create tests that prove Rust, std, or dependency behavior:

- `Option::is_some()`, casts, arithmetic, derived `Default`/`Debug`/`Clone`/`Eq`/`Hash`.
- `thiserror` `#[error]` string equality, `#[from]` conversion works.
- Trivial getters and setters, constructor stores argument, struct literal readback, constant equals itself.
- Plain serde roundtrip with no custom `Serialize`/`Deserialize` impl, `#[serde(default)]` mechanics, `Default::default()`.
- Mock call counts without asserted output.
- Whole-string snapshot of big SQL or JSON when no part of it is contract. Assert fields or use `insta` with redactions.
- Branch already covered by a named existing test.
- Test named for a behavior but asserting something weaker.
- Copy-pasted test doubles or encoders across modules. One `tests/support` or `src/test_support.rs` (`#[cfg(test)]`) per crate.
- Re-proving a generic contract per implementation. One generic assert helper, called per impl.

Keep: wire and on-disk layout pins (`size_of`, `align_of`, discriminant values, format magic), config compatibility across versions, migration idempotence.

## Unit test isolation

- No DB, network, API, or filesystem I/O outside `tempfile::tempdir()` in unit tests. `#[ignore]` does not make external I/O acceptable in a unit test file.
- Real DB, network, filesystem: `tests/` integration binary or e2e suite with own command, gated by env var (`TEST_DATABASE_URL`) or `#[ignore = "needs postgres"]` and run with `--run-ignored all` in CI job that has the dependency.
- Localhost ephemeral servers acceptable for protocol tests: `wiremock`, `httpmock`, `tokio::net::TcpListener` bound to port 0.
- Env vars: `temp-env::with_var` or `serial_test` `#[serial]`. Never `std::env::set_var` unscoped (unsafe in 2024 for good reason).
- Time: inject `now: fn() -> Instant` or `tokio::time::pause()` via `#[tokio::test(start_paused = true)]`.

## Structure

- Unit tests in `#[cfg(test)] mod tests { use super::*; }` beside code. Move to sibling `tests.rs` (`#[cfg(test)] mod tests;`) when >40% of file.
- Integration tests in `tests/<feature>.rs`. Each file is a binary: share helpers via `tests/support/mod.rs`.
- Test names: `fn parse_rejects_trailing_comma()`, `fn retry_stops_after_max_attempts()`. Behavior, not method name.
- Arrange, act, assert. One behavior per test. Fixtures small and readable over broad dumps.
- `#[should_panic(expected = "index out of range")]` only for documented panics. Prefer `Result`-returning APIs and assert error kind.
- `#[ignore = "reason"]` always with reason.
- Tests returning `Result<(), E>` allowed so `?` works; final expression `Ok(())`.

## Assertions

- `assert_eq!(got, want, "context")`. Left is got, right is want, consistent.
- `assert_matches!(value, Pattern)` (1.96+) and `matches!` for enum shape.
- `pretty_assertions` for large structs when repo has it.
- Error asserts: variant or kind, source presence, caller action. Not `is_err()` alone. Not message text unless contract. See `errors.md`.
- Floats: `approx::assert_relative_eq!` or tolerance, never `==`.

## Fixtures and parametrization: rstest

```rust
#[rstest]
#[case("a=1", Config { a: 1 })]
#[case("a=1\nb=2", Config { a: 1, b: 2 })]
fn parses_pairs(#[case] input: &str, #[case] want: Config) {
    assert_eq!(parse(input).unwrap(), want);
}

#[fixture]
fn store() -> MemStore { MemStore::seeded() }

#[rstest]
fn finds_seeded_user(store: MemStore) { ... }
```

- `rstest` when repo has it. Otherwise a plain loop over `&[(input, want)]` with a message naming the case.
- `#[values(...)]` for cartesian combos. Keep combos small.

## Snapshots: insta

- `insta::assert_snapshot!`, `assert_debug_snapshot!`, `assert_json_snapshot!`. Review with `cargo insta review`. Snapshots committed under `snapshots/`.
- Redact volatile fields: `insta::assert_json_snapshot!(v, { ".id" => "[id]", ".ts" => "[ts]" })`.
- Snapshot only outputs that are contract or large structured render (CLI help, generated code, error reports). Not internal structs that churn.
- Name files `<test>__<case>.snap`. Never `golden` in names (terminology guard).

## Property tests: proptest

```rust
proptest! {
    #[test]
    fn roundtrip(v in any::<Message>()) {
        prop_assert_eq!(decode(&encode(&v)).unwrap(), v);
    }
}
```

- Properties: roundtrip, idempotence, invariant holds, no panic, agrees with reference impl.
- `proptest-regressions/` committed. Failing seeds stay caught.
- Custom `Strategy` for domain types via `prop_compose!` or `Arbitrary` derive (`proptest-derive`).
- `cargo fuzz` (nightly, libFuzzer) for parsers and decoders taking untrusted bytes. Corpus committed. Runs in scheduled CI, not on every push.

## Test doubles

- Hand-written fake implementing the consumer's trait, holding state, returning canned values. Default choice.
- `mockall` (`#[automock]` on trait, `mock!` for external traits) when interaction order or argument predicates matter. Assert outcome, not only `times(1)`.
- Trait at consumer side, 1-3 methods. No trait created solely to mock a concrete type with one impl: test through the real type.
- Async traits: `#[automock]` works with `async fn` in traits (1.75+); `#[async_trait]` only if repo already uses it.

## Async tests

- `#[tokio::test]` default current-thread. `#[tokio::test(flavor = "multi_thread", worker_threads = 2)]` when testing parallelism or `spawn_blocking`.
- `#[tokio::test(start_paused = true)]` + `tokio::time::advance` for timeouts, backoff, tickers. No real sleeps.
- Cancellation tests: drop the future or fire `CancellationToken`, assert cleanup ran (channel closed, flag set).
- `tokio::time::timeout` around awaits that must complete, so hangs fail instead of stalling CI.
- `loom` for lock-free and hand-rolled sync primitives: `#[cfg(loom)]` model with `loom::model(|| ...)`.

## Coverage and mutation

- `cargo llvm-cov --workspace --all-features --lcov --output-path lcov.info` (`cargo llvm-cov nextest` to use nextest). Coverage is a map of untested code, not a target number.
- `cargo mutants --workspace` in scheduled CI or before release. Surviving mutants name weak tests; fix the test or delete dead code.
- `cargo hack --feature-powerset --no-dev-deps check` catches feature-gated compile errors tests miss.

## Doctests

- Every public item with non-trivial usage gets a doctest. `?` not `unwrap`. Hidden setup lines start with `# `.
- `no_run` for examples needing network or files. `ignore` only with a reason comment. `compile_fail` for type-level guarantees.
- Edition 2024 merges doctests into one binary: faster, but shared process. No global-state assumptions.

## Benchmarks

- `criterion` (stable, statistical) or `divan` (simpler API). Under `benches/`, `[[bench]] harness = false`. `#[bench]` is unstable, never.
- `std::hint::black_box` on inputs and outputs. Realistic input sizes. See `performance.md`.

## Commands

```sh
cargo nextest run --workspace --all-features
cargo nextest run -P ci --no-fail-fast
cargo nextest run -E 'test(parse)' -p core
cargo nextest run --run-ignored all -E 'test(/integration/)'
cargo test --doc --workspace
cargo test --workspace --all-features -- --nocapture         # fallback runner
cargo llvm-cov nextest --workspace --html
cargo mutants -p core
cargo +nightly fuzz run parse_input -- -max_total_time=60
```

## Avoid

- `std::thread::sleep` or `tokio::time::sleep` to wait for another task. Channels, `Notify`, paused time.
- Global mutable test state without `serial_test`.
- Testing private functions through `#[cfg(test)] pub` hacks. Test via the module's public surface; `pub(crate)` if needed.
- `#[allow(dead_code)]` in tests. Delete the code.
- Asserting log lines unless logs are contract.
- Tests that pass with the implementation deleted.
