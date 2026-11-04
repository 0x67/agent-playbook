# Rust Style

Loaded via `rust` SKILL.md routing table. Sources: Rust API Guidelines, Rust Style Guide (2024), Edition Guide 2024, clippy docs, rustdoc book.

## Naming (API guidelines C-CASE, C-CONV, C-GETTER, C-ITER)

- Types, traits, enum variants: `UpperCamelCase`. Functions, methods, locals, modules: `snake_case`. Constants, statics: `SCREAMING_SNAKE_CASE`. Lifetimes: short lowercase `'a`, `'de`.
- Acronyms as words: `HttpClient`, `parse_url`, `UserId`. Not `HTTPClient`, `parseURL`.
- Conversions: `as_` (free, borrowed view), `to_` (expensive or owned copy), `into_` (consumes self). `from_` on the target type.
- Getters: field name, no `get_` prefix: `fn len(&self)`, `fn name(&self) -> &str`. Mutable: `fn name_mut`. Setters: `set_name`.
- Iterators: `iter()`, `iter_mut()`, `into_iter()`. Iterator type named after producer: `Iter`, `IterMut`, `IntoIter`, `Keys`.
- Constructors: `new`, `with_capacity`, `from_parts`. Fallible: `try_new` or `Type::parse`. Builders: `builder()`.
- Predicates: `is_`, `has_`, `can_`. Never `check_` returning bool.
- Modules: singular noun for type-holding modules (`error`, `config`), plural only for collections of similar items (`handlers`).
- Newtypes: `UserId`, `Bytes`, `Millis`. Unit suffix in name when unit matters.
- Feature names: `serde`, `tokio`, `ffi-c`. No `use-`, `with-` placeholders. Optional dependency features use `dep:` syntax.

## Module layout

```
src/
  lib.rs            pub mod tree, re-exports, crate docs. No logic.
  main.rs           parse args, build deps, call lib run(). No logic.
  config.rs         one concern per file
  store/
    mod.rs          pub use children, shared private items
    postgres.rs
    memory.rs
    tests.rs        #[cfg(test)] mod tests; when tests exceed 40% of file
```

- One concern per file. Second concern or >600 non-test LOC projected: mod dir from the start, never "split later".
- Child module sees parent private items; siblings need `pub(super)`. Move code by exact line range, keep paths via `pub use`.
- Inherent impls may split across files. One trait impl per file when the file is about that trait.
- `pub(crate)` default for internal items. `pub` only for the crate's contract. Re-export at `lib.rs` so external paths stay stable across internal moves.
- Binary + library split in the same package (`src/lib.rs` + `src/main.rs`) so logic is testable.
- Workspace: one crate per deployable or per reusable boundary. `[workspace.dependencies]`, `[workspace.lints]`, `[workspace.package]` for shared metadata.
- `build.rs` only for codegen or FFI linking. Keep it tiny; heavy work goes in a separate crate.

## Edition 2024 idioms

Edition 2024 for every new crate (`edition = "2024"`, Rust 1.85+). Migrate 2021 crates with `cargo fix --edition` then review.

- Let chains (1.88+, 2024 only): `if let Some(x) = a && x > 0 && let Ok(y) = f(x) { }`. Replaces nested `if let`.
- `if let` guards on match arms (1.95+): `Some(v) if let Ok(n) = v.parse::<u32>() => ...`.
- RPIT captures all in-scope lifetimes by default. Opt out with `-> impl Iterator<Item = u32> + use<>` when the return must outlive the borrow.
- `unsafe extern "C" { pub safe fn sqrt(x: f64) -> f64; pub unsafe fn strlen(p: *const c_char) -> usize; }`. Unqualified items default to `unsafe`.
- `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "...")]`, `#[unsafe(link_section = "...")]`.
- `unsafe_op_in_unsafe_fn` warns by default: every unsafe op inside `unsafe fn` needs its own `unsafe {}` block with `// SAFETY:`.
- `static mut` references are denied. Use `AtomicX`, `Mutex`, `OnceLock`, or `&raw mut` for true FFI needs.
- Tail expression temporaries drop before locals now. `if let` scrutinee temporaries drop before `else`. Fixes borrow errors, may change lock lifetimes: check `Mutex` guards in tail position.
- `gen` is reserved. Rename identifiers named `gen`.
- `Box<[T]>` iterates by value. `for x in boxed_slice` yields `T`.
- `cargo fix --edition` handles mechanical changes. Never edit `edition` without running it.

## Control flow

- Early return with `?`. Happy path at minimum indent.
- `let Some(x) = opt else { return Err(..) };` for refutable bindings. Not `match` with one arm.
- `matches!(x, Pat)` for boolean pattern checks. `assert_matches!` (1.96+) in tests.
- Combinators when they read linearly: `map`, `and_then`, `ok_or_else`, `unwrap_or_default`, `is_none_or` (1.82+), `is_some_and`. `match` when branches carry logic.
- No `else` after `return`, `continue`, `break`.
- Nesting depth 3 max. Extract function past that.
- `loop` with `break value` over flag variables. Labeled breaks only for nested loops.
- Exhaustive `match` on own enums. No `_ =>` arm that hides future variants; `#[non_exhaustive]` external enums require it, comment why.
- `if cond { a } else { b }` as expression. Avoid `let mut x; if ... { x = }`.

## Iterators and collections

- Iterator chains over index loops. `enumerate`, `zip`, `windows`, `chunks`, `array_windows` (1.94+), `as_chunks` (1.88+).
- No `collect()` mid-chain. Collect once at the end, into the type the caller needs. `collect::<Result<Vec<_>, _>>()` to short-circuit errors.
- Return `impl Iterator<Item = T> + '_` when caller may stop early or transform. Return `Vec<T>` when data is already materialized.
- `Vec::with_capacity` when size known. `extend` over push loops. `retain`, `extract_if` (1.87+), `pop_if` (1.86+), `get_disjoint_mut` (1.86+).
- `HashMap` default. `BTreeMap` for ordered iteration or range queries. `FxHashMap`/`ahash` only when profile shows hashing hot.
- `entry()` API over get-then-insert.
- Slices in signatures: `&[T]` not `&Vec<T>`, `&str` not `&String`, `&Path` not `&PathBuf`, `impl AsRef<Path>` only for ergonomics at public API.
- `Box<[T]>` and `Box<str>` for immutable owned data stored long-term. `Arc<str>` for shared immutable strings. `Cow<'_, str>` when sometimes borrowed.
- `Option<&T>` via `as_ref()`, `as_deref()`. `Option<&mut T>` via `as_mut()`, `as_deref_mut()`.

## Types

- Newtype for every id, key, unit: `struct UserId(u64);` with `Debug`, `Clone`, `Copy`, `Eq`, `Hash`, `Display` as needed. No newtype with no invariant and no distinction purpose.
- Enums for state machines and modes. Data-carrying variants over parallel `Option` fields.
- `NonZeroU32` etc. when zero is invalid: niche optimization and documented invariant.
- `Duration` for time spans, `Instant` for monotonic, `SystemTime` for wall clock. Never `u64` millis in signatures.
- `u8`/`u16`/`u32`/`u64` by domain range; `usize` only for indexes and lengths. `i64` for wire ints when sign unknown.
- `bool` params banned. Two-variant enum or builder method.
- Struct fields private; constructor validates. Derive `Default` only when zero-state is valid.
- `Copy` for small plain data. Never `Copy` on types holding heap data or with drop semantics.
- `impl Trait` in argument position for simple generic params; named generics when used twice or referenced in return.

## Strings

- `&str` params. `String` return when allocated. `impl Into<String>` in builders only.
- `format!` for building; `write!` into `String` in loops; `String::with_capacity` when size known.
- `str::split_once`, `strip_prefix`, `strip_circumfix` (1.98+), `trim_*` over manual indexing. Byte indexing only on ASCII-guaranteed input.
- `char` methods (`is_ascii_digit`) over ranges. `to_ascii_lowercase` when ASCII known.
- `Path`/`PathBuf` for paths, never `String`. `OsStr` at OS boundary.

## Comments and docs

- Rustdoc on every `pub` item. First line one sentence, imperative or noun phrase. Blank line, then detail.
- Sections when applicable: `# Errors` (each variant returned and when), `# Panics` (conditions), `# Safety` (caller obligations on `unsafe fn`), `# Examples` (compiled; use `?`, never `unwrap`).
- Intra-doc links: [`Type::method`]. `#[doc(hidden)]` for public-for-macro items.
- Crate docs in `lib.rs` `//!`: purpose, one example, feature flags table.
- `// SAFETY:` above every `unsafe {}` block. States the invariant and why it holds here.
- Inline comments explain why, invariants, non-obvious ordering, links to specs. Never restate code. Plain humanizer prose. No em dash. No plan/task ids.
- No commented-out code. Git holds history.

## Formatting and lints

- `cargo fmt --all` on every change. `rustfmt.toml` only for `style_edition = "2024"` when edition line is older, `max_width` if repo demands. Never disable rustfmt per file.
- Import order: `std`/`core`/`alloc`, external crates, `crate`/`super`/`self`. One `use` block per group, blank line between. rustfmt 2024 sorts within groups.
- `use` specific items. Glob imports only for preludes and in tests (`use super::*`). `enum_glob_use` denied.
- Lints in `Cargo.toml` `[lints]` (or `[workspace.lints]` + `lints.workspace = true`), never in `lib.rs` attributes. See `tooling.md`.
- `#[expect(clippy::too_many_arguments, reason = "FFI shim mirrors C signature")]` for deliberate suppression. Compiler errors when the lint stops firing, so dead suppressions die.
- `#[allow]` only in generated code.
- `#[must_use]` on functions returning values that are meaningless to drop, on builders, on `Result`-like custom types.
- `#[deprecated(since = "1.2.0", note = "use `x` instead")]` for public API removal path.

## Avoid

- `.clone()` on `Arc`, `String`, `Vec` inside loops or hot paths without measured need.
- `Rc<RefCell<T>>` in library APIs. Shows unclear ownership.
- `Box<dyn Error>` in library public API. Typed error.
- `impl Trait` return hiding a type the caller needs to name.
- `String` for paths, ids, enums, durations.
- `as` casts for narrowing. `try_from` or explicit `u8::try_from(x)?`. `as` only for widening and `usize` index math with comment.
- `unwrap()` in examples, doc tests, library code. `expect("reason")` only for proven invariants.
- `#[derive(Default)]` on types where zero-state is invalid.
- `pub` fields on types with invariants.
- `mod.rs` with logic inside. `mod.rs` declares and re-exports.
- Macros where a function or generic fits. `macro_rules!` only for repetition the type system cannot express.
- `lazy_static!`, `once_cell::sync::Lazy` in new code. `std::sync::LazyLock` (1.80+).
- `#![deny(warnings)]` in source. Breaks builds on new compiler lints. Use `-D warnings` in CI or `build.warnings = "deny"` (1.97+).
