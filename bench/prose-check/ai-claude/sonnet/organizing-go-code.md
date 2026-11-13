# Organizing Go code

Every Go project starts the same way: a `main.go` and a few functions. Six months later, there are forty packages, three of them called `util`, and nobody is sure where new code belongs. Go gives you very few rules about project layout, which is a feature, but it means the team has to supply its own discipline. This post covers the conventions that have worked for us.

## Start simple, and stay simple longer than you think

The most common mistake we see is premature structure. Developers create `controllers/`, `services/`, `repositories/`, and `models/` directories before there is a single endpoint. This imports habits from other ecosystems and works against how Go packages are meant to be used.

A new service can live happily in one package:

```
myservice/
├── go.mod
├── main.go
├── server.go
├── store.go
└── store_test.go
```

Split files freely, since files are cheap. Split packages only when you have a reason. A package boundary is a promise about API surface, and every exported identifier is something you now have to maintain.

## Organize by responsibility, not by type

When a package does need to be split, resist grouping code by what kind of thing it is. A `models` package that holds every struct in the system becomes a dumping ground, and everything ends up depending on it.

Group by what the code does for the domain instead:

```
billing/
invoice/
auth/
notification/
```

Each package owns its types, its logic, and its storage interface. A reader looking for how invoices work opens one directory, not four.

A good test is the package name at the call site. `invoice.Create` reads well. `services.CreateInvoice` repeats itself, and `utils.Helper` says nothing at all.

## Use `internal/` to make boundaries real

Go's `internal` directory is one of the most underused tools in the language. Any package under `internal/` can only be imported by code rooted at the parent of that directory. The compiler enforces it.

```
myservice/
├── cmd/
│   └── myservice/
│       └── main.go
├── internal/
│   ├── invoice/
│   ├── auth/
│   └── platform/
└── go.mod
```

Unless you are writing a library meant for external consumers, put most of your code in `internal/`. You can refactor freely because no one outside the module can depend on it. Promote a package out of `internal/` deliberately, when you actually want to support it as public API.

## Keep `main` thin

Put binaries under `cmd/<name>/` and keep `main.go` boring. It should parse flags and environment, construct dependencies, wire them together, and start the program. Business logic belongs elsewhere.

```go
func main() {
    cfg := config.FromEnv()
    db := postgres.Open(cfg.DatabaseURL)
    svc := invoice.NewService(invoice.NewStore(db))
    log.Fatal(http.ListenAndServe(cfg.Addr, api.NewHandler(svc)))
}
```

This makes the interesting code testable without launching a process, and it makes the dependency graph readable in one place.

## Define interfaces where they are used

In Go, interfaces are satisfied implicitly, so the consumer should define the interface, not the producer. If the `invoice` package needs to save data, it declares the small interface it needs:

```go
type Store interface {
    Save(ctx context.Context, inv Invoice) error
}
```

The Postgres implementation lives elsewhere and never needs to import `invoice` just to implement an interface. This keeps interfaces small, avoids import cycles, and makes fakes in tests trivial to write.

## Avoid import cycles by design

Go forbids import cycles, and it is tempting to treat the error as an annoyance to route around. Treat it as feedback. A cycle usually means two packages are really one, or that a shared concept needs to be pulled into a third, lower-level package. Dependencies should point in one direction: from entry points, through domain logic, down to infrastructure.

## Name things plainly

Package names should be short, lowercase, and singular, with no underscores. Avoid `util`, `common`, and `helpers`. If you cannot name a package by what it provides, the code in it probably does not belong together. Also avoid stutter: `invoice.InvoiceService` should be `invoice.Service`.

## Refactor when it hurts

No layout is correct forever. Revisit structure when you feel real friction: a package that everything imports, a file that has grown to thousands of lines, or tests that need heavy setup. Moving code in Go is cheap, with good tooling like `gopls` handling renames and moves, so you do not need to get it right on day one.

## Summary

- Start with one package and split only with reason.
- Group by domain responsibility, not by type.
- Use `internal/` to enforce boundaries.
- Keep `main` thin and put binaries in `cmd/`.
- Define interfaces in the consumer.
- Treat import cycles as design feedback.
- Name packages for what they provide.

The goal is not a perfect tree. It is a codebase where a new engineer can guess where something lives, and guess correctly most of the time.
