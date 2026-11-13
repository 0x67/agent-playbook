# Go 1.10 is released

Go 1.10 shipped on February 16, 2018, six months after Go 1.9. As usual, the language itself barely changed. Most of the work went into the toolchain, and that is where your day-to-day experience will improve. Here's what we think matters most and what to watch for when you upgrade.

## Builds are now cached

The biggest change is the new **build cache**. `go build` and `go install` now store compiled packages in a cache directory and reuse them whenever the inputs haven't changed. You can find the location with `go env GOCACHE`.

In practice, you no longer need `go build -i` or a careful `go install` routine to keep incremental builds fast. Rebuilding a large service after a one-line change now recompiles only what depends on that change. The cache is keyed on source content, build flags, and toolchain version, so you shouldn't have to clear it by hand. If you ever want to, `go clean -cache` will do it.

One related change: `go install` now installs only the packages named on the command line, not their dependencies. The cache makes the old behavior unnecessary.

## Tests are cached too

`go test` now caches successful test results. If you rerun a package's tests and nothing relevant has changed (sources, test binary, flags, environment variables, or files the test reads), you'll see `(cached)` instead of a fresh run.

This makes `go test ./...` on a large repository much cheaper, but it has consequences:

- Caching applies only in package-list mode (`go test ./...`, not plain `go test`) and only with a small set of flags, such as `-run`, `-short`, `-v`, and `-cpu`.
- Tests that depend on external state the toolchain can't see, like a database, network service, or the wall clock, may be skipped when you expected them to run.
- To force a run, use `-count=1`. This is the idiomatic way to disable test caching.

We've added `-count=1` to the integration test targets in our CI configuration. We recommend you check your own pipelines for the same issue.

## `go vet` runs during `go test`

`go test` now runs a high-confidence subset of `go vet` checks before it runs your tests. A vet failure fails the test run. The checks were chosen to have very few false positives. Typical catches are malformed `Printf` format strings and similar bugs that are almost always real. If you need to turn this off temporarily, pass `-vet=off`.

## Other toolchain improvements

- **`go test -json`** produces machine-readable output, which helps CI dashboards and IDE integrations. The new `go tool test2json` converts existing test binary output.
- **`go test -failfast`** stops after the first failing test.
- **Scoped build flags:** `-gcflags`, `-ldflags`, and `-asmflags` now apply only to the packages named on the command line. To apply them everywhere, use a pattern, for example `-gcflags=all=-N -l` for debugger-friendly builds.
- **Better debug info:** the compiler emits improved DWARF for optimized binaries, including lexical scopes and constants. Delve users will notice the difference.
- **Cgo** can now pass Go strings to C directly using the `_GoString_` type in the preamble.
- **GOROOT** is now inferred from the location of the `go` binary, so relocated installations work without extra configuration.

## Standard library highlights

A few additions we expect to use right away:

**`strings.Builder`** builds strings efficiently with minimal copying:

```go
var b strings.Builder
for i := 3; i > 0; i-- {
	fmt.Fprintf(&b, "%d...", i)
}
b.WriteString("ignition")
fmt.Println(b.String())
```

**`json.Decoder.DisallowUnknownFields`** makes strict config parsing easy. Typos in configuration files now become errors instead of being silently ignored:

```go
dec := json.NewDecoder(r)
dec.DisallowUnknownFields()
if err := dec.Decode(&cfg); err != nil {
	return fmt.Errorf("parsing config: %v", err)
}
```

Also worth knowing:

- `math.Round` and `math.RoundToEven` finally exist, so you can drop the hand-written rounding helpers.
- `math/rand.Shuffle` gives you a correct Fisher–Yates shuffle.
- `database/sql/driver.Connector` and `sql.OpenDB` let drivers accept structured configuration instead of DSN strings.
- `time.LoadLocationFromTZData` loads time zones from raw tzdata bytes.
- The `unicode` package now supports Unicode 10.0.

## Runtime changes

- The 1024 limit on `GOMAXPROCS` is gone.
- `runtime.LockOSThread` and `UnlockOSThread` now nest. If a goroutine exits while still locked to its thread, that thread is terminated instead of being returned to the pool. This makes it safer to modify per-thread state, such as Linux namespaces.
- The garbage collector has been tuned to reduce its impact on allocation latency.

## Upgrade notes

Our checklist for the move to 1.10:

1. **Audit tests that touch external systems** and add `-count=1` where cached results would be misleading.
2. **Expect new vet failures** in `go test` output. Fix them rather than reaching for `-vet=off`.
3. **Update scripts that pass `-gcflags` or `-ldflags`** if they relied on the flags applying to all dependencies.
4. **Check your platforms:** Go 1.10 is the last release that will run on OS X 10.8 Mountain Lion, OS X 10.9 Mavericks, and OpenBSD 6.0.

## Wrapping up

Go 1.10 is a quality-of-life release: faster builds, smarter tests, and a handful of useful library additions, all with the usual Go 1 compatibility promise. You can download it from [golang.org/dl](https://golang.org/dl/), and the [full release notes](https://golang.org/doc/go1.10) cover everything we skipped. Thanks to the Go team and the many contributors who made this release happen.

---

*Note: Go 1.10 came out in February 2018, and many newer Go releases have followed. If this post is meant for publication today rather than as an archival or example piece, consider covering a current release instead.*
