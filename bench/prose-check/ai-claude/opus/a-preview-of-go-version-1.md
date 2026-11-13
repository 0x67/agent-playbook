# A preview of Go version 1

Go has moved quickly since its open-source release. Weekly snapshots have brought steady improvements, but also a steady stream of breaking changes. Anyone running Go in production knows the routine: pull a new release, rebuild, fix whatever broke, and repeat. That pace made sense for a young language finding its shape. For teams like ours who want to build long-lived services on it, the cost adds up.

That is why we're excited about Go version 1. The Go team has published a plan for a stable release of the language and its core libraries, and the central promise is simple: **programs written for Go 1 will keep compiling and running correctly for the lifetime of the Go 1 series.** This post walks through what's changing, what we expect the transition to look like, and how we're preparing.

## Why a stable release matters

Go 1 is less about new features and more about drawing a line. The team is using this moment to clean up rough edges in the language and reorganize the standard library. After that, they intend to stop breaking things. For us, that means:

- **Fewer upgrade surprises.** A minor Go 1.x release should not force code changes.
- **Better books, tutorials, and third-party libraries.** Authors can target one stable surface instead of a moving one.
- **Easier adoption.** It is much simpler to propose Go for a new project when you can point to a compatibility guarantee.

The promise has sensible limits. Security fixes, bug fixes, and changes involving the `unsafe` package may still affect some programs. In practice, though, this is the stability we've been waiting for.

## Language changes

Most of the language changes are small, but a few will touch nearly every codebase.

**A built-in `error` type.** The `os.Error` interface is being replaced by a predeclared `error` interface. This makes sense: errors are fundamental, and having them live in the `os` package was always a bit odd.

```go
// Before
func Open(name string) (*File, os.Error)

// Go 1
func Open(name string) (*File, error)
```

**A `rune` type for Unicode code points.** Ranging over a string now yields values of type `rune` instead of `int`, which makes intent clearer and leaves room for future changes to `int`'s size.

**Deleting map entries.** The unusual `m[k] = 0, false` syntax is replaced by a built-in function:

```go
delete(m, k)
```

**Other notable changes:**

- Struct and array values can be compared with `==` when their elements are comparable.
- Map iteration order is deliberately unpredictable, so code that relied on an accidental ordering will need fixing.
- Composite literals can omit the `&T` in elements of pointer type, which trims noise from table-driven tests.
- Goroutines may now be started during package initialization.

## Library reorganization

The standard library is getting a significant restructuring. Packages are moving into a clearer hierarchy, for example:

| Old path   | Go 1 path        |
|------------|------------------|
| `json`     | `encoding/json`  |
| `http`     | `net/http`       |
| `template` | `text/template`  |
| `utf8`     | `unicode/utf8`   |

Some less mature packages are moving out of the core distribution so they can keep evolving without being bound by the compatibility promise. The `time` package has also been redesigned around `time.Time` and `time.Duration` types, which should end a lot of ambiguity about units and representations.

## Tooling: `go fix` and the `go` command

Here's the most reassuring part: much of the migration is automated. The `go fix` tool rewrites source code to use the new APIs, handling import path changes, `os.Error` to `error`, the new `delete` syntax, and more. It won't catch everything, especially subtle behavioral changes like map ordering, but it removes most of the mechanical work.

Go 1 also introduces the `go` command as the standard way to build, test, and install packages. It replaces the Makefiles many of us have been maintaining. Projects that follow the expected directory layout will need almost no build configuration at all.

## How we're preparing

We have several internal services written in Go, so we're taking a staged approach:

1. **Tracking weekly snapshots in CI.** We build and test against the latest weekly so breakage shows up early, not on release day.
2. **Running `go fix` on a branch per service** and reviewing the diffs by hand rather than merging them blindly.
3. **Auditing for map-order assumptions.** We've found a few tests that passed only because iteration order happened to be stable.
4. **Migrating builds to the `go` command** and retiring our custom Makefiles.

## Looking ahead

Go 1 marks Go's transition from an interesting experiment to a dependable foundation. The language isn't done evolving, but future changes will happen within a compatibility framework that respects the code people have already written. We think that tradeoff is exactly right, and we're looking forward to building on it.

If you're using Go today, now is a great time to try the weekly snapshots, run `go fix`, and report anything that breaks. The more feedback the Go team gets before the release, the better Go 1 will be for all of us.
