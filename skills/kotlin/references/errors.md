# Kotlin Errors

Loaded via `kotlin` SKILL.md routing table. Sources: Kotlin language reference (exceptions, `Nothing`), standard library docs (`require`, `check`, `error`, `Result`, `runCatching`, `use`), kotlinx.coroutines exception-handling guide.

## Which mechanism

| Situation | Use |
|---|---|
| caller passed a bad argument | `require(cond) { "message with the value" }` (throws `IllegalArgumentException`) |
| object in the wrong state | `check(cond) { "..." }` (`IllegalStateException`) |
| unreachable branch, impossible state | `error("...")` (returns `Nothing`) |
| expected business outcome (declined, not found, insufficient funds) | `sealed interface` result, or a nullable return when "absent" is the only outcome |
| failure from I/O, network, or a library | exception, translated at your module boundary with the cause attached |
| Java callers must catch a checked exception | `@Throws(IOException::class)` on the function (`interop.md`) |

```kotlin
sealed interface Transfer {
    data class Done(val reference: String) : Transfer
    data class Rejected(val reason: RejectReason) : Transfer
}

fun transfer(from: AccountId, to: AccountId, amount: BigDecimal): Transfer {
    require(amount.signum() > 0) { "amount must be positive: $amount" }
    val account = accounts.find(from) ?: error("account $from vanished after validation")
    if (account.balance < amount) return Transfer.Rejected(RejectReason.INSUFFICIENT_FUNDS)
    return Transfer.Done(ledger.move(from, to, amount))
}
```

`when` over `Transfer` without `else` makes every caller handle a new outcome at compile time.

## Rules

- Kotlin has no checked exceptions, so nothing forces callers to handle failures. Document thrown exceptions in KDoc for public API, and prefer result types for outcomes callers must handle.
- Never swallow. An empty `catch` or one that only logs needs a comment saying why continuing is correct.
- Catch the narrowest type the block can handle. `catch (e: Exception)` only at a boundary (request handler, consumer loop, `main`) that logs once and maps.
- Chain causes: `throw StoreException("save order $id", e)`.
- Log or rethrow, not both.
- `Nothing`-returning helpers (`fail(...)`, `error(...)`) let the compiler narrow types after them; use that instead of `!!`.

## `Result` and `runCatching`

- `runCatching` catches every `Throwable`: `Error`s such as `OutOfMemoryError`, and `CancellationException`. In suspending code that breaks cancellation. Use it only around non-suspending calls, or rethrow cancellation:

  ```kotlin
  suspend fun fetchQuote(id: String): Quote? =
      try {
          client.quote(id)
      } catch (e: CancellationException) {
          throw e
      } catch (e: IOException) {
          log.warn("quote {} unavailable", id, e)
          null
      }
  ```

- `Result<T>` is fine as a local value. As a public return type it hides which failures can happen; a sealed result names them.
- `getOrThrow()` immediately after `runCatching` is a longer `try` with worse types; write the `try`.

## Resources

- `use { }` closes any `Closeable`/`AutoCloseable`, including on exceptions, and keeps the primary exception with the close failure suppressed.

  ```kotlin
  Files.newBufferedReader(path).use { reader ->
      reader.lineSequence().count { it.isNotBlank() }
  }
  ```

- Sequences from `lineSequence()` must be consumed inside the `use` block.

## Coroutines

- An exception in a `launch`ed child cancels its parent scope unless the scope uses a `SupervisorJob`/`supervisorScope`. Choose deliberately: one failed request should not cancel the server scope; one failed step of a transaction should cancel its siblings.
- `async` stores the exception until `await()`; an unawaited failed `async` still cancels its parent in a regular scope.
- `CoroutineExceptionHandler` only applies to root coroutines started with `launch`; it is a last-resort logger, not error handling.
- Details in `coroutines.md`.
