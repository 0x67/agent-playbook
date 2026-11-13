# Introducing the Go Playground

Every language has a moment when a newcomer asks, "Can I just try it?" For years, the honest answer for Go was: install the toolchain, set up a workspace, write a file, run `go run`. None of that is hard, but each step is friction, and friction kills curiosity. Today we're introducing the Go Playground, a place to write, run, and share Go code directly in your browser, with nothing to install.

## Why we built it

Our engineers kept running into the same situations:

- **Explaining a bug.** A snippet pasted into chat loses its context. Is it a compile error or a runtime panic? Which version? Nobody knows until someone sets up a project to find out.
- **Teaching.** Onboarding new teammates meant walking them through installation before they wrote a single line of Go.
- **Quick experiments.** "How does `append` behave when capacity is exceeded?" shouldn't require creating a directory and a `go.mod`.

We wanted a scratchpad that is fast to open, safe to run untrusted code in, and easy to link to. The Playground is that scratchpad.

## What it does

The Playground gives you an editor, a Run button, and an output pane. Under the hood, it provides:

- **Compile and run** with output streamed back as the program executes.
- **Formatting** via `gofmt` on demand or on every run, so shared snippets look consistent.
- **Shareable links.** Click Share and you get a short, permanent URL containing your exact code.
- **Standard library support** for the packages you'd expect, including `fmt`, `strings`, `sort`, `sync`, `time`, and `net/http` types (though not outbound network access).

Here's the sort of thing it's perfect for:

```go
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	results := make([]int, 5)

	for i := range results {
		wg.Add(1)
		go func() {
			defer wg.Done()
			results[i] = i * i
		}()
	}

	wg.Wait()
	fmt.Println(results)
}
```

Paste that in, press Run, and you can immediately discuss Go 1.22's per-iteration loop variable semantics with a colleague, who can fork your snippet and change it.

## How it works

Running arbitrary code from strangers is the hard part, so most of our engineering effort went into isolation.

**The request path.** The browser sends source to a frontend service, which validates size limits and checks a cache keyed by a hash of the code. Identical programs with deterministic output don't need to run twice.

**The sandbox.** Each program is compiled and executed in a short-lived, locked-down container with no network access, a read-only filesystem apart from a small scratch area, and strict limits on CPU time, memory, and output size. Containers are destroyed after every run, so nothing persists between users.

**Deterministic time.** Programs see a fake clock that advances only when they sleep. This means `time.Sleep(10 * time.Second)` returns instantly in real time while still behaving correctly, which keeps resource use low and makes concurrent examples reproducible.

**Storage.** Shared snippets are stored by content hash. Because the same code always maps to the same ID, links are stable, deduplicated, and cheap to keep forever.

## What we learned

A few lessons are worth passing on:

1. **Limits need to be layered.** A timeout alone isn't enough. A program can exhaust memory or flood output well before it expires. We enforce limits at the container, process, and output-stream levels independently.
2. **Caching changes the economics.** A surprising share of traffic is the same popular examples run repeatedly. Caching by content hash cut our compute costs substantially.
3. **Error messages are the product.** Beginners spend most of their time reading compiler errors. We invested in presenting them with line highlighting so the first failure is a useful one.

## Limitations

The Playground is deliberately constrained. There's no outbound networking, no persistent filesystem, and a modest execution time limit. Programs that depend on third-party modules are limited for now. For anything larger than a snippet, a local toolchain is still the right choice.

## What's next

We're working on several improvements: multi-file programs, module support with a curated allowlist, a built-in test runner so you can share `go test` examples, and embeddable snippets for documentation and blog posts like this one.

## Try it

Open the Playground, paste in a snippet that's been puzzling you, and share the link with someone. If you hit a rough edge or have an idea, tell us. We're building this in the open, and the best features usually start as a complaint.

Happy hacking.
