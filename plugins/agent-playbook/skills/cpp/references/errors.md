# C++ Error Handling

Loaded via `cpp` SKILL.md routing table. Sources: C++ Core Guidelines (E section), cppreference (exceptions, `noexcept`, `std::expected`, `std::from_chars`, contracts).

## Find the repo's model first

Look for `-fno-exceptions` in flags, an `Expected`/`Result`/`Status` type, `absl::Status`, `std::error_code` use. One model per layer; convert at boundaries.

| Failure | Mechanism |
|---|---|
| expected, the caller decides (parse, lookup, I/O, validation) | `std::expected<T, E>` (C++23) or the repo's result type; exceptions where the codebase uses them for this |
| no value, and that is not an error | `std::optional<T>` |
| constructor cannot establish the invariant | throw, or a private constructor plus a static factory returning `expected` |
| caller broke a precondition (a bug) | assertion or contract; hardened checks in release |
| unrecoverable (corrupted state) | log, then terminate |
| C API, ABI boundary, `-fno-exceptions` code | error code or `std::error_code`, or `expected` |

- Code built with `-fno-exceptions` avoids throwing APIs whose failure matters (`std::stoi`, `.at()`). Parse with `std::from_chars` (C++17).
- Exceptions never cross a C ABI, a C callback, a thread boundary, or a destructor. Catch and convert there.

## Exceptions, when the repo uses them

- Throw by value, catch by `const&`. Derive from `std::exception`, usually `std::runtime_error` or a project base. The message says what failed and with which input.
- Catch where you can act: retry, translate, report. No catch-and-ignore. `catch (...)` only at the top of `main`, a thread, or a C boundary, where it logs and converts.
- Rethrow with `throw;`, never `throw e;` (slices to the caught type). Add context with `std::throw_with_nested` or the project's wrapper.
- Strong guarantee for operations that can fail midway: build the new state aside, then commit with a `noexcept` swap.
- `noexcept` on destructors (implicit), moves, swaps, and leaf functions that cannot throw. A `noexcept` function that throws calls `std::terminate`.

## `std::expected` (C++23)

```cpp
enum class PortError { empty, bad_digit, out_of_range };

[[nodiscard]] std::expected<std::uint16_t, PortError> parse_port(std::string_view s) {
    if (s.empty()) {
        return std::unexpected(PortError::empty);
    }
    const char* first = std::to_address(s.begin());
    const char* last = std::to_address(s.end());
    unsigned value = 0;
    auto [ptr, ec] = std::from_chars(first, last, value);
    if (ec == std::errc::invalid_argument || ptr != last) {
        return std::unexpected(PortError::bad_digit);
    }
    if (ec == std::errc::result_out_of_range || value > 65535) {
        return std::unexpected(PortError::out_of_range);
    }
    return static_cast<std::uint16_t>(value);
}
```

- `[[nodiscard]]` on every function returning `expected`.
- Chain with `and_then`, `transform`, `or_else`, `transform_error` instead of nested `if`.
- `.value()` throws `std::bad_expected_access`; `*e` on an error is UB. Check `has_value()` first or use `value_or`.
- Error type: `enum class` for a closed set, a struct with code plus context for diagnostics, `std::error_code` at OS boundaries.
- Before C++23: the repo's type, or `tl::expected` if it is already a dependency. Do not hand-roll one.

## Preconditions and assertions

- `assert` for internal invariants in debug builds. It vanishes under `NDEBUG`, so never put side effects in it.
- Checks that must hold in release at trust boundaries: explicit check, then error return or throw.
- `static_assert` for anything checkable at compile time: sizes, layout, trait requirements.
- Contracts (C++26: `pre`, `post`, `contract_assert`) only after confirming every compiler the repo uses supports them.
- The hardened standard library turns container precondition bugs into traps in release (`tooling.md`).

## `main`, threads, and exit

- `main` catches at the top, logs, returns non-zero. `std::exit` skips destructors of local objects; return from `main` instead.
- An exception escaping a thread function terminates the process. Catch inside and hand the error to the joiner (`std::promise`, `std::exception_ptr`, shared state).
- `std::abort`/`std::terminate` only for unrecoverable states, after logging.

## Logging

Handle once: return or throw with context, or log and stop. Never log and rethrow at every layer. The boundary that decides does the logging.
