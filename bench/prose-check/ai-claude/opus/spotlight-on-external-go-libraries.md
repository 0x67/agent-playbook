# Spotlight on external Go libraries

Go's standard library is one of the language's best features. You can build an HTTP server, parse JSON, run concurrent work, and write tests without a single third-party import. We lean on that heavily, and our default answer to "should we add a dependency?" is "probably not."

Still, a few external packages have earned a permanent place in our `go.mod` files. This post covers those libraries, why we picked them, and how we keep our dependency list short.

## How a library earns its place

Before anything new lands in a service, we ask four questions:

1. **Does it solve a problem the standard library doesn't, or solve it meaningfully better?**
2. **Is it actively maintained?** We look at release cadence, issue response times, and whether more than one person can merge.
3. **How deep is its dependency tree?** A small utility that pulls in forty transitive modules is a hard sell.
4. **Could we remove it later?** We prefer libraries we can wrap behind a narrow interface.

Here's what passed.

## `golang.org/x/sync/errgroup`

The `golang.org/x` modules sit just outside the standard library. Of these, `errgroup` is the one we use most. It takes the usual `sync.WaitGroup` pattern and adds error propagation, context cancellation, and concurrency limits.

```go
g, ctx := errgroup.WithContext(ctx)
g.SetLimit(8)

results := make([]Result, len(ids))
for i, id := range ids {
    g.Go(func() error {
        r, err := fetch(ctx, id)
        if err != nil {
            return fmt.Errorf("fetch %s: %w", id, err)
        }
        results[i] = r
        return nil
    })
}
if err := g.Wait(); err != nil {
    return nil, err
}
```

When one goroutine fails, the shared context is cancelled and the others can stop early. Since Go 1.22 gave each loop iteration its own variables, capturing `i` and `id` directly is safe.

## `github.com/jackc/pgx/v5`

Most of our services talk to PostgreSQL, and pgx is our driver. We use its native interface rather than going through `database/sql`. That gets us connection pooling via `pgxpool`, support for Postgres-specific types like arrays and `jsonb`, and `CopyFrom` for bulk loads. The v5 generic helpers also cut out a lot of scanning boilerplate:

```go
pool, err := pgxpool.New(ctx, os.Getenv("DATABASE_URL"))
if err != nil {
    return err
}
defer pool.Close()

// CollectRows checks rows.Err(), so the Query error surfaces there.
rows, _ := pool.Query(ctx,
    "SELECT id, email FROM users WHERE org_id = $1", orgID)
users, err := pgx.CollectRows(rows, pgx.RowToStructByName[User])
```

## `github.com/google/go-cmp`

`reflect.DeepEqual` tells you *that* two values differ, not *where*. `go-cmp` gives you a readable diff, and its `cmpopts` package handles common cases like ignoring timestamps or treating nil and empty slices as equal:

```go
opts := cmpopts.IgnoreFields(Order{}, "CreatedAt")
if diff := cmp.Diff(want, got, opts); diff != "" {
    t.Errorf("unexpected order (-want +got):\n%s", diff)
}
```

We chose this over a full assertion framework on purpose. Our tests use plain `if` statements and `t.Errorf`, and `go-cmp` makes that style pleasant without bringing in a new vocabulary.

## `golang.org/x/time/rate`

Any service that calls a third-party API needs to respect rate limits. This package provides a token-bucket limiter that works naturally with contexts:

```go
limiter := rate.NewLimiter(rate.Limit(10), 5) // 10 req/s, burst of 5

if err := limiter.Wait(ctx); err != nil {
    return err // context cancelled or deadline exceeded
}
```

It's small, has no surprising behavior, and has replaced several hand-rolled ticker loops in our codebase.

## `github.com/spf13/cobra`

For internal CLI tools such as migration runners, debugging utilities, and on-call helpers, Cobra gives us nested subcommands, consistent flag handling, generated help text, and shell completion. The standard `flag` package is fine for a single-purpose binary. Once a tool grows a third subcommand, we reach for Cobra.

## Libraries we've retired

The list shrinks as Go grows, and we take that seriously.

- **Structured logging.** We used a third-party logger for years. After Go 1.21 added `log/slog`, we migrated, and new services use only the standard library. A thin internal wrapper made the switch mostly mechanical.
- **HTTP routing.** Go 1.22 added method matching and path wildcards to `http.ServeMux`, so patterns like `GET /orders/{id}` work out of the box. New services start with the standard mux, and we're moving older ones over as we touch them.

Deleting a dependency is one of the most satisfying pull requests you can open.

## Keeping dependencies healthy

Adopting a library is a long-term commitment, so we build in some maintenance:

- **`govulncheck` runs in CI.** It reports only vulnerabilities in code paths we actually call, which keeps the noise down.
- **Automated update PRs** arrive weekly, grouped by module, and merge once tests pass.
- **`go mod why`** is required reading before adding anything. If a new package shows up as an indirect dependency, we want to know why.
- **We wrap at the edges.** Database access, rate limiting, and similar concerns sit behind small internal packages, so swapping an implementation touches one directory instead of fifty.

## Wrapping up

None of these libraries are exotic, and that's the point. Each one solves a specific problem well, stays out of the way, and has proven itself across many services. If your team has a dependency that has earned its keep, or one you were glad to delete, we'd love to hear about it.
