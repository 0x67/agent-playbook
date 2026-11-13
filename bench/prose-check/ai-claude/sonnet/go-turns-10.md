# Go Turns 10

Ten years ago, Go 1.0 shipped, and a small language with a deliberately short feature list began its quiet takeover of the infrastructure we all depend on. (Go was open-sourced in 2009 and hit 1.0 in March 2012, so "ten" is a loose number depending on where you start counting. Whichever milestone you pick, the point stands: Go has been around long enough to earn a retrospective.) Here is what our team has learned from living with it.

## Why We Chose Go

When we started building our backend services, the shortlist was familiar: Java, Python, Node, and Go. We picked Go for reasons that sounded boring at the time and have turned out to be decisive:

- **Fast compile times.** Feedback loops stayed tight as the codebase grew.
- **A single static binary.** Deployment became copying a file. Container images shrank from hundreds of megabytes to tens.
- **Concurrency in the language.** Goroutines and channels made concurrent code approachable for engineers who had never written it before.
- **A small spec.** A new hire can read the language specification over lunch and be productive within days.

## What Held Up

### Simplicity as a feature

Go's refusal to add features is easy to mock and hard to replicate. Code written in 2015 still reads like code written today. When we review a pull request, we argue about design, not about which of five idioms the author chose. `gofmt` ended style debates before they began.

### The standard library

`net/http`, `encoding/json`, `context`, and `testing` carried us further than we expected. Several of our production services have only a handful of third-party dependencies. Fewer dependencies means a smaller attack surface and fewer midnight upgrade emergencies.

### Tooling

`go test`, `go vet`, the race detector, and `pprof` are built in and work the same everywhere. The race detector alone has caught bugs that would have cost us days in production. Profiling a live service with `pprof` is routine, not heroic.

### Backward compatibility

The Go 1 compatibility promise is perhaps the most underrated decision in the project. We have upgraded through many releases, and the typical upgrade is changing a version number and rerunning CI. That's rare in this industry.

## What Took Time

Go was not always comfortable, and we'd be doing readers a disservice to pretend otherwise.

**Error handling.** The `if err != nil` pattern drew criticism for years. We came to appreciate its explicitness, but it's verbose. Wrapping errors with `%w` and using `errors.Is` and `errors.As` made it far more workable, and we still invest in conventions so errors carry useful context.

**Dependency management.** Before modules, we lived through `GOPATH`, vendoring, and a rotating cast of third-party tools. Go modules fixed this, and we'd never go back, but the transition years were rough.

**Generics.** We waited a long time for them. Since they arrived in Go 1.18, we've used them sparingly: for collection helpers and a few data structures, not as a default. The restraint the language encourages turns out to apply here too.

## Lessons for Our Own Code

Go shaped how we write software beyond the language itself:

1. **Prefer boring.** Clear code that any teammate can maintain beats clever code that only its author understands.
2. **Make the zero value useful.** Types that work without elaborate initialization are easier to use correctly.
3. **Accept interfaces, return structs.** Small interfaces defined by the consumer keep packages decoupled and testing simple.
4. **Pass `context` everywhere.** Cancellation and deadlines are far easier to design in from the start than to retrofit.
5. **Measure before optimizing.** The tooling makes it cheap to find out where time really goes.

## Where We're Looking Next

The language continues to evolve carefully. Improvements to the runtime, the garbage collector, and tooling keep arriving without breaking existing code. We're watching structured logging in the standard library, ongoing work on generics ergonomics, and better supply chain tooling such as vulnerability scanning built into the toolchain.

## Thank You

To the Go team and the wider community: thank you for ten years of disciplined, thoughtful stewardship. You proved that a language can succeed by saying no more often than yes, and that productivity comes from removing friction, not adding features.

Happy birthday, Go. Here's to the next decade of readable, reliable, boring-in-the-best-way software.
