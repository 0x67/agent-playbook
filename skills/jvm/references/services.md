# JVM Services

Loaded via `jvm` SKILL.md routing table. Covers Spring Boot (the common case), plain JDK services, and the Kotlin differences. Sources: Spring Boot reference (docs.spring.io/spring-boot, system requirements and JSON pages), Spring Framework reference (transactions, `RestClient`, `JdbcClient`), Hibernate ORM user guide.

## Versions

- Spring Boot 4.x: Java 17 or later (4.1 is tested up to Java 27), Spring Framework 7, Jackson 3 by default with Jackson 2 support deprecated. Boot 3.x: Java 17 or later, Jackson 2. Both use `jakarta.*`; `javax.persistence`/`javax.servlet` imports mean Boot 2, which is out of open-source support.
- Use the Boot BOM (`org.springframework.boot` plugin or `spring-boot-dependencies`) for managed versions; never pin a managed library without a comment why.
- Jackson 3 moves databind and core to `tools.jackson.*` packages. Upgrading a Boot 3 app to 4 touches every `ObjectMapper` import and custom serializer.

## Wiring

- Constructor injection, `final` fields, one constructor (no `@Autowired` needed). No field injection: it hides dependencies and blocks plain unit tests.
- A class with more than about five dependencies is doing several jobs; split it.
- `@Configuration` classes create beans that need setup; ordinary components use `@Component`/`@Service`/`@Repository` scanning.
- No `ApplicationContext.getBean` in business code.

## Configuration

- Typed config through `@ConfigurationProperties` on a record, validated at startup:

  ```java
  @ConfigurationProperties("payments.gateway")
  @Validated
  public record GatewayProperties(@NotNull URI baseUrl, @NotNull Duration timeout, @Positive int maxRetries) {}
  ```

  Register with `@ConfigurationPropertiesScan` or `@EnableConfigurationProperties`. No scattered `@Value("${...}")` for anything with more than one key.
- Secrets come from the environment or a secret manager, never from a committed `application.yml`. Profiles select config, not code paths.
- Defaults that differ per environment (timeouts, pool sizes) are explicit, not left to library defaults.

## Web layer

- Controllers translate HTTP to a service call and back; no business logic, no repositories.
- Request and response bodies are records, separate from JPA entities. Validate with `@Valid` and Jakarta Validation annotations.
- Errors map in one `@RestControllerAdvice` to `ProblemDetail` (RFC 9457) responses. Stack traces and SQL never reach the client.
- Every outbound call has connect and read timeouts. Spring: `RestClient` (Framework 6.1+, Boot 3.2+) for blocking calls, `WebClient` only in reactive apps. Outside Spring: `java.net.http.HttpClient` with `connectTimeout` and a per-request `timeout`.
- Retries only for idempotent operations, with backoff and a cap; a payment POST is not retried without an idempotency key.
- Virtual threads for blocking servers: `spring.threads.virtual.enabled=true` (Boot 3.2+, Java 21+).

## Transactions

- `@Transactional` on public service methods that need atomicity. It works through a proxy: calls from inside the same class (`this.save()`) skip it.
- Rollback is automatic for unchecked exceptions and `Error`, not for checked exceptions; add `rollbackFor` when a checked exception must roll back.
- `@Transactional(readOnly = true)` on query paths.
- No remote calls, message sends, or long computations inside a transaction; they hold connections and locks. Publish events after commit (`@TransactionalEventListener(phase = AFTER_COMMIT)` or an outbox table).
- Isolation and locking explicit where money or counters change: optimistic `@Version` on entities, or `SELECT ... FOR UPDATE` through a pessimistic lock where contention is expected.

## Persistence

- Schema changes through migrations (Flyway or Liquibase) committed with the code. `spring.jpa.hibernate.ddl-auto` is `validate` or `none` outside throwaway local setups.
- `spring.jpa.open-in-view=false`, so lazy loading cannot run SQL during view rendering.
- JPA entities: mutable classes with a protected no-arg constructor; records cannot be entities but work as query projections and DTOs. `@ManyToOne` and `@OneToOne` default to eager fetching; set `fetch = FetchType.LAZY`.
- N+1 queries: fetch joins, `@EntityGraph`, or a projection query for the screen; check the SQL log (`spring.jpa.show-sql` locally, or Hibernate statistics) for repeated selects.
- Entity `equals`/`hashCode` on a stable business key or the id with care for transient instances; never on all fields, never Lombok `@Data` on entities.
- Plain SQL: `JdbcClient` (Framework 6.1+) or `JdbcTemplate` with bound parameters. Never concatenate values into SQL.
- Paginate every list endpoint; unbounded `findAll()` is an outage waiting for data growth.

## JSON

- Records serialize and deserialize with Jackson 2.12+ and 3.x without annotations.
- Field names in the API contract are explicit (`@JsonProperty`) when renaming a Java field must not change the wire format.
- Money as string or integer minor units in JSON, never a float. Dates as ISO-8601 (`java.time` types with the JSR-310 module, built into Jackson 3).

## Kotlin services

- Spring with Kotlin needs the all-open and no-arg compiler plugins (`plugin.spring`, `plugin.jpa`; `build.md`). Constructor injection is the primary constructor; `@ConfigurationProperties` binds to a data class.
- JSON: Jackson needs `jackson-module-kotlin` for data classes without a no-arg constructor (Spring Boot picks it up from the classpath), or use kotlinx.serialization with `@Serializable`. One JSON library per service.
- JPA entities are regular classes, not data classes: generated `equals`/`hashCode` over all fields breaks with lazy loading and generated ids.
- Ktor: coroutine-native server and client. The same rules apply: timeouts on every client call, validation at the edge, one place that maps errors to responses (`StatusPages`).
- Suspending controllers and repositories: `kotlin` skill, `coroutines.md`.

## Logging and observability

- SLF4J API, Logback in Boot by default. Structured logs: `logging.structured.format.console` (Boot 3.4+) with `ecs` or `logstash`.
- Log events with ids and outcomes at the boundary; no request or response bodies that may hold personal data or secrets.
- Actuator: expose `health` and `info` publicly at most; metrics and env endpoints behind auth or a management port.
- Metrics and traces through Micrometer; propagate trace context on outbound calls by using the auto-configured `RestClient.Builder`/`WebClient.Builder` beans, not `new RestTemplate()`.

## Security

- Spring Security defaults stay on unless there is a reason in a comment: CSRF off only for stateless token APIs.
- Passwords through `PasswordEncoderFactories.createDelegatingPasswordEncoder()` or an explicit Argon2/BCrypt encoder.
- Authorization checks in the service or with method security, not only in URL patterns.
- Inputs that reach SQL, shell, file paths, or templates are validated and parameterized; deserialization of untrusted data never uses polymorphic default typing.
