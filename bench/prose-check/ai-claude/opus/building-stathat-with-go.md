# Building StatHat with Go

StatHat started with a simple promise: add one line of code to your app, and you get a graph. Count signups, time database queries, or track queue depth. Call our API with a stat name and a number, and StatHat handles storage, aggregation, charts, and alerts.

Keeping that promise means the unglamorous parts have to be solid. The ingestion API must accept a steady stream of tiny requests without slowing down the applications that send them. The aggregation layer must roll raw data points into clean time series. The web app must render those series fast enough that people actually look at them. We built all three in Go. This post covers why we chose it and what we learned.

## Why Go

We wanted one language across the whole stack, and we wanted it to be boring in the best sense. Go is compiled and fast, and it's small enough that someone new to the codebase can open any file and follow it. Concurrency is built into the language. The standard library covers most of what a web service needs: `net/http`, `encoding/json`, `html/template`, and `testing`. Builds take seconds, which makes the edit-compile-test loop feel almost like a scripting language.

## Ingestion: Answer Fast, Work Later

Our main rule for the API is to do no real work on the request path. A handler validates the input, puts it on a queue, and returns.

```go
var incoming = make(chan Point, 50000)

func handleCount(w http.ResponseWriter, r *http.Request) {
	p, err := parsePoint(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	select {
	case incoming <- p:
		w.WriteHeader(http.StatusAccepted)
	default:
		http.Error(w, "busy, retry", http.StatusServiceUnavailable)
	}
}
```

The `default` branch in that `select` is a small detail that matters a lot. When the buffer fills up, we return a 503 right away instead of blocking. Our client libraries retry with backoff, so a traffic spike never turns into thousands of hung connections.

## Aggregation with Goroutines

A pool of worker goroutines drains the queue. We shard by a hash of the stat key, so each stat belongs to exactly one worker. Workers collect points into in-memory, minute-sized buckets and flush them to storage on a timer.

```go
func (w *worker) run(ctx context.Context) {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case p := <-w.in:
			w.buckets.Add(p)
		case <-ticker.C:
			w.flush(ctx)
		case <-ctx.Done():
			w.flush(context.Background())
			return
		}
	}
}
```

Sharding by key turned out to be our most important design decision. Because only one goroutine ever touches a given stat, the hot path needs no mutexes. There's no lock contention, and the race detector stays quiet.

## Interfaces Keep It Testable

Workers don't know or care where data ends up. They depend on a small interface:

```go
type Store interface {
	Flush(ctx context.Context, buckets []Bucket) error
	Range(ctx context.Context, stat string, from, to time.Time) ([]Bucket, error)
}
```

Production uses a database-backed implementation, while tests use a map in memory. As a result, most of our test suite runs in well under a second, and every CI build runs `go test -race`. Go's implicit interfaces mean we never had to plan this abstraction in advance. We extracted it the first time we needed a fake.

## Deployment Is a File Copy

Every service compiles to a single static binary. A deploy means building, copying the file to the server, and signaling the old process to exit. `http.Server.Shutdown` drains in-flight requests, and the workers flush their buckets when the context is canceled. To roll back, we copy the previous binary into place. Servers don't need a runtime, and nothing gets installed on deploy day.

## Lessons Learned

- **Profile before you optimize.** We were sure our bottleneck was the database. Then `pprof` showed that a large share of CPU time went to allocations during JSON decoding. Reusing buffers and hand-parsing the hottest endpoint gave us more headroom than any database tuning did.
- **Every goroutine needs a way out.** Our worst early bugs were goroutines blocked forever on channels nobody would ever write to again. Now we pass a `context.Context` to every long-lived goroutine, and code review checks how each one exits.
- **Lean on the standard library.** We've added dependencies cautiously. Each one is code we have to understand and upgrade, and the standard library has rarely let us down.
- **Let `gofmt` settle style debates.** It sounds trivial, but never discussing brace placement in review frees up a lot of attention for discussing design.

## Wrapping Up

Go wasn't the only language that could have built StatHat. It was the one that let a small team build it quickly and keep it running reliably. Simple concurrency, a strong standard library, and painless deploys added up to a system that's easy to reason about at 3 a.m. when an alert goes off.

If you're building a service that needs to handle many small requests and you value code your teammates can read, give Go a serious look.

---

*Note: StatHat is a real product, and the architecture, code, and anecdotes above are illustrative. Before publishing, swap in your team's actual design details, numbers, and war stories.*
