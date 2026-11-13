# The Next Step for Generics

When Go 1.18 shipped generics, we were cautious. Our backend is several hundred thousand lines of Go, and we've learned that a new language feature can spread through a codebase faster than our understanding of it. So we started small: generics were allowed only in a shared `internal/x` package, and every new generic API needed a second reviewer.

That experiment has run long enough to show us where generics pay off and where they don't. This post covers what we learned and the next step we're taking.

## What we did first

The first wave was the obvious one: collection helpers. We had dozens of hand-written functions like `ContainsString`, `ContainsInt64`, and `UniqueUserIDs`, each a slightly different copy of the same loop. These became a handful of functions:

```go
func Contains[T comparable](s []T, v T) bool
func Map[T, U any](s []T, f func(T) U) []U
func Uniq[T comparable](s []T) []T
```

Many of these now exist in the standard library's `slices` and `maps` packages, so we've been deleting our own versions as we go. That's the best possible outcome for a utility package.

The second wave replaced `any`-based containers. Our in-process cache used to look like this:

```go
func (c *Cache) Get(key string) (any, bool)
```

Every caller followed it with a type assertion, and every type assertion was a place where a refactor could cause a runtime panic. The generic version moves that check to compile time:

```go
type Cache[K comparable, V any] struct {
    mu    sync.RWMutex
    items map[K]V
}

func (c *Cache[K, V]) Get(key K) (V, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    v, ok := c.items[key]
    return v, ok
}
```

## What we learned

**Generics work best at the edges of type safety.** The biggest wins weren't about deleting duplicate code. They came from removing `any`, `interface{}`, and reflection from places where the types were always known and simply couldn't be expressed.

**Most code doesn't need them.** Some early pull requests made business logic generic "just in case." These were harder to read, harder to debug, and almost never instantiated with more than one type. We reverted most of them.

**Performance is not automatic.** Go compiles generic code using a mix of specialization and runtime dictionaries. In a couple of hot paths, a generic function that called methods through a type constraint was measurably slower than the hand-written version. That's fine for most code, but it means "make it generic" is not a free refactor for latency-sensitive services.

## The next step: typed messaging

Our next target is the internal event bus, which is the largest remaining source of runtime type errors. Today, handlers receive raw bytes and decode them on their own:

```go
bus.Subscribe("orders.created", func(ctx context.Context, raw []byte) error {
    var evt OrderCreatedEvent
    if err := json.Unmarshal(raw, &evt); err != nil {
        return err
    }
    // ...
})
```

Nothing stops a publisher from sending the wrong payload to `orders.created`, and nothing stops a subscriber from decoding into the wrong struct. The new API binds each topic to its payload type:

```go
var OrderCreated = events.NewTopic[OrderCreatedEvent]("orders.created")

events.Subscribe(bus, OrderCreated, func(ctx context.Context, evt OrderCreatedEvent) error {
    // evt is already decoded and correctly typed
})

events.Publish(ctx, bus, OrderCreated, OrderCreatedEvent{ID: id})
```

Note that `Subscribe` and `Publish` are package-level functions, not methods on `Bus`. Go doesn't allow methods to declare their own type parameters, and we found the function form reads just as well.

With this change, publishing a `RefundIssuedEvent` to `OrderCreated` becomes a compile error instead of a production incident. Decoding, error wrapping, and tracing all live in one place rather than in every handler.

## Guidelines going forward

As generics move out of `internal/x` and into service code, we're adopting a few rules:

1. **Write it concretely first.** Extract a generic version once you have a second real use, not a hypothetical one.
2. **Prefer generic functions over generic types.** They're easier to read and easier to remove.
3. **Use the narrowest constraint that works.** Reach for `comparable` or a small interface before `any`.
4. **Benchmark hot paths.** If a generic version is slower where it matters, keep the specialized one.
5. **Don't simulate inheritance.** If a design needs three type parameters and a constraint with five methods, an interface is probably the better tool.

## Rollout

The typed event bus will ship alongside the existing API, and we'll migrate topics team by team. The old string-based `Subscribe` will stay until the last topic moves over. Linters will flag new uses of it starting next quarter.

If your team owns a topic with a particularly tangled payload, reach out in the platform channel. We'd rather find the hard cases now than at the end of the migration.
