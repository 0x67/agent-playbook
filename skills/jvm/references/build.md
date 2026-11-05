# JVM Build Tooling

Loaded via `jvm` SKILL.md routing table. Sources: Kotlin Gradle plugin and kotlin-maven-plugin docs, Gradle user guide (toolchains, compatibility matrix, version catalogs, dependency verification), Maven compiler and enforcer plugin docs, Error Prone installation docs, NullAway configuration wiki, gradle-errorprone-plugin README, Spotless README, google-java-format release notes.

## Gate (run in order, after every change)

```sh
./gradlew spotlessCheck                       # Maven: ./mvnw spotless:check
./gradlew test --tests 'com.example.FooTest'  # Maven: ./mvnw test -Dtest=FooTest
./gradlew build                               # Maven: ./mvnw verify
```

- Red: fix, rerun the whole gate. Report failures verbatim.
- Always the wrapper (`./gradlew`, `./mvnw`), never a global `gradle` or `mvn`: the wrapper pins the build tool version the repo tested.
- Multi-module: build the changed module and its dependents (`./gradlew :svc:build`, `./mvnw -pl svc -am verify`), then the whole build before reporting done on a shared module.
- `--offline` failing because a dependency is missing means the change added a dependency; say so.

## Gradle

Kotlin DSL (`build.gradle.kts`), version catalog in `gradle/libs.versions.toml`, convention plugins in `build-logic/` for multi-module repos.

```kotlin
import net.ltgt.gradle.errorprone.CheckSeverity
import net.ltgt.gradle.errorprone.errorprone

plugins {
    java
    alias(libs.plugins.spotless)
    alias(libs.plugins.errorprone)
}

java {
    toolchain { languageVersion = JavaLanguageVersion.of(21) }
}

dependencies {
    implementation(libs.jspecify)
    errorprone(libs.errorprone.core)
    errorprone(libs.nullaway)
    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testRuntimeOnly(libs.junit.platform.launcher)
    testImplementation(libs.assertj)
}

tasks.withType<JavaCompile>().configureEach {
    options.compilerArgs.addAll(listOf("-Xlint:all", "-Werror", "-parameters"))
    options.errorprone {
        disableWarningsInGeneratedCode = true
        check("NullAway", CheckSeverity.ERROR)
        option("NullAway:OnlyNullMarked", "true")
        option("NullAway:JSpecifyMode", "true")
    }
}

tasks.test { useJUnitPlatform() }

spotless {
    java {
        googleJavaFormat(libs.versions.googleJavaFormat.get())
        removeUnusedImports()
    }
}
```

- A toolchain compiles and tests with that exact JDK, so APIs above it cannot leak in. Building with a newer JDK for an older target: `options.release = N` instead.
- `-parameters` keeps parameter names in bytecode; Spring 6.1+ needs it for name-based binding (the Boot plugin adds it).
- `-Xlint:all` with `-Werror`: each JDK can add lint categories (21 added `this-escape`), so pin the CI JDK and fix new warnings when upgrading it. Turn off a category only with a reason (`-Xlint:all,-processing` when annotation processors trigger it).
- `implementation` by default, `api` only for types that appear in the module's public signatures (`java-library` plugin).
- Gradle runs on JVM 17 to 27 (Gradle 9.8). Run Gradle on a supported JVM and pick the project's JDK with the toolchain; `Version compatibility` below has which Gradle version each JDK needs.
- Dependency safety: `gradle/verification-metadata.xml` (`./gradlew --write-verification-metadata sha256 help`) and dependency locking for apps; validate the wrapper jar in CI.
- Configuration cache and build cache on for big repos (`org.gradle.configuration-cache=true`); new build logic must not resolve configurations at configuration time.

## Maven

```xml
<properties>
  <maven.compiler.release>21</maven.compiler.release>
  <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
</properties>

<build>
  <plugins>
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-compiler-plugin</artifactId>
      <configuration>
        <compilerArgs>
          <arg>-Xlint:all</arg>
          <arg>-parameters</arg>
        </compilerArgs>
        <failOnWarning>true</failOnWarning>
      </configuration>
    </plugin>
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-enforcer-plugin</artifactId>
      <executions>
        <execution>
          <id>enforce</id>
          <goals><goal>enforce</goal></goals>
          <configuration>
            <rules>
              <requireJavaVersion><version>[21,)</version></requireJavaVersion>
              <dependencyConvergence/>
              <banDuplicatePomDependencyVersions/>
            </rules>
          </configuration>
        </execution>
      </executions>
    </plugin>
  </plugins>
</build>
```

- Plugin versions pinned in `<pluginManagement>` (or inherited from a parent such as `spring-boot-starter-parent`); unpinned plugins change under you.
- Surefire runs unit tests in `test`; Failsafe runs `*IT` in `integration-test`/`verify`. `./mvnw verify` runs both.
- `dependencyManagement` with BOMs (`<scope>import</scope>`) instead of per-dependency versions.
- Maven 3.9 and 3.10 run on Java 8 or later; Maven 4 is still a release candidate (needs Java 17). Use what the wrapper pins.

## Kotlin and mixed Java/Kotlin modules

```kotlin
plugins {
    alias(libs.plugins.kotlin.jvm)
    java
}

kotlin {
    jvmToolchain(21)                      // same JDK and target for Java and Kotlin
    compilerOptions {
        allWarningsAsErrors = true
        freeCompilerArgs.add("-Xjsr305=strict")
    }
}
```

- One toolchain for both compilers. Mismatched `jvmTarget` and Java `targetCompatibility` fail the build by default (`kotlin.jvm.target.validation.mode`); fix the mismatch, never switch the check to `warning`.
- Kotlin and Java sources can live in `src/main/kotlin` and `src/main/java` of the same module. Kotlin compiles first and sees Java sources; Java then compiles against Kotlin output. Both directions of calls work within one module.
- `-Xjsr305=strict` turns JSR-305 annotations (common in Spring 5 and older libraries) into Kotlin nullability. JSpecify annotations are strict by default and need no flag.
- Maven: `kotlin-maven-plugin` with `<extensions>true</extensions>` derives `jvmTarget` from `maven.compiler.release` (Kotlin 2.4). For mixed sources, follow the Kotlin Maven docs so `kotlin:compile` runs before the Java compile and Java sees Kotlin classes.
- Spring: `kotlin("plugin.spring")` (all-open for `@Component`, `@Configuration`, `@Transactional` classes) and `kotlin("plugin.jpa")` (no-arg constructors for entities). Without them, proxies fail on Kotlin's final classes.
- Annotation processing: KSP for processors that support it; kapt generates Java stubs, slows builds, and the Kotlin docs point to KSP as the replacement. Lombok in a mixed module needs the Kotlin Lombok compiler plugin so Kotlin sees generated members, and it only covers part of Lombok; new code in that module avoids Lombok.

## Version compatibility

Oldest version of each tool that supports a target Java release. Every tool in the build must support the target, not only the JDK. Sources: Gradle compatibility matrix, Kotlin "What's new" pages, Lombok changelog, Spring Boot system requirements, Error Prone installation docs, JUnit user guide; checked 2026-11.

| Target release | Gradle (toolchain / runs Gradle) | Kotlin `jvmTarget` | Lombok | Notes |
|---|---|---|---|---|
| 17 | 7.3 / 7.3 | any 2.x | any current | JUnit 6 and Spring Boot 3 and 4 start here |
| 21 | 8.4 / 8.5 | 1.9.20 or later | 1.18.30 | Mockito inline mocks: attach as `-javaagent` (`testing.md`); Error Prone 2.43+ needs this JDK to run |
| 22 | 8.7 / 8.8 | 2.0 | | |
| 23 | 8.10 / 8.10 | 2.1 | | |
| 24 | 8.14 / 8.14 | 2.2 | | |
| 25 | 9.1.0 / 9.1.0 | 2.3 | 1.18.40 | |
| 26 | 9.4.0 / 9.4.0 | 2.4 | 1.18.46 | |
| 27 | 9.8.0 / 9.8.0 | check the Kotlin release notes | 1.18.48 | Spring Boot 4.1 tested up to 27 |

- Gradle 9.x runs only on JVM 17 or later; 8.14.x is the last line that runs on 8 to 16. The wrapper picks the Gradle version; the toolchain picks the compile JDK, and Gradle can download it (Foojay resolver plugin).
- Error Prone 2.42.0 was the last release that runs on JDK 17. Later versions need JDK 21 or later to run but still compile `--release 17` code.
- jdtls runs on JDK 17 or later.
- Kotlin rows come from each release's "What's new" page ("the compiler can generate classes containing Java N bytecode").

## Static analysis

| Tool | Catches | Notes |
|---|---|---|
| javac `-Xlint:all` | unchecked, deprecation, fallthrough, `this-escape` (21+) | always on |
| Error Prone | bug patterns at compile time | runs on JDK 21 or later (2.42.0 was the last for JDK 17); `--release` still targets older bytecode |
| NullAway | null dereferences | needs exactly one of `AnnotatedPackages` or `OnlyNullMarked`; `JSpecifyMode` for full JSpecify semantics, including generics |
| SpotBugs, PMD, Checkstyle | bytecode bugs, rule sets, style | follow the repo |
| detekt, ktlint | Kotlin smells and style | follow the repo; check the tool supports the repo's Kotlin version before upgrading Kotlin |
| OWASP dependency-check or OSV-Scanner | known-vulnerable dependencies | in CI |

The `net.ltgt.errorprone` Gradle plugin adds the `--add-exports` and `--add-opens` flags JDK 16+ needs. Maven: Error Prone's installation page lists the `.mvn/jvm.config` entries.

## Formatting

- Spotless runs the formatter; `spotlessApply` fixes, `spotlessCheck` gates. Maven: `spotless:apply`/`spotless:check`.
- Java: google-java-format or palantir-java-format, whichever the repo uses; pin the version. google-java-format 2.0 (2026-10) replaced its layout engine and adds a cleanup pass on by default, so upgrading from 1.x reformats a lot: do it in its own commit.
- Spotless loads the formatter reflectively, so a formatter newer than the Spotless release can fail on every file with `InvocationTargetException` (seen with google-java-format 1.37.0 on Spotless 8.11.0; 1.36.1 works). Upgrade the formatter and Spotless together and run `spotlessCheck` after.
- Kotlin: ktlint through Spotless (`kotlin { ktlint() }`, `kotlinGradle { ktlint() }`) or the ktlint Gradle plugin.
- Format only files you changed unless the repo formats everything (Spotless `ratchetFrom("origin/main")` limits it to changed files).

## Coverage

JaCoCo (`jacoco` plugin, `./gradlew jacocoTestReport`; Maven `jacoco-maven-plugin`). Use it to find untested branches in changed code, not to hit a number with assertion-free tests.

## CI skeleton

1. Wrapper validation (`gradle/actions/wrapper-validation` on GitHub Actions).
2. `./gradlew build` (or `./mvnw -B verify`) on the minimum supported JDK and the latest LTS the project supports.
3. Integration tests with Docker available for Testcontainers.
4. Formatter check, static analysis, and dependency vulnerability scan.
5. Publish test reports (`build/reports/tests`, `target/surefire-reports`) on failure.

## Install missing tools

```sh
mise use java@temurin-21          # or: sdk install java 21-tem; brew install openjdk@21
brew install jdtls                # Java LSP for the jdtls-lsp plugin
brew install JetBrains/utils/kotlin-lsp
./gradlew wrapper --gradle-version <version>   # upgrade the Gradle wrapper
mvn wrapper:wrapper                             # add a Maven wrapper to a repo without one
```
