# Concurrency Is Not Parallelism

If you've spent any time around backend engineering, you've heard someone use "concurrent" and "parallel" as if they were synonyms. They aren't, and the confusion costs teams real time: they reach for threads when they need better structure, or they restructure code when they just need more cores. Getting the distinction right changes how you design systems, how you debug them, and what you expect from them under load.

## Two Different Ideas

**Concurrency** is about *structure*. A concurrent program is composed of independently executing pieces of work that can make progress in overlapping time periods. It's a way of dealing with many things at once.

**Parallelism** is about *execution*. A parallel program literally runs multiple computations at the same instant, on multiple cores or machines. It's a way of doing many things at once.

A useful mental picture: a single barista at a coffee shop handling five orders is concurrent. She starts the espresso, steams milk while it pulls, takes the next order while the milk heats. Only one person is working, but the work is interleaved. Add a second barista and a second machine, and now you have parallelism as well. Concurrency was the design; parallelism is what the extra hardware lets you do with it.

You can have either without the other:

- **Concurrent, not parallel:** An event loop in Node.js or Python's `asyncio` on a single thread. Thousands of in-flight requests, one thread of execution.
- **Parallel, not concurrent:** A SIMD instruction or a GPU kernel applying the same operation across a big array. Lots of simultaneous execution, but one logical task with no independent pieces to coordinate.
- **Both:** A Go or Erlang service with many goroutines or processes scheduled across all available cores.
- **Neither:** A plain sequential script.

## Why the Distinction Matters

### Concurrency helps with waiting

Most services spend the majority of their time waiting on databases, caches, other services, and disks. Concurrency lets one worker use that idle time productively. If a request spends 90 ms of a 100 ms lifetime waiting on I/O, a single thread running a concurrent design can juggle dozens of those requests without any parallel hardware at all.

Adding cores to an I/O-bound service with a blocking, one-request-at-a-time design just gives you more idle cores.

### Parallelism helps with computing

If you're resizing images, encoding video, or running a large aggregation, the CPU is the bottleneck, not waiting. Here, a perfectly concurrent design on one core still gives you one core's worth of throughput. You need to split the work and run it simultaneously.

### They fail differently

Concurrency bugs are mostly about *coordination*: race conditions, deadlocks, lost updates, and ordering assumptions that hold in testing but not in production. Parallelism problems are mostly about *efficiency*: false sharing, uneven work distribution, memory bandwidth limits, and the serial fraction of your workload that Amdahl's law says will cap your speedup.

Knowing which category you're in tells you where to look. A flaky test is probably a concurrency issue. A service that doesn't get faster when you double the cores is probably a parallelism one.

## A Practical Example

Suppose an endpoint needs to fetch a user profile, their recent orders, and recommendations, each from a different service.

Written sequentially, latency is the *sum* of the three calls. Written concurrently, you issue all three requests and await them together, so latency approaches the *slowest* call. This works fine on a single thread, because the time is spent waiting on the network.

```python
async def get_dashboard(user_id):
    profile, orders, recs = await asyncio.gather(
        fetch_profile(user_id),
        fetch_orders(user_id),
        fetch_recommendations(user_id),
    )
    return render(profile, orders, recs)
```

Now suppose the endpoint also has to score ten thousand items with a CPU-heavy model. Concurrency won't help, because nothing is waiting. You'd move that work to a process pool or a worker fleet, which is parallelism.

## Rules of Thumb

1. **Profile before you pick a tool.** Is the workload waiting or computing? That one question usually settles the approach.
2. **Design for concurrency first.** Breaking a system into independent pieces with clear communication boundaries is valuable on its own, and it makes parallelism possible later.
3. **Treat parallelism as an optimization.** Add it where measurements show a CPU-bound bottleneck, and expect diminishing returns.
4. **Prefer communication over shared state.** Message passing, queues, and immutable data remove whole classes of concurrency bugs, whether or not you run in parallel.

## Closing Thought

Concurrency gives you a program that is *able* to handle many things at once. Parallelism gives you the hardware to *actually* do many things at once. Keep the two separate in your head and in your design reviews, and you'll make better decisions about both.
