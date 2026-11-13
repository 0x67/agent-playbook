# Contexts and structs

Few types in Go's standard library appear in as many function signatures as `context.Context`. It carries deadlines, cancellation signals, and request-scoped values across API boundaries. In a typical service it threads through nearly every layer: HTTP handlers, database calls, queue consumers, and outbound RPCs.

Because it's everywhere, it's tempting to stop typing it. A question we see regularly in code review goes something like this: "This struct already holds the database handle and the logger. Can't I just put the context on it too?"

Usually, no. Here's why, and what to do instead.

## Pass it as the first argument

The `context` package documentation recommends passing a context explicitly as the first parameter of any function that needs one:

```go
type Store struct {
    db *sql.DB
}

func (s *Store) GetUser(ctx context.Context, id string) (*User, error) {
    row := s.db.QueryRowContext(ctx, "SELECT name, email FROM users WHERE id = $1", id)
    // ...
}
```

This looks repetitive, but it gives every caller precise control. A request handler can call `GetUser` with a 200ms deadline, and a background reconciliation job can call it with no deadline at all. Cancellation flows from the caller, through `GetUser`, into the database driver, and nobody has to wonder which context is "the" context.

## What goes wrong when it lives in a struct

Compare that with a version that stores the context when the struct is built:

```go
type Store struct {
    ctx context.Context
    db  *sql.DB
}

func NewStore(ctx context.Context, db *sql.DB) *Store {
    return &Store{ctx: ctx, db: db}
}

func (s *Store) GetUser(id string) (*User, error) {
    row := s.db.QueryRowContext(s.ctx, "SELECT ...", id)
    // ...
}
```

This change looks harmless, but it causes several problems.

**Lifetimes get tangled.** A context describes the lifetime of an *operation*. A struct like `Store` usually outlives any single operation. When you couple the two, the struct inherits a lifetime it was never meant to have. One common failure goes like this. A client is built with the context from a startup routine. That context is canceled once initialization finishes, and from then on every call fails with `context canceled`, far away from the actual cause.

**Callers lose control.** With the context baked in, a caller can't set a tighter deadline for one call or cancel a single in-flight operation. Every method shares the same signal, so cancellation is all or nothing.

**The API hides what it does.** `GetUser(id string)` looks like it never blocks on anything cancelable. To learn that it does, and which context it uses, a reader has to open the struct definition. An explicit `ctx` parameter documents itself.

**Concurrent use becomes ambiguous.** Suppose two goroutines share a `Store` and each needs its own request context. No single value in the field is correct for both. Some people respond by adding a setter, which turns a data race into a design pattern.

## The exception: compatibility

Storing a context in a struct can be a reasonable trade-off in one situation: adding context support to an existing API that can't break.

The standard library faced exactly this when contexts arrived. `database/sql` added parallel methods such as `QueryContext` and `ExecContext` next to the originals, and the old methods now delegate to the new ones with `context.Background()`. This approach is explicit and backward compatible, and it should be your first choice.

`net/http` went the other way. An `*http.Request` carries its context internally. You read it with `req.Context()` and replace it with `req.WithContext(ctx)`. This works because a `Request` *is* a single operation, so the struct and the context share a lifetime by design. Even so, `WithContext` returns a shallow copy instead of mutating the request, so nobody's context changes unexpectedly.

If you're tempted by this pattern, ask whether your struct really represents one operation. If it's a long-lived client, service, or repository, the answer is almost certainly no.

## Our guidelines

In code review, we check for the following:

- Any function that does I/O or blocks, directly or through something it calls, takes `ctx context.Context` as its first parameter.
- Long-lived types (clients, stores, servers) don't have a `context.Context` field.
- Types scoped to a single request or operation may hold a context. They expose it through a method and never mutate it in place.
- When extending an existing API, we add `...Context` variants instead of hiding a context in a struct.
- Nobody passes `nil` as a context. While you're still wiring a real context through, use `context.TODO()` as a placeholder.

## Wrapping up

Passing contexts explicitly costs a few keystrokes per function. In return, every call site states how long the work may take and who can stop it. That clarity pays off quickly the first time you debug a mysterious `context deadline exceeded` at 2 a.m.

Keep the context in the argument list. Store things in a struct only if they live as long as the struct does.
