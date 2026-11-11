# Rust API Design

Loaded via `rust` SKILL.md routing table. Sources: Rust API Guidelines checklist, Cargo reference (features, lints, workspace), Edition Guide 2024, cargo-semver-checks, rustdoc book.

## Common traits (C-COMMON-TRAITS, C-DEBUG, C-SEND-SYNC)

- Eagerly derive where meaningful: `Debug`, `Clone`, `PartialEq`, `Eq`, `Hash`, `PartialOrd`, `Ord`, `Default`, `Copy` (small plain data only).
- Every public type implements `Debug`. Never empty output (C-DEBUG-NONEMPTY). Redact secrets with manual `Debug`.
- `Display` for user-facing values and errors. Not for structs with no natural text form.
- `Send` and `Sync` auto-derived; never `unsafe impl` without a proof comment. Add `static_assertions::assert_impl_all!(T: Send, Sync)` test for public types meant to cross threads.
- Conversion traits: `From` (infallible, obvious meaning), `TryFrom` (validating), `AsRef`/`AsMut` (cheap view), `FromStr` for parsing text, `Into<String>` in builder setters only.
- Collections implement `FromIterator`, `Extend`, `IntoIterator` for `&T`, `&mut T`, `T` (C-COLLECT, C-ITER).
- `serde::{Serialize, Deserialize}` behind a `serde` feature for data types (C-SERDE). Field renames via attributes, never by matching wire shape in the type name.
- Binary numeric types: `LowerHex`, `UpperHex`, `Octal`, `Binary` (C-NUM-FMT).

## Type safety and predictability

- Newtypes for static distinctions (C-NEWTYPE): `UserId(u64)`, `Meters(f64)`. Encapsulate implementation types (C-NEWTYPE-HIDE).
- Arguments convey meaning via types, not `bool` or `Option` (C-CUSTOM-TYPE). Two-variant enum.
- Flag sets: `bitflags` crate, not an enum (C-BITFLAG).
- Functions with a clear receiver are methods (C-METHOD). Constructors are static inherent methods `new`, `with_*`, `from_*` (C-CTOR).
- No out-parameters; return tuples or structs (C-NO-OUT).
- Only smart pointers implement `Deref`/`DerefMut` (C-DEREF). Smart pointers add no inherent methods (C-SMART-PTR).
- Operator overloads unsurprising and consistent with `PartialOrd`/`Eq` (C-OVERLOAD).
- Builders for construction with several optional parts (C-BUILDER). Owned `self` chaining for one-shot builders; `&mut self` when reused. `build()` returns `Result` when validation can fail. `#[must_use]` on the builder type.
- Validate arguments at the boundary; return typed error (C-VALIDATE). Never re-validate already-typed input.
- Destructors never fail and never block without an explicit alternative (C-DTOR-FAIL, C-DTOR-BLOCK): provide `close()`/`shutdown()` returning `Result`.

## Flexibility

- Expose intermediate results where cheap (C-INTERMEDIATE): return the parsed struct, not just a bool.
- Caller controls allocation (C-CALLER-CONTROL): take `&[T]`, `&str`, `impl Read`; return owned only when allocated anyway. Provide `_into(&mut buf)` variants on hot paths.
- Generics to minimize assumptions (C-GENERIC): `impl AsRef<Path>`, `impl Into<String>`, `impl IntoIterator<Item = T>` at public entry points. Concrete types internally.
- `impl Trait` argument position for single use; named generic when used twice or in return. `&dyn Trait` when many types share a call site and monomorphization cost matters.
- Traits object-safe when dyn use is plausible (C-OBJECT). `where Self: Sized` on generic methods to keep the rest dyn-compatible.
- Trait upcasting (1.86+): `&dyn Sub` coerces to `&dyn Super`. No manual `as_super()` methods.

## Return-position `impl Trait`

- `-> impl Iterator<Item = T>` when the concrete type is unnameable or an implementation detail. Name the type when callers store it in structs.
- Edition 2024 captures all lifetimes. `+ use<>` or `+ use<'a, T>` (1.82+, in traits 1.87+) to control captures. Add `use<>` on functions taking `&self` but returning owned iterators.
- RPITIT (1.75+) for trait methods returning iterators or futures. Document `Send` expectations explicitly.

## Future proofing

- `#[non_exhaustive]` on public enums, error types, and config structs that may grow. Provide constructors when it blocks struct literals.
- Sealed traits when downstream impls must be prevented (C-SEALED):

```rust
mod private { pub trait Sealed {} }
pub trait Backend: private::Sealed { ... }
impl private::Sealed for Postgres {}
```

- Private fields by default (C-STRUCT-PRIVATE). `pub` fields only on plain data types with no invariants.
- No duplicated derive bounds on data structures (C-STRUCT-BOUNDS): `struct Wrapper<T>(T)` without `T: Clone` bound; bounds go on impls.
- `#[deprecated(since = "x.y.z", note = "use `foo`")]` one release before removal. Keep the old path as thin forwarder only when the user asks for compatibility.
- `#[doc(hidden)]` for items public only for macros; not a stability promise.
- `#[diagnostic::on_unimplemented(message = "...", label = "...", note = "...")]` (1.78+) on traits users implement. `#[diagnostic::do_not_recommend]` (1.85+) on blanket impls that produce confusing suggestions.
- Run `cargo semver-checks check-release` before every release. Breaking change means major bump (or minor pre-1.0).

## Errors (C-GOOD-ERR)

- Error types implement `Debug`, `Display`, `std::error::Error`, `Send`, `Sync`, `'static`. Never `()` or `String`.
- Typed, `#[non_exhaustive]`, documented per variant. Full rules in `errors.md`.

## Documentation (C-CRATE-DOC, C-EXAMPLE, C-FAILURE, C-LINK, C-METADATA)

- Crate docs: purpose, quick example, feature table, MSRV.
- Every public item: rustdoc with example using `?` (C-QUESTION-MARK). `# Errors`, `# Panics`, `# Safety` sections.
- Intra-doc links to related items. `#![warn(missing_docs)]` on libraries via `[lints]`.
- `Cargo.toml` metadata: `description`, `license`, `repository`, `documentation`, `keywords`, `categories`, `rust-version`, `readme`. `include`/`exclude` to keep the package small.
- `CHANGELOG.md` per release (C-RELNOTES). Keep a Changelog format.
- `#[doc = include_str!("../README.md")]` when README doubles as crate docs; keep doctests passing.

## Cargo features and dependencies

- Features additive, never mutually exclusive. `default` minimal. No `no-*` features.
- Optional dependencies via `dep:name` and explicit feature names. `serde = ["dep:serde", "chrono/serde"]`.
- `[workspace.dependencies]` single source of versions. Members use `workspace = true`.
- `rust-version` set and verified (`cargo msrv verify`). MSRV bump is a minor version change; note it in changelog.
- Every dependency justified: `cargo machete` clean, `cargo deny check` for licenses and advisories. Prefer std (`LazyLock`, `OnceLock`, let chains) over crates it replaced.
- `Cargo.lock` committed for binaries and, since 1.83 guidance, libraries too. `cargo update` deliberate.
- Publish metadata: `cargo package --list` reviewed; `cargo publish --dry-run` in CI on tags.

## Visibility and paths

- `pub(crate)` default. `pub` is a promise.
- Re-export leaf types at crate root or a `prelude` module. Internal module tree is not public API: `pub mod` only for namespaced APIs users are expected to path into.
- `#[doc(inline)]` on re-exports so docs render at the public path.
- `no_std` libraries: `#![no_std]` with `extern crate alloc` behind an `alloc` feature; `std` feature enables `std::error::Error` when MSRV < 1.81, else `core::error::Error`.

## Inlining

- No `#[inline]` by default. Compiler decides within a crate; cross-crate generic code is inlined anyway.
- `#[inline]` only with a reason: small hot function, trait-forwarding wrapper, cross-crate non-generic per-message call. Hot path rule: concrete non-generic per-message fn callable across a crate boundary gets `#[inline]` at write time.
- `#[inline(always)]` rarely: measured hot path, tiny wrapper around an invariant-checked primitive, abstraction boundary where a missed inline defeats the design. Cite the measured delta.
- Never on cold paths, error paths, large functions, allocation-heavy code, async fns. Remove cargo-cult `#[inline]`.
- `#[cold]` and `std::hint::cold_path()` (1.95+) on error branches in hot loops.

## Unsafe in public API

- `unsafe fn` only when the caller must uphold an invariant the type system cannot express. `# Safety` section lists every obligation.
- Safe wrappers over unsafe internals. Public API surface should be mostly safe.
- `#[unsafe(no_mangle)]`, FFI: `ffi.md`.

## Avoid

- `Box<dyn Error>` in signatures. `String` errors. `Result<T, ()>`.
- `bool` params, `Option<bool>`, positional tuples with 3+ fields in public API.
- Public struct with all-`pub` fields plus invariants.
- Traits with one impl created "for flexibility". Add the trait when the second impl exists.
- Generic params that only ever take one type.
- `impl Trait` return hiding a type users must name.
- Breaking changes in patch releases. `cargo semver-checks` gates.
- Feature flags that change behavior instead of adding capability.
- `#[inline]` sprinkled without measurement.
- Mutually recursive `From` impls, `From` that loses information (use `TryFrom`).
