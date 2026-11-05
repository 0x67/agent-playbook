# Java and Kotlin Code Navigation

Loaded via `jvm` SKILL.md routing table. Text search misses overloads, inherited members, generic bridges, interface default methods, Lombok-generated members, annotation-driven wiring, and Kotlin names as Java sees them; a language server resolves most of them. Sources: Eclipse JDT.LS README, Kotlin LSP README (github.com/Kotlin/kotlin-lsp), the Claude Code `LSP` tool's operation list.

## Setup

- jdtls imports the project through the build: Gradle (Buildship) or Maven (m2e). The first start resolves dependencies and indexes the JDK, so expect a long wait on a large repo; results before the import finishes are partial.
- jdtls needs a JDK 17 or later to run. It compiles the project against the toolchain the build declares, so the build must sync (`./gradlew help` or `./mvnw -q validate` succeed) before results are trustworthy.
- kotlin-lsp (JetBrains) reads Gradle and Maven JVM projects. It is Alpha: treat an empty or odd result as "server unsure", not as "no usages".
- Claude Code: `jdtls-lsp` and `kotlin-lsp` plugins from `claude-plugins-official` serve them through the `LSP` tool. Install the servers first (`brew install jdtls`, `brew install JetBrains/utils/kotlin-lsp`). Other agents: their Java and Kotlin integrations.
- No server: say so, then use text search plus the compiler (`./gradlew compileJava compileTestJava`) as the check that every site was updated.

## Which operation

| Need | `LSP` operation | Fallback (state why) |
|---|---|---|
| where it is defined | `goToDefinition` | `fff-grep` the bare name, then `Read` |
| every use | `findReferences` | `fff-grep` the bare name, filter by hand |
| who calls this | `prepareCallHierarchy`, then `incomingCalls` | grep call sites |
| what this calls | `outgoingCalls` | read the body |
| type, signature, Javadoc | `hover` | `Read` the declaration |
| implementations of an interface or abstract method | `goToImplementation` | grep `implements`/`extends` plus the name |
| symbols in a file | `documentSymbol` | `Read` |
| find a symbol by name across the project | `workspaceSymbol` with `query` | `fff-grep` |

Diagnostics after edits are a hint; the build is the authority.

## Rules

1. `findReferences` before renaming, deleting, or changing what a symbol means. Grep is the fallback, never the plan.
2. Before changing a method signature (parameters, return type, checked exceptions, visibility, generics): `incomingCalls` for callers, then `findReferences` for the rest (method references `Foo::bar`, overrides, interface implementations, reflection). Update every site.
3. `hover` or `goToDefinition` before using an unfamiliar symbol. Overload resolution picks by static argument types, boxing, and varargs; never assume which overload a call binds to.
4. Overrides: changing an interface or superclass method touches every implementation. `goToImplementation` on the declaration, then check each.
5. Mixed Java/Kotlin: each server answers for its own language. After `findReferences`, text-search the other language for the JVM name too: Kotlin property `name` is `getName()`/`setName()` in Java (`isActive()` for `isActive`), companion members go through `Companion` unless `@JvmStatic`, top-level functions live in `FileNameKt` unless `@file:JvmName`, and `@JvmName` renames anything.
6. Invisible callers need text search: Spring and Jakarta wiring by annotation or name (`@Bean`, `@Value("${...}")`, `@ConfigurationProperties` prefixes), reflection, `ServiceLoader` (`META-INF/services`), serialization by field or property name (Jackson, JPA columns), and string names in YAML, XML, or SQL. Search those before a rename.
7. Lombok and other annotation processors generate members the source does not show. With jdtls the Lombok agent must be configured to see them; otherwise grep the field name and read the annotations.

## Positions

- `line` and `character` are 1-based. Take the line from `Read` output, confirm the symbol is on it, count the column. Never guess either.
- Absolute file paths.
- Empty result means no references only once the import has finished and the file is part of a source set; check that first.
- Query independent symbols in parallel.

## When text search is right

String literals, comments, log messages, YAML/properties keys, SQL, build scripts, Spring profiles, resource files, generated sources, and anything in a module the server did not import.
