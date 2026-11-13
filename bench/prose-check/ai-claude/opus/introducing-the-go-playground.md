# Introducing the Go Playground

Every Go developer has opened a browser tab to [go.dev/play](https://go.dev/play) at some point, to check how a slice behaves after an `append` or to send a teammate a minimal reproduction of a bug. The public playground is one of the most useful tools in the Go ecosystem. Inside a company codebase, though, it has two hard limits: it can't import our internal modules, and it's no place to paste proprietary code.

Today we're introducing our internal **Go Playground**. It's a browser-based environment for writing, running, and sharing Go programs that can import anything in our monorepo and private module registry. It's available now to every engineer, with no setup required.

## Why we built it

Over the past year, we kept seeing the same pattern in code reviews and incident channels. Someone would ask, "What does `retry.Do` actually do when the context is canceled?" Twenty minutes later the answer would arrive, after someone had cloned a repo, written a throwaway `main.go`, and pasted the output into chat. Across hundreds of engineers, that time adds up.

We wanted the answer to be a link. You click it and see the code and its output, then edit it and run it again.

## What it does

- **Imports internal packages.** You can import any module published to our internal proxy, either at a tagged version or at the head of `main`.
- **Supports multiple Go versions.** A dropdown lets you choose from the three most recent Go releases, so you can check behavior changes before an upgrade.
- **Handles multi-file programs.** As in the public playground, you can separate files with `-- filename --` headers, including a `go.mod`, to build small multi-package examples.
- **Runs tests and benchmarks.** If your snippet defines `TestXxx` functions, the playground runs `go test` instead of `go run`. Benchmarks work too, but shared hardware makes the numbers noisy.
- **Creates permanent links.** Every snippet gets a short URL that never changes, so links in design docs and postmortems keep working.

Here's a typical snippet:

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"

	"go.example.internal/platform/retry"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()

	attempts := 0
	err := retry.Do(ctx, func() error {
		attempts++
		return errors.New("still failing")
	})
	fmt.Println(attempts, err)
}
```

One click, and the question from chat has a definitive answer.

## How it works

When you hit **Run**, the editor sends your code and chosen Go version to a stateless API service. The service hashes the request and checks a result cache. Most playground traffic comes from people opening shared links, so cache hits are common and return instantly.

On a cache miss, the program is built and run inside a fresh container sandboxed with [gVisor](https://gvisor.dev), which handles system calls in a user-space kernel so a misbehaving program can't reach the host. During the build, the container can reach only our internal module proxy. During execution, it has no network access at all. Each run is limited to 2 CPUs, 512 MB of memory, 10 seconds of wall-clock time, and 1 MB of output.

Compilation was our biggest early bottleneck. A snippet that imports a few internal packages can pull in hundreds of transitive dependencies, and building them from scratch took far too long. We fixed this by mounting a read-only, pre-warmed build cache for each Go version. A nightly job rebuilds it from our most commonly imported modules. That brought median run time from about 14 seconds to under 2.

## A deliberate difference

The public playground fakes time. Its clock starts at `2009-11-10 23:00:00 UTC`, and `time.Sleep` returns instantly. That keeps output deterministic and easy to cache, which makes sense for a public service.

We chose real time instead. Many of the questions our engineers bring to the playground are about timeouts, deadlines, and retries, which a fake clock hides. As a result, cached output is labeled with when it ran, and re-running a shared snippet takes one click.

## What's next

We're already working on:

- Autocomplete and hover documentation powered by `gopls`
- Embedding live, runnable snippets in our internal docs site
- An **Open in Playground** button on code search results

## Try it

The playground is live now. Look for the link pinned in the `#go` channel. The next time you're about to write a throwaway `main.go` to answer a question, try sending a link instead. If something breaks, or you have an idea that would make it more useful, tell us. We built it for you.

---

*Note: The company details, internal URLs, package names, and performance figures above are placeholders. Swap in your own before publishing.*
