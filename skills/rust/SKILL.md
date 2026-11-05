---
name: rust
description: >
  Idiomatic Rust engineering: writing, reading, reviewing, refactoring, testing,
  and profiling Rust code (.rs, Cargo.toml, Cargo.lock, rust-toolchain.toml,
  build.rs). Use whenever the user works in a Rust workspace or asks anything
  involving ownership, traits, generics, async/tokio, error handling, unsafe,
  FFI, cargo, clippy, nextest, or benchmarks. Trigger even when "Rust" is not
  said but files or commands are clearly Rust. Core rules inline; specialist
  rules live in references/ and load through the routing table below.
---

# Rust engineering skill

Write Rust a careful maintainer would merge without comment: strong types, explicit ownership, small modules, typed errors at boundaries, zero warnings, `unsafe` only with a proof. Edition 2024 is the default for new crates.

## Routing table (mandatory)

Read matching reference BEFORE writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| naming, module layout, edition 2024 idioms, control flow, iterators, docs, formatting, lint attributes | `references/style.md` |
| `Result`, `thiserror`, `anyhow`, error enums, panics, `main` exit | `references/errors.md` |
| any `#[test]`, `tests/`, benches, nextest, rstest, insta, proptest, mockall, coverage, mutants | `references/testing.md` |
| ownership across threads, `Arc`, locks, atomics, channels, tokio, async traits, cancellation, shutdown | `references/concurrency.md` |
| public API, traits, newtypes, builders, features, MSRV, semver, inlining | `references/api-design.md` |
| `extern "C"`, `#[unsafe(no_mangle)]`, cbindgen, UniFFI, react-native bindings, `src/ffi/` | `references/ffi.md` |
| cargo commands, clippy config, `[lints]`, nextest config, deny/audit, CI, profiles | `references/tooling.md` |
| choosing APIs for a given `rust-version`/edition, migrating old idioms | `references/modern.md` |
| benchmarks, profiling, allocation, release profile, PGO | `references/performance.md` |

Multiple matches: read all matched. Unsure: read `style.md` and `errors.md`.

## Before writing

1. Read `Cargo.toml` (package and workspace root): `edition`, `rust-version`, `[lints]`, features. `rust-toolchain.toml` if present. Never use API newer than `rust-version`; `references/modern.md` lists what each version unlocks.
2. Check repo conventions: `rustfmt.toml`, `clippy.toml`, `.config/nextest.toml`, `deny.toml`, error crate in use (`thiserror`/`anyhow`/`snafu`), async runtime, test helpers. Repo convention beats these defaults.
3. Find existing module for the change. New module only for new concern. Projected >600 non-test LOC: mod dir from the start.

## Non-negotiables

- Zero warnings: rustc, clippy, rustdoc. Fix, never `#[allow]`. `#[expect(lint, reason = "...")]` when suppression is deliberate.
- Ownership: one owner, borrow by default, `&str`/`&[T]`/`&Path` params, clone only with a reason. No `.clone()` to dodge the borrow checker.
- Strong types: newtypes for ids and units, enums for state, `NonZero*`, `Duration`, `PathBuf`. No `bool` params, no stringly-typed state.
- `Result<T, E>` for recoverable failures. No `unwrap()`/`expect()` on library paths. `expect` message states the invariant.
- Errors typed (`thiserror`) at public and domain boundaries; `anyhow` only in binaries and internal glue. Context added at I/O, network, DB, parse, config boundaries. Source chain preserved.
- No global mutable state. `LazyLock`/`OnceLock` for immutable init only. Inject dependencies.
- `unsafe` only with `// SAFETY:` comment stating the upheld invariant, `# Safety` rustdoc on `unsafe fn`, smallest `unsafe {}` block per operation.
- Modules: one concern per file. Test module >40% of file: sibling `tests.rs`. `main.rs` thin; logic in lib.
- Iterators over index loops. No premature `collect()`. Return `impl Iterator` when caller may stop early.
- Edition 2024 idioms: let chains, `if let` guards (1.95+), `use<>` when returned `impl Trait` must not capture a lifetime, `unsafe extern` blocks, `#[unsafe(no_mangle)]`.
- `#[must_use]` on builders and pure functions. `#[non_exhaustive]` on public enums and structs that may grow.
- Async: no blocking calls on runtime threads (`spawn_blocking`), no lock guard across `.await`, every spawned task joined or tracked, cancellation via `CancellationToken`.
- Comments: plain humanizer prose, why not what, no plan/task ids, no em dash. Rustdoc on every `pub` item; `# Errors`, `# Panics`, `# Safety` sections when applicable.
- Tests must fail from a project bug. No derive/stdlib restatement, no field echo, no mock-call-count-only.

## After writing (gate, in order)

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo nextest run --workspace --all-features     # fallback: cargo test --workspace --all-features
cargo test --doc --workspace                     # nextest skips doctests
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --workspace   # library crates
```

Feature-gated code: every command carries the `--features` it validates. Not done until gate green. Report failures verbatim. `references/tooling.md` covers deny, audit, semver-checks, coverage, mutants.

## Tool preference

- Symbols, references, hover, diagnostics: `rust_analyzer_*` MCP tools or `LSP` tool (rust-analyzer). Never guess signatures; `cargo doc --open` or docs.rs when unsure.
- Exact text search: `fff-grep`/`rg`. Semantic: Semble.
- Global rules still apply: Code Growth Discipline, Code Simplicity Discipline, Useless Test Ban, terminology guard (`snapshot`/`expected`, never `golden`). Cross-language naming, function size, and architecture: skill `software-design`.
