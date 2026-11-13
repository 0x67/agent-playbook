# Proposals for Go 1.15

Every Go release cycle begins with a quiet but important phase: the community and the core team decide what's worth changing. For Go 1.15, the proposals on the table reflect a language that is mature and deliberately cautious. The focus is less on new syntax and more on the toolchain, the runtime, and the long tail of papercuts that engineers hit every day. In this post, we walk through the proposals that caught our attention, what they mean for production systems, and how we're preparing our own codebases.

## The Philosophy Behind the Cycle

Go's compatibility promise shapes everything. Since Go 1.0, programs written against the language specification and standard library are expected to keep working. That constraint makes each proposal a negotiation: is the benefit large enough to justify the cost of any churn for users?

Go 1.15 proposals tend to pass that test when they fall into one of three categories:

1. **Improvements invisible to source code**, such as linker and runtime changes.
2. **Additive library changes** that don't break existing callers.
3. **Tooling and diagnostics** that make correct code easier to write.

Proposals that alter the language itself face a much higher bar, and most of the discussion this cycle reflects that.

## Linker Improvements

One of the most practical areas of work is the linker. For large monorepos like ours, link time is a meaningful part of the edit-build-test loop. Proposals in this area aim to reduce both link time and binary size by improving how the linker handles symbols and by trimming unneeded data.

For teams shipping many services, smaller binaries mean faster container pulls and quicker deploys. Faster linking means shorter CI runs. Neither requires a source change, which makes this the kind of work we welcome most: we upgrade the toolchain and benefit immediately.

## Runtime and Allocation Performance

The runtime has seen steady attention to small-object allocation, particularly for workloads with many concurrent goroutines. Contention in the allocator can show up as latency spikes under load, and reducing it helps tail latency in services that handle bursty traffic.

We'd encourage anyone evaluating a new release to benchmark with their real workloads rather than relying on microbenchmarks. Allocation improvements often shift behavior in ways that only show up in production-shaped traffic. Before upgrading, we capture representative profiles with `pprof`, then compare them after the upgrade.

## Standard Library Additions

Several library proposals add small but useful pieces of functionality. The common thread is reducing boilerplate that nearly every Go project reimplements. Examples of the kinds of changes under discussion include:

- Better support for embedding data, such as time zone information, directly into binaries so programs behave consistently in minimal container images.
- Improvements to error handling helpers that make wrapping and inspection less verbose.
- Refinements to the `testing` package that make cleanup and test helpers more ergonomic.

Embedding time zone data is a good example of a proposal that solves a real operational problem. Anyone who has deployed a service to a scratch or distroless image and watched `time.LoadLocation` fail understands the appeal.

## Vet and Diagnostics

The `go vet` tool continues to grow. New checks catch classes of bugs that compile cleanly but misbehave at runtime, such as suspicious conversions between integer and string types. Because vet runs as part of `go test`, new checks can surface in existing projects as unexpected failures.

That's a feature, not a bug, but it does mean upgrades can require cleanup. We recommend running `go vet ./...` on the new toolchain in a separate branch before rolling the version bump across your repositories.

## What About the Language?

Generics, error handling syntax, and other language-level ideas continue to be discussed, but they move slowly by design. The team has been explicit that a good solution matters more than a fast one. We think that's the right call. A language feature adopted too early is a permanent liability.

Meanwhile, we're staying pragmatic. Our teams write Go that is clear and conventional, which keeps the eventual adoption of any new language feature straightforward.

## How We're Preparing

Our upgrade checklist for any new Go release looks like this:

1. **Read the draft release notes** and flag anything touching our dependencies.
2. **Build and test in CI** against the release candidate as soon as one is available.
3. **Run `go vet` and the race detector** across all modules.
4. **Compare benchmarks and profiles** for our highest-traffic services.
5. **Roll out gradually**, starting with internal and low-risk services.

Treating the release candidate as a first-class CI target has paid off repeatedly. Bugs found during the RC period can still be fixed before the final release, and reporting them helps everyone.

## Get Involved

The proposal process is open. If a change would affect your systems, read the discussion, add concrete data from your own experience, and file issues with reproducible examples. Experience reports from real production use carry far more weight than abstract arguments.

We'll follow up with a deeper post once the release candidate lands, including benchmark results from our own services. Until then, happy shipping.
