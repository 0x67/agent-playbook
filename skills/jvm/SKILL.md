---
name: jvm
description: >
  JVM platform engineering shared by Java and Kotlin: Gradle and Maven
  builds (wrappers, toolchains, version catalogs, multi-module, mixed
  Java/Kotlin modules), compiler flags and static analysis (Error Prone,
  NullAway, Spotless, ktlint, detekt), the test platform (JUnit, AssertJ,
  Mockito, MockK, Kotest, Testcontainers, coverage), Spring Boot and other
  services (configuration, HTTP, JDBC, JPA, transactions, Jackson,
  logging), runtime performance (JFR, JMH, GC, heap, AOT cache), version
  compatibility between JDK and tools, and code navigation with jdtls and
  kotlin-lsp. Use whenever the user touches pom.xml, build.gradle(.kts),
  settings.gradle(.kts), gradle.properties, gradle/libs.versions.toml,
  runs ./gradlew or ./mvnw, writes or runs JVM tests, or works on a Spring
  or Ktor service. Pair with skill `java` or `kotlin` for language rules.
---

# JVM platform skill

Java and Kotlin are different languages on one platform. This skill owns what they share: how the code is built, tested, wired into a service, run, and navigated. Language idioms live in skill `java` and skill `kotlin`; load the one for the files you touch (both in a mixed module).

## Routing table (mandatory)

Read matching reference BEFORE writing code or build changes. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| finding definitions, references, callers; rename; signature change; mixed Java/Kotlin usages | `references/navigation.md` |
| Gradle, Maven, toolchains, compiler flags, Kotlin Gradle plugin, mixed modules, Error Prone, NullAway, Spotless, ktlint, detekt, dependencies, JDK and tool version compatibility, CI | `references/build.md` |
| any test, JUnit, AssertJ, Mockito, MockK, Kotest, Testcontainers, Spring test slices, coverage | `references/testing.md` |
| Spring Boot, Ktor, dependency injection, configuration, HTTP clients and servers, JDBC, JPA/Hibernate, transactions, JSON, logging, security | `references/services.md` |
| JMH, JFR, profiling, GC, heap sizing, containers, allocation, startup, AOT cache | `references/performance.md` |

Multiple matches: read all matched.

## Before changing a build

1. Use the wrapper (`./gradlew`, `./mvnw`); never a globally installed `gradle` or `mvn`. The wrapper pins the build tool the repo tested.
2. Find the JDK target (toolchain or `release`) and the Kotlin version if any. Every tool must support both: the version compatibility table in `references/build.md`.
3. Find where versions live: `gradle/libs.versions.toml`, a BOM, a parent POM, `build-logic/` convention plugins. Change versions there, not inline.
4. No new dependency or plugin without the user's agreement. Prefer what the JDK, Kotlin standard library, or an existing dependency already provides.

## Non-negotiables

- Zero compiler warnings in both compilers (`-Xlint:all` for javac, `allWarningsAsErrors` for Kotlin where the build sets it).
- Java and Kotlin in one module share one toolchain and target; mismatches are fixed, never downgraded to warnings.
- Versions pinned: plugins, dependencies, formatters, static analysis tools. No dynamic versions (`+`, `latest.release`, `RELEASE`).
- Tests run through the build (`./gradlew test`, `./mvnw test`), not only from an IDE. Integration tests that need Docker report "not run" when Docker is missing, never green.
- Secrets never in build files, `gradle.properties` in the repo, or test resources.
- Generated sources (KSP, annotation processors, OpenAPI, protobuf) are not edited by hand.

## Gate (run in order, after every change)

```sh
./gradlew spotlessCheck                       # Maven: ./mvnw spotless:check; or ktlintCheck/detekt for Kotlin
./gradlew test --tests 'com.example.FooTest'  # Maven: ./mvnw test -Dtest=FooTest
./gradlew build                               # Maven: ./mvnw verify
```

Multi-module: build the changed module and its dependents (`./gradlew :svc:build`, `./mvnw -pl svc -am verify`), then the whole build before reporting done on a shared module. Integration tests (Gradle `integrationTest`, Maven Failsafe under `verify`) run when the change touches what they cover, or the report says they were not run. Not done until gate green. Report failures verbatim.

## Tool preference

- Navigation: `LSP` tool with jdtls (`jdtls-lsp`) for `.java` and kotlin-lsp (`kotlin-lsp`) for `.kt`/`.kts`; each answers for its own language, so cross-check the other with text search (`references/navigation.md`).
- Build facts: `./gradlew dependencies --configuration runtimeClasspath`, `./gradlew dependencyInsight --dependency <name>`, `./mvnw dependency:tree`, `./gradlew help --task <task>`. Run them instead of guessing what the build resolves.
- Tool versions and compatibility: each tool's release notes; the table in `references/build.md` was checked 2026-11.
- Global rules still apply: Code Growth Discipline, Code Simplicity Discipline, Useless Test Ban. Architecture choices for services: skill `software-design`.
