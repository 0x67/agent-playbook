# Kotlin Style and Idioms

Loaded via `kotlin` SKILL.md routing table. Sources: Kotlin coding conventions (kotlinlang.org/docs/coding-conventions.html), Kotlin language reference (classes, data classes, sealed classes, inline value classes, scope functions, null safety), ktlint rule set.

## Naming and files

- Packages lowercase, no underscores, by feature. Directory structure follows the package, with the common root prefix omitted when the repo does that (pure Kotlin modules often do).
- A file holding one class is named after it. A file of top-level functions or extensions is named for what they share (`Collections.kt` is too broad; `OrderPricing.kt` is right). No `Utils.kt` dumping ground.
- Classes and objects `UpperCamelCase`; functions, properties, and locals `lowerCamelCase`. Factory functions may share the class name (`fun Money(cents: Long): Money`).
- `const val` and top-level or `object` `val`s holding deeply immutable data: `UPPER_SNAKE_CASE`. Other properties, including those holding mutable objects: `lowerCamelCase`.
- Backing property for a mutable internal with a read-only view: `private val _items = mutableListOf<Item>()` plus `val items: List<Item> get() = _items`. From Kotlin 2.4, explicit backing fields can replace this pattern (`modern.md`).
- Test names may use backticks: `` fun `rejects withdrawal above balance`() ``.
- Acronyms: two letters stay upper (`IOStream`), longer ones capitalize only the first letter (`HttpClient`, `XmlParser`).

## Types

| Shape | Use |
|---|---|
| value with equality by content | `data class` with `val` properties |
| closed set of variants | `sealed interface` (or `sealed class` when variants share state) with `data class`/`data object` members |
| single-field domain type (id, amount, email) | `@JvmInline value class` with validation in `init` |
| fixed constants with behavior | `enum class` |
| stateless singleton or namespace | `object`; a `companion object` only for factories and constants tied to the class |
| behavior with state | regular `class` (final by default) |

```kotlin
@JvmInline
value class AccountId(val value: String) {
    init {
        require(value.isNotBlank()) { "account id must not be blank" }
    }
}

sealed interface Withdrawal {
    data class Done(val balance: BigDecimal) : Withdrawal
    data class Insufficient(val available: BigDecimal) : Withdrawal
    data object Frozen : Withdrawal
}

fun describe(w: Withdrawal): String = when (w) {
    is Withdrawal.Done -> "ok, balance ${w.balance}"
    is Withdrawal.Insufficient -> "only ${w.available} available"
    Withdrawal.Frozen -> "account frozen"
}
```

- Classes are final by default; `open` only for designed extension points. Frameworks that proxy classes (Spring) get the all-open compiler plugin instead of hand-written `open` (`jvm` skill).
- `data class` properties are `val`. A `var` in a data class breaks `hashCode` for keys in sets and maps.
- Validation in `init` also runs for `copy()`. A `private` constructor does not hide `copy()` by default: since 2.0.20 the compiler warns, and `@ConsistentCopyVisibility` (or `-Xconsistent-data-class-copy-visibility` for a module) makes `copy()` as private as the constructor. Use it when a factory must be the only way in.
- Value classes box when used as a nullable, generic, or interface type; they are for type safety first.
- Prefer default and named arguments over overloads and builders: `fun connect(host: String, port: Int = 443, timeout: Duration = 5.seconds)`.
- Visibility: `private` and `internal` by default for anything not in the module's API. `internal` is module-wide, not package-wide.

## Null safety

- Nullable types only where absence is a real state. Use `?.` and `?:` for local handling; return early with `?: return` or fail with `?: error("...")`.
- `requireNotNull(x) { "..." }` for argument preconditions, `checkNotNull` for state.
- `lateinit var` only for framework injection and test setup; never for values that can legitimately be missing.
- `let` for a short nullable block, not as a general `if` replacement. `if (x != null)` works with smart casts on `val`s and local variables.

## Collections

- Read-only interfaces in APIs (`List`, `Map`, `Set`); build with `buildList { }`, `listOf`, `mapOf`, `associateBy`, `groupBy`.
- Read-only is not immutable: a `List` can be a view over a `MutableList` someone else changes. Copy (`toList()`) at boundaries when that matters.
- Collection operations are eager and allocate a list per step. Use `asSequence()` for long chains over large collections or when stopping early; plain collection operations otherwise.
- `first()`, `single()`, `getValue()` throw on absence; the `OrNull` variants return null. Pick by whether absence is a bug.
- `forEach` with a lambda cannot `break` or `continue` before Kotlin 2.2 (non-local break and continue); a plain `for` loop is clearer for early exit on any version.

## Functions

- Expression bodies for single expressions; block bodies when there is more than one step.
- Extension functions for small helpers on types you do not own, kept close to their use (private or internal when only one file needs them). Not a way to scatter the behavior of your own classes across files.
- Scope functions: `apply` to configure an object, `also` for a side effect that returns the receiver, `let` to transform a nullable, `run`/`with` to group calls on one receiver. One level deep; nested scope functions hide what `this` and `it` mean.
- Trailing lambdas outside parentheses; name lambda parameters when `it` would be ambiguous or the lambda is long.
- `inline` for higher-order functions on hot paths or with reified type parameters; not by default.
- String templates over concatenation; `trimIndent()` for multi-line strings.

## Formatting and comments

- ktlint (`ktlint_official` code style by default since ktlint 1.0) through Spotless or the ktlint Gradle plugin; detekt for smells where the repo uses it.
- No wildcard imports (ktlint `no-wildcard-imports`).
- KDoc on public API: what it does, `@param`/`@return`/`@throws` only where not obvious. Comments say why.
