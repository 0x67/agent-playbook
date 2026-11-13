# Go: one year ago today

One year ago today, at 2:47 on a Thursday afternoon, we switched production traffic to our first Go service. It was the event ingestion gateway, which sits in front of everything else and handles roughly 40,000 requests per second at peak. If it went down, so did we. It wasn't a low-stakes place to try a new language.

Twelve months later, we run 14 Go services in production, three teams write Go as their primary language, and the ingestion gateway hasn't paged anyone since February. This post looks back at why we made the bet, what paid off, what went wrong, and what we'd tell a team considering the same move.

## Why we reached for Go

Our backend was (and largely still is) Python. Python has served us well, and nothing here is an argument against it. But the ingestion path had specific problems. We were scaling horizontally to absorb load that was mostly waiting on I/O. Our p99 latency was unpredictable under burst traffic. And each instance needed close to a gigabyte of memory before it handled a single request.

We evaluated a few options. Go won for practical reasons:

- New hires could read the language within a week.
- Concurrency is built into the language.
- Each service compiles to a single static binary.
- The standard library is good enough that we didn't need a framework to build an HTTP server.

## What paid off

**Operational simplicity.** Our Go container images are around 20 MB. There's no runtime to install, no dependency resolution at deploy time, and services start almost immediately. Our platform team noticed this before anyone else did.

**Predictable performance.** After the cutover, p99 latency on the gateway dropped from about 410 ms to 35 ms, and we went from 48 instances to 9. Some of that came from the rewrite itself, since we fixed old design mistakes along the way. But goroutines and a lightweight runtime made it easy to handle many concurrent connections without contorting the code.

**Tooling that ends arguments.** `gofmt` settled formatting debates permanently. `go test`, the race detector, and `pprof` ship with the toolchain, so engineers actually profile their code instead of planning to. In our second month, we tracked down a lock contention issue in about twenty minutes using a flame graph and no new dependencies.

## What went wrong

**Goroutine leaks.** Starting a goroutine is easy, but making sure it stops is your job. In month three we shipped a worker that blocked forever on a channel nobody would write to again. Memory climbed slowly over four days. The fix was simple. The lesson was to give every `go` statement a clear exit path, usually through `context.Context`.

**Errors without context.** `if err != nil` is explicit, and we've come to appreciate that. Early on, though, people returned errors unchanged, and our logs filled with "connection refused" with no hint of where it came from. Wrapping errors with `fmt.Errorf("...: %w", err)` is now a code review requirement.

**The nil interface trap.** An interface holding a nil pointer is not itself nil. Every Go developer learns this once, usually in production. Ours cost us a confusing afternoon.

**Abstracting too early.** Engineers coming from other languages wanted interfaces for everything and generics wherever they fit. We've settled on a simpler rule: write concrete code first. Add an interface only when a second implementation or a real testing need appears.

## What we'd tell another team

Start with a service that has a real performance or operational problem, not a toy project. Go's strengths show up under load and at 3 a.m., not in a hello-world.

Agree on shared conventions early and write them down. That means project layout, logging, error wrapping, and context propagation.

Keep the old service running in shadow mode longer than you think you need to. Our two weeks of mirrored traffic caught three bugs that our tests missed.

## What's next

This coming year, we're moving our job scheduler and notification pipeline to Go. We're also building an internal library for common service plumbing and starting Go office hours for engineers who want to learn. Python isn't going anywhere. We're just getting better at choosing the right tool for each job.

Here's to year two. If this kind of work sounds interesting, we're hiring.

---

*Note: The metrics (service count, latency, instance counts, image size) and anecdotes are placeholders. Replace them with your team's real figures before publishing.*
