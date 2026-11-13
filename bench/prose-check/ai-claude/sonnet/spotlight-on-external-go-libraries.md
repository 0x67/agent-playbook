# Spotlight on external Go libraries

Go's standard library is one of the language's great strengths. `net/http`, `encoding/json`, `database/sql`, and `log/slog` take you remarkably far without a single `go get`. But every team eventually reaches the point where the standard library is not the right tool for a specific job. This post covers how we think about external dependencies, and highlights a few libraries that have earned a permanent place in our codebase.

## How we decide whether to add a dependency

Before pulling in a library, we ask four questions:

1. **Does the standard library already do this well enough?** Often it does. Go 1.22's enhanced `http.ServeMux` made many routers unnecessary for simple services.
2. **Who maintains it, and how active is it?** We look at release cadence, open issue triage, and whether more than one person can merge.
3. **How large is the transitive dependency tree?** A small helper that drags in forty modules is rarely a good trade. `go mod graph` is your friend.
4. **Can we replace it later?** Libraries that sit behind a narrow interface are cheap to swap. Libraries that leak their types through your whole codebase are not.

If a candidate passes all four, we add it, and we wrap it where it makes sense.

## Libraries we reach for

### cobra and pflag: command-line tools

For internal CLIs, [spf13/cobra](https://github.com/spf13/cobra) gives us subcommands, flag parsing, shell completion, and generated help text. The standard `flag` package works fine for a single-purpose binary, but once a tool grows to several subcommands, cobra saves a lot of boilerplate and gives users a consistent experience.

```go
var rootCmd = &cobra.Command{
    Use:   "deployctl",
    Short: "Manage deployments",
}

func main() {
    if err := rootCmd.Execute(); err != nil {
        os.Exit(1)
    }
}
```

### testify: readable tests

[stretchr/testify](https://github.com/stretchr/testify) is polarizing, but we find `require` and `assert` make table-driven tests much easier to scan. We use `require` for preconditions that should stop the test and `assert` for checks where continuing gives useful extra context.

```go
got, err := ParseConfig(input)
require.NoError(t, err)
assert.Equal(t, "production", got.Environment)
```

We pair it with [google/go-cmp](https://github.com/google/go-cmp) when comparing complex structs, since its diffs are far more informative than a plain equality failure.

### pgx: PostgreSQL access

[jackc/pgx](https://github.com/jackc/pgx) is our default PostgreSQL driver. Its native interface supports connection pooling through `pgxpool`, batching, `COPY`, and rich type support, including arrays and JSONB. For most services we use it directly rather than through `database/sql`, accepting a tighter coupling in exchange for better performance and features. Pairing it with [sqlc](https://sqlc.dev) lets us write plain SQL and get type-safe Go code generated from it, which has eliminated an entire class of runtime scan errors.

### errgroup and singleflight: concurrency helpers

The `golang.org/x/sync` module is technically maintained by the Go team, but it lives outside the standard library, so it counts as external. Two packages stand out:

- **errgroup** coordinates a group of goroutines, propagates the first error, and cancels a shared context. It replaces a lot of hand-rolled `sync.WaitGroup` and error channel code.
- **singleflight** collapses duplicate concurrent calls for the same key into one. It has been very effective at protecting downstream services from cache stampedes.

```go
g, ctx := errgroup.WithContext(ctx)
for _, id := range ids {
    g.Go(func() error {
        return process(ctx, id)
    })
}
if err := g.Wait(); err != nil {
    return err
}
```

### OpenTelemetry: observability

The [OpenTelemetry Go SDK](https://opentelemetry.io/docs/languages/go/) is how we standardize traces and metrics across services. It is a large dependency, so we hide it behind a small internal package that configures exporters and exposes a handful of helpers. That keeps instrumentation consistent and leaves us room to adjust when the SDK evolves.

## Keeping dependencies healthy

Choosing good libraries is only half the job. A few habits keep our dependency footprint manageable:

- **Run `govulncheck` in CI.** It reports only vulnerabilities in code paths you actually call, which keeps the signal-to-noise ratio high.
- **Automate updates.** Dependabot or Renovate opens small, frequent PRs, which are far easier to review than a yearly mega-upgrade.
- **Run `go mod tidy` and `go mod why` regularly.** Unused or surprising dependencies tend to accumulate quietly.
- **Vendor only when needed.** For most services, the module proxy and checksum database are sufficient. We vendor for a few build environments with restricted network access.

## Wrapping up

The best Go dependencies tend to share a few traits: a focused scope, a stable API, a modest dependency tree, and maintainers who care about compatibility. When a library meets that bar, it can save weeks of work and raise the quality of your code. When it does not, the standard library and a few dozen lines of your own code are often the better answer.

What libraries have earned a place in your Go projects? We would love to hear about them, so share your favorites with us and we may feature them in a future spotlight.
