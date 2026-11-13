# Gobs of data

Every engineering team eventually hits the moment when a system that worked fine yesterday starts to groan. For us, it came on an ordinary Tuesday, when a dashboard that had loaded in two seconds took forty. Nothing had changed in the code. What had changed was the data: gobs of it, arriving faster than we had planned for.

This post is about what we learned scaling our event pipeline from millions of records a day to billions, and the unglamorous decisions that mattered more than any clever trick.

## The problem with "it works"

Our original pipeline was simple. Services emitted events, a consumer wrote them to a relational database, and analytics queries ran against the same tables. It was easy to reason about, and for a long time that was the right tradeoff.

But simplicity has a ceiling. Three things broke at roughly the same time:

- **Write amplification.** Every event touched several indexes, so ingestion slowed as tables grew.
- **Query contention.** Long analytical scans competed with ingestion for the same resources.
- **Storage costs.** We were keeping raw, rarely queried data on our most expensive disks.

Each problem alone was manageable. Together, they meant we had outgrown the architecture rather than just the hardware.

## Separate the paths

The most important change was also the most obvious in hindsight: we stopped asking one system to do two jobs.

We split the pipeline into a **write path** and a **read path**. The write path is optimized for one thing, which is accepting events durably and quickly. Events land in an append-only log, partitioned by tenant and time. No secondary indexes, no joins, no surprises.

The read path is built from that log. Background jobs compact events into columnar files and publish aggregates to a serving layer designed for low-latency queries. Analysts and dashboards never touch the ingestion system.

This separation gave us independent scaling. When ingestion spikes, we add writers. When query load grows, we add readers. Neither team pages the other.

## Choose your partitions carefully

If there's one decision we'd urge you to spend time on, it's partitioning. Our first scheme partitioned by tenant alone, which seemed natural until one customer grew to 40% of our traffic. That single partition became a hot spot, and no amount of hardware could fix it.

We moved to a composite key of tenant, day, and a small hash bucket. The hash spreads heavy tenants across many partitions, and the day component makes retention trivial: dropping old data means deleting whole partitions instead of running expensive row-level deletes.

A few rules we now follow:

1. Pick a key that distributes writes evenly, not one that merely matches how you think about the data.
2. Make time a first-class part of the key if you have retention requirements.
3. Revisit the scheme when your largest customer doubles, not after it hurts.

## Tier your storage

Not all data deserves equal treatment. We now classify events by age and access pattern:

| Tier | Age | Storage | Typical use |
|------|-----|---------|-------------|
| Hot | 0–7 days | SSD-backed, replicated | Live dashboards, alerting |
| Warm | 7–90 days | Columnar files on object storage | Ad hoc analysis |
| Cold | 90+ days | Compressed archives | Compliance, rare backfills |

Automated lifecycle jobs move data between tiers. The result was a storage bill roughly 60% lower, with no change in the experience for the queries people actually run.

## Measure what matters

None of this would have worked without good observability. We track three numbers above all others: ingestion lag (how far behind the read path is), p99 query latency, and cost per million events. When a change improves one at the expense of another, we want to see it immediately, not discover it in a quarterly review.

We also learned to load-test with realistic skew. Uniform synthetic data hides exactly the hot-partition problems that bite in production. Replaying anonymized traffic shapes found issues that clean benchmarks never did.

## What we'd do differently

We waited too long. The warning signs, such as slowing ingestion and creeping costs, were visible months before the outage-adjacent Tuesday. A lightweight capacity review every quarter would have let us make these changes calmly instead of urgently.

We also over-built at first. Our initial design for the read path included a custom query planner that we later replaced with an off-the-shelf engine. Building it taught us a lot, but buying would have gotten us to the same place sooner.

## Takeaways

Handling gobs of data is less about exotic technology and more about discipline:

- Separate write and read paths so each can scale on its own terms.
- Design partition keys around distribution and retention.
- Tier storage by how data is actually used.
- Measure lag, latency, and cost continuously.
- Test with skewed, realistic data.

The data will keep growing. Our goal isn't to build a system that never strains, but one that tells us early, scales predictably, and lets us sleep through the night.

*Have questions or war stories of your own? We'd love to hear them in the comments.*
