# Java Style and Design

Loaded via `java` SKILL.md routing table. Sources: Effective Java (3rd ed.), Google Java Style Guide, JSpecify user guide (jspecify.dev), JDK Javadoc for `java.util` and `java.lang`.

## Naming and layout

- Packages lowercase, by feature (`com.acme.billing.invoice`), not by layer (`controllers`, `services`, `models`) across the whole app.
- Types `UpperCamelCase` nouns; methods `lowerCamelCase` verbs; constants `UPPER_SNAKE_CASE` only for `static final` deeply immutable values. No `I` prefix on interfaces, no `Impl` suffix when there is one implementation (then you need no interface).
- One top-level type per file. Members ordered so a reader finds them: constants, fields, constructors, factories, public methods, private helpers near their caller.
- Visibility as tight as works: package-private is the default for anything not part of the module's API.
- Imports explicit; no wildcard imports in code (formatters enforce this). Module import declarations (`import module java.base;`, 25+) are for scripts and teaching, not production code.

## Types

| Shape | Use |
|---|---|
| immutable data carrier | `record` (16+); validate in the compact constructor |
| closed set of variants | `sealed interface` plus `record` implementations (17+) |
| fixed set of constants with behavior | `enum` |
| behavior with state | `final class` |
| extension point | interface; abstract class only for shared state or template methods |
| static helpers | `final class` with a private constructor, only when no type owns the function |

```java
public record Money(BigDecimal amount, Currency currency) {
    public Money {
        Objects.requireNonNull(amount, "amount");
        Objects.requireNonNull(currency, "currency");
        if (amount.scale() > currency.getDefaultFractionDigits()) {
            throw new IllegalArgumentException("scale " + amount.scale() + " exceeds " + currency);
        }
    }

    public Money plus(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("currency mismatch: " + currency + " vs " + other.currency);
        }
        return new Money(amount.add(other.amount), currency);
    }
}
```

- Records holding arrays or mutable collections: copy in the compact constructor (`items = List.copyOf(items);`). Records compare arrays by identity.
- `BigDecimal.equals` compares scale (`2.0` is not `2.00`); records containing one inherit that. Normalize the scale in the constructor or compare with `compareTo`.
- Static factory (`Money.of`, `Duration.ofSeconds`) over a public constructor when it names intent, caches, or returns a subtype.
- Builder only above roughly four optional parameters. Records with many fields usually mean two types.
- `equals` and `hashCode` together, over the same fields, or not at all. `toString` never prints secrets.
- `Comparable` consistent with `equals` for types used in sorted sets and maps.

## Nullness

- New code: JSpecify. `@NullMarked` on `package-info.java` makes every type non-null unless marked `@Nullable`. NullAway in JSpecify mode checks it at compile time (`jvm` skill, `build.md`). Kotlin reads JSpecify as strict by default (`kotlin` skill, `interop.md`).

  ```java
  @NullMarked
  package com.acme.billing;

  import org.jspecify.annotations.NullMarked;
  ```

- `@Nullable` goes on the type, so arrays and generics read `String @Nullable []` and `List<@Nullable String>`.
- Repo already on JSR-305, Spring's `@Nullable`, or Checker Framework: follow it; do not mix vocabularies in one module.
- `Optional<T>` as a return type for "may be absent". Never a field, parameter, or collection element; never `Optional.get()` without `isPresent` (use `orElseThrow()`, `orElse`, `map`). Primitive variants (`OptionalInt`) for primitives.
- Return `List.of()`/`Map.of()`, not `null`. `List.of` and friends reject null elements and are unmodifiable; `Collections.unmodifiableList` is a view that changes with its source.

## Generics

- No raw types (`List` instead of `List<Order>`); `-Xlint:rawtypes,unchecked` flags them.
- PECS at API boundaries: `Collection<? extends T>` to read from, `Consumer<? super T>` to write to. Return concrete parameterized types, never wildcards.
- Generic arrays do not exist; use `List<T>`.
- `@SafeVarargs` only on `static`, `final`, or `private` methods that never store or expose the varargs array.

## Control flow and expressions

- `var` when the right side names the type (`var orders = new ArrayList<Order>()`) or the name says it; spell the type when it carries meaning the reader needs.
- Switch expressions with arrows; no fallthrough. On sealed types and enums, list every case and omit `default` so a new case is a compile error.

  ```java
  sealed interface Payment permits Card, Transfer, Wallet {}
  record Card(String last4) implements Payment {}
  record Transfer(String iban) implements Payment {}
  record Wallet(String provider) implements Payment {}

  static String label(Payment p) {
      return switch (p) {
          case Card c -> "card " + c.last4();
          case Transfer t -> "transfer " + t.iban();
          case Wallet w -> "wallet " + w.provider();
      };
  }
  ```

- Pattern matching `instanceof` (16+) instead of cast after check. Record patterns (21+) to destructure.
- Text blocks for multi-line SQL, JSON, and messages; `formatted(...)` for interpolation.
- Streams for transformations that read as a pipeline; a loop when there is early exit, checked exceptions, index math, or more than one accumulator. No side effects in `map`/`filter`. `Stream.toList()` (16+) returns an unmodifiable list; `Collectors.toList()` makes no promise either way.
- `Map.computeIfAbsent`, `merge`, `getOrDefault` instead of get-check-put.
- Integer overflow wraps silently: `Math.addExact`/`multiplyExact` or `long` where values can grow; `Math.floorMod` for non-negative remainders.
- String concatenation in loops: `StringBuilder` or `String.join`/`Collectors.joining`.

## Classes and inheritance

- Constructors do assignment and validation only; no I/O, no thread start, no `this` escaping (registering listeners, passing `this` to other objects).
- Inheritance only from types designed for it. Overridable methods are never called from constructors.
- Interfaces small and named for what callers need. Default methods for evolution, not for sharing state.
- Static mutable state is a global; avoid it. Constants are `static final` and deeply immutable (`List.of`, not `new ArrayList`).

## Comments and Javadoc

- Javadoc on public API: first sentence states what it does; then `@param`, `@return`, `@throws` where not obvious, nullness when not annotated, and thread safety for shared types.
- Markdown doc comments (`///`, 23+) are fine where the release allows and the repo uses them; otherwise `/** */`.
- `@snippet` (18+) instead of `<pre>{@code}</pre>` for examples on 18+.
- Comments say why. No commented-out code, no `TODO` without an issue reference the repo uses.
