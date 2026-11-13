# Half a decade with Go

Five years ago, we shipped our first production Go service: a small webhook dispatcher meant to replace a worker that kept falling over under load. It was supposed to be an experiment. Today, Go runs most of our backend, including the API gateway, the billing pipeline, and much of our internal tooling. This is our look back at what worked, what didn't, and what we'd tell a team starting out today.

## Why we chose Go

We weren't searching for the most powerful language. We wanted one that a growing team could read, review, and operate at 3 a.m. without much ceremony. Go offered fast compile times, a strong standard library, first-class concurrency, and deployment as a single static binary. That last point turned out to matter more than we expected.

## What went right

### Boring code is a feature

Go has a small surface area, and because of that, our codebases look alike. An engineer moving from the notifications service to the billing service doesn't have to learn a new dialect of the language first. Code review spends its time on logic, not style. `gofmt` settled formatting before anyone could argue about it, and we've never missed those arguments.

### Onboarding got faster

New hires, including those who had never written Go, usually ship meaningful changes within their first couple of weeks. The language spec is short enough to read in an afternoon, and *Effective Go* still covers most of what people need. We had far fewer "you have to understand the framework first" conversations than we did with earlier stacks.

### The tooling earned its keep

`go test`, `go vet`, the race detector, and `pprof` are built in, and we use all of them daily. Profiling a production service with `pprof` once took us from "the service is slow sometimes" to a specific allocation-heavy JSON path in under an hour. When the tools are already installed, people actually use them.

### Deployment got simpler

A statically linked binary in a minimal container image is easy to build, scan, and ship. Our images shrank, cold starts got faster, and "works on my machine" bugs caused by runtime version drift largely disappeared.

## What hurt

### Concurrency is easy to start and hard to finish

Starting a goroutine takes one keyword. Making sure it stops again takes discipline. Early on we leaked goroutines in long-running services, usually because a channel send blocked forever or a background task ignored cancellation. The fix was cultural as much as technical. Every goroutine needs a clear owner and a clear exit path, and `context.Context` gets passed everywhere, no exceptions. We also added goroutine count to our standard dashboards, which caught several regressions before customers did.

### Error handling felt verbose

Yes, we wrote a lot of `if err != nil`. Engineers coming from exception-based languages complained, and so did we. Over time, though, most of us came to appreciate that the failure paths are visible right there in the code. Once we standardized on wrapping errors with `%w` and checking them with `errors.Is` and `errors.As`, our logs became noticeably more useful. Our rule now is to add context when you wrap, and never to swallow an error silently.

### We over-abstracted early

Our first services were full of interfaces with exactly one implementation, a habit carried over from other ecosystems. These made the code harder to navigate without making it easier to test. We now follow the Go proverb of accepting interfaces and returning structs, and we define interfaces at the point where they're consumed, only once they're needed.

### Generics: worth the wait, used sparingly

When generics arrived in Go 1.18, we were tempted to rewrite everything. We didn't, and we're glad. They've been great for collection helpers, typed caches, and a few data pipeline utilities. Everywhere else, plain concrete code is still easier to read.

## What we'd do differently

If we were starting over, we would:

- **Set conventions on day one** for project layout, error wrapping, logging, and configuration. Retrofitting consistency across dozens of services was expensive.
- **Adopt structured logging immediately.** Since `log/slog` joined the standard library, we've consolidated on it, and we wish we'd had a single approach from the start.
- **Write Go like Go.** The biggest friction we hit came from importing patterns from other languages, not from Go itself.
- **Invest in shared internal libraries carefully.** A small, well-maintained set of packages beats a sprawling "common" repo that everyone depends on and nobody owns.

## Looking ahead

Five years in, Go is still the default choice for new backend services here. It isn't perfect, and it isn't the right fit for every problem. We still reach for other tools for data science and some front-end-heavy work. But for building reliable networked services with a growing team, its constraints have helped us more often than they've gotten in the way.

The webhook dispatcher that started it all is still running, by the way, mostly untouched and quietly doing its job.
