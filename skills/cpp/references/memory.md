# C++ Memory, Ownership, and Lifetimes

Loaded via `cpp` SKILL.md routing table. Sources: C++ Core Guidelines (R, ES, F, Lifetime sections), cppreference (object lifetime, iterator invalidation, undefined behavior), Clang sanitizer docs.

## Ownership

| Situation | Use |
|---|---|
| single owner on the heap | `std::unique_ptr<T>` from `std::make_unique<T>(...)` |
| dynamic array | `std::vector<T>`; `std::unique_ptr<T[]>` only at a C boundary |
| shared ownership, lifetime decided at run time by several owners | `std::shared_ptr<T>` from `std::make_shared<T>(...)` |
| observer that may outlive the owner | `std::weak_ptr<T>`, `lock()` before each use |
| non-owning, never null | `T&` |
| non-owning, nullable | `T*` |
| non-owning contiguous range | `std::span<T>` / `std::span<const T>` (C++20) |
| non-owning string | `std::string_view` |
| C handle (`FILE*`, fd, `HANDLE`, library context) | `std::unique_ptr<T, Deleter>` or a small RAII class |

```cpp
struct FileCloser {
    void operator()(std::FILE* f) const noexcept { std::fclose(f); }
};
using FilePtr = std::unique_ptr<std::FILE, FileCloser>;
```

- `new`/`delete` only inside an RAII type's implementation; `malloc`/`free` only at C boundaries.
- `shared_ptr` is not a default: it hides who decides lifetime and costs atomic reference counts. Cycles leak; break them with `weak_ptr`.
- Take a smart pointer parameter only when the callee joins in ownership. Otherwise take `T&` or `T*` and call `f(*p)` or `f(p.get())`.
- `std::enable_shared_from_this` only when an object must hand out `shared_ptr` to itself, typically for async callbacks.

## Moves

- A moved-from object is valid but unspecified: assign to it or destroy it, nothing else, unless its type documents more (a moved-from `std::unique_ptr` is null).
- `std::move` on a `const` object silently copies.
- Never `return std::move(local);`: it blocks copy elision (`-Wpessimizing-move`).
- Move constructor and move assignment `noexcept`, or `std::vector` copies instead of moving on growth.

## Views and dangling

The most common modern C++ memory bug is a view or reference that outlives what it points into.

- A `std::string_view` or `std::span` built from a temporary dangles at the end of the full expression: `std::string_view name = make_name();` is a bug.
- No view members unless the class documents that the source outlives it. Store `std::string` or `std::vector`.
- Return a reference or view only into `*this` or into parameters the caller keeps alive, and document it. `[[clang::lifetimebound]]` on those parameters lets Clang warn (`-Wdangling`).
- Range-for over a member of a temporary (`for (auto& x : make().items())`) dangles before C++23; C++23 extends temporaries in the range initializer.
- Lambdas that capture by reference and are stored (callbacks, threads, `std::function` members) dangle when the scope ends. Capture by value or hold a `shared_ptr`.
- `c_str()` and `data()` pointers die on the next mutation of the string or vector.

## Iterator and reference invalidation

| Container | Invalidated by |
|---|---|
| `std::vector`, `std::string` | growth past capacity: everything; insert or erase: at and after the position |
| `std::deque` | insert in the middle: everything; insert at either end: iterators, not references |
| `std::unordered_map`/`set` | rehash on insert: iterators, not references; erase: the erased element |
| `std::map`/`set`/`list` | erase: the erased element only |

- Erase while iterating: `it = c.erase(it);`, or `std::erase_if(c, pred)` (C++20). Never `c.erase(it); ++it;`.
- Across mutations of a `vector`, keep indices or keys, not iterators or pointers.

## Undefined behavior checklist

Each item can silently miscompile. Sanitizers catch most at run time; review catches the rest.

- Out-of-bounds: `operator[]`, `front()`/`back()` on empty, pointer arithmetic past one-past-the-end. Use `.at()` at trust boundaries and the hardened standard library in builds (`tooling.md`).
- Signed overflow and shifts by a negative amount or by at least the bit width. Check ranges first; `std::saturating_add` and friends (C++26), `__builtin_add_overflow`, or `ckd_add` (C23).
- Uninitialized reads. Initialize at declaration. C++26 makes them erroneous behavior instead of UB; still a bug.
- Use after free, double free, use of a destroyed object.
- Null dereference.
- Data races (`concurrency.md`).
- Strict aliasing: reading an object through an unrelated pointer type. `std::bit_cast` or `std::memcpy` instead.
- Misaligned access through `reinterpret_cast`.
- Writing to a `const` object through `const_cast`.
- Breaking a standard function's precondition: a comparator that is not a strict weak order in `std::sort`, overlapping ranges in `std::copy`.
- ODR violations: one name with different definitions across translation units, often from inline functions or templates compiled under different macros.

## Containers

- `std::vector` by default; `reserve()` when the size is known.
- `std::array` for fixed size; `std::inplace_vector` (C++26) for a bounded size without heap.
- `std::unordered_map` for lookup without order; `std::map` when order or stable iterators matter; `std::flat_map` (C++23) for small, read-heavy maps.
- `emplace_back` to construct from arguments; `push_back` when you already hold the object.
- Lookup by `std::string_view` in a `std::string`-keyed unordered map needs a transparent hash and `std::equal_to<>` (C++20 heterogeneous lookup).

## Tools

- AddressSanitizer plus UndefinedBehaviorSanitizer on the test suite; LeakSanitizer comes with ASan on Linux. MemorySanitizer (Clang, Linux, every dependency instrumented) for uninitialized reads. Flags and presets in `tooling.md` and `testing.md`.
- Valgrind memcheck where sanitizers cannot run; never together with ASan.
- Hardened standard library: `_GLIBCXX_ASSERTIONS` (libstdc++), `_LIBCPP_HARDENING_MODE` (libc++), debug iterators or `/fsanitize=address` on MSVC.
