# Eleven Years of Go

When we wrote our first production Go service, the language was barely six years old, and the team was split on whether it was a sensible bet. Eleven years later, Go runs the majority of our backend infrastructure. This post looks back at what we got right, what we got wrong, and what we've learned along the way.

## How We Got Here

Our original stack was a Python monolith with a handful of Java services bolted on. It worked, until it didn't. Latency tail behavior was unpredictable, deploys were heavy, and our on-call engineers spent too much time debugging memory issues and dependency conflicts.

The first Go service was deliberately small: a webhook dispatcher that had been our most frequent source of pages. A single engineer rewrote it over a few weeks. It used a fraction of the memory, handled bursts without drama, and deployed as one static binary. That last point sold more skeptics than any benchmark did.

## What Worked

**Simplicity as a feature.** Go's small surface area meant new engineers became productive quickly. Our onboarding data shows that engineers new to the language typically ship their first meaningful change within their first couple of weeks. Code review conversations focus on design rather than on which clever feature someone used.

**Concurrency that people can reason about.** Goroutines and channels made it natural to express work that used to require thread pools and callback chains. We still hit races and leaks, but the race detector and good tooling made them findable.

**Operational ergonomics.** Static binaries, fast builds, built-in profiling with `pprof`, and a solid standard library meant fewer moving parts in production. Our container images shrank dramatically, and cold starts stopped being a topic of discussion.

**Backward compatibility.** The Go 1 compatibility promise is underrated. We've upgraded through many releases with minimal churn. Upgrades are usually a version bump, a CI run, and a merge.

## What Hurt

**Error handling boilerplate.** For years we debated `if err != nil`. In practice, the verbosity forced us to think about failure paths, but it also produced noise. We eventually settled on conventions: wrap errors with context, define sentinel errors sparingly, and keep handling close to the source.

**Life before generics.** Before generics arrived, we wrote a lot of repetitive helpers or leaned on `interface{}` and code generation. Generics fixed much of this, though we've learned to use them with restraint. A generic abstraction that saves ten lines but costs readability isn't a win.

**Dependency management.** The early years, before modules, were rough. Vendoring tools came and went, and builds were occasionally unreproducible. Modules ended that era, and we don't miss it.

**Unbounded goroutines.** Cheap concurrency tempts people to spawn goroutines freely. We've had incidents caused by leaks and by fan-out that overwhelmed downstream services. Today we require explicit lifecycle management, context propagation, and bounded worker pools in code review.

## Lessons We'd Pass On

1. **Start with a painful, well-bounded service.** A small win with clear metrics builds credibility better than a grand migration plan.
2. **Write conventions down early.** Project layout, error handling, logging, and context usage are easier to standardize at ten services than at a hundred.
3. **Invest in shared libraries carefully.** Internal libraries sped us up, but a large shared core also became a coordination bottleneck. We now prefer small, focused packages with clear owners.
4. **Use the tooling.** `go vet`, the race detector, fuzzing, and linters catch an enormous amount. Make them mandatory in CI.
5. **Resist cleverness.** The most maintainable Go code we have is the most boring. That's a compliment.

## What's Next

We're leaning further into structured logging with `slog`, exploring iterator-based APIs now that range-over-func has settled, and tightening our approach to observability across services. We're also revisiting some older services that predate modern idioms, not to rewrite them wholesale, but to modernize them incrementally as we touch them.

Go isn't perfect, and it isn't the right tool for everything. We still use other languages where they fit, particularly for data science and some front-end tooling. But for services that need to be reliable, understandable, and cheap to operate, it has been an excellent choice for over a decade.

To everyone who has written, reviewed, debugged, and deployed Go with us: thank you. Here's to the next eleven.
