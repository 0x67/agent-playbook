# Rust Error Handling

Loaded via `rust` SKILL.md routing table. Sources: `std::error` docs, thiserror 2.x docs, anyhow docs, Sabrina Jewson "Modular Errors in Rust", Rust API Guidelines C-GOOD-ERR.

## Decide first: caller action

- Before choosing a type, name the caller's action: retry, return user-correctable validation error, degrade, alert, abort.
- Error type must make that action possible without string matching.
- Caller action decides typed vs `anyhow`. Crate label (lib vs bin) is a hint, not the rule.

## Typed errors required

- Public, reusable, or published library API.
- Caller matches, retries, or recovers by kind.
- Domain boundary crossing.
- User or operator correctable failure: config key, path, invalid input.

## `anyhow` allowed

- Binaries, CLI, service `main` and wiring.
- Internal workspace glue where callers only propagate or log.
- Requirements: `.context()` / `.with_context(|| ...)` at I/O, config, network, SQL, parse, user-input, external-service boundaries. Source chain preserved. No secrets in messages. Rationale stated in review when any library API exposes `anyhow`.
- `bail!`, `ensure!` for early exits. `anyhow::Error::downcast_ref::<T>()` only at the top layer, and rarely.

## Shape errors (Modular Errors)

- Error type lives next to its unit of fallibility. Per-operation error when failure modes or messages differ.
- Layered: high-level operation error wraps lower-level cause via `source`. Report shows operation plus root cause.
- No kitchen-sink `crate::Error` / `errors.rs` when operation errors fit. Aggregate at the boundary only.
- `#[non_exhaustive]` on every public error enum and struct.
- Tiny private validation errors: manual `Display` + `impl std::error::Error` is fine. `thiserror` when variants, sources, `#[from]`, or formatting boilerplate justify it.

## thiserror 2.x

```rust
#[derive(Debug, thiserror::Error)]
#[non_exhaustive]
pub enum LoadError {
    #[error("read config {path}")]
    Read { path: PathBuf, #[source] source: std::io::Error },
    #[error("parse config {path}: line {line}")]
    Parse { path: PathBuf, line: u32, #[source] source: toml::de::Error },
    #[error("missing key {0}")]
    MissingKey(String),
    #[error(transparent)]
    Other(#[from] anyhow::Error), // escape hatch, only in app-layer errors
}
```

- `#[error("...")]` interpolates fields: `{path}`, `{0}`, `{path:?}`. Message states failed operation plus stable identifier. Lowercase, no trailing period, no `error:` prefix.
- Message must not repeat the source's text. Source prints in the chain.
- `#[source]` explicit or field named `source`. Implements `Error::source()`.
- `#[from]` only when conversion loses no operation context. Implies `#[source]`. One `#[from]` per source type per enum.
- `#[error(transparent)]` for opaque forwarding wrappers: Display and source delegate.
- `#[error(fmt = path::to_fn)]` (2.x) when Display needs custom logic.
- `#[backtrace]` on a `std::backtrace::Backtrace` field when capture matters; costs at construction.
- `no_std`: `thiserror = { version = "2", default-features = false }` uses `core::error::Error` (1.81+).
- `thiserror` never appears in public API. Switching implementations later is non-breaking.

## Context rules

- Add context once at a meaningful boundary, not after every `?`.
- Context adds what the inner error lacks: path, key, endpoint, table, symbol, index. Never a vague `failed`.
- `map_err` with explicit variant when adding data. `?` alone when the variant already carries it via `#[from]`.
- Chain reporting: `{err:#}` for anyhow one-line chain, `{err:?}` for multi-line with backtrace. Custom reporter iterates `source()`.
- Redact: no tokens, credentials, DSNs, full SQL with values, PII. Put detail in `tracing` fields with redaction, not in `Display`.

## Panics

- `panic!` only for violated invariants and programmer bugs. Message names the invariant.
- Never panic on user input, I/O, network, config, or in library public paths.
- `expect("...")` on a truly infallible path: message explains why it cannot fail (`"regex is a literal"`), not what failed.
- `unwrap()` allowed only in tests, examples with `?` unavailable, and build scripts.
- `#[track_caller]` on functions that panic on caller misuse so the panic points at the caller.
- `catch_unwind` only at FFI and thread boundaries. Never as control flow.
- `panic = "abort"` in release profiles for binaries where unwinding is never caught. Not in libraries (consumer decides).
- `debug_assert!` for invariants that are expensive to check. `assert!` for cheap invariants that must hold in release.

## `main` and exit

```rust
fn main() -> std::process::ExitCode {
    if let Err(err) = run() {
        eprintln!("{err:#}");
        return std::process::ExitCode::FAILURE;
    }
    std::process::ExitCode::SUCCESS
}
```

- `fn main() -> anyhow::Result<()>` acceptable for small CLIs: prints `{:?}` (multi-line chain) and exits 1.
- `std::process::exit` only in `main`. Destructors do not run on exit.
- Exit codes: 1 generic, 2 usage. Specific codes only when scripts depend on them; document them.
- `run()` takes config and writers so tests can call it.

## Boundary conversions

- Transport layer (HTTP, gRPC, CLI) maps domain errors to status or exit code in one `match`. Domain never imports transport types.
- FFI: integer codes or out-params. See `ffi.md`.
- Serde: `#[serde(try_from = "Raw")]` or `Deserialize` impl returning typed validation error.
- Async task join: `JoinError` wrapped with which task failed. Panics in tasks surface as `JoinError::is_panic`.
- `std::io::Error::other(e)` (1.74+) to box a typed error into io::Error at `Read`/`Write` impls. `io::Error::kind()` for matching.

## Useful std APIs

- `Result::flatten` (1.89+) for `Result<Result<T, E>, E>`.
- `Option::ok_or_else`, `Result::ok`, `transpose` for `Option<Result>` flips.
- `Result::inspect_err` (1.76+) to log without consuming.
- `std::error::Error::source()`, `Error::description` deprecated, never implement it.
- `core::error::Error` (1.81+) for `no_std` crates.

## Test assertions

- Assert kind: `assert!(matches!(err, LoadError::MissingKey(k) if k == "port"))` or `assert_matches!(err, LoadError::MissingKey(_))` (1.96+).
- Assert source presence when chain matters: `err.source().is_some()`, or downcast: `err.source().unwrap().downcast_ref::<io::Error>()`.
- Not `is_err()` alone when kind matters. Not `err.to_string() == "..."` unless message text is public contract.
- `anyhow` in tests: `err.downcast_ref::<LoadError>()` or `err.chain().any(|e| e.is::<io::Error>())`.

## Avoid

- `Box<dyn Error>` or `Box<dyn Error + Send + Sync>` in library public API. Typed error or `anyhow` at app layer.
- `String` as error type. `Result<T, String>` only in throwaway scripts.
- `#[from]` on every variant: hides which operation failed.
- `.to_string()` on source errors then wrapping the string. Loses chain and type.
- `unwrap()`/`expect()` in production paths.
- Context spam: `"a: b: c: d: open file"`.
- `impl From<E> for MyError` that silently maps unrelated failures into one variant.
- Logging and returning the same error. Handle once.
- `Result<(), ()>`. Use `Option` or a unit error type with meaning.
