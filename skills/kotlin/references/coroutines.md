# Kotlin Coroutines

Loaded via `kotlin` SKILL.md routing table. Sources: kotlinx.coroutines guide (coroutine context and dispatchers, cancellation and timeouts, exception handling, Flow, shared mutable state), kotlinx-coroutines-test docs.

## Structured concurrency

- Every coroutine runs in a scope owned by something with a lifecycle: a request, a component, a test. Cancelling the owner cancels the children.
- `coroutineScope { }` to fan out inside a suspending function and wait for all children; any child failure cancels the rest and rethrows.
- `supervisorScope { }` (or a `SupervisorJob`) when children fail independently, such as handlers in a long-lived server scope.
- Long-lived components hold one `CoroutineScope(SupervisorJob() + dispatcher)` and cancel it on shutdown.
- No `GlobalScope`. No `CoroutineScope(...)` created inside a function and dropped; nobody can cancel it.

```kotlin
suspend fun quotes(providers: List<QuoteProvider>, request: Request): List<Quote> =
    coroutineScope {
        providers.map { p -> async { p.quote(request) } }.awaitAll()
    }
```

## Dispatchers and blocking

| Work | Dispatcher |
|---|---|
| CPU-bound | `Dispatchers.Default` |
| blocking I/O (JDBC, `java.io`, blocking SDKs) | `withContext(Dispatchers.IO) { ... }` |
| bounded blocking resource | `Dispatchers.IO.limitedParallelism(n)` |
| UI or single-threaded confinement | the framework's main dispatcher |
| Java 21+, many blocking calls | `Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()`, closed on shutdown |

- Suspending functions are main-safe: a function that blocks wraps its own blocking part in `withContext`, so callers do not need to know.
- Never block `Dispatchers.Default` (it has one thread per core) or a single-threaded dispatcher.
- `runBlocking` only in `main`, tests, and bridges from blocking frameworks at the outermost edge.

## Cancellation

- Cancellation is cooperative: suspending calls from kotlinx.coroutines check it; tight CPU loops call `ensureActive()` or `yield()`.
- `CancellationException` is normal control flow. Catch it only to rethrow; `catch (e: Exception)` around suspending code must rethrow it first.
- Cleanup that must suspend after cancellation goes in `withContext(NonCancellable) { }` inside `finally`.
- Timeouts: `withTimeout` throws `TimeoutCancellationException`; `withTimeoutOrNull` returns null. Put them around the remote call, not around the whole request.

## Shared state

- Prefer confinement: one coroutine owns the state and others send it messages (`Channel`), or state lives in a `StateFlow` updated with `update { }`.
- `Mutex` for suspending critical sections; never `synchronized` or `ReentrantLock` held across a suspension point.
- Atomics (`java.util.concurrent.atomic` or `kotlinx.atomicfu`) for counters.

## Flow

- `Flow` is cold: nothing runs until `collect`. Each collector runs the producer again.
- `flowOn(dispatcher)` changes where upstream runs; never `withContext` inside a `flow { }` builder to emit from another context.
- `StateFlow` for current state with an initial value (conflated, equality-deduplicated); `SharedFlow` for events, with `replay` and buffer sized on purpose.
- `stateIn`/`shareIn` need a scope and a `SharingStarted` policy; `WhileSubscribed(5_000)` is a common choice for UI-driven sources.
- Operators: `map`, `filter`, `debounce`, `distinctUntilChanged`, `catch` (upstream only), `onCompletion`, `retryWhen` with backoff.
- Collect in the owner's scope; a `collect` never returns for an infinite flow, so launch it.

## Java interop and frameworks

- Java callers: expose `CompletableFuture` via `scope.future { }` or a blocking wrapper; `CompletableFuture.await()` goes the other way (both in kotlinx-coroutines-core on the JVM).
- Reactive Streams and Reactor: kotlinx-coroutines-reactive and -reactor (`Flow.asPublisher()`, `Mono.awaitSingle()`).
- Spring: `suspend` controller and repository methods and `Flow` return types are supported; `@Transactional` on suspending functions needs a reactive transaction manager (`jvm` skill, `services.md`).
- Ktor is coroutine-native: handlers are suspending; do not block in them.

## Testing

```kotlin
@Test
fun `retries once after a timeout`() = runTest {
    val client = FakeQuoteClient(failFirst = true)
    val service = QuoteService(client, retryDelay = 1.seconds)

    val quote = service.quote("EURUSD")

    assertEquals(2, client.calls)
    assertEquals(Quote("EURUSD", BigDecimal("1.0841")), quote)
}
```

- `runTest` from kotlinx-coroutines-test skips `delay`s with virtual time; the test above takes milliseconds.
- Inject dispatchers (constructor parameter with a default) so tests can pass a `StandardTestDispatcher(testScheduler)`; hard-coded `Dispatchers.IO` escapes virtual time.
- `advanceUntilIdle()`/`advanceTimeBy()` to drive scheduled work; `backgroundScope` for coroutines that outlive the test body.
- Turbine (`app.cash.turbine`) where the repo uses it for asserting `Flow` emissions.
