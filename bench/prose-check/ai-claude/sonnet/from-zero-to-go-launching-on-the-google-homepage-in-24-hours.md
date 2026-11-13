# From zero to Go: launching on the Google homepage in 24 hours

Last month, our team got a call that every engineer secretly hopes for and quietly dreads: a feature of ours had been selected for a placement on the Google homepage, and the window opened in 24 hours. We had a working prototype, a backend written in a language none of us loved operating at scale, and a launch estimate that, until that morning, said "six weeks."

This is the story of how we rewrote the critical path in Go, shipped it, and survived the traffic. It's also a story about what we'd do differently.

## The constraints

Our situation was simple to state and hard to meet:

- **Traffic**: We expected a spike two to three orders of magnitude above our normal load, with no ramp-up.
- **Latency**: A homepage placement means users expect instant response. Our p99 target was under 150 ms.
- **Time**: 24 hours, including testing, deploy, and sleep, which we treated as optional.
- **Team**: Five engineers, only one of whom had shipped production Go.

The existing service was a monolith with a heavy runtime and slow cold starts. Scaling it horizontally was possible but expensive and unpredictable. We needed something lean, fast to start, and easy to reason about under pressure.

## Why Go

We didn't choose Go because it was fashionable. We chose it because of what it removes.

**Small, static binaries.** A single compiled artifact meant our container images dropped from hundreds of megabytes to under 30 MB. Autoscaling went from "eventually" to "within seconds."

**Concurrency that's hard to misuse.** Goroutines and channels let us fan out calls to downstream services without building a thread-pool tuning exercise into the launch plan.

**A boring standard library.** `net/http`, `encoding/json`, and `context` covered about 90% of what we needed. Fewer dependencies meant fewer surprises at 3 a.m.

**Readable by newcomers.** With one experienced Go developer, code review had to double as teaching. Go's small surface area made that feasible.

## The plan

We split the work into three tracks and resisted the urge to rewrite everything.

1. **Rewrite only the hot path.** Roughly 5% of our endpoints would take 95% of the traffic. Those went to Go. Everything else stayed behind the old service.
2. **Put a thin routing layer in front.** A small Go proxy sent the hot endpoints to the new service and the rest to the legacy one, so we could roll back per route.
3. **Cache aggressively.** Most responses were identical across users for short windows. A two-tier cache, in-process plus a shared store, absorbed the bulk of the load.

## The 24 hours

**Hours 0–4: Scope and skeleton.** We agreed on the endpoints, wrote the API contracts, and had the one Go veteran pair with each teammate to establish project layout, error handling, and logging conventions. Conventions first meant the next twenty hours produced consistent code.

**Hours 4–14: Build.** We ported handlers one at a time, each with a table-driven test comparing outputs against the legacy service. That parity testing caught a surprising number of subtle behavior differences, from date formatting to how empty arrays serialized.

**Hours 14–19: Load test.** We replayed production traffic at 3x our expected peak. We found two real problems: an unbounded goroutine spawn in a retry loop, and a database connection pool sized for the old architecture. Both were fixed within the hour.

**Hours 19–22: Deploy and rehearse.** We shipped behind the routing layer at 1%, then 10%, then 50%, watching latency and error dashboards. We also rehearsed the rollback until it was boring.

**Hours 22–24: Rest.** Not everyone slept, but everyone stepped away. A fresh pair of eyes is worth more than another hour of staring.

## Launch

When the placement went live, traffic climbed steeply and kept climbing. Our p99 latency held at around 90 ms. Autoscaling added instances in seconds. The cache hit rate settled above 92%, which meant our database barely noticed the event.

We had one scare: a downstream dependency slowed down, and our context timeouts kicked in exactly as designed, serving slightly stale cached data instead of failing. Users never noticed.

## What we'd do differently

- **Invest in observability earlier.** We added metrics and tracing mid-sprint. Having them from hour one would have shortened debugging.
- **Write the runbook before the code.** Our rollback plan was good, but we wrote it too late.
- **Say no sooner.** Several "quick wins" were proposed during the build. Each one was tempting and each one was a risk.

## Takeaways

Speed under pressure doesn't come from heroics. It comes from narrowing scope, picking tools that stay out of your way, and building in the ability to undo your decisions. Go helped, but the real win was deciding what *not* to rewrite.

The legacy service is still running behind the proxy, and we're migrating the rest at a calmer pace. Next time the phone rings, we'll be ready, and maybe even a little rested.
