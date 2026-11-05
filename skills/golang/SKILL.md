---
name: golang
description: >
  Idiomatic Go (Golang) engineering: writing, reviewing, refactoring, testing,
  and profiling Go code and services. Use whenever the user works in a Go
  codebase or asks anything involving .go files, go.mod, goroutines, channels,
  context, error handling, interfaces, generics, net/http, gRPC, testing,
  benchmarks, pprof, or Go tooling (go build, go test, go vet, golangci-lint).
  Trigger even when the user does not say "Go" but files or commands are
  clearly Go, or when they ask to build a service, CLI, or worker in a repo
  that has a go.mod. Specialist rules live in references/ and load through
  the routing table below.
---

# Go engineering skill

Write Go a seasoned Gopher would merge without comment: small interfaces, explicit errors, no clever abstractions, concurrency only where it pays for itself. Go rewards boring code. Goal: code that reads top-to-bottom and fails loudly.

## Routing table (mandatory)

Read matching reference BEFORE writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| naming, package layout, declarations, control flow, receivers, options, generics, iterators, comments | `references/style.md` |
| error returns, wrapping, sentinels, custom error types, panics, main/exit | `references/errors.md` |
| goroutines, channels, context, errgroup, sync, atomics, timers, shutdown, leaks | `references/concurrency.md` |
| any `_test.go`, benchmarks, fuzz, fakes, httptest, synctest | `references/testing.md` |
| net/http, middleware, slog, config, database, pgx, sqlc, gRPC, connect, workers, CLI | `references/services.md` |
| pprof, benchmark results, allocations, GC, PGO, escape analysis | `references/performance.md` |
| go vet, staticcheck, golangci-lint, govulncheck, go fix, go.mod, build flags, CI | `references/tooling.md` |
| picking APIs for a given go.mod version, migrating old idioms | `references/modern.md` |

Multiple matches: read all matched. Unsure: read `style.md` and `errors.md`.

## Before writing

1. Read `go.mod`. Note `go` line. Never use stdlib API newer than that line (`stdversion` vet fails otherwise). `references/modern.md` lists what each version unlocks.
2. Check repo conventions: `.golangci.yml`, existing test helpers, logger, router, DB driver. Repo convention beats these defaults.
3. Find existing package for the change. New package only for new concern.

## Non-negotiables

- `gofmt` clean. Imports grouped: stdlib, third-party, module-local.
- `context.Context` first parameter, named `ctx`. Never stored in struct.
- Accept interfaces, return concrete types. Define interfaces where consumed. 1-3 methods.
- Check every error. Handle once: wrap and return, or log and stop. Never both.
- Wrap: `fmt.Errorf("open config %q: %w", path, err)`. Lowercase, no trailing punctuation.
- Match: `errors.Is`, `errors.As`, `errors.AsType` (1.26+). Never `==` or type switch on wrapped errors.
- No panic in library code. `os.Exit` and `log.Fatal` only in `main`.
- No package-level mutable state. No `init()` except stdlib driver registration.
- Every goroutine: known starter, known stopper, error path. No fire-and-forget.
- Synchronous API by default. Caller adds concurrency.
- Zero values usable: `var mu sync.Mutex`, `var buf bytes.Buffer`, nil slice, nil map for reads.
- Early return. No `else` after `return`. Nesting depth 3 max.
- `any` not `interface{}`. `slices`, `maps`, `cmp`, `min`, `max`, `clear` over hand loops.
- `for i := range n`, `for range n`. Per-iteration loop vars (go >= 1.22): no `i := i`.
- `time.Duration` for durations, `time.Time` for instants. Never `int` seconds.
- `crypto/rand` for anything security-related. `math/rand/v2` otherwise.
- Comma-ok on type assertions and map reads where absence matters.
- Field names in struct literals. Struct tags on every serialized field.
- `internal/` for anything not public API. No `pkg/`, `util/`, `common/`, `helpers/`.
- Comments: full sentences starting with identifier name. Doc every exported symbol. Delete comments that restate code. No em dash characters.
- Tests must fail from project bug. No stdlib restatement, no getter tests, no struct readback.

## After writing (gate, in order)

```sh
gofmt -l .                 # must print nothing
go vet ./...
go build ./...
go test -race ./...
staticcheck ./...          # or: golangci-lint run   (when .golangci.yml present)
```

Optional: `go fix -diff ./...` (1.26+) to spot modernizable idioms. `govulncheck ./...` when deps changed. Not done until gate green. Report failures verbatim.

## Tool preference

- Symbols, references, hover: `LSP` tool (gopls) when exposed. Else `go doc <pkg>.<Sym>`, `mcp__fff__grep`, `rg`.
- Package API: `go doc -all <pkg>`. Never guess signatures.
- Global rules still apply: humanizer comments, Code Simplicity Discipline, Useless Test Ban, terminology guard (`snapshot`/`expected`, never `golden`). Cross-language naming, function size, and architecture: skill `software-design`.
