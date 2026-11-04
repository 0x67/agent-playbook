# Rust FFI

Loaded via `rust` SKILL.md routing table. Base conventions: `rust` SKILL.md. FFI boundary rules override normal Rust API idioms at the ABI and binding layers only; core logic stays in `lib.rs`. Sources: Rustonomicon FFI, Edition Guide 2024 (unsafe extern, unsafe attributes), cbindgen, UniFFI 0.32 docs, uniffi-bindgen-react-native.

## Core principles

- FFI is an ABI contract. Simplicity and long-term compatibility over Rust ergonomics.
- Separate API layer, not a direct exposure of internal types. Minimal surface. Flat, C-compatible interfaces.
- ABI stability: no breaking changes once published. Add functions, never change signatures.
- All logic in `lib.rs`. FFI layers are thin translation boundaries.
- Each binding layer behind a Cargo feature:

```toml
[features]
ffi-c      = []
ffi-uniffi = ["dep:uniffi"]
```

## Project layout

```
src/
  lib.rs              core logic, no FFI concerns
  ffi/
    mod.rs            shared helpers (string conversion, error mapping)
    c/
      mod.rs          raw extern "C" exports (feature = "ffi-c")
      error.rs        C error codes
    uniffi/
      mod.rs          UniFFI exports (feature = "ffi-uniffi")
      error.rs        uniffi::Error types
build.rs              cbindgen + uniffi scaffolding
cbindgen.toml
```

Different path forced by a framework: document with `// ffi-exception: <reason>`.

## Edition 2024 rules (mandatory)

- Exports: `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "...")]`, `#[unsafe(link_section = "...")]`. Plain `#[no_mangle]` is a hard error in 2024.
- Imports: `unsafe extern "C" { ... }` blocks. Mark items `safe fn` only when every input is valid for every call (`sqrt`); default `unsafe fn` otherwise. `safe static` for read-only data.
- `unsafe_op_in_unsafe_fn` warns: inside `unsafe fn`, wrap each unsafe operation in its own `unsafe {}` with `// SAFETY:`.
- `#[export_name]` and `#[link_name]` validated strictly (1.97+). `invalid_runtime_symbol_definitions` (1.98+) denies defining symbols the runtime owns (`main`, allocator entry points). `c_void_returns` (1.98+) warns on returning `c_void` by value: return `()` or a pointer.
- `#[track_caller]` combines with `#[unsafe(no_mangle)]` (1.92+) for better panic locations in shims.
- Types from `core::ffi`: `c_char`, `c_int`, `c_void`, `CStr`, `CString`. Not `libc::*` unless the crate already depends on `libc`.

## Raw FFI: `extern "C"` + cbindgen

Use for C, C++, any language with a C bridge, or full ABI control.

```rust
/// # Safety
///
/// `ptr` must be non-null, aligned, and point to a `MyStruct` returned by
/// `mylib_mystruct_new` that has not been freed.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn mylib_mystruct_do_thing(ptr: *mut MyStruct) -> i32 {
    if ptr.is_null() {
        return FfiError::NullPointer as i32;
    }
    // SAFETY: caller upholds validity per doc; null checked above.
    let s = unsafe { &mut *ptr };
    match s.do_thing() {
        Ok(()) => FfiError::Ok as i32,
        Err(_) => FfiError::Internal as i32,
    }
}
```

### ABI-safe types

| Safe | Avoid |
|---|---|
| `u8`..`u64`, `i8`..`i64`, `usize`, `f32`, `f64`, `bool` | `String`, `Vec<T>`, `HashMap`, `&str` |
| `*const T`, `*mut T`, `Option<&T>`, `Option<NonNull<T>>` | `Result`, `Option<T>` for non-pointer `T` |
| `*const c_char` (NUL-terminated) | trait objects, generics, closures |
| `#[repr(C)]` structs, `#[repr(u32)]`/`#[repr(C)]` enums | Rust enums without repr, tuples |
| `Option<unsafe extern "C" fn(...)>` (null-pointer optimized callback) | `fn(...)` Rust ABI |

- Enums: `#[repr(u32)]` (or `i32`) for a stable size. `#[repr(C)]` enum size is compiler-defined `int`.
- Structs: `#[repr(C)]`; never rely on field reordering. `#[repr(C, packed)]` only with a proven ABI need and no references into it.
- Slices: pass `(*const T, usize)` pairs. Strings: `*const c_char` + `CStr::from_ptr` (unsafe, caller guarantees NUL and lifetime); or `(*const u8, usize)` for non-NUL data.
- `bool` is ABI-safe (1 byte, 0/1); C side must use `bool`/`_Bool`, not `int`.
- `NonNull` provenance APIs (1.89+): `NonNull::from_ref`, `without_provenance`, `expose_provenance` when doing pointer-integer tricks.

### Error handling

- Integer codes, never `Result`/`Option`. `#[repr(i32)] enum FfiError { Ok = 0, NullPointer = 1, InvalidInput = 2, Internal = 3 }`.
- Last-error pattern for detail: thread-local `RefCell<Option<CString>>`, `mylib_last_error_message() -> *const c_char` valid until next call. Document lifetime.
- Out-params for values: `fn f(input: *const T, out: *mut U) -> i32`. Write `out` only on `Ok`.

### Panics

- Panic across `extern "C"` aborts the process (1.81+). Every export catches: `std::panic::catch_unwind(AssertUnwindSafe(|| ...))` returning `FfiError::Internal`, or `extern "C-unwind"` when the caller is Rust/C++ that can unwind through. Pick one per library and document.
- `panic = "abort"` in the cdylib profile makes `catch_unwind` a no-op: then choose abort deliberately and document.

### Memory ownership

```rust
#[unsafe(no_mangle)]
pub extern "C" fn mylib_mystruct_new() -> *mut MyStruct {
    Box::into_raw(Box::new(MyStruct::default()))
}

/// # Safety
///
/// `ptr` must come from `mylib_mystruct_new` and not be freed twice.
/// After return the pointer is invalid.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn mylib_mystruct_free(ptr: *mut MyStruct) {
    if ptr.is_null() {
        return;
    }
    // SAFETY: caller guarantees ptr from Box::into_raw, not yet freed.
    drop(unsafe { Box::from_raw(ptr) });
}
```

- Rust allocates, Rust frees: matching `_free` for every `_new`. `CString::into_raw` pairs with `CString::from_raw` in a `_string_free`. Never `free()` Rust memory from C.
- Caller-owned buffers: Rust writes into `(*mut u8, usize)` and returns bytes written or needed.
- `# Safety` doc names the owner of every pointer, lifetime of returned pointers, thread-safety.
- Callbacks: `Option<unsafe extern "C" fn(user_data: *mut c_void, ...)>` plus `user_data: *mut c_void`. Rust never dereferences `user_data`.
- Thread safety: state exported as opaque pointer must be `Send`; document whether callers may use one handle from multiple threads (internal `Mutex`) or not.

### Null handling

- Check every pointer argument before deref. Return `FfiError::NullPointer`.
- `Option<&T>` / `Option<NonNull<T>>` in signatures when null is a valid "absent" input; still ABI-safe.

### cbindgen

```toml
# cbindgen.toml
language = "C"
include_guard = "MYLIB_H"
cpp_compat = true
usize_is_size_t = true
[export]
prefix = "mylib_"
[parse]
parse_deps = false
[parse.expand]
crates = ["mylib"]   # only when macros generate exports
```

```rust
// build.rs
fn main() {
    let crate_dir = std::env::var("CARGO_MANIFEST_DIR").expect("set by cargo");
    cbindgen::Builder::new()
        .with_crate(&crate_dir)
        .with_config(cbindgen::Config::from_root_or_default(&crate_dir))
        .generate()
        .expect("cbindgen")
        .write_to_file("include/mylib.h");
    println!("cargo:rerun-if-changed=src/ffi/c");
}
```

- CLI `cbindgen --config cbindgen.toml --crate mylib --output include/mylib.h` in CI when build.rs recompiles too often. Commit the header or verify `git diff --exit-code` after generation.
- cbindgen reads `#[unsafe(no_mangle)]` (0.27+). Upgrade cbindgen alongside edition bump.
- `crate-type = ["cdylib", "staticlib", "rlib"]` in `[lib]`. `cargo build --release` then link; `cargo xwin`, `cargo ndk` for cross targets.

## UniFFI (0.32)

Idiomatic bindings for Swift, Kotlin, Python, Ruby. Proc-macros preferred over UDL: co-located, refactor-safe. UDL only for shapes macros cannot express or when repo already uses it.

```rust
uniffi::setup_scaffolding!();          // once per crate

#[uniffi::export]
pub fn add(a: u32, b: u32) -> u32 { a + b }

#[uniffi::export]
pub async fn fetch(url: String) -> Result<String, FetchError> { ... }   // Swift async, Kotlin suspend, JS Promise

#[derive(uniffi::Record)]              // by value, no methods
pub struct Point { pub x: f64, pub y: f64 }

#[derive(uniffi::Enum)]
pub enum Direction { North, South }

#[derive(uniffi::Object)]              // by reference, Arc<T>
pub struct Engine { inner: Mutex<State> }

#[uniffi::export]
impl Engine {
    #[uniffi::constructor]
    pub fn new(cfg: Config) -> Arc<Self> { Arc::new(Self { ... }) }
    pub fn process(&self, input: String) -> Result<String, EngineError> { ... }
}

#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum EngineError {
    #[error("invalid input: {reason}")]
    InvalidInput { reason: String },
    #[error("internal")]
    Internal,
}

#[uniffi::export(callback_interface)]  // foreign implements, Rust calls
pub trait Logger { fn log(&self, message: String); }

#[uniffi::export(with_foreign)]        // either side implements
pub trait Processor: Send + Sync { fn process(&self, input: String) -> String; }
```

- Errors implement `uniffi::Error`; keep separate from C error codes. `#[uniffi(flat_error)]` only for string-only errors.
- `uniffi::custom_type!(Uuid, String)` for newtypes over supported primitives. `uniffi::use_remote_type!` for types from other crates.
- Supported: primitives, `String`, `Option`, `Vec`, `HashMap<String, V>` and other supported key types, `Result`, records, enums, objects via `Arc`, `Duration`, `SystemTime`. Unsupported: raw pointers, lifetimes, generics beyond `Arc<T>`, `Box<T>`, `Rc<T>`, trait objects outside declared traits.
- Objects must be `Send + Sync`. Interior mutability via `Mutex`; never hold the lock while calling a foreign callback (deadlock: foreign thread may call back in).
- Bindings: `cargo run --bin uniffi-bindgen generate --library target/release/libmylib.dylib --language swift --out-dir bindings/swift`. Library mode reads metadata from the built artifact; no UDL path needed.
- `uniffi.toml` for per-language options (package names, module names, custom type mappings).

## React Native and WASM: `uniffi-bindgen-react-native`

Generates TypeScript + C++ (JSI) for iOS/Android, WASM crate for web, N-API for Node/Bun (`@ubjs/node`). Runtime package `@ubjs/core` (new code); `uniffi-bindgen-react-native` npm package is legacy runtime. Production use exists; still evaluate stability per release, pin versions.

- Same proc-macros as above. `ubrn.config.yaml` sets manifest path, output dirs, targets. `ubrn build ios --and-generate`, `ubrn build android --and-generate`, `ubrn build web`. Never hand-edit generated TS/C++.
- Type mapping: `u64`/`i64` to `bigint`; `Vec<u8>` to `ArrayBuffer`; `Option<T>` to `T | undefined` (never `null`); `HashMap<String, V>` to `Map`; `SystemTime` to `Date`; `Duration` to `number` ms; `Result<T, E>` returns `T` or throws `E`.
- No `Option<Option<T>>`: explicit tri-state enum.
- Objects: TS class plus `${Name}Interface`; use the interface in signatures for mockability. JS GC is unreliable: expose explicit `close()`/`destroy()`; `uniffiDestroy()` and `uniffiUse(obj, fn)` exist.
- Errors: `#[derive(uniffi::Error)]` enums become throwable; check with generated `instanceOf` helpers, not JS `instanceof`. Types named `Error` are renamed `Exception`; avoid the name.
- Callbacks: `callback_interface` with `Box<dyn Trait>`, `with_foreign` with `Arc<dyn Trait>`. Never hold a `Mutex` while calling into JS (single-threaded JS + blocking Rust = deadlock). Prefer async callbacks.
- Async: exported `async fn` returns `Promise<T>`; generated Promises take optional `{ signal: AbortSignal }`; abort drops the Rust future. Domain cancel method for meaningful cleanup. Futures as arguments unsupported.
- WASM is single-threaded: `Send` bounds may need `#[cfg(target_arch = "wasm32")]` relaxations; avoid `async_trait` or use `?Send` variant there.
- Multiple crates in one library ("megazord"): unique exported type names across crates (TS flattens namespaces).
- Reserved names: TS keywords, `uniffiDestroy`, `uniffiUse`, `instanceOf`, `hashCode`, `equals`, `toString`, `toDebugString`.

## Both layers together

- Shared core in `lib.rs`; `src/ffi/c` and `src/ffi/uniffi` each wrap it. No duplicated logic.
- Separate error types per layer, both converted from core error via `From` or `map_err`.
- Symbol namespace is global: every `#[unsafe(no_mangle)]` export prefixed with the library name (`mylib_engine_new`). UniFFI generates its own prefixed symbols; never collide.
- CI matrix: `cargo test --features ffi-c`, `--features ffi-uniffi`, `--all-features`, plus platform builds (`cargo ndk`, `xcodebuild`, `ubrn build`). Bindings validated by building the consumer, not Rust tests alone.

| Consumer | Approach |
|---|---|
| C / C++ | `extern "C"` + cbindgen |
| Swift, Kotlin, Python, Ruby | UniFFI |
| React Native, WASM, Node/Bun | uniffi-bindgen-react-native |
| Several languages | both, layered over one core |
| Embedded / `no_std` | `extern "C"` only |

## Testing FFI

- Rust unit tests call the `extern "C"` functions directly through the null and error paths.
- `cargo +nightly miri test` on the unsafe core when feasible. `-Zsanitizer=address` builds in CI for the C layer.
- A C test program compiled against the generated header in CI (`cc` crate in a `tests/` build or `cmake`). Catches header drift.
- UniFFI: `uniffi::build_foreign_language_testcases!` or foreign-language test suites run in CI.

## Checklist

- [ ] Only ABI-safe types cross the boundary; enums have explicit int repr.
- [ ] Every allocation has a documented owner and matching free function.
- [ ] Every pointer argument null-checked; `# Safety` on every `unsafe fn`; `// SAFETY:` on every block.
- [ ] Panic policy chosen (`catch_unwind` or `C-unwind` or abort) and documented.
- [ ] All exports prefixed with library name; `#[unsafe(no_mangle)]` used.
- [ ] Imports in `unsafe extern` blocks with correct `safe`/`unsafe` qualifiers.
- [ ] `ffi-c` and `ffi-uniffi` compile independently and together.
- [ ] FFI code under `src/ffi/` or documented `// ffi-exception:`.
- [ ] Header or bindings regenerated and diff-checked in CI; consumer build in CI.
