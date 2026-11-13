# Contexts and structs

Few pieces of Go advice get repeated as often as this one: *don't store a `context.Context` in a struct.* It appears in the package documentation, in code review comments, and in linter rules. Like most rules of thumb, it is right most of the time and misleading some of the time. This post explains why the rule exists, where it holds, and where we have chosen to break it.

## What the rule actually says

The `context` package documentation puts it plainly: contexts should not be stored inside a struct type. Instead, pass a `Context` explicitly to each function that needs it, as the first parameter, conventionally named `ctx`.

```go
func (s *Store) Get(ctx context.Context, id string) (*Item, error) {
    // ...
}
```

The reasoning comes down to what a context represents. A context is scoped to a *call*: a request, an RPC, a job. It carries a deadline, a cancellation signal, and request-scoped values such as trace IDs. Those things have a lifetime, and that lifetime is almost never the lifetime of a long-lived object like a client, a repository, or a service.

## What goes wrong

When you store a context in a struct, you tie two lifetimes together that usually should not be tied. We have run into three failure modes.

**Stale cancellation.** A constructor takes the request context and stores it. The request finishes, the context is canceled, and the object, which was cached or shared, now fails every operation with `context canceled`. These bugs tend to show up only under load, when caching kicks in.

**Ambiguous deadlines.** If a method takes no context but the struct holds one, a reader cannot tell what bounds the call. Is it the deadline from construction time? Is there one at all? Explicit parameters make the answer visible at every call site.

**Leaked values.** Request-scoped values, such as user identity or trace spans, can silently attach to work that has nothing to do with the original request. We once traced a mislabeled span problem to a shared client that had captured the context of whichever request happened to create it first.

## A before and after

Here is a pattern we found in an older internal service:

```go
type Fetcher struct {
    ctx    context.Context
    client *http.Client
}

func NewFetcher(ctx context.Context) *Fetcher {
    return &Fetcher{ctx: ctx, client: &http.Client{}}
}

func (f *Fetcher) Fetch(url string) ([]byte, error) {
    req, err := http.NewRequestWithContext(f.ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }
    resp, err := f.client.Do(req)
    // ...
}
```

The fix is mechanical:

```go
type Fetcher struct {
    client *http.Client
}

func NewFetcher() *Fetcher {
    return &Fetcher{client: &http.Client{}}
}

func (f *Fetcher) Fetch(ctx context.Context, url string) ([]byte, error) {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }
    resp, err := f.client.Do(req)
    // ...
}
```

Now every caller decides how long each fetch may take, and the `Fetcher` can be shared safely.

## Where we break the rule

There are legitimate exceptions, and pretending otherwise leads to contortions.

**Request-shaped structs.** The standard library's own `http.Request` carries a context. That makes sense: the struct *is* the call. The same applies to our job and task types. If a struct is created for one unit of work and discarded when that work ends, its lifetime matches the context's, and storing it is reasonable.

**Long-running workers.** A background worker that owns a loop often needs a context representing the worker's own lifetime, not any caller's. Storing a context created in `Start` and canceled in `Stop` is a clean way to coordinate shutdown. The key difference is that the worker *owns* this context rather than borrowing one from a caller.

**Backward compatibility.** Sometimes an interface cannot change. In those cases we store the context, document why, and plan the migration.

## A rule of thumb for review

Rather than banning the pattern outright, we ask one question in code review: *whose lifetime does this context represent, and does it match the struct's?*

If the context is borrowed from a caller and the struct outlives that caller, it is a bug. If the struct is a short-lived carrier for a single operation, or if it owns the context it holds, it is probably fine. In the latter cases we ask for a comment stating the ownership, so the next reader does not have to rediscover the reasoning.

## Takeaways

- Pass contexts explicitly as the first parameter by default.
- Never capture a caller's context in an object that outlives the call.
- Structs that represent a single operation, or that own their context, are valid exceptions.
- Document the exception. A one-line comment saves a future debugging session.

The guideline exists to protect you from mismatched lifetimes. Once you understand that, you can follow the rule where it helps and break it deliberately where it does not.
