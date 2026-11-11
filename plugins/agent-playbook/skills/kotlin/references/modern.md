# Modern Kotlin by Version

Loaded via `kotlin` SKILL.md routing table. Sources: Kotlin "What's new" pages for 1.9.20, 2.0.0, 2.1.0, 2.2.0, 2.3.0, 2.4.0, and 2.4.20 (kotlinlang.org/docs/whatsnew*.html), Kotlin data classes docs. Checked 2026-11.

## Rule

- The Kotlin Gradle plugin version (or `kotlin.version` in Maven) is the ceiling for language and standard library features. A `languageVersion` or `apiVersion` setting lowers it further; check both.
- The JDK target (`jvmToolchain`, `jvmTarget`) is a separate ceiling for JDK APIs called from Kotlin. The `java` skill's `references/modern.md` lists what each JDK release adds; the `jvm` skill lists which Kotlin version can emit which bytecode.
- Experimental and preview features (`-X` flags, `@OptIn` of experimental APIs) only when the repo already enables them. They change or disappear between versions.
- Upgrading Kotlin is a repo decision: compiler plugins (Compose, KSP, kapt, serialization, all-open), detekt, and IDE support move with it. Ask before raising it.
- Kotlin 2.0+ compiles with K2. Compiler plugins and detekt versions must support the K2 compiler the repo uses.

## Ladder

| Version | Stable and default changes that matter on the JVM |
|---|---|
| 1.9.20 (2023-11) | Java 21 bytecode; K2 in Beta; Kotlin Multiplatform stable |
| 2.0.0 (2024-05) | K2 compiler stable and default; lambdas compiled with `invokedynamic` by default; Java 22 bytecode; `kotlinx-metadata-jvm` stable; Compose compiler moved into the Kotlin repo as a Gradle plugin |
| 2.0.20 | warning when a data class has a non-public constructor but a public `copy()`; `@ConsistentCopyVisibility` and `-Xconsistent-data-class-copy-visibility` to opt into matching visibility |
| 2.1.0 (2024-11) | Java 23 bytecode; previews of guard conditions in `when`, non-local `break`/`continue`, and multi-dollar interpolation (not for production) |
| 2.2.0 (2025-06) | stable: guard conditions in `when` (`is Card if amount > limit ->`), non-local `break`/`continue` from inline lambdas, multi-dollar interpolation (`$$"..."`); `kotlin.io.encoding.Base64` and `HexFormat` stable; interface functions with bodies compile to JVM default methods (`-jvm-default` replaces `-Xjvm-default`); Java 24 bytecode; context parameters in preview |
| 2.2.20 | `when` compiled with `invokedynamic` on JVM 21+ (experimental) |
| 2.3.0 (2025-12) | stable: nested type aliases, data-flow-based exhaustiveness for `when`; `return` in expression bodies with an explicit return type on by default; `kotlin.time.Clock` and `kotlin.time.Instant` stable; Java 25 bytecode; Gradle 9.0 support; unused return value checker added as experimental (`-Xreturn-value-checker=check`) |
| 2.4.0 (2026-06) | stable: context parameters (except context arguments and callable references), explicit backing fields, the `@all` annotation meta-target and new use-site target defaulting rules; `kotlin.uuid.Uuid` stable; annotations in Kotlin metadata on by default; Java 26 bytecode; Gradle 7.6.3 to 9.5.0; minimum Android Gradle plugin 8.5.2 |
| 2.4.20 (2026-09) | `when` with `invokedynamic` on JVM 21+ stable and on by default; Gradle up to 9.7.0; new collection functions for checking element equality and uniqueness; more `kotlin.test` assertion overloads |

## Below the feature's version

| Feature (version) | On an older version |
|---|---|
| guard conditions in `when` (2.2) | a nested `if` inside the branch, or order the branches so the more specific case comes first |
| non-local `break`/`continue` in `forEach` (2.2) | a `for` loop |
| multi-dollar interpolation (2.2) | `${'$'}` for a literal dollar sign |
| `kotlin.io.encoding.Base64`, `HexFormat` (2.2) | `java.util.Base64`, `java.util.HexFormat` (JDK 17) |
| nested type alias (2.3) | a top-level `typealias` |
| data-flow `when` exhaustiveness (2.3) | make the sealed value the `when` subject so the compiler checks it; no `else` that hides new cases |
| `kotlin.time.Clock`/`Instant` (2.3) | `java.time.Clock` and `java.time.Instant` |
| context parameters (2.4) | pass the dependency as an ordinary parameter; context receivers are deprecated, do not add them |
| explicit backing fields (2.4) | `private val _items = mutableListOf<Item>()` with `val items: List<Item> get() = _items` |
| `kotlin.uuid.Uuid` (2.4) | `java.util.UUID` |
| `@ConsistentCopyVisibility` default | annotate the data class, or hide the constructor behind a regular class with a factory |

## Replacement table

Old idioms to replace in new or touched code:

| Old | Modern |
|---|---|
| `kapt` with a processor that has a KSP version | KSP |
| `kotlin-android-extensions` synthetic views | view binding (Android; out of this skill's scope beyond the pointer) |
| `GlobalScope.launch` | a scope owned by a component, cancelled on shutdown |
| `runBlocking` inside server code | `suspend` all the way, or `withContext(Dispatchers.IO)` for blocking work |
| `ConflatedBroadcastChannel`, `BroadcastChannel` | `StateFlow`, `SharedFlow` |
| `kotlinx.coroutines.channels.actor` for state | `StateFlow.update { }` or a `Mutex` |
| `Pair`/`Triple` in public API | a named `data class` |
| `sealed class` with no shared state | `sealed interface` |
| `object` variants of a sealed type without `toString` | `data object` (1.9+) |
| `!!` after a Java call | annotate the Java side (JSpecify) or check at the boundary |
| context receivers (`context(Foo)` in the old experimental form) | context parameters (2.4+) or plain parameters |
