# Go Turns 10

Ten years ago this month, a small team here shipped our first production service written in Go. It was a webhook dispatcher: about 2,000 lines, one binary, and nothing outside the standard library. It was supposed to be an experiment. Today Go runs most of our backend, including the API gateway, the job scheduler, the billing pipeline, and the internal tooling that ties it all together.

The language itself turned 17 on November 10. Ours is a smaller anniversary, but it's a good moment to look back at what we bet on, what changed, and what we'd tell a team considering the same move today.

## Why we picked it

In 2016 our backend was a Ruby monolith straining under background work. We needed something that handled concurrency well, deployed easily, and that engineers from different backgrounds could read on day one.

Go fit almost embarrassingly well. Goroutines and channels made the dispatcher's fan-out logic simple to express. A single statically linked binary turned our deploy process from "bundle install and pray" into "copy a file." And `gofmt` permanently ended a whole category of code review arguments.

The less obvious win was Go's compatibility promise. Since Go 1.0, code written against the spec has kept compiling. That first dispatcher still builds on the current toolchain. The only changes it needed were to the build setup, not the code.

## What changed along the way

Go in 2016 was a different experience. A few milestones mattered most to us:

**Modules (Go 1.11, 2018).** Before modules, we lived with `GOPATH`, vendored directories, and a rotating cast of third-party dependency tools. Migrating took most of a quarter across our repos, and it was worth every hour. We no longer had to engineer reproducible builds ourselves.

**Error wrapping (Go 1.13, 2019).** `errors.Is`, `errors.As`, and the `%w` verb gave us a standard way to add context without losing the original error. We deleted two homegrown error packages.

**Generics (Go 1.18, 2022).** We were skeptics. In practice, generics replaced a handful of code-generated collection helpers and a lot of `interface{}` casting in our caching layer. We use them sparingly, which seems to be what the language intended.

**Structured logging (Go 1.21, 2023).** `log/slog` let us standardize on one logging API across every service without a third-party dependency.

**Loop variable semantics (Go 1.22, 2024).** Each loop iteration now gets its own variable. That quietly eliminated a bug class we'd hit in production at least twice: goroutines closing over a shared loop variable.

## What was hard

Not everything was smooth. Verbose error handling is real, and `if err != nil` accounts for a lot of our line count. Early on, engineers used to heavy dependency-injection frameworks tried to rebuild those patterns in Go. The result was code that fought the language. We eventually wrote an internal style guide whose main message is "prefer the boring version."

We also learned that goroutines are cheap but not free. Leaking one goroutine per request goes unnoticed until suddenly it doesn't. Two things caught more issues than any linter: using `context` cancellation consistently, and adding goroutine counts to our standard dashboards.

## What we'd tell a team starting today

- **Lean on the standard library.** `net/http`, `encoding/json`, `database/sql`, and `testing` cover more than you'd expect.
- **Make `context` non-negotiable.** Pass it everywhere, honor cancellation, and set timeouts at the edge.
- **Run the tools in CI.** `go vet`, `staticcheck`, and `go test -race` are cheap insurance.
- **Name packages for what they provide**, not what they contain. A package called `utils` is a smell.
- **Upgrade regularly.** Thanks to the compatibility promise, staying current is usually low-risk, and you get performance and tooling improvements for free.

## The next ten

We're not planning a rewrite. The reasons Go was a good bet in 2016 still hold: simplicity, fast builds, easy deployment, and a language team that takes stability seriously.

To everyone who has written, reviewed, or been paged for a line of Go here over the past decade: thank you. And to the Go team and community: happy birthday, and thanks for keeping it boring in the best possible way.

*Want to work on our Go services? We're hiring.*

---

**A note on the framing:** Go was open-sourced in November 2009, so the language itself is 17 this year. I wrote the post as your company's tenth anniversary with Go. Company-specific details like the webhook dispatcher, the Ruby monolith, and the incident counts are placeholders to swap for your real story. If you'd prefer a retrospective written as of Go's actual 10th birthday in 2019, I can rework it that way.
