# Half a decade with Go

Five years ago, we made a decision that felt bigger than it was: we would write our next backend service in Go. It was meant to be a small experiment, a single service with a modest scope, owned by a team of four. Today, Go powers the majority of our backend, from API gateways to data pipelines to the internal tooling that keeps our engineers productive. This post is a look back at what worked, what surprised us, and what we'd tell a team considering the same path.

## Why we started

Our earlier stack was a mix of dynamically typed services that had grown organically. They were quick to write and increasingly painful to operate. Deploys required careful dependency management, memory usage was unpredictable, and onboarding new engineers meant explaining years of accumulated conventions.

Go promised something different: a single static binary, fast compile times, a small language specification, and concurrency built into the runtime. None of those claims were exaggerated. The first service we shipped was running in production within six weeks, and it has needed remarkably little attention since.

## What worked

**Boring is a feature.** Go's small surface area means code written by different people looks similar. Code review shifts from arguing about style to discussing design. New hires are typically productive within their first week or two, and reading a service they've never seen is rarely a struggle.

**Deployment became trivial.** Static binaries and small container images simplified our CI pipelines and cut cold-start times. We stopped thinking about runtime versions on hosts entirely.

**Concurrency is approachable.** Goroutines and channels let engineers build concurrent systems without needing to be experts in threading. That said, approachable is not the same as foolproof, which brings us to the lessons.

**Tooling out of the box.** `gofmt`, `go test`, `go vet`, the race detector, and `pprof` gave us a baseline of quality and observability before we added a single third-party tool. Profiling a production issue with `pprof` has saved us more than once.

## What surprised us

**Error handling is a cultural matter.** The much-debated `if err != nil` pattern is verbose, but our real problem wasn't verbosity. It was inconsistency. Early on, errors were returned without context, and debugging meant guessing where something went wrong. We settled on wrapping errors with `fmt.Errorf("doing X: %w", err)` and defining a few sentinel errors at package boundaries. Logs became dramatically more useful.

**Goroutine leaks are quiet.** The first time we saw memory creep upward in a long-running service, the culprit was a goroutine blocked forever on a channel nobody was reading. We now pass `context.Context` everywhere, treat cancellation as a first-class concern, and use leak detection in tests.

**Generics changed less than expected.** When generics landed, some of us expected a wave of rewrites. In practice, we use them sparingly, mostly for collection helpers and a few type-safe utilities. Most of our code remains plain and concrete, and we think that's healthy.

**Dependencies need curation.** Go's module system is solid, but a small standard library culture doesn't mean a small dependency graph. We now review new dependencies deliberately and prefer the standard library where it's good enough, which is more often than you'd think. `net/http` and `encoding/json` carry a lot of our weight.

## What we'd do differently

We'd invest in shared project layout and internal libraries sooner. For the first two years, each team solved logging, configuration, and metrics slightly differently, and reconciling them later was tedious. A thin internal platform library, kept deliberately small, would have paid for itself early.

We'd also write down our conventions earlier. Go's simplicity lulled us into assuming we didn't need a style guide. We did, particularly around package naming, interface design ("accept interfaces, return structs" took a while to sink in), and where to put business logic.

## Where we are now

Five years in, the numbers tell part of the story: faster builds, lower infrastructure costs, and fewer production incidents tied to runtime behavior. But the more meaningful change is harder to measure. Engineers across teams can move between services with little friction, and the codebase feels like one system rather than many.

Go isn't perfect. We still reach for other languages for data science work and some frontend-adjacent tooling, and we don't pretend one language fits everything. But for building reliable, maintainable network services, it has been an excellent choice.

## Looking ahead

We're excited about continued improvements to the toolchain, better observability integrations, and the ongoing evolution of the standard library. We're also planning to open-source a few of our internal libraries, starting with our context-aware worker pool.

If you're considering Go for your team, our advice is simple: start small, write down your conventions, and give it a year. If you're already on the journey, we'd love to hear what you've learned. Here's to the next five years.
