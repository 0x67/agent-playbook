# The App Engine SDK and workspaces (GOPATH)

When we first moved part of our backend to Google App Engine, our Go code ended up in two places. The application lived in one directory tree, shaped the way the App Engine SDK expected. The libraries we shared with our command-line tools and internal services lived in our regular Go workspace. Keeping the two in sync meant copying files, using symlinks, and occasionally discovering in production that the copies had drifted apart.

This post covers how we fixed that by organizing our App Engine code around a standard Go workspace (`GOPATH`), and what we learned along the way.

## How things used to work

Early versions of the App Engine Go SDK had their own idea of where code lived. The development server compiled every `.go` file under your application directory, and imports were resolved relative to that directory. To use a package from elsewhere, you had to put a copy of it inside the app.

That model was simple for small apps. It worked against the rest of the Go toolchain, though. The `go` tool expects code to live in a workspace, with import paths that correspond to directories under `$GOPATH/src`. Our App Engine packages could not be built, vetted, or tested with the same commands we used everywhere else.

## The `goapp` tool and GOPATH support

Newer releases of the SDK shipped a tool called `goapp`. It is a thin wrapper around the standard `go` command that also knows where the App Engine packages live. More importantly, the SDK began resolving imports through `GOPATH`. An App Engine app could now import a package from your workspace the same way any other Go program would.

The practical effect was that the App Engine app no longer had to be an island. It became one more consumer of the code in our workspace.

## Our layout

Here is a simplified version of how we structured things:

```
$GOPATH/
  src/
    example.com/
      billing/            # shared business logic, no App Engine imports
        invoice.go
        invoice_test.go
      billing/gae/        # App Engine-specific glue
        handlers.go
      cmd/
        reconcile/        # command-line tool using billing
          main.go
apps/
  billing-api/
    app.yaml
    main.go               # tiny: imports example.com/billing/gae
```

There are a few deliberate choices here.

**The app directory is thin.** `apps/billing-api` contains `app.yaml` and one small Go file that imports our handlers package. Everything substantial lives in the workspace under a real import path.

**Core logic does not import App Engine.** The `billing` package knows nothing about the datastore or request contexts. It takes plain interfaces and returns plain values. This let our `reconcile` tool, our tests, and our App Engine app all share the same code.

**Platform glue is isolated.** The `billing/gae` package is the only place that talks to App Engine APIs. It adapts the datastore, URL fetch, and logging services to the interfaces `billing` expects.

## Build constraints for the in-between cases

Sometimes the boundary is not clean. You might want a package that uses App Engine services when it runs on App Engine and falls back to something else when it doesn't. The SDK sets the `appengine` build tag, so you can split implementations across files:

```go
// +build appengine

package storage

// Implementation backed by the App Engine datastore.
```

```go
// +build !appengine

package storage

// Implementation backed by our standard database client.
```

We use this sparingly. Every pair of tagged files is two code paths that can disagree, and each one needs its own tests. Where we can, we prefer the interface-and-adapter approach described above.

## Day-to-day workflow

With everything in one workspace, our commands became predictable:

- `go test example.com/billing/...` runs the platform-independent tests quickly, with no SDK involved.
- `goapp test example.com/billing/gae` runs tests that need the App Engine packages.
- `goapp serve apps/billing-api` starts the local development server.
- `goapp deploy apps/billing-api` uploads the app, including any workspace packages it imports.

Because the deploy step follows imports, we never have to remember which shared packages need to be copied in. If the app imports it, it ships.

## What we'd tell our past selves

1. **Treat the app directory as an entry point.** It should contain configuration and wiring, not logic.
2. **Keep platform imports at the edges.** Code that doesn't import App Engine is easier to test, reuse, and eventually migrate.
3. **Use one workspace.** Two sources of truth for the same package will drift apart eventually.
4. **Use build tags as a last resort.** They solve real problems, but they double your surface area.

## Looking forward

The Go ecosystem has since moved from `GOPATH` to modules, and newer App Engine runtimes build ordinary Go programs using a standard `go.mod`. The specific mechanics in this post have aged. The underlying lesson has held up: when your platform's tooling matches your language's tooling, the platform-specific layer can stay small, and the rest of your code can just be Go.
