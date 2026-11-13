# Concurrency is not parallelism

"Concurrency" and "parallelism" get used interchangeably in standups, design docs, and code reviews. They describe different things, and mixing them up leads to real mistakes: the wrong tool for a performance problem, a misread benchmark, or a race condition someone was sure "couldn't happen on one core."

Rob Pike drew the distinction in a 2012 talk that gave this post its title:

> Concurrency is about *dealing* with lots of things at once. Parallelism is about *doing* lots of things at once.

Concurrency is a property of how a program is **structured**. Parallelism is a property of how it **executes**.

## A coffee shop analogy

Picture one barista with a line of customers. She takes an order, starts the espresso, steams milk for the previous order while the shot pulls, and rings up the next customer while the milk heats. She is only ever doing one thing at a given instant, yet several orders are in progress. That's concurrency: one worker interleaving independent tasks so nobody waits on idle time.

Now hire a second barista with a second espresso machine. Two drinks are being made at the same moment. That's parallelism.

Hiring the second barista helps only if the work can be divided. If every order must go through a single register, the second barista mostly stands around. Parallelism depends on a concurrent structure underneath it.

## What it looks like in code

Here is a Go function that fetches a list of URLs:

```go
func fetchAll(urls []string) []Result {
    results := make(chan Result, len(urls))
    for _, u := range urls {
        go func(u string) {
            results <- fetch(u)
        }(u)
    }

    out := make([]Result, 0, len(urls))
    for range urls {
        out = append(out, <-results)
    }
    return out
}
```

This code is concurrent. Each fetch is an independent unit of work, and the program says so explicitly. Whether those goroutines run in parallel is up to the runtime and the hardware. Run it with `GOMAXPROCS=1` and it still finishes in roughly the time of the slowest request rather than the sum of all of them, because almost all of that time is spent waiting on the network. One core is enough to keep a hundred requests in flight.

The same reasoning explains why Node.js can serve heavy traffic on a single-threaded event loop, and why Python's `asyncio` is useful even though it runs on one thread. Neither one gives you parallelism. They give you a way to avoid idle time while you wait.

## Why the distinction matters

**It tells you which tool fits.** Ask first whether the workload is I/O-bound or CPU-bound.

- **I/O-bound** work (HTTP calls, database queries, file reads) spends most of its time waiting. Concurrency is the fix. More cores do little because the CPU isn't the bottleneck.
- **CPU-bound** work (image processing, compression, number crunching) spends its time computing. Interleaving tasks on one core doesn't help, because there's no idle time to reclaim. You need parallelism: more cores doing work simultaneously.

Python makes this easy to see. In the default CPython build, the Global Interpreter Lock lets only one thread execute Python bytecode at a time. Threads still help for I/O-bound work, since the lock is released while waiting, but they won't speed up a CPU-bound loop. For that you use `multiprocessing`, a native extension that releases the lock, or the newer free-threaded builds.

**Race conditions come from concurrency, not parallelism.** A common and dangerous assumption is that a single-core machine or a single-threaded runtime makes shared state safe. It doesn't. A preemptive scheduler can switch threads between a read and a write on one core. In `async` code, any `await` is a point where another task can run and change the state you just checked:

```python
async def withdraw(account, amount):
    if account.balance >= amount:      # check
        await audit_log(account, amount)  # another task may run here
        account.balance -= amount      # act on stale information
```

There's no parallelism here at all, and this is still a check-then-act bug. If tasks can interleave, you need to think about synchronization.

**It changes how you read benchmarks.** If a service gets faster when you add cores, it was CPU-bound and structured to parallelize. If it doesn't, the cause could be I/O, lock contention, or a serial bottleneck like that single register. Knowing which one you're dealing with saves a lot of guessing.

## Practical takeaways

1. **Design for concurrency first.** Break work into independent pieces with clear communication between them. Good structure makes parallelism possible later and makes the code easier to follow now.
2. **Profile before you parallelize.** Find out whether you're waiting or computing before you reach for thread pools or extra instances.
3. **Assume interleaving.** If two tasks can be in progress at once, treat shared mutable state as a hazard, whatever the core count.
4. **Use the vocabulary precisely.** "This endpoint is slow because the calls run sequentially" and "this job is slow because it only uses one core" describe different problems with different fixes.

Concurrency is a way to structure a program. Parallelism is one of the things that structure makes possible. Keeping the two separate in your head makes it easier to choose the right fix for a slow system.
