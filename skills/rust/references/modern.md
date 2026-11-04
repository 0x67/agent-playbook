# Modern Rust by Version

Loaded via `rust` SKILL.md routing table. Sources: Rust release notes 1.75 through 1.98 (releases.rs), Edition Guide 2024.

## Rule

- `rust-version` in `Cargo.toml` is the ceiling. No API or syntax above it. Missing `rust-version`: treat the workspace toolchain (`rust-toolchain.toml`, else installed stable) as the ceiling and say so.
- `edition` controls syntax and semantics; `rust-version` controls std API. Both matter: let chains need edition 2024 and 1.88.
- Bumping `rust-version` is a minor release for libraries. Bumping `edition`: `cargo fix --edition`, review, one commit.
- New code uses the newest idiom the crate allows. Existing code migrates only when asked; `cargo clippy` `msrv` setting keeps suggestions honest.
- Third-party crates replaced by std: switch in new code; migrate existing when touching that code or when asked.

## Ladder

| Version | Unlocks |
|---|---|
| 1.75 (Dec 2023) | async fn and RPIT in traits (RPITIT), `pointer::byte_offset`, `Option::as_slice` |
| 1.76 | `Result::inspect`/`inspect_err`, `Arc::unwrap_or_clone`, `ptr::addr_eq` |
| 1.77 | C-string literals `c"..."`, `slice::first_chunk`, `array::each_ref`, `File::create_new`, `offset_of!` |
| 1.78 | `#[diagnostic::on_unimplemented]`, `impl_trait_projections`, `unchecked_*` int ops, `Duration::abs_diff` |
| 1.79 | inline `const { }` blocks, `<T as Trait>::Assoc` bounds in associated type position, `Option::take_if`, `slice::split_at_unchecked` |
| 1.80 | `LazyCell`/`LazyLock`, exclusive range patterns `a..b`, `#[cfg]` name checking (`unexpected_cfgs`), `Box<[T]>::from_iter`, `slice::split_once` |
| 1.81 | `#[expect(lint)]`, `core::error::Error`, `panic = "abort"` on `extern "C"` unwind, `slice::sort` becomes `sort_unstable`-safe, `fs::exists`, `Duration::abs_diff`, new `sort` implementations |
| 1.82 | `use<..>` precise capturing, `&raw const`/`&raw mut`, `unsafe extern` blocks (opt-in), `unsafe` attributes (opt-in), `Option::is_none_or`, `[T]::get_many_mut` (unstable then), `std::process::ExitCode::exit_process`, `size_of` in prelude |
| 1.83 | `const` context expansion (`&mut` in const, `Option::unwrap`), `Entry::insert_entry`, `MaybeUninit` slice APIs, `io::ErrorKind` variants stabilized |
| 1.84 | strict provenance APIs (`with_addr`, `addr`), MSRV-aware resolver `resolver = "3"`, `Ipv6Addr::is_unique_local`, `<[T]>::get_disjoint_mut` (unstable) |
| 1.85 | edition 2024, async closures + `AsyncFn*` traits, `#[diagnostic::do_not_recommend]`, `{float}::midpoint`, `Waker::noop`, tuple `FromIterator` |
| 1.86 | trait upcasting (`&dyn Sub` to `&dyn Super`), `get_disjoint_mut`, `Vec::pop_if`, `Once::wait`, `f32::next_up`/`next_down`, safe `#[target_feature]` fns |
| 1.87 | `Vec::extract_if`, `LinkedList::extract_if`, `use<>` in trait RPITs, anonymous pipes (`std::io::pipe`), `slice::split_off*`, `unbounded_shl/shr`, `String: TryFrom<Vec<u8>>` |
| 1.88 | let chains (edition 2024), naked functions, `#[cfg(true)]`/`#[cfg(false)]`, `Cell::update`, `HashMap::extract_if`, `slice::as_chunks`, cargo cache auto-GC |
| 1.89 | explicitly inferred const args `_`, `Result::flatten`, `File::lock*`, `NonNull` provenance APIs, `OsString::leak`, `mismatched_lifetime_syntaxes` lint, doctest cross-compile |
| 1.90 | `lld` default on x86_64 linux, `cargo publish --workspace`, `CStr` cross-comparisons, const float rounding, unsigned `checked_sub_signed` etc |
| 1.91 | `strict_*` int ops, `carrying_add`/`borrowing_sub`, `Path::file_prefix`, `PathBuf::add_extension`, `BTreeMap::extract_if`, `Duration::from_mins/hours`, `str::ceil_char_boundary`, `build.build-dir`, C variadics on sysv64/win64 |
| 1.92 | `#[track_caller]` with `#[unsafe(no_mangle)]`, `Box::new_zeroed`, `RwLockWriteGuard::downgrade`, `btree_map::Entry::insert_entry`, const slice rotation, never-type lints deny |
| 1.93 | `MaybeUninit` slice `assume_init_ref`/`write_clone_of_slice`, `String::into_raw_parts`, `Vec::into_raw_parts`, `unchecked_neg/shl/shr`, `VecDeque::pop_front_if`, `cargo clean --workspace`, `const_item_interior_mutations` lint |
| 1.94 | `array_windows`, `element_offset`, `LazyLock::get`/`force` accessors, `char: TryFrom<usize>`, `Peekable` map variants, `EULER_GAMMA`/`GOLDEN_RATIO`, const `mul_add`, `unused_visibilities` lint, cargo config `include`, TOML 1.1 |
| 1.95 | `if let` guards in match arms, `AtomicX::update`, `cfg_select!`, `Vec::push_mut`/`insert_mut`, `Layout::dangling_ptr`/`repeat`, `ptr::as_ref_unchecked`, `hint::cold_path`, `bool: TryFrom<int>`, `--remap-path-scope` |
| 1.96 | `assert_matches!`/`debug_assert_matches!`, `From` for `AssertUnwindSafe`/`LazyCell`/`LazyLock`, `NonZero` ranges iterate, `expr` metavariable in `cfg`, cargo git+registry dual sources |
| 1.97 | `build.warnings` config, `resolver.lockfile-path`, `bit_width`/`isolate_highest_one` int ops, rustdoc `--emit`, `cargo -m` alias, v0 symbol mangling default, `pin!` blocks deref coercion, `unused_pub_in_binary` style lint |
| 1.98 | `str::substr_range`, `String::from_utf16le`, `strip_circumfix`, algebraic float ops, `derive` at `std::derive`, atomic conversions, `invalid_runtime_symbol_definitions` deny, `c_void_returns` warn, stricter `repr(transparent)` |

## Edition 2024 migration checklist

1. `cargo fix --edition --all-features` per crate (or `--workspace`), then set `edition = "2024"`.
2. Review every `use<>` inserted: most are removable when the function no longer needs to hide a capture.
3. `unsafe extern` blocks: verify each item's `safe`/`unsafe` qualifier against the C signature. Auto-migration marks everything `unsafe`.
4. `#[unsafe(no_mangle)]` and friends: mechanical.
5. `unsafe_op_in_unsafe_fn` warnings: add inner `unsafe {}` blocks with `// SAFETY:`.
6. `static mut` references: replace with atomics, `OnceLock`, `Mutex`, or `&raw`.
7. Tail-expression and `if let` temporary scope changes: recompile, check for borrow errors that now pass or new "does not live long enough"; lock guards in tail position are the usual suspect.
8. Rename identifiers named `gen`.
9. `Box<[T]>` iteration now by value: `.iter()` where references were intended.
10. `resolver = "3"` in workspace root; `rustfmt` style 2024 reformat in its own commit.
11. Run the full gate. `cargo clippy` with `msrv` set catches 2021-era idioms to replace.

## Replacement table

| Old | New | Since |
|---|---|---|
| `lazy_static!`, `once_cell::sync::Lazy` / `OnceCell` | `std::sync::LazyLock` / `OnceLock`, `std::cell::LazyCell` | 1.80 |
| `#[allow(lint)]` for deliberate suppression | `#[expect(lint, reason = "...")]` | 1.81 |
| `std::error::Error` in `no_std` shims | `core::error::Error` | 1.81 |
| `#[async_trait]` on new traits | native `async fn` in traits, `trait_variant` for `Send` | 1.75 |
| nested `if let Some(a) = x { if let Some(b) = y { ... } }` | let chains (edition 2024) | 1.88 |
| `match` arm + inner `if let` | `if let` guard | 1.95 |
| `std::ptr::addr_of!(x)` / `addr_of_mut!` | `&raw const x` / `&raw mut x` | 1.82 |
| `x.map_or(true, f)` | `x.is_none_or(f)` | 1.82 |
| `x.map_or(false, f)` | `x.is_some_and(f)` | 1.70 |
| `std::mem::size_of::<T>()` | `size_of::<T>()` (prelude) | 1.82 |
| manual `Vec` retain-and-collect loops | `Vec::extract_if`, `HashMap::extract_if` | 1.87 / 1.88 |
| `slice.chunks_exact(N)` + array conversion | `slice.as_chunks::<N>()` | 1.88 |
| `Result<Result<T, E>, E>` match | `Result::flatten` | 1.89 |
| `checked_*` + `unwrap` for overflow bugs | `strict_*` int ops (panic on overflow in release) | 1.91 |
| `Duration::from_secs(60 * n)` | `Duration::from_mins(n)` / `from_hours` | 1.91 |
| `assert!(matches!(x, P))` | `assert_matches!(x, P)` | 1.96 |
| `cfg_if!` crate | `cfg_select!` | 1.95 |
| `#[cold] fn unlikely()` hacks | `std::hint::cold_path()` | 1.95 |
| `CString::new("lit")` for constant C strings | `c"lit"` literals | 1.77 |
| `Box::<[T]>::from(vec)` iterate by ref | by value in edition 2024 | 1.85 |
| `-> impl Trait + '_` gymnastics | edition 2024 implicit capture, `use<>` to opt out | 1.82 / 1.85 |
| `impl Trait for dyn Sub { fn as_super(&self) -> &dyn Super }` | trait upcasting coercion | 1.86 |
| `RwLock` write then reacquire read | `RwLockWriteGuard::downgrade` | 1.92 |
| `atomic.fetch_update(SeqCst, SeqCst, f)` boilerplate | `atomic.update(...)` | 1.95 |
| `#![deny(warnings)]` | `[lints]` table + `build.warnings = "deny"` in CI config | 1.74 / 1.97 |
| `cargo publish` per crate in order | `cargo publish --workspace` | 1.90 |
| `#[bench]` | `criterion` / `divan` | (never stable) |
| `error-chain`, `failure` | `thiserror` 2 + `anyhow` | |
| `std::env::set_var` in tests | `temp-env` / `serial_test`; `set_var` is `unsafe` in 2024 | 1.85 |

## Still third-party, still right

- `thiserror`, `anyhow` for errors. `tokio`, `tokio-util` for async. `serde`, `serde_json`. `tracing`, `tracing-subscriber` for logs and spans.
- `parking_lot`, `crossbeam`, `rayon`, `dashmap`, `arc-swap` per `concurrency.md` criteria.
- `rstest`, `insta`, `proptest`, `mockall`, `wiremock`, `tempfile` for tests. `criterion`/`divan` for benches.
- `bitflags`, `bytes`, `itertools` (check std first: many `itertools` helpers landed in std), `smallvec`, `indexmap`.
- `clap` (derive) for CLIs. `reqwest` (rustls) for HTTP clients. `sqlx` or `diesel` per repo.
- `uniffi`, `cbindgen` for FFI.

## Detect version

```sh
grep -E '^(edition|rust-version)' Cargo.toml          # per crate
grep -A3 '^\[workspace.package\]' Cargo.toml         # inherited values
cat rust-toolchain.toml 2>/dev/null
rustc --version; cargo --version
cargo msrv find                                       # compute actual MSRV
```

- Installed toolchain newer than `rust-version` is normal; API still capped by `rust-version`.
- No `rust-version` and no toolchain file: propose adding `rust-version` set to the lowest version CI tests.
