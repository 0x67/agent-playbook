# The App Engine SDK and workspaces (GOPATH)

If you've built Go services for Google App Engine, you've probably hit this: your project builds fine with `go build`, but `goapp serve` or `dev_appserver.py` can't find your packages. Or the reverse: everything runs locally, then the deploy fails with an import error. Almost every time, the cause is the same, which is how the App Engine SDK interacts with your `GOPATH`.

This post explains how the SDK finds your code, the mistakes we've seen on our own teams, and the layout that has worked best for us.

## A quick refresher on GOPATH

In the classic Go workflow, `GOPATH` is an environment variable pointing to one or more workspace directories. Each workspace has a conventional structure:

```
$GOPATH/
  src/
    github.com/yourco/yourapp/
  pkg/
  bin/
```

Import paths map directly to directories under `src`. When your code says `import "github.com/yourco/yourapp/handlers"`, the toolchain looks in `$GOPATH/src/github.com/yourco/yourapp/handlers`.

The App Engine SDK for Go bundles its own modified Go toolchain and standard library, including the `appengine` packages. It doesn't simply use the Go installation on your machine, and that is where most of the confusion starts.

## How the SDK resolves your code

When you run the development server, the SDK does roughly three things:

1. **Reads `app.yaml`** from the directory you point it at, to learn the runtime and handlers.
2. **Builds the application** using its bundled Go tooling, resolving imports against the `GOPATH` in effect.
3. **Runs the result** in a sandboxed environment that mimics production.

The key point is step 2. The SDK's toolchain consults `GOPATH` just like the standard one, but the SDK's own packages take precedence for anything in its standard library. If your workspace contains a conflicting copy of `google.golang.org/appengine` or an older `appengine` package, you can get confusing type mismatches where two seemingly identical packages are treated as different.

## Common failure modes

**1. `app.yaml` outside the workspace.**
If your application directory lives outside `$GOPATH/src`, imports of your own sub-packages won't resolve. The build succeeds for single-file apps and then breaks the moment you split code into packages. Keep the app inside the workspace.

**2. Multiple workspaces, ambiguous resolution.**
`GOPATH` can list several directories separated by colons (semicolons on Windows). When the same import path exists in more than one, the first match wins. We've seen stale vendored copies in a secondary workspace silently shadow the real code.

**3. Vendored dependencies versus workspace dependencies.**
Mixing a `vendor/` directory with libraries installed via `go get` leads to duplicates. Two copies of a package produce errors like `cannot use x (type *foo.T) as type *foo.T`. Pick one strategy per application.

**4. Shell and IDE environments disagree.**
Your terminal may have `GOPATH` set while your editor or a CI runner doesn't. The SDK inherits whatever environment launched it, so the same command can behave differently in different places. Print `go env GOPATH` as the first step of any debugging session.

**5. Deploying from the wrong directory.**
Deployment uploads files relative to the application directory. If `app.yaml` sits deeper than your shared packages, those packages may never be uploaded, and the deployed app fails even though local runs worked.

## The layout we recommend

For a service with shared code, we keep one workspace per developer and place the app as a subdirectory of the repository:

```
$GOPATH/src/github.com/yourco/platform/
  services/
    api/
      app.yaml
      main.go
  internal/
    auth/
    storage/
```

Then:

```sh
export GOPATH=$HOME/go
cd $GOPATH/src/github.com/yourco/platform/services/api
goapp serve
```

A few rules keep this stable:

- **One workspace, one source of truth.** Avoid secondary entries in `GOPATH` unless you have a clear reason.
- **No copies of the `appengine` package in your workspace.** Let the SDK supply it, and check that `go get` hasn't pulled in a rival version.
- **Use `goapp` consistently.** Running `goapp test` and `goapp build` ensures you compile against the same libraries the dev server uses, rather than your system Go.
- **Pin the environment in scripts.** Our Makefile sets `GOPATH` explicitly so CI and local runs behave identically.

## Debugging checklist

When something doesn't resolve, work through this list:

1. Run `go env GOPATH` and confirm it matches your expectation.
2. Confirm the app directory is under `$GOPATH/src`.
3. Search the workspace for duplicate packages: `find $GOPATH/src -type d -name appengine`.
4. Check for a stray `vendor/` directory shadowing workspace packages.
5. Try `goapp build ./...` from the app directory to surface import errors without starting the server.

## Looking ahead

Go modules have changed how dependencies are managed, and newer App Engine runtimes build your code with the standard toolchain and modules rather than the legacy SDK. If you're starting a new service, prefer a modern runtime and skip `GOPATH` entirely. But many production systems still run on the older model, and for those, understanding how the SDK reads your workspace saves hours of guessing.

The short version: keep your app inside a single workspace, let the SDK own the `appengine` packages, and make sure every tool in your pipeline sees the same `GOPATH`.
