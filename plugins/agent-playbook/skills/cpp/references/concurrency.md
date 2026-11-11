# C++ Concurrency

Loaded via `cpp` SKILL.md routing table. Sources: C++ Core Guidelines (CP section), cppreference (thread support library, memory model, coroutines), ThreadSanitizer docs, Clang thread safety analysis docs.

## Rules

- A data race is undefined behavior. Every piece of shared mutable state is guarded by one mutex, is atomic, or stays on one thread. Say which in a comment next to the data.
- Share less: pass messages through queues, give each thread its own data, merge results at the end.
- Synchronous APIs by default; the caller adds threads. A library that starts threads says so in its docs.
- Every thread has an owner that joins it and a way to stop it. Never `detach()`: a detached thread outlives everything it references.

## Threads and stopping

```cpp
std::jthread worker([](const std::stop_token& st) {
    while (!st.stop_requested()) {
        process_one();
    }
});
// ~jthread requests stop, then joins
```

- `std::jthread` (C++20) joins on destruction and passes a `std::stop_token` when the callable accepts one.
- Blocking waits must be stoppable: `std::condition_variable_any::wait(lock, token, pred)`.
- Before C++20: `std::thread` owned by an RAII wrapper that joins, plus a `std::atomic<bool>` stop flag.
- Thread pools: use the repo's executor. No thread per task.
- `std::async` without `std::launch::async` may run lazily on `get()`, and the returned future's destructor blocks. Pass the policy explicitly or use the executor.

## Mutexes

- `std::scoped_lock lock(m);` (C++17) by default; with several mutexes it locks them without deadlock. `std::unique_lock` when you must unlock early or wait on a condition variable.
- Hold locks briefly. Never call unknown code (callbacks, virtual functions, user lambdas) while holding one.
- Nested locking needs a fixed, documented order.
- `std::shared_mutex` only when reads dominate and profiling shows contention on a plain mutex.
- Keep the mutex next to the data it guards, `mutable` when `const` members lock it. Clang thread safety annotations (`GUARDED_BY`, `REQUIRES`) with `-Wthread-safety` when the repo uses them.

## Condition variables

- Always wait with a predicate: `cv.wait(lock, [&] { return !queue.empty() || stopping; });`. Spurious wakeups happen.
- Change the condition while holding the mutex, then notify (after unlocking is fine).
- Higher-level primitives when they fit: `std::latch`, `std::barrier`, `std::counting_semaphore`, `std::atomic<T>::wait`/`notify_one` (all C++20).

## Atomics

- `std::atomic<T>` for single values: counters, flags, a pointer published once. Two values that must change together need a mutex.
- Default `memory_order_seq_cst`. Weaker orders only when profiling shows the cost and the happens-before argument is written in a comment: `release` stores paired with `acquire` loads; `relaxed` only for statistics nobody synchronizes on.
- `std::atomic_ref` (C++20) for atomic access to plain objects, such as array elements.
- Lock-free data structures come from a vetted library, never from a feature change.
- `volatile` is not synchronization.

## Coroutines

- C++20 ships the language feature only. Use the repo's task type (Asio `awaitable`, folly, cppcoro-style) or `std::generator` (C++23) for lazy sequences. Do not write a promise type inside a feature change.
- Reference parameters and reference captures dangle once the caller's frame is gone while the coroutine is suspended. Take coroutine parameters by value.
- `std::execution` (C++26 senders and receivers) only with compiler support and agreement from the repo.

## Shutdown

- Order: stop accepting work, request stop, drain or cancel queues, join, then destroy shared state.
- Statics are destroyed after `main` returns. Threads still running then touch destroyed objects. Join everything before leaving `main`.

## Checks

- ThreadSanitizer build (`-fsanitize=thread`, not combinable with ASan) for every test that touches concurrency.
- Repeat flaky-prone tests: `ctest --repeat until-fail:100 -R <name>`, and under TSan.
- Tests synchronize with latches, futures, or fake clocks, never with sleeps.
