# Go at Google I/O and Gopher SummerFest

Every year, a few events remind us why we bet on Go. This year, Google I/O and Gopher SummerFest gave a few of our engineers a chance to compare notes with the wider community, and we came home with plenty to think about. Here's what stood out and what we're changing in our own codebase as a result.

## Why we went

Go sits at the center of much of our backend: API gateways, data pipelines, internal tooling, and the infrastructure that holds them together. Conferences are where we find out which patterns are becoming standard and which are fading. They're also where we meet the maintainers and users who've already hit the problems we're about to hit.

Google I/O gave us a broad view of where the platform is heading. Gopher SummerFest was the opposite: smaller, more hands-on, and focused on the day-to-day craft of writing Go.

## Theme 1: Go as a foundation for AI-integrated systems

At I/O, the recurring question was how to build reliable services around fast-moving AI components. The Go angle was less about model work and more about the plumbing: concurrency, predictable latency, small deployable binaries, and strong tooling.

Our takeaways:

- **Treat model calls like any other unreliable dependency.** Timeouts, retries with backoff, and circuit breakers belong at the boundary. `context.Context` is still the right tool for propagating deadlines and cancellation.
- **Keep orchestration boring.** Goroutines and channels, or better yet `errgroup`, handle fan-out and fan-in without a heavy framework.
- **Observe everything.** Structured logging with `log/slog` and consistent tracing made it much easier to debug non-deterministic behavior.

## Theme 2: The language keeps getting more ergonomic

Several SummerFest talks showed how much recent language and standard library work has changed day-to-day Go. Generics are now mature enough that the community has settled on conventions for when they help and when they just add noise. Iterators and range-over-func are reshaping how people design collection APIs.

The consensus advice was refreshingly pragmatic:

1. **Reach for generics when you're writing the same logic over multiple types**, such as data structures and utility functions. Don't use them to avoid writing an interface.
2. **Prefer the standard library's `slices`, `maps`, and `cmp` packages** before writing your own helpers.
3. **Use iterators for lazy or streaming sequences**, but keep simple loops simple.

We've already opened a cleanup effort to replace a handful of hand-rolled helper packages with their standard library equivalents.

## Theme 3: Performance work is increasingly data-driven

A well-attended SummerFest session covered profiling and optimization. The message was that guessing is expensive and measurement is cheap. Profile-guided optimization, benchmark discipline, and execution traces keep showing up as high-leverage tools.

Practical habits we're adopting:

- Run benchmarks with `-count` and compare results using `benchstat` instead of eyeballing single runs.
- Capture CPU and heap profiles from production-like load, not just synthetic tests.
- Use `go tool trace` when latency problems smell like scheduling or GC interactions rather than raw CPU cost.

## Theme 4: Security and supply chain

Both events emphasized supply chain hygiene. `govulncheck` was mentioned repeatedly as a low-effort, high-value addition to CI because it reports only vulnerabilities your code actually reaches. We're making it a required check on all Go repositories, alongside tighter dependency pinning and regular module updates.

## The hallway track

Some of the most valuable conversations happened between sessions. We swapped war stories about monorepo layouts, migration strategies for large modules, and testing approaches for concurrent code. One recurring piece of advice was to invest in table-driven tests, race detector runs in CI, and fuzzing for any code that parses untrusted input. We've started a fuzzing pilot on two of our parsers.

## What we're doing next

Here's the short list coming out of the trip:

- **Audit custom helpers** and replace them with standard library packages where possible.
- **Make `govulncheck` and `-race` mandatory** in CI.
- **Standardize on `slog`** for structured logging across services.
- **Run a profiling week** on our three highest-traffic services.
- **Write internal guidelines** for when to use generics and iterators.

## Closing thoughts

What we value most about the Go community is its restraint. The language evolves carefully, the tooling is cohesive, and the culture favors clarity over cleverness. Both events reinforced that this is a feature, not a limitation.

If you were at either event and want to compare notes, or you're working on similar problems, we'd love to hear from you. And if you'd like to help shape how we build with Go, [we're hiring](#).

---

*A note on the draft: I kept session-specific details general because I don't have verified records of the talks. You may want to add specific session titles, speakers, and announcements your team attended, plus real links in place of the placeholder.*
