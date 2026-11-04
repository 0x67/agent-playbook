# Rust Tooling

Loaded via `rust` SKILL.md routing table. Sources: Cargo reference (lints, profiles, workspaces, config), clippy docs, rustfmt docs, nexte.st, cargo-deny, cargo-audit, cargo-semver-checks, cargo-llvm-cov, cargo-mutants, cargo-hack, cargo-msrv.

## Gate (run in order, after every change)

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo nextest run --workspace --all-features       # fallback: cargo test --workspace --all-features
cargo test --doc --workspace
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --workspace   # library crates
```

- Any red: fix, rerun the whole gate. Report failures verbatim.
- Feature-gated code compiles only under its feature: every command carries the `--features` it validates. Green without compiling the target is false green. `cargo hack --feature-powerset check` for full coverage.
- `--all-features` conflicts (mutually exclusive features are a bug; see `api-design.md`): run per feature set and state which.

## Lints: `[lints]` table

Lints live in `Cargo.toml`, never in `lib.rs` attributes. Workspace root:

```toml
[workspace.lints.rust]
unsafe_op_in_unsafe_fn = "deny"
missing_docs = "warn"                 # library crates
unused_qualifications = "warn"
rust_2024_compatibility = "warn"      # while migrating 2021 crates

[workspace.lints.clippy]
all = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
nursery = { level = "warn", priority = -1 }
# targeted relaxations from pedantic/nursery, each with a reason in a comment
module_name_repetitions = "allow"     # `config::ConfigError` is fine
must_use_candidate = "allow"          # too noisy on internal fns
missing_errors_doc = "warn"
missing_panics_doc = "warn"
unwrap_used = "deny"                  # lib crates; tests get expect(...) at module level
expect_used = "warn"
dbg_macro = "deny"
todo = "deny"
unimplemented = "deny"
enum_glob_use = "deny"
```

Each member:

```toml
[lints]
workspace = true
```

- `priority = -1` on groups so individual lints override them. Without it, order is unspecified and cargo warns.
- Groups and defaults: `correctness` deny, `suspicious`/`style`/`complexity`/`perf` warn (these five = `clippy::all`), `pedantic`/`nursery`/`restriction`/`cargo` allow. Enable `pedantic` and `nursery` as warn, then allow specific lints with reasons. Never `restriction` as a group; pick lints (`unwrap_used`, `dbg_macro`, `todo`, `print_stdout` in libs).
- `clippy.toml` for thresholds and MSRV: `msrv = "1.85"`, `too-many-arguments-threshold = 8`, `avoid-breaking-exported-api = false`, `disallowed-methods` for banned APIs (e.g. `std::env::set_var`).
- Suppression in code: `#[expect(lint, reason = "...")]`. `#[allow]` only in generated code.
- `cargo clippy --fix --allow-dirty` for mechanical fixes; review the diff.

## Formatting

- `cargo fmt --all`. Check mode in CI: `--check`.
- `rustfmt.toml` only when needed: `style_edition = "2024"` for crates still on edition 2021 that want new style; `max_width`, `use_small_heuristics = "Max"` per repo taste. Unstable options need nightly; avoid.
- rustfmt 2024 style: version-sorted imports (`u8` before `u16`), consistent raw identifier sorting, expression formatting fixes. Expect churn on edition bump; one dedicated formatting commit.

## nextest

- `.config/nextest.toml` in `testing.md`. `cargo nextest run -P ci` in CI. `--no-fail-fast` locally when triaging.
- `cargo nextest run --workspace --all-features --no-tests=warn` for crates without tests.
- Doctests separately: `cargo test --doc --workspace`.

## Supply chain and hygiene

```sh
cargo deny check            # advisories, licenses, bans, sources (deny.toml)
cargo audit                 # advisories only (RustSec DB)
cargo machete               # unused dependencies (fast, no nightly)
cargo +nightly udeps        # unused deps, more precise, nightly
cargo tree -d               # duplicate crate versions
cargo tree -i <crate>       # who pulls this in
cargo update -p <crate>     # targeted update; plain `cargo update` deliberate
cargo msrv verify           # rust-version holds; `cargo msrv find` to compute
cargo semver-checks check-release   # before every release of a library
cargo hack --feature-powerset --no-dev-deps check
cargo llvm-cov nextest --workspace --html
cargo mutants -p <crate>
```

- `deny.toml`: `[advisories] ignore = []` only with issue links; `[licenses] allow = ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC", "Unicode-3.0"]` per policy; `[bans] multiple-versions = "warn"`, `deny = [{ name = "openssl" }]` when rustls is standard; `[sources] unknown-registry = "deny"`.
- `cargo install --locked <tool>` or `cargo binstall <tool>`. Pin tool versions in CI.
- `Cargo.lock` committed. `cargo update` in a dedicated commit. Renovate/Dependabot for automation.

## Modules and workspace config

- `rust-toolchain.toml`: `[toolchain] channel = "1.98.1"` (exact pin for hermetic builds) or `"stable"`, `components = ["rustfmt", "clippy"]`, `targets` list. `profile = "minimal"` in CI images.
- `rust-version = "1.85"` in `[package]` or `[workspace.package]`. Bumping is a minor release.
- `[workspace] resolver = "3"` (edition 2024 default; enables MSRV-aware resolution).
- `.cargo/config.toml`:

```toml
[build]
warnings = "deny"            # 1.97+; CI only or under [profile]-like env

[target.x86_64-unknown-linux-gnu]
rustflags = ["-C", "target-cpu=native"]   # never in a published lib; deploy images only

[alias]
xt = "nextest run --workspace --all-features"
xc = "clippy --workspace --all-targets --all-features -- -D warnings"
```

- `build.build-dir` (1.91+) to separate intermediates from `target/` artifacts on shared caches.
- `cargo clean --workspace` (1.93+). `cargo sweep` for stale targets.

## Profiles

```toml
[profile.release]
lto = "thin"            # "fat" for max perf at slower link; measure
codegen-units = 1       # smaller, faster binary; slower compile
panic = "abort"         # binaries only, and only when catch_unwind is never needed
strip = "symbols"       # or keep debug = "line-tables-only" for profiling builds
opt-level = 3

[profile.release-debug]   # profiling
inherits = "release"
debug = "line-tables-only"
strip = "none"

[profile.dev.package."*"]
opt-level = 2           # fast deps in debug builds
```

- `opt-level = "z"`/`"s"` for size (wasm, embedded). `overflow-checks = true` in release for financial code, measure the cost.
- `-C target-cpu=native` only for binaries built on the deploy machine.
- `lld` is default linker on `x86_64-unknown-linux-gnu` since 1.90; `mold` via `rustflags = ["-C", "link-arg=-fuse-ld=mold"]` for faster dev links elsewhere.

## Build performance

- `cargo build --timings` to find slow crates. `cargo check` in the inner loop; `cargo clippy` covers check.
- `sccache` or `cargo-chef` in Docker. `CARGO_INCREMENTAL=0` in CI, `1` locally (default).
- Feature unification: `cargo hack` reveals features that force heavy deps. Split heavy deps behind features.
- `cargo depgraph`, `cargo tree --edges features` to see why a dep compiles.

## Docs and inspection

- `cargo doc --no-deps --open`. `RUSTDOCFLAGS="-D warnings"` in CI. `--document-private-items` while refactoring internals.
- `cargo expand` (nightly-friendly) to see macro output. `cargo asm` / `cargo show-asm` for codegen checks.
- `cargo metadata --format-version 1` for scripting. `cargo pkgid`.
- rust-analyzer via `rust_analyzer_*` MCP tools or `LSP` tool: definition, references, hover, diagnostics, rename. Fall back to `rg` only when they fail; state why.

## CI skeleton

1. `cargo fmt --all --check`
2. `cargo clippy --workspace --all-targets --all-features -- -D warnings`
3. `cargo nextest run -P ci --workspace --all-features` + `cargo test --doc --workspace`
4. `cargo hack --feature-powerset --no-dev-deps check` (libraries)
5. `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --workspace`
6. `cargo deny check`, `cargo audit`
7. `cargo msrv verify` (libraries), `cargo semver-checks check-release` on release branches
8. Nightly job: `cargo +nightly miri test -p <unsafe-crate>`, `cargo mutants`, `cargo fuzz`
9. Matrix: `stable`, `beta` (early warning), MSRV. `RUSTFLAGS="-D warnings"` set once at job level.

## Install missing tools

```sh
cargo install --locked cargo-nextest cargo-llvm-cov cargo-hack cargo-machete cargo-msrv
cargo install --locked cargo-deny cargo-audit cargo-semver-checks
cargo install --locked cargo-mutants cargo-insta cargo-expand
cargo install --locked flamegraph samply
rustup component add clippy rustfmt rust-analyzer llvm-tools
rustup toolchain install nightly --component miri rust-src
```

`cargo binstall` fetches prebuilt binaries when available.
