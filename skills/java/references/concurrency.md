# Java Concurrency

Loaded via `java` SKILL.md routing table. Sources: JEP 444 (virtual threads), JEP 491 (synchronize virtual threads without pinning), JEP 506 (scoped values), JEP 525/533 (structured concurrency previews), Java Concurrency in Practice, `java.util.concurrent` Javadoc.

## Choosing a model

| Work | Use |
|---|---|
| many blocking I/O tasks (HTTP, JDBC, files), 21+ | virtual threads: `Executors.newVirtualThreadPerTaskExecutor()` |
| CPU-bound parallel work | a fixed platform pool sized to cores, or parallel streams for pure, large, splittable data |
| periodic or delayed tasks | `ScheduledExecutorService` |
| async pipeline with composition | `CompletableFuture` with an explicit executor |
| fan out and wait for all, below 21 | `ExecutorService.invokeAll` on a bounded pool |
| producer and consumer | `BlockingQueue` (`ArrayBlockingQueue` bounded) |
| Kotlin code | coroutines (`kotlin` skill, `coroutines.md`) |

## Virtual threads (21+)

```java
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<Quote>> futures = providers.stream()
            .map(p -> executor.submit(() -> p.quote(request)))
            .toList();
    for (var f : futures) {
        quotes.add(f.get());
    }
}
```

- One virtual thread per task. Never pool them; a pool limits nothing useful and keeps `ThreadLocal`s alive.
- Limit concurrency against a scarce resource with a `Semaphore`, not with pool size. A connection pool still caps database concurrency.
- Pinning: on 21 to 23 a virtual thread blocked inside `synchronized` pins its carrier thread; on those releases use `ReentrantLock` around blocking calls in hot paths. 24+ (JEP 491) removes that pinning for `synchronized`. Native frames still pin.
- `ThreadLocal` works but each virtual thread gets its own copy; caches in `ThreadLocal` stop caching. Prefer `ScopedValue` (25+) for request context.
- CPU-bound work gains nothing from virtual threads.
- Spring Boot 3.2+: `spring.threads.virtual.enabled=true` switches the web server and task executors (`jvm` skill, `services.md`).

## Executors and shutdown

- `ExecutorService` is `AutoCloseable` from 19: try-with-resources waits for submitted tasks. Before 19, `shutdown()` then `awaitTermination` in `finally`, and `shutdownNow()` on timeout.
- Name threads (`Thread.ofPlatform().name("ingest-", 0).factory()` on 21+, a `ThreadFactory` before). Unnamed threads make dumps unreadable.
- Bounded queues for platform pools (`new ThreadPoolExecutor(..., new ArrayBlockingQueue<>(n), ...)`); `Executors.newFixedThreadPool` has an unbounded queue that hides overload until memory runs out.
- Every long-running loop checks `Thread.currentThread().isInterrupted()` or blocks interruptibly, so `shutdownNow` works.
- Application shutdown closes executors in dependency order; a JVM shutdown hook only for the outermost owner.

## `CompletableFuture`

- Always pass an executor to `*Async` methods. The default is the common `ForkJoinPool`, shared with parallel streams and sized for CPU work; blocking there starves everything.
- Handle failures where the chain ends: `exceptionally`, `handle`, or `whenComplete`; exceptions arrive wrapped in `CompletionException`, so unwrap `getCause()`.
- Timeouts: `orTimeout`/`completeOnTimeout` (9+).
- `join()` or `get()` only at the edge; blocking in the middle of a chain defeats it.

## Structured concurrency and scoped values

- `ScopedValue` is final in 25 (JEP 506): immutable per-scope context, inherited by structured child tasks, cheap with virtual threads.

  ```java
  static final ScopedValue<RequestContext> CONTEXT = ScopedValue.newInstance();

  ScopedValue.where(CONTEXT, ctx).run(() -> handle(request));
  // inside handle(...): CONTEXT.get()
  ```

- `StructuredTaskScope` is still a preview in 26 (sixth) and 27 (seventh) and its API changed between previews. Use it only when the build already enables preview features for that exact release; otherwise use an executor in try-with-resources.

## Shared state

- Prefer no sharing: confine mutable state to one thread, pass immutable messages.
- Shared mutable state needs one of: `final` fields set in the constructor (safe publication of immutable objects), `volatile` for a single flag or reference, `java.util.concurrent.atomic` for counters and single-variable compare-and-set, a lock for invariants across variables.
- Concurrent collections (`ConcurrentHashMap`, `CopyOnWriteArrayList`) make single operations atomic, not sequences: `if (!map.containsKey(k)) map.put(k, v)` races; use `putIfAbsent`/`computeIfAbsent`.
- `ConcurrentHashMap.computeIfAbsent` holds a bin lock while the function runs: keep the function short and never touch the same map from it.
- Lock order fixed and documented when code takes more than one lock. `tryLock` with timeout where a deadlock would be worse than a failure.
- `LongAdder` over `AtomicLong` for hot counters written by many threads.
- `SimpleDateFormat`, `HashMap`, `ArrayList`, and `StringBuilder` are not thread-safe. `DateTimeFormatter` is.

## Waiting

- No `Thread.sleep` loops to wait for a condition. `CountDownLatch`, `CompletableFuture`, `BlockingQueue.poll(timeout)`, or `Condition.await` with a timeout.
- `wait`/`notify` only inside existing low-level code; new code uses `java.util.concurrent`.

## Tests

- Data races hide in unit tests. Use `jcstress` for lock-free code, run concurrency tests many times, and give every wait a timeout so a deadlock fails instead of hanging CI.
- Inject the `Executor` and `Clock` so tests can run tasks inline and control time.
