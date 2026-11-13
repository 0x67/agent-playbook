# Go: one year ago today

A year ago today, we merged a pull request titled "Move the ingestion service to Go." It touched 41 files, deleted a lot of code we were fond of, and made a few of us nervous. We want to look back on what we expected, what actually happened, and what we'd tell a team considering the same move.

## Why we did it

Our ingestion service had grown the way many services do: one reasonable decision at a time. It was a dynamically typed codebase with a thread pool bolted on, a handful of worker processes, and a growing collection of tuning flags. It worked, but three problems kept coming back:

- **Memory behavior was hard to predict.** Under bursty load, worker memory would climb, and we'd restart processes on a schedule to keep things healthy.
- **Concurrency was bolted on.** Every new feature that touched I/O meant a debate about threads, processes, or async, and each answer had sharp edges.
- **Deploys were heavy.** Our container image carried a runtime, a dependency tree, and a build step that occasionally broke for reasons unrelated to our code.

We didn't pick Go because it was fashionable. We picked it because its strengths lined up with these specific complaints: lightweight concurrency, a single static binary, and a standard library that covers most of what a network service needs.

## What we expected

We expected a performance win and a readability cost. We assumed Go would be faster, but we worried that its explicitness, with the `if err != nil` blocks, the lack of expressive abstractions, and the verbosity, would slow us down and make the code tedious.

## What actually happened

**The performance win was real, but not the main win.** CPU use per request dropped substantially, and we retired roughly two-thirds of the instances we'd been running. But the thing people mention most in retrospectives isn't the benchmark. It's that the service became boring. Memory is flat. Scheduled restarts are gone. Our on-call rotation noticed before we did.

**The verbosity cost was smaller than feared.** Error handling is repetitive, and we won't pretend otherwise. But the repetition made failure paths visible in code review. Several bugs we would previously have found in production were caught because a reviewer could see exactly where an error was being dropped. We now treat that explicitness as a feature.

**Concurrency became a design tool instead of a hazard.** Goroutines and channels let us model the pipeline the way we draw it on a whiteboard: stages that receive, validate, transform, and write, with bounded queues between them. Backpressure, which had been an afterthought, became a property of the design. Context propagation gave us consistent cancellation and timeouts across the whole request path.

**Deployment got simpler.** One static binary in a minimal image. Build times dropped, image size shrank by an order of magnitude, and cold starts stopped being a topic of conversation.

## What was harder than expected

It wasn't all smooth.

- **Learning curve for idioms.** Writing Go syntax is easy in a week. Writing idiomatic Go takes months. Early code had too many interfaces, too much cleverness, and not enough plain structs and functions. We rewrote some early modules.
- **Goroutine leaks.** Cheap concurrency makes it easy to start work and forget to stop it. We learned to be disciplined about context cancellation and added leak detection to our test suite.
- **Ecosystem gaps.** For a couple of integrations we had to write clients that would have been a one-line import before. Most were small, but they weren't free.
- **The migration itself.** We ran old and new services side by side, mirrored traffic, and compared outputs for weeks. It was slow and sometimes tedious, but it's the reason the cutover was uneventful.

## What we'd tell another team

1. **Start with a pain you can name.** "We want to use Go" isn't a goal. "We want predictable memory and simpler deploys" is.
2. **Migrate incrementally.** Shadow traffic and diff the results. Boring cutovers are the best cutovers.
3. **Invest in conventions early.** Agree on project layout, error wrapping, logging, and context usage before the codebase gets big.
4. **Budget for the idiom gap.** Pair experienced Go engineers with newcomers, and expect to refactor early work.
5. **Measure before and after.** Memory, latency, instance count, deploy time, and on-call pages. Memory is easy to forget, and it's often where the story is.

## Looking ahead

A year in, Go has become unremarkable for us, which is the highest compliment we can give infrastructure. Two more services are in the queue for migration, and we're investing in shared libraries for tracing, retries, and configuration so the next moves are faster than the first.

If you're weighing a similar move, we're happy to compare notes. And to the engineers who carried that 41-file pull request across the line: thank you. It turned out to be a good day to merge.
