# Modern C++ by Standard

Loaded via `cpp` SKILL.md routing table. Sources: cppreference per-standard pages (cppreference.com/w/cpp/17, /20, /23, /26) and compiler support tables (cppreference.com/w/cpp/compiler_support).

## Rule

- The project's standard is the ceiling: `CMAKE_CXX_STANDARD`, `cxx_std_NN`, `-std=c++NN`, `/std:c++NN`. No feature above it.
- The standard is only half of it. The oldest compiler and standard library the repo supports must implement the feature: check `Minimum toolchains` below. When either rules a feature out, use `Below the feature's standard`. Code that supports several toolchains guards with feature-test macros:

  ```cpp
  #include <version>
  #if defined(__cpp_lib_expected)
  // std::expected path
  #endif
  ```

  One required baseline beats a forest of `#if`; macros are for libraries that span standards.
- Raising the standard is a repo decision (toolchains, ABI, downstream users). Ask before raising it in someone else's project.
- New code uses the newest idiom the standard allows. Existing code: modernize in a separate commit (`clang-tidy -checks='-*,modernize-*' --fix`), then review the diff.

## Ladder

| Standard | Unlocks |
|---|---|
| C++11 (assumed baseline) | `auto`, range-for, lambdas, move semantics, `nullptr`, `enum class`, `override`/`final`, `constexpr`, `static_assert`, `= default`/`= delete`, `using` aliases, variadic templates, `noexcept`, `std::unique_ptr`/`shared_ptr`, `std::thread`/`mutex`/`atomic`/`condition_variable`, `<chrono>`, `std::array`, unordered containers |
| C++14 | `std::make_unique`, generic lambdas, lambda init capture `[x = std::move(x)]`, return type deduction, `decltype(auto)`, relaxed `constexpr`, binary literals, digit separators `1'000'000`, `[[deprecated]]`, `std::exchange`, chrono literals `250ms`, `std::shared_timed_mutex` |
| C++17 | `std::optional`, `std::variant` + `std::visit`, `std::string_view`, `std::any`, `std::filesystem`, structured bindings, `if constexpr`, `if`/`switch` with initializer, fold expressions, class template argument deduction, `[[nodiscard]]`, `[[maybe_unused]]`, `[[fallthrough]]`, inline variables, nested namespaces `a::b`, guaranteed copy elision, `std::scoped_lock`, `std::shared_mutex`, `std::from_chars`/`to_chars`, `std::byte`, `std::clamp`, `std::gcd`/`lcm`, `std::size`, parallel algorithms, `std::pmr` |
| C++20 | concepts and `requires`, abbreviated templates `void f(auto x)`, ranges and views, `std::span`, `<=>` and defaulted `==`, `std::format`, `consteval`, `constinit`, designated initializers, coroutines (language), modules (language), `using enum`, `[[likely]]`/`[[unlikely]]`, `[[no_unique_address]]`, `char8_t`, `std::jthread`, `std::stop_token`, `std::latch`, `std::barrier`, `std::counting_semaphore`, `std::atomic_ref`, `atomic::wait`/`notify_one`, `std::source_location`, `std::bit_cast`, `<bit>` (`popcount`, `countl_zero`, `has_single_bit`, `bit_width`, `rotl`), `std::endian`, `<numbers>`, `std::ssize`, `std::erase`/`erase_if`, `contains` on associative containers, `starts_with`/`ends_with`, `std::cmp_less` and `std::in_range`, `std::midpoint`, `std::to_array`, `make_shared` for arrays, chrono calendar and time zones |
| C++23 | `std::expected`, `std::print`/`println`, deducing this, `if consteval`, `std::unreachable`, `std::to_underlying`, `std::move_only_function`, `std::mdspan`, `std::flat_map`/`flat_set`, `std::generator`, `std::stacktrace`, `std::byteswap`, `import std;`, multidimensional `operator[]`, `static operator()`, `auto(x)` decay copy, `[[assume]]`, `std::ranges::to`, views `zip`, `enumerate`, `chunk`, `slide`, `stride`, `cartesian_product`, `join_with`, `adjacent`, `repeat`, `std::ranges::fold_left`, `ranges::contains`, `string::contains`, monadic `optional` (`and_then`, `transform`, `or_else`), `std::out_ptr`, `resize_and_overwrite`, `uz`/`z` literal suffixes, `#elifdef`, `#warning`, range-for temporaries live to the end of the loop |
| C++26 | static reflection (`^^` operator, `<meta>`), contracts (`pre`, `post`, `contract_assert`, `<contracts>`), `std::execution` (senders and receivers), standard library hardening, erroneous behavior for uninitialized reads, `#embed`, pack indexing `Ts...[0]`, placeholder variables `_`, `= delete("reason")`, structured binding as a condition, `constexpr` placement new, `std::inplace_vector`, `std::hive`, `std::simd`, `std::linalg`, `std::optional<T&>`, `std::function_ref`, `std::copyable_function`, saturation arithmetic (`std::saturating_add`, `saturating_sub`, `saturating_mul`, `saturating_div`, `saturating_cast`; early drafts and some compilers spell them `add_sat` and `saturate_cast`), `<debugging>` (`std::breakpoint`, `std::is_debugger_present`), `std::text_encoding` |

C++26 support is partial in every compiler. Check the support table for each feature before using it, even under `-std=c++26`.

## Minimum toolchains

First version with the feature, from cppreference's compiler support tables (read 2026-11). Library rows: GCC means libstdc++, Clang means libc++, MSVC means MSVC STL. Clang on Linux usually builds against libstdc++, so its library support follows the GCC column. MSVC 19.xx matches `_MSC_VER` 19xx. Apple Clang has its own numbering; check its column on cppreference. "partial" means some of the feature is missing: treat it as unavailable unless the part you need is confirmed. "no" means not listed yet.

| Feature | GCC | Clang | MSVC |
|---|---|---|---|
| **C++14** generic lambdas, `std::make_unique` | 4.9 | 3.4 | 19.0 |
| relaxed `constexpr` | 5 | 3.4 | 19.10 |
| **C++17** structured bindings, `if constexpr` | 7 | 4 (`if constexpr` 3.9) | 19.11 |
| class template argument deduction | 7 | 5 | 19.14 |
| `optional`, `variant`, `string_view` | 7.1 | 4 | 19.11 |
| `std::filesystem` | 8 (link `-lstdc++fs` until 9) | 7 | 19.14 |
| `from_chars`/`to_chars` integer / floating point | 8 / 11 | 7 / 14 | 19.14 / 19.24 |
| `std::pmr` | 9.1 | 16 | 19.13 |
| parallel algorithms | 9 (needs TBB) | 17 partial | 19.14 |
| **C++20** concepts | 10 | 10 | 19.23 partial |
| ranges | 10 | 13 partial | 19.29 |
| `std::span` | 10 | 7 | 19.26 |
| `<=>` | 10 | 8 partial | 19.20 |
| `constinit` | 10 | 10 | 19.29 |
| `consteval` | 10 partial | 11 partial | 19.28 |
| `std::format` | 13 | 17 | 19.29 |
| `std::jthread`, `stop_token` | 10 | 17 partial | 19.28 |
| `std::source_location` | 11 | 15 partial | 19.29 |
| `std::bit_cast` | 11 | 14 | 19.27 |
| latch, barrier, semaphore, atomic wait | 11 | 11 | 19.28 |
| `std::atomic_ref` | 10 | 19 | 19.28 |
| chrono calendar and time zones | 11 partial | 7 partial | 19.29 |
| coroutines, modules | partial in early versions everywhere; check the page for your compiler | | |
| **C++23** `std::expected` | 12 | 16 | 19.33 |
| `std::unreachable`, `std::move_only_function` | 12 | 15 / no | 19.32 |
| `if consteval` | 12 | 14 | 19.44 |
| multidimensional `operator[]` | 12 | 15 | 19.42 |
| `views::zip` / `views::enumerate` | 13 | 15 partial / 23 | 19.33 partial / 19.37 |
| `[[assume]]` | 13 | 19 | 19.51 |
| `std::print` | 14 | 17 partial | 19.37 |
| deducing this | 14 | 18 | 19.32 partial, 19.43 |
| `std::ranges::to` | 14 partial | 17 | 19.34 |
| `std::generator` | 14 | no | 19.43 |
| `std::stacktrace` | 12 partial | no | 19.34 |
| `import std;` | 15 | 17 partial | 19.35 partial |
| `std::flat_map` | 15 | 20 | 19.51 |
| `std::mdspan` | 16 | 17 partial | 19.39 |
| **C++26** placeholder `_` | 14 | 18 | no |
| pack indexing, `= delete("reason")`, `#embed` | 15 | 19 | no |
| saturation arithmetic (`saturating_*` names) | 16 (`add_sat` names from 14) | 23 (`add_sat` names from 18) | no |
| `std::optional<T&>` | 16 | 22 | no |
| `std::function_ref` | 16 | 24 | no |
| reflection, contracts | 16 | no | no |
| `std::inplace_vector` | 16 | no | no |
| `std::simd` | 16 partial | no | no |
| `std::execution`, `std::hive` | no | no | no |

Before using a feature, find the oldest compiler the repo supports (CI matrix, `README`, toolchain files, Docker base images) and check its row. A compiler older than the row means the feature is out, whatever `-std` says.

## Below the feature's standard

When the repo's standard or oldest compiler rules a feature out, use the fallback. First choice: a library already in the dependency tree (abseil, Boost, fmt, GSL); most mirror the `std` API, so migrating later is a rename. Adding a new library is the repo's decision: ask first. Plain-language fallbacks need no dependency.

| Missing | Plain fallback | Library fallback |
|---|---|---|
| `std::make_unique` (14) | `std::unique_ptr<T>(new T(...))` inside a local `make_unique` helper | |
| structured bindings (17) | `std::tie`, or named members | |
| `if constexpr` (17) | overloads or tag dispatch | |
| `std::optional` (17) | | `absl::optional`, `boost::optional`, `tl::optional` |
| `std::variant` (17) | | `absl::variant`, `boost::variant2`, `mpark::variant` |
| `std::string_view` (17) | `const char*` plus length | `absl::string_view`, `boost::core::string_view` |
| `std::filesystem` (17) | | `ghc::filesystem` (same API), `boost::filesystem` |
| `std::from_chars` (17) | `std::strtol`/`strtod` with end-pointer and `errno` checks | `fast_float` for floating point |
| `std::span` (20) | pointer plus size | `gsl::span`, `absl::Span` |
| concepts (20) | `std::enable_if_t` constraints, `static_assert` on traits for readable errors | |
| ranges (20) | iterator-pair algorithms | range-v3 |
| `<=>`, defaulted `==` (20) | `std::tie(a, b) == std::tie(o.a, o.b)` style comparisons | |
| `std::format` (20) | | `fmt::format` (same syntax) |
| `std::jthread`, `stop_token` (20) | `std::thread` in a joining RAII wrapper plus `std::atomic<bool>` | |
| `std::source_location` (20) | `__FILE__`, `__LINE__`, `__func__` passed through a macro | |
| `std::bit_cast` (20) | `std::memcpy` into a local | |
| latch, barrier, semaphore (20) | mutex plus condition variable | |
| chrono calendar and time zones (20) | | HowardHinnant `date` (same API) |
| `std::expected` (23) | | `tl::expected`, `absl::StatusOr`, Boost.Outcome |
| `std::print` (23) | | `fmt::print` |
| `std::to_underlying` (23) | `static_cast<std::underlying_type_t<E>>(e)` | |
| `std::unreachable` (23) | `__builtin_unreachable()` (GCC, Clang) or `__assume(false)` (MSVC) in one helper | |
| deducing this (23) | CRTP, or a `const`/non-`const` overload pair | |
| `std::ranges::to` (23) | construct the container from `begin()`/`end()` | range-v3 `ranges::to` |
| `std::flat_map` (23) | sorted `std::vector<std::pair<K, V>>` with `lower_bound` | `boost::container::flat_map` |
| `std::mdspan` (23) | index arithmetic in one accessor | Kokkos `mdspan` reference implementation |
| `std::generator` (23) | an iterator class, or a callback parameter | |
| `std::stacktrace` (23) | | cpptrace, `boost::stacktrace` |
| `std::move_only_function` (23) | | `fu2::unique_function` (function2) |
| `std::optional<T&>` (26) | `T*` | |
| `std::function_ref` (26) | template parameter `F&&` | `tl::function_ref` |
| `std::inplace_vector` (26) | | `boost::container::static_vector` |
| reflection (26) | | `magic_enum` for enum names, `boost::pfr` for aggregate fields |
| saturation arithmetic (26) | `__builtin_add_overflow` and friends, then clamp | |

The `_t` trait aliases above (`enable_if_t`, `underlying_type_t`) need C++14; in C++11 write `typename std::enable_if<...>::type`.

Keep each fallback behind one name in the codebase (an alias or a small helper) so raising the standard later is a one-line change, made in its own commit.

## Replacement table

| Old | New | Since |
|---|---|---|
| `NULL`, `0` as a pointer | `nullptr` | 11 |
| `typedef` | `using` | 11 |
| `new T(...)` | `std::make_unique<T>(...)` | 14 |
| `std::bind` | lambda | 14 |
| `boost::optional`, `variant`, `any`, `filesystem`, `string_view` | `std::` versions | 17 |
| `const std::string&` parameter that only reads | `std::string_view` | 17 |
| `std::lock_guard` | `std::scoped_lock` | 17 |
| tag dispatch, `enable_if` branches inside one function | `if constexpr` | 17 |
| `std::enable_if` constraints | concepts, `requires` | 20 |
| `T* data, std::size_t n` parameters | `std::span<T>` | 20 |
| `sprintf`, `snprintf` into buffers, iostream format chains | `std::format` (20), `std::print`/`println` (23) | 20 |
| `std::thread` + manual join + atomic stop flag | `std::jthread` + `std::stop_token` | 20 |
| `reinterpret_cast` or union punning | `std::bit_cast` | 20 |
| `m.find(k) != m.end()` / `m.count(k)` | `m.contains(k)` | 20 |
| `s.rfind(p, 0) == 0` | `s.starts_with(p)` | 20 |
| erase-remove idiom | `std::erase_if(c, pred)` | 20 |
| `std::sort(v.begin(), v.end())` | `std::ranges::sort(v)` | 20 |
| hand-written `==`, `!=`, `<`, `<=`, `>`, `>=` | defaulted `<=>` and `==` | 20 |
| `__builtin_popcount` and bit tricks | `<bit>` | 20 |
| `M_PI` | `std::numbers::pi` | 20 |
| `static_cast<int>(v.size())` in comparisons | `std::ssize(v)`, `std::cmp_less` | 20 |
| `__FILE__`/`__LINE__` logging macros | `std::source_location::current()` | 20 |
| `std::is_constant_evaluated()` | `if consteval` | 23 |
| `static_cast<std::underlying_type_t<E>>(e)` | `std::to_underlying(e)` | 23 |
| `__builtin_unreachable()` | `std::unreachable()` | 23 |
| `std::function` holding a move-only callable | `std::move_only_function` | 23 |
| CRTP or `const`/non-`const` overload pairs | deducing this | 23 |
| loop that collects a range into a container | `std::ranges::to<std::vector>()` | 23 |
| index counter beside a range-for | `std::views::enumerate` | 23 |
| `s.find(x) != std::string::npos` | `s.contains(x)` | 23 |
| out parameter plus `bool` return | `std::optional` (17), `std::expected` (23) | 17 |
| `std::function` parameter that is not stored | `std::function_ref` | 26 |
| `T*` meaning an optional reference | `std::optional<T&>` | 26 |
| `[[maybe_unused]] auto unused = ...` | `auto _ = ...` | 26 |

## C standards

C11, C17, and C23 ladder: `c.md`.
