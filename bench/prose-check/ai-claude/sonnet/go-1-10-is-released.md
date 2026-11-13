# Go 1.10 is released

Last month, the Go team shipped Go 1.10, the eleventh major release of the language and toolchain. Six months after Go 1.9, this release continues the project's steady, conservative cadence: few language changes, meaningful tooling improvements, and performance gains that most teams get simply by recompiling. Here's what stood out to us as an engineering team that runs Go in production, and what we're doing about it.

## Language and ports

Go 1.10 makes only small refinements to the language. The spec clarifies a few corner cases around method expressions and constant shifts, but nothing that should change the behavior of existing programs. The Go 1 compatibility promise holds, so upgrading is low-risk.

On the platform side, Go 1.10 is the last release to support OS X 10.8 through 10.9 and the last to support FreeBSD 10.x. It also adds support for the 64-bit MIPS big-endian architecture on Linux. If you target older Apple or FreeBSD environments, now is the time to plan your migration.

## Build and test caching

The headline feature for day-to-day development is the new build cache. The `go` command now caches compiled packages and reuses them across builds, so repeated builds, and especially incremental ones, are noticeably faster. The cache lives in a user-level directory by default and is managed automatically.

This changes an old habit: `go install` is no longer needed just to speed up later builds. Stale results are detected using content hashes of inputs rather than timestamps, so correctness doesn't depend on file modification times.

Test results are cached too. When you run `go test` in package list mode and neither the code nor the test inputs have changed, Go replays the prior output and marks it `(cached)`. For our larger repositories this noticeably shortens the inner development loop. For tests that must always run, such as those touching external services, `-count=1` bypasses the cache.

## Automatic `go vet` during `go test`

`go test` now runs a small, high-confidence subset of `go vet` checks before executing tests. If vet finds problems, the tests fail to run. The subset focuses on issues that are almost always real bugs, such as printf-style format mismatches. This surfaces mistakes earlier in the workflow, though it may expose latent issues in older code bases. Teams can disable it with `-vet=off` while they clean up, though we'd recommend fixing the findings instead.

## Toolchain and runtime improvements

Several smaller changes add up:

- **Compiler and linker:** Binaries are built with improved optimizations, and the compiler's inlining and code generation continue to improve. In our benchmarks, most services saw small but real CPU improvements without code changes.
- **`strings.Builder`:** A new type for efficiently building strings, avoiding the extra copy that `bytes.Buffer` incurs when converting to a string. It's a simple win in hot paths that assemble output.
- **`runtime` and cgo:** Cgo gains better handling for C types and more precise behavior around pointer passing. Teams with cgo-heavy code should read the release notes carefully.
- **`go fmt` and `go doc`:** Minor formatting changes and better documentation output. Expect a few small diffs if you reformat an existing tree.
- **Security and crypto:** The standard library tightens several TLS and x509 behaviors, including stricter hostname verification.

Together these changes make Go 1.10 feel less like a flashy release and more like a refinement of the workflow Go developers already use.

## What we're doing

Our upgrade plan follows the approach we've used for previous releases:

1. **Update CI first.** We add Go 1.10 as a build target alongside our current version and watch for new vet failures or behavioral changes.
2. **Fix vet findings.** Automatic vet in `go test` will likely flag some old issues. We treat those as real bugs and fix them rather than disabling the checks.
3. **Audit caching assumptions.** Any test that depends on external state gets `-count=1` or is rewritten to be hermetic. Cached passes can mask flaky or environment-dependent tests.
4. **Roll out gradually.** Internal tools go first, then lower-risk services, then critical-path systems, with benchmark and error-rate comparisons at each step.

## Should you upgrade?

For most teams, yes. The compatibility guarantee keeps the risk small, and the build and test caching alone make the upgrade worth it for developer productivity. The main friction points are stricter vet checks and any dependence on older OS versions.

We're grateful to the Go team and the many contributors who made this release possible. If you've already upgraded, we'd love to hear how it went, especially any surprises in your build times or test suites. Check the official release notes for the full list of changes, then give Go 1.10 a try in your own environment.
