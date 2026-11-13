# A preview of Go version 1

For the past two years, the Go team has been iterating on a language that aims to make systems programming feel less like a chore. Go has grown from an experiment into something we rely on for real work. Now we are approaching a milestone: **Go version 1**, a stable release that we expect to hold steady for years. This post explains what that means, what is changing on the way there, and how you can prepare.

## Why a "version 1" at all?

Until now, Go has moved quickly. Weekly snapshots have shipped with changes to syntax, the standard library, and tooling. That pace has been great for refining the language, but it has been hard on anyone trying to build something lasting. Every snapshot has meant another round of fixing code that used to compile.

Version 1 is a promise. Programs written to the Go 1 specification will continue to compile and run correctly, unchanged, for the lifetime of that specification. Libraries, books, tutorials, and production services can all be built on that foundation without fear of the ground shifting.

This stability is not just a convenience. It is a feature of the language. Teams can invest in learning Go, writing tooling, and hiring for it, knowing the investment will not be wiped out by the next release.

## What is changing

Reaching a stable release means cleaning up rough edges while we still can. The changes fall into three groups.

### Language changes

We are making a small number of deliberate adjustments to the language itself:

- **A built-in `error` type.** Error handling is central to Go, so `error` becomes a predeclared interface type with a single `Error() string` method. This replaces ad hoc conventions that varied between packages.
- **Simpler map deletion.** Deleting from a map becomes a built-in operation, `delete(m, k)`, replacing the old assignment-with-flag idiom that confused newcomers.
- **Tighter rules for composite literals and struct copying.** Some corner cases that were previously ambiguous are now defined precisely.
- **Clarified `for range` semantics.** The behavior of range loops over maps, strings, and channels is specified more carefully, including what happens when a map is modified during iteration.

None of these are sweeping redesigns. The goal is to remove ambiguity, not to add novelty.

### Standard library reorganization

The standard library has accumulated packages that grew organically. For Go 1 we are reorganizing them into a more coherent hierarchy. Related packages move under common roots, a few rarely used packages are retired from the core distribution, and names are made more consistent. Some packages, such as `os` and `time`, gain cleaner APIs.

This is the largest source of breakage, which is exactly why it must happen *before* the freeze rather than after.

### Tooling

The `go` command is becoming the single entry point for building, testing, formatting, and fetching code. Alongside it we are shipping a tool called `fix` that rewrites old programs to match the new APIs automatically. Running it over your codebase should handle the bulk of the mechanical changes, and `gofmt` will continue to keep the result consistently formatted.

## What stability does and does not mean

It helps to be precise. The compatibility promise covers the language specification and the core standard library APIs. It does not cover everything:

- Programs that depend on unspecified behavior, such as map iteration order, may still break.
- Code that uses the `unsafe` package or depends on internal implementation details is outside the guarantee.
- Experimental packages and tools outside the main distribution may continue to evolve.

Performance will also keep improving. The compiler, garbage collector, and scheduler are free to get better, as long as correct programs stay correct.

## How to prepare

You do not need to wait for the final release to get ready. Here is what we suggest:

1. **Track the release candidates.** Build your code against recent snapshots so you see breakage early, in small doses.
2. **Run `fix` regularly.** Apply it to your repositories and review the diffs. It is designed to be safe to run repeatedly.
3. **Avoid relying on unspecified behavior.** If your tests pass only because of map ordering or similar accidents, fix them now.
4. **Pin your toolchain.** Record which release your builds use, so upgrades are a deliberate choice rather than a surprise.
5. **Report problems.** If `fix` mishandles your code or the new APIs feel wrong, tell us. After the freeze, that feedback becomes much harder to act on.

## Looking ahead

Go 1 is not the end of Go's evolution. It is the point where the language becomes a dependable base for everything built on top of it. After the release, work will continue on performance, tooling, and the ecosystem, while the core stays steady.

We are excited to see what you build once the ground stops moving. Try the release candidates, send us your feedback, and help us make Go 1 something worth depending on.
