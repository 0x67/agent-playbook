# Eleven Years of Go

In the fall of 2015, a small team here shipped a service that did one unglamorous thing: it accepted webhook events from our partners, validated them, and put them on a queue. It was about 1,200 lines of Go, built with Go 1.5, and it was our first production code not written in Python or Java.

That service still runs. It has been partly rewritten, moved across three deployment platforms, and upgraded through more than twenty Go releases. Today most of our backend, well over 300 services, is written in Go. Eleven years in, it's a good time to look back at what worked, what didn't, and what we'd tell a team starting today.

## Why We Picked It

Honestly, we didn't pick Go so much as stop resisting it. A few engineers had been using it for internal tools, and those tools rarely drew complaints. They started fast, deployed as a single binary, and were readable by people who hadn't written them.

When we needed a high-concurrency ingestion service, goroutines and channels looked simpler than the thread pools we kept tuning in Java. The webhook service was the experiment. It worked, and the next team asked to use Go too.

## What Held Up

**The compatibility promise.** The Go 1 compatibility guarantee has been the language's most valuable feature for us. Upgrading the compiler usually takes a boring afternoon, not a quarter-long project. We've had a handful of real breakages in eleven years, and nearly all of them came from depending on behavior we shouldn't have.

**Boring code.** Go's small surface area means code from 2016 reads like code from last month. New hires become productive quickly. `gofmt` ended our style debates before they started, so code review focuses on design.

**The toolchain.** Testing, benchmarking, race detection, and profiling all come built in. `pprof` alone has paid for itself many times over. Some of our biggest infrastructure savings came from one engineer spending an afternoon with a CPU profile.

## What Hurt

**Dependency management before modules.** Between 2015 and 2019 we went through GOPATH, vendoring, Glide, and `dep`. Each migration cost real time, and for a while different repositories used different tools. Modules arrived in Go 1.11, and once they matured we moved everything over and never looked back.

**Years without generics.** We wrote a lot of code generators. A few were good. Several were not. When generics landed in Go 1.18, we adopted them slowly on purpose. Today we use them mostly for collection helpers and typed caches, and we're glad we didn't rewrite working code just to make it more abstract.

**The loop variable.** Every Go shop has a closure-capture story. Ours was a batch job that processed the last item in a slice several thousand times. Go 1.22 made loop variables per-iteration, and we happily deleted a lint rule.

**Error handling.** `if err != nil` is verbose, but it keeps failure paths visible. Since Go 1.13 added error wrapping, our errors carry enough context to debug from logs alone. We've made peace with it.

## What We've Learned

Our advice for a team adopting Go today:

1. **Pass `context.Context` everywhere from day one.** Retrofitting cancellation and deadlines into a large codebase is miserable. We've done it once and don't plan to again.
2. **Avoid packages named `utils`.** Our worst packages are the ones named after nothing.
3. **Lean on the standard library.** `net/http`, `database/sql`, and `log/slog` cover more than you'd expect. We eventually removed nearly every framework we adopted early on.
4. **Upgrade often.** Staying within a release or two of current is cheap. Falling five behind is not.
5. **Profile before optimizing.** Our guesses about where time goes have been wrong more often than right.

## Looking Ahead

Go is no longer the new language here. It's the default, and that carries its own risk: the temptation to use it for problems it isn't suited to. We still write data pipelines in Python and a few performance-critical components in Rust, and we think that's healthy.

For the services that make up most of our infrastructure, though, Go has done exactly what we hoped in 2015: it has stayed out of the way. That first webhook service is still running, still small, still boring. We can't think of higher praise.

*If this sounds like a codebase you'd enjoy working in, [we're hiring](#).*
