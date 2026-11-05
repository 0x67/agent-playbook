---
name: kotlin
description: >
  Idiomatic Kotlin engineering on the JVM: writing, reading, reviewing,
  refactoring, and testing Kotlin code in Kotlin-only or mixed Java/Kotlin
  repos (.kt, .kts). Use whenever the user works in Kotlin or asks anything
  involving data classes, sealed types, value classes, null safety, scope
  functions, extension functions, coroutines, Flow, structured concurrency,
  kotlinx.serialization, Ktor, Spring with Kotlin, MockK, Kotest, ktlint,
  detekt, K2, or a Kotlin version (1.9, 2.0 to 2.4). Trigger even when
  "Kotlin" is not said but files are clearly Kotlin. Language rules live
  here; builds (Gradle, Maven), JUnit, Mockito, MockK, Spring, profiling,
  and code navigation come from the `jvm` skill. Core rules inline;
  specialist rules load through the routing table below.
---

# Kotlin engineering skill

Write Kotlin a careful maintainer would merge without comment: types that make illegal states unrepresentable, nulls handled by the type system instead of `!!`, immutable data, coroutines that are always owned and cancellable, and Java interop designed in rather than patched on. The repo's Kotlin version is the ceiling for language and standard library features.

Kotlin is its own language with its own idioms; it shares only the JVM platform with Java. Build tools, the test platform, frameworks, and runtime profiling are JVM concerns: load skill `jvm` (`agent-playbook:jvm` in Claude Code) for those. In a mixed repo, Java files follow skill `java`.

## Routing table (mandatory)

Read matching reference BEFORE writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| naming, files, classes, data/sealed/value classes, objects, properties, null safety, collections, scope and extension functions, KDoc | `references/style.md` |
| exceptions, `require`/`check`, `Result` and `runCatching`, sealed result types, `use` for resources | `references/errors.md` |
| coroutines, scopes, dispatchers, cancellation, `Flow`, `StateFlow`, coroutine tests, virtual threads | `references/coroutines.md` |
| calling Java from Kotlin or Kotlin from Java, platform types, nullness annotations, `@Jvm*` annotations, kapt/KSP, Lombok | `references/interop.md` |
| choosing features for the repo's Kotlin version, fallbacks on older versions, compiler and Gradle plugin compatibility | `references/modern.md` |
| Gradle or Maven setup, JUnit, MockK, Kotest, Testcontainers, Spring, Ktor deployment, profiling, LSP navigation | skill `jvm` |

Multiple matches: read all matched. Unsure: read `style.md` and `errors.md`.

## Before writing

1. Find the Kotlin version (Kotlin Gradle plugin in `libs.versions.toml` or `plugins {}`, or `kotlin.version` in Maven) and any `languageVersion`/`apiVersion` pin. Never use a feature above it; `references/modern.md` lists what each version made stable. The JDK target (`jvmToolchain`, `jvmTarget`) bounds which JDK APIs you can call.
2. Check repo conventions: ktlint or detekt config, `.editorconfig`, coroutines or blocking style, serialization library (kotlinx.serialization, Jackson with the Kotlin module, Moshi), DI (Spring, Koin, manual), test libraries (JUnit with kotlin.test or AssertJ, Kotest, MockK). Repo convention beats these defaults.
3. Experimental and opt-in APIs (`@OptIn`, `-X` compiler flags) only when the repo already uses them.
4. Find the existing file and module for the change. New file only for a new concern.

## Non-negotiables

- Zero compiler warnings (`allWarningsAsErrors` where the build sets it). `@Suppress` only on the narrowest element, with a comment saying why it is sound.
- No `!!` without a comment saying why the value cannot be null. Prefer `?:` with `return`, `error(...)`, or `requireNotNull(x) { "..." }`.
- `val` over `var`; read-only `List`/`Map`/`Set` in signatures; mutable collections stay private.
- `data class` for values, `sealed interface` plus exhaustive `when` (no `else`) for closed sets, `value class` for single-field domain types (ids, amounts) where the boxing cost is acceptable.
- Platform types from Java are given an explicit Kotlin type at the boundary; they never spread through Kotlin code.
- Coroutines are always launched in a scope that someone cancels. No `GlobalScope`; no `runBlocking` outside `main` and tests; blocking calls only on `Dispatchers.IO` or a dedicated dispatcher.
- `CancellationException` is never swallowed: no bare `catch (e: Exception)` or `runCatching` around suspending code without rethrowing it.
- Resources closed with `use { }`.
- Money and exact decimals in `BigDecimal`, never `Double`. Time through `java.time` or `kotlin.time` with an injected clock.
- Public API meant for Java callers gets `@JvmStatic`, `@JvmOverloads`, `@Throws`, and `@JvmName` where needed at design time (`references/interop.md`).
- Comments: plain humanizer prose, why not what, no plan/task ids, no em dash. KDoc on public declarations of a library API.
- Tests must fail from a project bug. No tests of generated `data class` members, no getter echo, no mock-call-count-only.

## After writing (gate, in order)

```sh
./gradlew spotlessCheck            # or: ./gradlew ktlintCheck, whichever runs ktlint in the repo
./gradlew detekt                   # when the repo uses detekt
./gradlew test --tests 'com.example.FooTest'
./gradlew build                    # Maven: ./mvnw verify
```

Use the repo's tasks and modules. Not done until gate green. Report failures verbatim. Build setup, mixed modules, and test libraries: skill `jvm`.

## Tool preference

- Definitions, references, call hierarchy, hover: `LSP` tool backed by kotlin-lsp (`kotlin-lsp` plugin in Claude Code) when exposed. It is Alpha: confirm surprising empty results with text search. Java callers of Kotlin code need a text search for the JVM names (`getX`, `Companion`, `FileKt`). Details in the `jvm` skill's `references/navigation.md`.
- Exact text search: `mcp__fff__grep`/`rg`. Semantic: Semble.
- Standard library and kotlinx APIs: kotlinlang.org API reference for the repo's version, or the sources jar. Never guess a signature.
- Global rules still apply: Code Growth Discipline, Code Simplicity Discipline, Useless Test Ban, terminology guard (`snapshot`/`expected`, never `golden`). Cross-language naming, function size, and architecture: skill `software-design`.
