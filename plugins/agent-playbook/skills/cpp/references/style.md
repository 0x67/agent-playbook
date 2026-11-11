# C++ Style

Loaded via `cpp` SKILL.md routing table. Sources: C++ Core Guidelines (isocpp.github.io/CppCoreGuidelines), cppreference, clang-tidy `readability-*`, `modernize-*`, `cppcoreguidelines-*` check docs. The repo's `.clang-format`, `.clang-tidy`, and existing naming beat everything here.

## Naming

- Follow the repo. No convention yet: types `PascalCase`; functions and variables `snake_case` (standard library style) or `camelCase`, one per repo, enforced with `readability-identifier-naming`; constants `kPascalCase` or `snake_case`; macros `UPPER_SNAKE` with a project prefix; private members with the repo's marker (`name_` or `m_name`).
- Names say what, not the type: `retry_count`, never `iCount`.
- Reserved: identifiers starting with `_` plus an uppercase letter, or containing `__` anywhere.
- One main class or concern per header/source pair with the same base name. `.hpp`/`.cpp` or `.h`/`.cc`: follow the repo.

## Headers and includes

- Every header compiles on its own and has `#pragma once` or an include guard.
- Order: matching header first (proves it is self-contained), then project, third-party, standard library. `IncludeBlocks: Regroup` in clang-format keeps it.
- Include what you use. Forward-declare in headers when a pointer or reference is enough. `misc-include-cleaner` or include-what-you-use finds the rest.
- No `using namespace` at header scope. In `.cpp` files, narrow `using` declarations and aliases (`namespace fs = std::filesystem;`). Never `using namespace std;`.
- Headers hold declarations, templates, `inline`/`constexpr` definitions. File-local helpers go in an unnamed namespace in the `.cpp`.
- C++20 modules only when the repo already builds them; toolchain support is uneven.

## Namespaces

- Everything in a project namespace, nested as `namespace app::net {`. Header-only internals in `detail`.

## Classes

- `struct` for plain aggregates with no invariant; `class` with private data when there is one.
- Rule of zero: members (`std::vector`, `std::unique_ptr`, `std::string`) manage resources, so declare no special members. Owning a raw handle: wrap it in a small RAII type and return to rule of zero, or write all five.
- Polymorphic base: public virtual destructor, or protected non-virtual. Delete copy on polymorphic bases to stop slicing.
- `override` on every override, without repeating `virtual`. `final` when nothing should derive.
- Single-argument and conversion constructors `explicit` unless implicit conversion is the point.
- Defaults as default member initializers; constructor initializer lists in declaration order (`-Wreorder`).
- Composition and free functions over inheritance and growing member lists.
- Strong types for ids and units (`struct UserId { std::uint64_t value; };`, `std::chrono::milliseconds`) instead of bare integers and `bool` parameters.
- `enum class`, with an explicit underlying type when serialized.
- Comparisons: `auto operator<=>(const T&) const = default;` and `bool operator==(const T&) const = default;` (C++20) instead of hand-written sets.

## Parameters and returns

| Parameter | Pass as |
|---|---|
| cheap to copy (scalars, pointers, `string_view`, `span`, small trivially copyable structs) | by value |
| read-only, larger | `const T&` |
| sink (callee keeps it) | by value, then `std::move` into place |
| result | return it (struct, `std::optional`, `std::expected`); no out parameters |
| optional, non-owning | `T*`; `std::optional<T&>` in C++26 |
| ownership transfer | `std::unique_ptr<T>` by value |
| forwarding | `T&&` in a template, with `std::forward<T>` |

- Return by value; elision and moves make it cheap. Never return a reference or view to a local.
- No `bool` flag parameters: split the function or take an `enum class`.
- One job per function, early return, nesting depth 3 max.
- `constexpr` where it can be; `consteval` (C++20) for compile-time-only helpers.
- `noexcept` on destructors, moves, swaps, and functions that truly cannot throw. Not on everything.
- `[[nodiscard]]` on factories, pure queries, and anything returning an error.

## Variables

- Initialize at declaration. Brace init rejects narrowing; watch `std::vector<int>{3}` (one element) against `std::vector<int>(3)` (three).
- `auto` when the type is obvious from the right side or unspellable (lambdas, iterators); spell the type when it documents intent. `const auto&` in range-for over non-trivial elements.
- `const` by default. `constexpr` for compile-time constants; `inline constexpr` at namespace scope in headers.
- Narrowest scope: `if (auto it = m.find(k); it != m.end())`. Structured bindings: `for (const auto& [key, value] : map)`.
- Integers: fixed width (`std::int32_t`, `std::uint64_t`) for wire and storage, `std::size_t` for sizes. Do not mix signed and unsigned (`-Wsign-conversion`); `std::ssize` and `std::cmp_less` (C++20) when mixing is unavoidable.

## Casts

- `static_cast` for value conversions. `reinterpret_cast` and `const_cast` only with a comment saying why it is sound.
- Type punning: `std::bit_cast` (C++20) or `std::memcpy`, never a pointer cast through an unrelated type.
- No C-style casts on values or pointers (`-Wold-style-cast`). `(void)expr` to discard a result is fine.
- Deliberate narrowing: `static_cast` after a range check, or `gsl::narrow` when the repo uses GSL.

## Control flow

- Early return; no `else` after `return`.
- `switch` over an `enum class` lists every enumerator and has no `default`, so `-Wswitch` flags new ones. `[[fallthrough]]` when intended.
- Range-for and `std::ranges` algorithms where they are clearer than index loops. A plain loop is fine when it is the clearer one.
- Lambdas capture explicitly: `[&total]`, `[this]`, `[buf = std::move(buf)]`. `[&]` only for lambdas that do not outlive the scope. Implicit `this` capture through `[=]` is deprecated (C++20).

## Comments and docs

- Doc comment (`///` or `/** */`, Doxygen if configured) on every public declaration: what it does, preconditions, ownership and lifetime of pointer and view parameters, thread safety, how it reports errors.
- Implementation comments say why. No restating code, no plan or ticket ids, no em dash characters.
- `// NOLINT(check-name): reason` only with a reason; never bare `NOLINT`.

## Formatting

- `clang-format` with the repo's `.clang-format`. None yet: start from `BasedOnStyle: Google` or `LLVM` and change only what the team disagrees with (`tooling.md` has a starting file).
- Existing code: format only touched lines (`git clang-format`). New files: whole file.
