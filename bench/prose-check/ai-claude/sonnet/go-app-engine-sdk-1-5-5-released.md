# Go App Engine SDK 1.5.5 released

We're happy to announce the release of version 1.5.5 of the Go App Engine SDK. This release focuses on the things you've told us matter most: a smoother local development loop, better visibility into production behavior, and fewer surprises when you deploy. Below is a tour of what's new, what's changed, and what you should know before upgrading.

## Highlights

- Faster local dev server startup and rebuilds
- Improved datastore query handling and clearer errors
- New request-scoped logging helpers
- Updated Go toolchain support
- Assorted bug fixes and stability improvements

## A faster local development loop

The most common complaint we hear is about the time between saving a file and seeing the result. In 1.5.5 we reworked how the development server detects changes and rebuilds your application.

Previously, the dev server rescanned the full application tree on every request to decide whether a rebuild was needed. For small projects this was fine, but for larger codebases with many packages the overhead added up. The server now keeps a file-watch index and only rebuilds the packages whose sources actually changed, then relinks. In our internal benchmarks on a mid-sized application (about 150 packages), incremental rebuilds dropped from several seconds to well under one second. Cold start also improved, because the dev server now caches dependency analysis between runs.

You don't need to change anything to benefit. If you'd like to opt out, for example because you work on a filesystem that doesn't deliver change notifications reliably, you can pass the `--watch=false` flag to fall back to the previous behavior.

## Datastore improvements

We've made several changes to the datastore package aimed at making queries easier to reason about.

**Clearer errors.** Missing-index errors now include the exact composite index definition you need, formatted so you can paste it straight into your `index.yaml`. Previously, you had to reconstruct it from the query yourself.

**Safer projections.** Projection queries now return a descriptive error when a projected property is also used in an equality filter, a combination the backend doesn't support. Before, this surfaced as an opaque RPC failure.

**Cursor handling.** We fixed an issue where cursors obtained from a query with an offset could, in rare cases, resume at the wrong position. If you paginate with both offsets and cursors, we recommend upgrading.

## Request-scoped logging helpers

Correlating log lines to a single request has always been possible but required boilerplate. 1.5.5 adds helpers to the `appengine/log` package that attach request metadata automatically:

```go
func handler(w http.ResponseWriter, r *http.Request) {
    c := appengine.NewContext(r)
    log.Infof(c, "processing order %s", orderID)
    // Lines are grouped with the request in the logs viewer
}
```

The existing `Debugf`, `Infof`, `Warningf`, and `Errorf` functions behave the same as before, but now preserve request grouping across goroutines that share a derived context. This makes it much easier to follow the path of a request that fans out into concurrent work.

## Toolchain support

The SDK now bundles an updated Go toolchain and standard library. Most applications will compile unchanged, but there are two things worth checking:

1. **Stricter vet checks.** The bundled `go vet` flags a few more suspicious constructs, such as misuse of `Printf`-style verbs in logging calls. These are reported as warnings during local builds and do not block deployment.
2. **Deprecated APIs.** A small number of long-deprecated helpers have been marked for removal in a future release. Build output now prints a notice when you use them, along with the recommended replacement.

## Bug fixes

- Fixed a race in the dev server's task queue emulator that could cause tasks to run twice under heavy load.
- Fixed memcache `CompareAndSwap` returning a spurious error when the item had been evicted between read and write.
- Resolved a crash in the blobstore upload handler when the multipart boundary contained unusual characters.
- Corrected timezone handling for cron schedule previews in the local admin console.
- Improved shutdown behavior so that in-flight requests complete before the dev server exits.

## Upgrading

Download the new SDK from the usual downloads page and unpack it over your existing installation, or replace the directory entirely if you prefer a clean install. Then rebuild your application and run your tests locally before deploying.

A few recommendations:

- Run your full test suite against the new SDK before pushing to production.
- Review any build warnings from the stricter vet checks; they often point at real bugs.
- If you rely on datastore cursors with offsets, redeploy soon to pick up the fix.

There are no breaking changes to the public API in this release, and applications built with earlier 1.5.x versions should continue to run without modification.

## What's next

We're already working on the next set of improvements, including better support for running multiple modules locally and more detailed profiling hooks for production requests. As always, your feedback shapes our priorities. If you hit a problem or have an idea, let us know through the issue tracker or the community forum.

Thanks to everyone who reported bugs and tested pre-release builds. Happy shipping!
