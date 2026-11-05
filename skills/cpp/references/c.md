# Plain C

Loaded via `cpp` SKILL.md routing table for `.c` files, C-only headers, and C ABI boundaries. Sources: cppreference C pages (C11, C17, C23), SEI CERT C Coding Standard, OpenSSF Compiler Options Hardening Guide for C and C++.

## Standard ladder

The ceiling is `CMAKE_C_STANDARD`, `c_std_NN`, or `-std=cNN`. Same rule as C++: nothing above it, and the oldest supported compiler must implement it.

| Standard | Unlocks |
|---|---|
| C99 (assumed baseline) | `//` comments, declarations anywhere, `<stdint.h>`, `<stdbool.h>`, `inline`, `restrict`, designated initializers, compound literals, `snprintf`, flexible array members |
| C11 | `_Static_assert`, `_Generic`, `_Alignas`/`_Alignof`, `_Atomic` and `<stdatomic.h>`, `<threads.h>` (optional, check `__STDC_NO_THREADS__`), anonymous structs and unions, `_Noreturn`, `aligned_alloc`, `quick_exit` |
| C17 | defect fixes only |
| C23 | `nullptr`; `bool`, `true`, `false`, `static_assert`, `alignas`, `thread_local` as keywords; `constexpr` objects; `typeof`/`typeof_unqual`; `auto` type inference; attributes `[[nodiscard]]`, `[[maybe_unused]]`, `[[deprecated]]`, `[[fallthrough]]`, `[[noreturn]]`; `#embed`; `#elifdef`/`#elifndef`; `#warning`; binary literals and `'` digit separators; `= {}` empty initializer; `<stdckdint.h>` (`ckd_add`, `ckd_sub`, `ckd_mul`); `<stdbit.h>`; `_BitInt(N)`; `memset_explicit`; `unreachable()`; `strdup`/`strndup`; `f()` now means `f(void)`, and K&R definitions are gone |

## Rules

- Every resource has one owner and one release function. The header says who allocates, who frees, and with what.
- Error paths: `goto cleanup;` to one cleanup block per function is idiomatic and fine.
- Check every return value: `malloc`, `fopen`, `read`, `write`, `snprintf` (truncation when the result is at least the buffer size). Mark functions `[[nodiscard]]` (C23) or `__attribute__((warn_unused_result))`.
- Sizes are `size_t`. Check multiplication before allocating: `ckd_mul` (C23) or `__builtin_mul_overflow`.
- Strings are always bounded. `snprintf` with a checked result, or `memcpy` with an explicit length and terminator. No `gets`, `strcpy`, `strcat`, `sprintf`. `strncpy` does not terminate on truncation.
- Implicit conversions and integer promotions bite: `-Wconversion -Wsign-conversion`.
- Opaque types in public headers (`typedef struct parser parser;` plus create and destroy functions) hide layout and keep the ABI stable.
- `static` on every function and file-scope variable not declared in a header.
- `const` on pointer parameters the function does not write through. `restrict` only when no aliasing is provable.
- Errors: `int` status (0 on success, negative errno-style code on failure) or an `enum`, with results through out parameters. Set `errno` only when mimicking POSIX.
- No variable-length arrays (`-Wvla`), no `alloca`.
- Macros: parenthesize every parameter and the whole expansion; `do { ... } while (0)` for statement macros. Prefer `static inline` functions and `enum` constants.

## Headers C++ can include

```c
#ifndef APP_PARSER_H
#define APP_PARSER_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct parser parser;
parser* parser_create(void);
void parser_destroy(parser* p);

#ifdef __cplusplus
}
#endif

#endif
```

## C and C++ together

- C++ wraps C handles in RAII at the boundary (`std::unique_ptr<T, Deleter>`, `memory.md`).
- C++ functions exported to C: `extern "C"`, plain-data parameters, no overloads, no exceptions crossing (catch everything and return a code).
- Rust interop: the `rust` skill's `references/ffi.md`.

## Build flags

- C-only errors from the OpenSSF guide: `-Werror=implicit -Werror=incompatible-pointer-types -Werror=int-conversion`. Multithreaded C on glibc: `-fexceptions`.
- Also useful: `-Wstrict-prototypes -Wmissing-prototypes -Wvla`.
- Warnings, hardening, and sanitizers otherwise as in `tooling.md`, with `CMAKE_C_*` and `C_COMPILER_ID` in place of the C++ spellings.
