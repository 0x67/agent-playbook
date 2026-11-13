# Go App Engine SDK 1.5.5 released

Today we're releasing version 1.5.5 of the Go App Engine SDK. You can download it now from the App Engine downloads page.

This release updates the App Engine APIs and the bundled Go toolchain together. It also includes changes that are **not backwards-compatible**, so this post covers what changed, why we changed it, and how to move your apps to the new version with as little effort as possible.

## A stable toolchain

The SDK now builds your apps with **Go release.r60.2**, the current stable release of Go. Your local development environment uses the same compiler and standard library that we use to build your app in production. The behavior described in the Go release notes is the behavior you'll get, both on your laptop and when your app is serving traffic.

Tying the SDK to a stable release also gives us a clear upgrade path. When the Go team publishes a new stable release, we can move the SDK forward deliberately. We'll ship tooling to handle the changes rather than letting them reach you by surprise.

## New tools in the box

Three tools from the Go distribution now ship with the SDK. You'll find them in the root directory of the SDK:

- **`gofmt`** formats Go source in the standard style. If you aren't already running it on save, now is a good time to start.
- **`godoc`** shows documentation for Go packages, from the command line or in your browser.
- **`gofix`** rewrites Go source to account for API changes. It's the most important tool in this release, and we describe it in more detail below.

Because these tools ship with the SDK, the versions you run always match the libraries your app is built against. You don't need to keep a separate Go installation in sync.

## Introducing api_version 3

Some of the changes in this release are backwards-incompatible, so we've raised the SDK's `api_version` to **3**. Existing apps will need code changes before they can use it.

To opt in, update the `api_version` field in your app's `app.yaml`:

```yaml
application: myapp
version: 1
runtime: go
api_version: 3

handlers:
- url: /.*
  script: _go_app
```

The `api_version` number tells App Engine which version of the runtime and APIs your app expects. When you change it, you're telling us your code is ready for the new APIs.

## Let gofix do the heavy lifting

Updating code by hand for an API change is tedious and easy to get wrong. To help with that, we've customized the `gofix` that ships with the SDK with **App Engine-specific modules**. It knows about the changes to the `appengine` packages as well as the updates to the Go standard library, and it can rewrite most affected code for you.

To update an app, point `gofix` at your source directory:

```sh
/path/to/sdk/gofix /path/to/your/app
```

A few tips for a smooth migration:

1. **Start from a clean working copy.** Commit or back up your code first, so `gofix`'s changes show up as one diff that's easy to review.
2. **Read the diff.** `gofix` handles mechanical rewrites well, but you should still understand what changed in your code.
3. **Build and fix the rest.** Some changes need human judgment and can't be fixed automatically. The compiler will point you to anything `gofix` left behind.
4. **Run `gofmt`.** `gofix` keeps your formatting intact, but it's a good habit to run `gofmt` once more after any large change.

## Documentation on your machine

The SDK now includes the **source code for the `appengine` packages**. That means the bundled `godoc` can show App Engine API documentation directly, with no network connection or browser required:

```sh
/path/to/sdk/godoc appengine/datastore Get
```

This is especially useful during a migration. You can check the exact signature of a function in the version of the API you're building against. You won't have to wonder whether a web page describes an older or newer release.

## Important: api_version 2 is deprecated

With this release, **`api_version` 2 is deprecated**. Go apps that still use `api_version: 2` **will stop working after 16 December 2011.**

Please update your apps before then. For most apps, the migration consists of running `gofix`, fixing the remaining compiler errors, testing locally, and redeploying. We recommend doing it soon rather than waiting until the deadline.

## Upgrade checklist

1. Download and install SDK 1.5.5.
2. Commit or back up your app's source.
3. Run `/path/to/sdk/gofix /path/to/your/app` and review the changes.
4. Set `api_version: 3` in `app.yaml`.
5. Fix any remaining build errors, using the local `godoc` as a reference.
6. Test with the development server.
7. Deploy, well before 16 December 2011.

## Learn more

For the complete list of changes in this release, see the release notes. If you have questions about the new SDK, run into trouble migrating, or have ideas for what we should build next, please post in the Go App Engine discussion group. We read every message, and your feedback has shaped much of this release.

Happy coding, and happy upgrading.
