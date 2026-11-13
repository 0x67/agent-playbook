# Go Modules: v2 and Beyond

Every library eventually hits a wall. An API that seemed reasonable two years ago now forces awkward workarounds, a function signature can't accommodate a new requirement, or a type was exported that never should have been. At some point the honest fix is a breaking change, and in Go a breaking change means a new major version.

Go handles major versions differently from most ecosystems. If you've only published v0 and v1 modules, your first v2 release can be surprising. This post covers how it works, why it was designed that way, and how to ship one without breaking your users.

## The Import Compatibility Rule

Go's approach rests on one principle, the *import compatibility rule*:

> If an old package and a new package have the same import path, the new package must be backwards compatible with the old package.

It follows that if you break compatibility, you must change the import path. Go enforces this through *semantic import versioning*. Starting at v2, the major version becomes part of the module path:

```
github.com/acme/widgets      // v0.x and v1.x
github.com/acme/widgets/v2   // v2.x
github.com/acme/widgets/v3   // v3.x
```

This can feel like extra ceremony, but it solves a real problem. Because v1 and v2 have different paths, they are effectively different modules, and both can exist in the same build. Suppose your service depends on library A, which uses `widgets` v1, and on library B, which has moved to v2. Everything still compiles. The diamond dependency doesn't stall, and the whole ecosystem doesn't have to upgrade in lockstep.

## Two Ways to Lay Out v2

**Major branch.** Update the `module` directive in your existing `go.mod`, update imports, and tag `v2.0.0`. If you still need to maintain v1, cut a `release/v1` branch first. Most projects use this approach today, and it's the one we recommend because it keeps the repository layout clean.

**Major subdirectory.** Create a `v2/` directory containing a copy of the code with its own `go.mod`. This layout mattered mainly for compatibility with pre-modules GOPATH tooling, which few teams still use. Because it duplicates code, we avoid it unless there's a specific reason.

## The Mechanics

With the major branch approach:

```sh
# 1. Change the module path
go mod edit -module github.com/acme/widgets/v2

# 2. Update every import of the module's own packages
#    (a tool like gomajor, or a careful find-and-replace)

# 3. Verify
go build ./... && go test ./...

# 4. Tag and push
git tag v2.0.0
git push origin v2.0.0
```

People often skip step 2. Any package in your module that imports a sibling package must use the new `/v2` path. If it doesn't, your v2 code will import packages from v1 instead. That bug is confusing because it compiles without complaint.

The package *name* does not change. Code in `github.com/acme/widgets/v2` still declares `package widgets`, and consumers still call `widgets.New()`.

## Consuming v2

To upgrade, users request the new path explicitly:

```sh
go get github.com/acme/widgets/v2@latest
```

Then they update their import statements. `go get -u` never moves to a new major version on its own, and that's intentional: users opt in to breaking changes rather than stumbling into them.

## Pitfalls We've Hit

**Mismatched tags.** If you tag `v2.0.0` without changing the module path, the Go command rejects it with an error saying the module path must match the major version. Repositories without a `go.mod` get the legacy `+incompatible` suffix instead. Always update the path before tagging.

**Tags are forever.** Once the module proxy caches a version, you can't change it. If you publish a broken release, don't delete the tag. Add a `retract` directive in a later version:

```
retract v2.1.0 // Contains a data race in Pool.Get.
```

**Not pointing users to the new version.** Add a deprecation comment to v1's `go.mod` and publish one final v1 release that includes it:

```
// Deprecated: use github.com/acme/widgets/v2 instead.
module github.com/acme/widgets
```

`go list -m -u` and gopls will then show the notice to anyone still on v1.

## Do You Actually Need v2?

Before reaching for a major version, ask whether the change can be additive. You might add a new function alongside the old one, an options struct, or a new package. Each major version splits your user base and, for a while, doubles your maintenance burden. We save v2 for changes that can't be made compatibly.

When you do need it, Go's design makes it safe. Changing the import path costs little, and in return upgrades are deliberate and old and new versions can run side by side.
