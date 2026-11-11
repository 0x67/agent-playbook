# Java Errors and Exceptions

Loaded via `java` SKILL.md routing table. Sources: Effective Java (3rd ed., chapter 10), JLS 14.20 (try statements), `java.lang.InterruptedException` and `Thread.interrupt` Javadoc.

## Which mechanism

| Situation | Use |
|---|---|
| caller bug: bad argument, wrong state | unchecked: `IllegalArgumentException`, `IllegalStateException`, `NullPointerException` via `Objects.requireNonNull`, `UnsupportedOperationException` |
| recoverable condition the caller must handle, and the repo uses checked exceptions | checked exception specific to the condition |
| expected business outcome (declined, not found, insufficient funds) | a return type: `Optional`, or a `sealed` result with one record per outcome |
| failure from a lower layer (I/O, SQL, HTTP) crossing your module boundary | translate to your layer's exception, cause chained |
| bug that must never happen | `throw new AssertionError(...)` or `IllegalStateException`; never `assert` for production checks (disabled by default) |

```java
sealed interface Withdrawal permits Withdrawal.Done, Withdrawal.Insufficient, Withdrawal.Frozen {
    record Done(Money balance) implements Withdrawal {}
    record Insufficient(Money available) implements Withdrawal {}
    record Frozen(String reason) implements Withdrawal {}
}
```

The caller's exhaustive `switch` then handles every outcome, and adding one breaks compilation at each site.

## Rules

- Never swallow. An empty `catch` or a `catch` that only logs and continues needs a comment saying why continuing is correct.
- Catch the narrowest type that the block can actually handle. `catch (Exception e)` or `Throwable` only at a boundary that logs and maps: the HTTP handler, the message listener, `main`, a thread's top frame.
- Chain causes: `throw new OrderStoreException("save order " + id, e);`. Never `new X(e.getMessage())`: it loses the stack and type.
- Log or rethrow, not both. The boundary that handles the failure logs it once with context.
- Messages carry the values that identify the failure (ids, sizes, states), never secrets or personal data.
- Validate at public boundaries: `Objects.requireNonNull(x, "x")`, `Objects.checkIndex(i, size)`, explicit `IllegalArgumentException` with the bad value.
- No exceptions for control flow (`try { parse } catch { default }` in a hot loop). Check first, or return a result type.
- `finally` never returns or throws; it would discard the original exception.
- Custom exceptions: few, named for the condition, extending the closest standard type. Unchecked unless the repo's convention is checked. Keep them serializable-safe (no non-serializable fields) only if they cross a serialization boundary.

## Resources

- Every `AutoCloseable` in try-with-resources. Resources close in reverse order; exceptions from `close()` attach as suppressed (`e.getSuppressed()`) instead of hiding the primary failure.

  ```java
  try (var lines = Files.lines(path, StandardCharsets.UTF_8)) {
      return lines.filter(l -> !l.isBlank()).count();
  }
  ```

- Streams from `Files.lines`, `Files.list`, `Files.walk`, and JDBC `ResultSet` hold OS or database resources; ordinary collection streams do not need closing.
- An object that owns a resource implements `AutoCloseable` and documents who closes it. `close()` is idempotent.
- Never rely on finalizers or `Cleaner` for correctness; finalization is deprecated for removal (18+).

## Interrupts

`InterruptedException` means someone asked this thread to stop. Either propagate it, or restore the flag and stop:

```java
try {
    queue.put(item);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new CancellationException("interrupted while enqueuing " + item.id());
}
```

Never catch it and continue as if nothing happened; that hangs shutdown.

## Checked exceptions and lambdas

Functional interfaces in `java.util.function` cannot throw checked exceptions. Options, in order: use a loop instead of a stream; wrap at the lambda edge in the layer's unchecked exception with the cause (`UncheckedIOException` for `IOException`); or declare a small functional interface that throws. Never `@SneakyThrows`-style rethrows in shared code.

## `main` and process exit

- `main` catches at the top, logs once, and exits non-zero: `System.exit(1)` only in `main` or a CLI entry point, never in library code.
- Uncaught exceptions on other threads go to the thread's `UncaughtExceptionHandler`; set one on executors you create (`Thread.ofPlatform().uncaughtExceptionHandler(...)` on 21+, a `ThreadFactory` before).
- Exceptions inside `ExecutorService.submit` tasks are captured in the `Future`; they are lost unless someone calls `get()`. Use `execute` for fire-and-forget work or always join the future.
