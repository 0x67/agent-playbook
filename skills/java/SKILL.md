---
name: java
description: >
  Idiomatic modern Java (17 and later): writing, reading, reviewing,
  refactoring, and testing Java code (.java) in Java-only or mixed
  Java/Kotlin repos. Use whenever the user works in Java or asks anything
  involving records, sealed types, pattern matching, switch expressions,
  virtual threads, executors, streams, Optional, nullness, JSpecify,
  exceptions, try-with-resources, generics, Lombok, or a Java release (17,
  21, 25, 26, 27). Trigger even when "Java" is not said but files are
  clearly Java. Language rules live here; builds (Gradle, Maven), JUnit,
  Mockito, Spring, profiling, and code navigation come from the `jvm`
  skill. Core rules inline; specialist rules load through the routing
  table below.
---

# Java engineering skill

Write Java a careful maintainer would merge without comment: immutable data, explicit nullness, exceptions handled at the layer that can act, every resource closed by try-with-resources, zero compiler warnings, and tests that fail for real bugs. The repo's `--release` level is the ceiling, the way `go.mod` and `rust-version` are.

Build tools, the test platform, frameworks, and runtime profiling are JVM concerns shared with Kotlin: load skill `jvm` (`ai-setup:jvm` in Claude Code) for those. Kotlin files in the same repo follow skill `kotlin`.

## Routing table (mandatory)

Read matching reference BEFORE writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| naming, packages, classes, records, enums, sealed types, generics, nullness, `Optional`, immutability, `equals`/`hashCode`, streams, comments, Javadoc | `references/style.md` |
| exceptions, checked vs unchecked, try-with-resources, interrupts, result types, failure logging | `references/errors.md` |
| threads, virtual threads, executors, `CompletableFuture`, locks, atomics, `ThreadLocal`, `ScopedValue`, shutdown | `references/concurrency.md` |
| choosing features for a given `--release`, preview features, fallbacks on older releases, migrating old idioms | `references/modern.md` |
| Gradle or Maven, JUnit, Mockito, Testcontainers, Spring Boot, JPA, profiling, LSP navigation | skill `jvm` |
| calling Kotlin from Java | skill `kotlin`, `references/interop.md` |

Multiple matches: read all matched. Unsure: read `style.md` and `errors.md`.

## Before writing

1. Find the release: Gradle `java { toolchain { languageVersion = JavaLanguageVersion.of(N) } }` or `options.release`; Maven `maven.compiler.release` or `<release>` on `maven-compiler-plugin`. `.java-version`, `.sdkmanrc`, and `mise.toml` name the JDK, not the release. Never use an API or syntax above the release; `references/modern.md` lists what each one unlocks. Preview features only when the build already passes `--enable-preview`.
2. Check repo conventions: formatter, static analysis (Error Prone, NullAway, Checkstyle, SpotBugs), nullness annotations (JSpecify, JSR-305, Spring's), Lombok, logging, DI framework, existing helpers. Repo convention beats these defaults.
3. Find the existing class and module for the change. New class only for a new concern; new module only for a new component.

## Non-negotiables

- Zero new compiler warnings (`-Xlint:all`; `-Werror` where the build has it). `@SuppressWarnings` only on the narrowest declaration, with a comment saying why it is sound.
- Compile against the release with `--release N` or a toolchain, never `-source`/`-target` alone: those let newer JDK APIs leak in.
- Nullness explicit. Follow the repo's annotations; new code in an unannotated repo uses JSpecify (`@NullMarked` package, `@Nullable` where null is allowed). Return empty collections, never `null`. `Optional` only as a return type for "may be absent", never as a field, parameter, or collection element. `Objects.requireNonNull` on public arguments that must not be null.
- Immutable by default: `record` for data carriers, `final` fields, `List.copyOf`/`Map.copyOf` for defensive copies, unmodifiable collections out. Mutable state only where it pays, and confined.
- Classes `final` unless designed for extension; `sealed` for closed hierarchies; composition over inheritance.
- Every `AutoCloseable` in try-with-resources: `Files.lines`/`Files.list` streams, JDBC objects, `ExecutorService` (19+), `HttpClient` (21+). Locks released in `finally`.
- Exceptions never swallowed. Catch `Exception` or `Throwable` only at a top-level boundary that logs and maps. Chain the cause. Restore the interrupt flag on `InterruptedException`. No exceptions for control flow.
- `switch` over enums and sealed types exhaustive without `default` (21+ patterns), so a new case breaks compilation instead of falling through.
- `java.time` only, never `Date`, `Calendar`, or `SimpleDateFormat`; inject a `Clock` where time drives logic. Money and exact decimals in `BigDecimal` built from a `String` or `BigDecimal.valueOf`, never `new BigDecimal(double)` or `double`; compare with `compareTo`.
- No raw types. No unchecked cast without a comment saying why it is sound. Public APIs take interfaces (`List`, `Map`) and the widest wildcard that works (`? extends` for inputs, `? super` for sinks).
- Logging through the repo's facade (SLF4J usually), parameterized (`log.info("loaded {}", id)`). No `System.out` or `printStackTrace` in production code. Never log secrets or personal data.
- Comments: plain humanizer prose, why not what, no plan/task ids, no em dash. Javadoc on every public type and method of a library API, stating nullness, thread safety, and thrown exceptions where not obvious.
- Tests must fail from a project bug. No getter/setter echo, no tests of record or Lombok generated members, no mock-call-count-only.

## After writing (gate, in order)

```sh
./gradlew spotlessCheck                       # or: ./mvnw spotless:check, or the repo's formatter check
./gradlew test --tests 'com.example.FooTest'  # fast loop; Maven: ./mvnw test -Dtest=FooTest
./gradlew build                               # compile (lint, Error Prone), all tests, check tasks; Maven: ./mvnw verify
```

Use the repo's tasks and modules. Not done until gate green. Report failures verbatim. Build setup, compiler flags, static analysis, and test libraries: skill `jvm`.

## Tool preference

- Definitions, references, call hierarchy, hover: `LSP` tool backed by jdtls (`jdtls-lsp` plugin in Claude Code) when exposed. Rules in the `jvm` skill's `references/navigation.md`.
- Exact text search: `mcp__fff__grep`/`rg` for strings, annotations, config keys. Semantic: Semble.
- JDK API and the release that added it: the Javadoc for that release (`docs.oracle.com/en/java/javase/<N>/docs/api/`, the "Since" line). Libraries: their docs or sources jar. Never guess a signature.
- Global rules still apply: Code Growth Discipline, Code Simplicity Discipline, Useless Test Ban, terminology guard (`snapshot`/`expected`, never `golden`). Cross-language naming, function size, and architecture: skill `software-design`.
