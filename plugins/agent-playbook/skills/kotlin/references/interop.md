# Java and Kotlin Interop

Loaded via `kotlin` SKILL.md routing table. Sources: Kotlin docs (calling Java from Kotlin, calling Kotlin from Java, Java interop nullability and JSpecify support, kapt, KSP, Lombok compiler plugin), Kotlin 2.2 "What's new" (JVM default methods). Build setup for mixed modules lives in the `jvm` skill (`references/build.md`).

## Kotlin calling Java

- Unannotated Java types are platform types (`String!`): Kotlin does not know their nullness and lets you treat them either way. Give them an explicit type at the boundary (`val name: String? = javaObj.name`) instead of letting `!` types spread into Kotlin code.
- Annotated Java gives real nullability. JSpecify annotations (`@NullMarked`, `@Nullable`) are reported as errors on mismatch by default; JSR-305 needs `-Xjsr305=strict` to be enforced; JetBrains, Android, and Spring annotations are also read. Annotate the Java side rather than adding `!!` on the Kotlin side.
- Java getters and setters appear as properties (`user.name` calls `getName()`); `is` getters keep their name (`user.isActive`).
- Java functional interfaces accept Kotlin lambdas (SAM conversion). Kotlin `fun interface` gives the same for Kotlin-declared interfaces.
- Checked exceptions are invisible to Kotlin: the compiler does not make you catch them. Read the Java signature and handle the ones that matter.
- Java `Optional` from a Java API: convert at the boundary (`.orElse(null)` to a nullable); Kotlin code does not pass `Optional` around.
- Java collections arrive as platform types (`(Mutable)List<String!>!`); copy or wrap them in read-only types if Kotlin code must not mutate them.

## Java calling Kotlin

| Kotlin | Java sees | Make it nicer |
|---|---|---|
| property `name` | `getName()`/`setName(...)`; `isActive` stays `isActive()` | `@JvmField` for a plain field without custom accessors |
| top-level `fun parse()` in `Parser.kt` | `ParserKt.parse()` | `@file:JvmName("Parsers")` |
| `companion object { fun of() }` | `Foo.Companion.of()` | `@JvmStatic` |
| `const val MAX = 10` in a companion | `Foo.MAX` | already static |
| `object Registry` | `Registry.INSTANCE` | `@JvmStatic` on members |
| default arguments | one method with all parameters | `@JvmOverloads` |
| function that throws `IOException` | no `throws` clause, so Java cannot `catch` it | `@Throws(IOException::class)` |
| `data class` | class with `equals`/`hashCode`/`toString`/`componentN`/`copy` | `@JvmRecord` to emit a Java record (target 16+, `val` properties only) |
| `suspend fun` | method with an extra `Continuation` parameter | a `CompletableFuture` (`scope.future { }`) or blocking wrapper |
| inline value class in a signature | mangled method name Java cannot call | `@JvmName` on the function, or no value classes in Java-facing API |
| interface function with a body | a JVM default method (2.2+; older versions depended on `-Xjvm-default`) | |
| nullable `String?` | `@Nullable` annotated `String` | |
| `internal` function or property | public in bytecode under a mangled name | do not call it from Java |

- A Kotlin API meant for Java callers gets these annotations when it is designed; adding them later changes binary signatures.
- Do not rely on Java `switch` exhaustiveness over Kotlin sealed types; handle the default branch on the Java side.
- Kotlin `Unit`-returning lambdas passed from Java need `return Unit.INSTANCE;`; a Kotlin `fun interface` or `java.util.function` type in the API avoids that.

## Annotation processing and code generation

- KSP for processors that support it (Room, Moshi, Dagger/Hilt, many others). kapt generates Java stubs first, which slows builds, and the Kotlin docs point to KSP as its replacement.
- Lombok in a mixed module: Kotlin cannot see Lombok-generated members unless the Kotlin Lombok compiler plugin is configured, and that plugin supports only part of Lombok. New code avoids Lombok; existing Lombok classes used from Kotlin are good candidates to become records or Kotlin data classes.
- MapStruct and other Java processors on Kotlin classes need kapt; prefer hand-written mapping functions in Kotlin.

## Choosing the language for new code in a mixed repo

- Match the module. A Java module gets Java, a Kotlin module gets Kotlin, unless the user decides otherwise.
- New modules follow the repo's stated direction (many repos move Java to Kotlin, some the reverse). No direction stated: ask.
- Converting a Java file to Kotlin is its own change with its own review, not a side effect of a feature. The IDE's converter output needs cleanup: platform types, `!!`, `lateinit`, Java-style getters.
