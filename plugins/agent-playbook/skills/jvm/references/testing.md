# JVM Testing

Loaded via `jvm` SKILL.md routing table. Sources: JUnit user guide (docs.junit.org), AssertJ docs, MockK and Kotest docs, kotlinx-coroutines-test docs, Mockito Javadoc (section 0.3, inline mocking on Java 21+), Testcontainers docs, ArchUnit user guide.

## Stack

| Need | Default | Notes |
|---|---|---|
| framework | JUnit Jupiter | JUnit 6 needs Java 17 at runtime; 5.x for repos that still test on older JDKs |
| assertions | AssertJ | `assertThat(x).isEqualTo(y)`; readable failures, fluent collection checks |
| doubles | hand-written fakes first; Mockito for collaborators you cannot fake cheaply | |
| real databases, brokers, HTTP dependencies | Testcontainers | containers per test class or shared via a singleton |
| architecture rules | ArchUnit | layer and dependency rules as tests |
| property-based | jqwik | parsers, codecs, arithmetic |
| coverage | JaCoCo | a signal, not a gate target to game |

Follow the repo's stack when it differs (TestNG, Hamcrest, Spock, Kotest).

The platform is shared: JUnit runs Java and Kotlin tests alike, and Gradle and Maven run them the same way. The language changes the doubles and some assertions; see `Kotlin tests` below.

## Structure

- Test class mirrors the class under test (`InvoiceServiceTest`), same package, `src/test/java`. Integration tests in their own source set or named `*IT` for Failsafe.
- Method names state the behavior: `rejectsWithdrawalAboveBalance()`, or `@DisplayName` when the repo uses it.
- Arrange, act, assert, separated by blank lines. One behavior per test; several assertions about that behavior are fine (`assertSoftly` or chained AssertJ).
- Package-private test classes and methods (JUnit 5+ needs no `public`).

```java
class MoneyTest {

    @Test
    void addsAmountsInSameCurrency() {
        var eur = Currency.getInstance("EUR");

        var total = new Money(new BigDecimal("1.10"), eur).plus(new Money(new BigDecimal("2.05"), eur));

        assertThat(total).isEqualTo(new Money(new BigDecimal("3.15"), eur));
    }

    @Test
    void rejectsMixedCurrencies() {
        var eur = new Money(BigDecimal.ONE, Currency.getInstance("EUR"));
        var usd = new Money(BigDecimal.ONE, Currency.getInstance("USD"));

        assertThatThrownBy(() -> eur.plus(usd))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("currency mismatch");
    }
}
```

## Parameterized and data-driven

- `@ParameterizedTest` with `@CsvSource`, `@MethodSource`, or `@EnumSource` instead of copy-pasted tests.
- Name cases (`@ParameterizedTest(name = "{0} -> {1}")`) so failures say which row broke.

## Doubles

- Fake the boundary you own (repository interface, clock, ID generator) with a small in-memory implementation. Fakes keep tests honest about behavior; mocks pin implementation details.
- Mockito: stub what the code under test reads, verify only calls that are the behavior (an event published, a message sent). A test whose only assertion is `verify(x).call()` against a mock it also stubbed tests nothing.
- No mocking of value types, records, or the class under test. `@Spy` and partial mocks signal a class that wants splitting.
- Java 21+ and Mockito's inline mock maker: the JDK warns about dynamically loaded agents (JEP 451) and a future release will refuse them. Attach Mockito as `-javaagent` in the test task, per Mockito's Javadoc:

  ```kotlin
  // build.gradle.kts
  val mockitoAgent = configurations.create("mockitoAgent")
  dependencies {
      testImplementation(libs.mockito)
      mockitoAgent(libs.mockito) { isTransitive = false }
  }

  abstract class MockitoAgentProvider : CommandLineArgumentProvider {
      @get:InputFiles
      @get:PathSensitive(PathSensitivity.RELATIVE)
      abstract val agentJar: ConfigurableFileCollection

      override fun asArguments(): Iterable<String> = listOf("-javaagent:${agentJar.asPath}")
  }

  tasks.test {
      jvmArgumentProviders.add(objects.newInstance<MockitoAgentProvider>().apply { agentJar.from(mockitoAgent) })
  }
  ```

  Maven: `maven-dependency-plugin` goal `properties`, then Surefire `<argLine>@{argLine} -javaagent:${org.mockito:mockito-core:jar}</argLine>`.

## Kotlin tests

- JUnit Jupiter with `kotlin.test` assertions or AssertJ; Kotest (specs, property testing) where the repo uses it.
- MockK instead of Mockito for Kotlin code: Kotlin classes are final by default, and MockK handles `object`s, extension functions, and `suspend` functions (`coEvery`, `coVerify`). `mockito-kotlin` only in repos already on Mockito.
- Coroutines: `runTest` from kotlinx-coroutines-test with virtual time, dispatchers injected (`kotlin` skill, `coroutines.md`).
- Backtick test names (`` fun `rejects withdrawal above balance`() ``) are fine on the JVM.
- Spring with Kotlin: SpringMockK (`@MockkBean`) where the repo uses MockK with Spring tests.

## Time, randomness, concurrency

- Inject `Clock`; tests use `Clock.fixed(...)` or a mutable test clock. No `Thread.sleep` to wait for time to pass.
- Seed random sources the test controls; print the seed on failure.
- Async code: inject an executor that runs inline, or await with a timeout (Awaitility), never a bare sleep.

## Integration tests

- Testcontainers for the real database or broker the code runs against; H2 or an in-memory substitute hides dialect, locking, and transaction differences.
- Reuse one container per test class (`@Container static`) or one per JVM; truncate tables between tests instead of restarting.
- Spring: `@SpringBootTest` only for wiring and end-to-end paths; slice tests (`@WebMvcTest`, `@DataJpaTest`, `@JsonTest`) for one layer; plain unit tests for logic. `@ServiceConnection` (Boot 3.1+) wires Testcontainers without property plumbing.
- Docker unavailable: say the integration tests did not run; never mark them skipped and report green.

## What not to test

- Generated members: record accessors, `equals`/`hashCode`/`toString`, Lombok getters and setters.
- Framework behavior: that Spring injects a bean, that Jackson serializes a field with default settings.
- Private methods directly; test them through the public behavior that needs them.

## Running

```sh
./gradlew test --tests 'com.acme.billing.MoneyTest'   # one class
./gradlew test --tests '*MoneyTest.rejects*'          # pattern
./mvnw test -Dtest='MoneyTest#rejects*'                # Maven
./gradlew test --rerun                                 # force rerun of up-to-date tests
```

Flaky test: find the shared state, time, or ordering dependency and fix it. `@Disabled` needs an issue reference and the reason.
