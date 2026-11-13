# Building StatHat with Go

StatHat began as a simple idea: developers should be able to send a number from anywhere in their code and see it on a graph seconds later. No agents to install, no schema to define, no dashboards to configure. Behind that simplicity sits a system that has to accept a steady flood of tiny writes, aggregate them in near real time, and serve queries without falling over. We chose Go to build it, and this post walks through why, and what we learned along the way.

## Why Go

When we started, our requirements were clear. We needed a service that could handle tens of thousands of concurrent connections, deploy as a single artifact, and stay readable for a small team that rotated across components. Go fit all three.

Goroutines made the concurrency model approachable. Each incoming stat could be handled by its own lightweight goroutine without us building a thread pool or an event loop. The standard library's `net/http` was production-ready from day one, and static binaries meant our deploys were a copy and a restart rather than a dependency-resolution exercise.

Just as important, Go's deliberate lack of cleverness kept the codebase uniform. A new engineer could open almost any file and understand it within minutes.

## The ingestion pipeline

Every stat enters through a thin HTTP layer that does as little as possible: parse, validate, authenticate, and hand off. We learned early that doing real work in the request path was a mistake. Instead, handlers push each datapoint onto a buffered channel and return immediately.

```go
type Datapoint struct {
    Key       string
    Value     float64
    Timestamp time.Time
}

func (s *Server) handleStat(w http.ResponseWriter, r *http.Request) {
    dp, err := parseDatapoint(r)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    select {
    case s.ingest <- dp:
        w.WriteHeader(http.StatusAccepted)
    default:
        http.Error(w, "overloaded", http.StatusServiceUnavailable)
    }
}
```

The `select` with a `default` case is our backpressure valve. If the buffer is full, we shed load explicitly instead of letting latency grow without bound. Clients can retry, and our own dashboards tell us immediately when we're approaching the limit.

## Aggregation with worker pools

Downstream of the channel, a pool of workers groups datapoints by key and rolls them into time buckets: per-minute, per-hour, per-day. Sharding by a hash of the key means a given stat always lands on the same worker, which lets us keep counters in plain maps with no locking on the hot path.

```go
func shardFor(key string, n int) int {
    h := fnv.New32a()
    h.Write([]byte(key))
    return int(h.Sum32()) % n
}
```

Workers flush their buckets to storage in batches. Batching cut our write volume by more than an order of magnitude compared to our first naive version, which wrote every datapoint individually and paid for it in latency.

## Lessons learned

**Profile before you optimize.** Go's built-in `pprof` tooling paid for itself repeatedly. Our biggest early win came from a profile showing that time formatting, not storage, dominated CPU in one handler. We would never have guessed it.

**Be deliberate about goroutine lifetimes.** Goroutines are cheap, but leaks are not. We standardized on passing a `context.Context` into every long-running goroutine and tying shutdown to its cancellation. This made graceful deploys boring, which is exactly what we wanted.

**Keep interfaces small.** Defining narrow interfaces at the point of use, such as a `Store` with just `Write` and `Query`, made testing straightforward. We could swap in an in-memory fake and exercise the aggregation logic without a database.

**Embrace explicit errors.** Go's error handling is verbose, and we complained about it at first. Over time we came to value that every failure path is visible in the code. When something breaks at 3 a.m., that explicitness is a gift.

## What we'd do differently

We underinvested in structured logging early on, and retrofitting it was tedious. We also waited too long to introduce load testing as a routine part of our release process. Both are now standard practice.

## Closing thoughts

Go didn't make the hard problems of a metrics system disappear. Aggregation, storage, and query performance still demanded careful design. What it did was remove friction around them: fast builds, simple concurrency, easy deploys, and a codebase that stays approachable as the team grows.

If you're building a high-throughput service and value operational simplicity, Go is hard to beat. We'd make the same choice again.
