# Go Modules: v2 and Beyond

Go modules have been the standard dependency system for years, yet major version bumps still trip up experienced teams. Our own migration of an internal library to v2 surfaced a few surprises, so we're sharing what we learned, along with the practices we now follow.

## Why Major Versions Are Different in Go

Most ecosystems treat a major version as a number in a manifest. Go treats it as part of the import path. This follows from the **import compatibility rule**:

> If an old package and a new package have the same import path, the new package must be backwards compatible with the old package.

When you make a breaking change, you can't reuse the path. A v2 module must declare itself differently:

```
module github.com/acme/widgets/v2

go 1.23
```

Consumers then import `github.com/acme/widgets/v2`. The payoff is large: v1 and v2 can coexist in one build, which makes incremental migration of large codebases possible.

## Choosing a Layout: Major Branch or Major Subdirectory

There are two supported ways to lay out a v2 release.

**Major branch.** Update the `module` line in `go.mod`, rewrite internal imports, and tag `v2.0.0`. Development continues on the same branch or on a dedicated `v2` branch. This is the simplest approach and the one we recommend for most projects.

**Major subdirectory.** Copy the code into a `v2/` directory with its own `go.mod`. This keeps v1 and v2 side by side on one branch. It helps if you need to support very old toolchains, but it duplicates code and complicates reviews.

We chose the major branch approach. Since modern Go resolves modules, not GOPATH, there was little reason to pay the duplication cost.

## The Migration Checklist

Here's the sequence that worked for us:

1. **Update the module path** in `go.mod` to end in `/v2`.
2. **Rewrite imports** across the repository. A simple tool does the job:
   ```
   find . -name '*.go' -exec sed -i '' \
     's#acme/widgets/#acme/widgets/v2/#g' {} +
   ```
   (On Linux, drop the empty string after `-i`.) Review the diff, since sed will also touch strings and comments.
3. **Run `go build ./...` and `go test ./...`** to catch missed paths.
4. **Update generated code**, such as protobuf outputs and mocks, which often embed import paths.
5. **Tag the release** with `git tag v2.0.0` and push it.
6. **Verify from a clean consumer** by running `go get github.com/acme/widgets/v2@v2.0.0` in a scratch module.

Step 6 is the one people skip. It catches problems like a stale `go.mod` or a tag pushed from the wrong commit.

## Pitfalls We Hit

**Forgetting nested modules.** If your repo contains other `go.mod` files, such as examples or tools, they import the root module by path. They need updating too.

**Partial rewrites.** One file importing the old path compiled fine, because v1 was still resolvable. The result was two copies of a type that looked identical but weren't interchangeable. The error messages ("cannot use x as widgets.Config value") are baffling until you notice the two import paths.

**Documentation drift.** READMEs, badges, and `pkg.go.dev` links all embed the path. Search for them.

**Pre-release tags.** Use `v2.0.0-rc.1` style tags to let early adopters test before you commit to the API. Once `v2.0.0` is published, the module proxy caches it permanently, so you can't quietly move it.

## Beyond v2: Habits That Reduce Pain

The best major version bump is the one you avoid. A few practices help:

- **Prefer additive change.** Add new functions and options rather than altering signatures. Functional options keep constructors extensible without breaking callers.
- **Keep the public surface small.** Use `internal/` packages liberally. Anything unexported or internal can change freely.
- **Deprecate deliberately.** Mark old APIs with a `// Deprecated:` comment so tooling surfaces it, and give consumers at least one minor release cycle.
- **Retract mistakes.** If you publish a bad version, the `retract` directive in `go.mod` warns users away without deleting history.
- **Run `gorelease`.** It compares your module against a prior version and flags incompatible changes before you tag.

## Closing Thoughts

Go's versioning model asks more of maintainers up front, but it rewards consumers with predictability: an import path tells you exactly which compatibility contract you're relying on. Once our team internalized that a major version is effectively a new module, the process stopped feeling like a special case.

If you're planning a v2, start with the checklist, validate from a clean consumer, and invest in tooling like `gorelease` so the next breaking change is a deliberate choice rather than an accident.
