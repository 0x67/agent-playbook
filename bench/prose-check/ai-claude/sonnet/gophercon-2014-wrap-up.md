# GopherCon 2014 Wrap Up

Last month a group of us from the engineering team traveled to Denver for the first-ever GopherCon. Two days, one track, roughly 700 Gophers in a single room. It felt less like a conference and more like the first big family reunion of a community that had mostly known each other through mailing lists and IRC. Here's our wrap-up of what we saw, what we learned, and what we're taking back to our codebase.

## The Vibe

A single-track format turned out to be a great decision. No one had to agonize over which room to pick, and hallway conversations were naturally anchored to shared talks. You could ask nearly anyone, "What did you think of that last session?" and get a real conversation going.

The tone was also refreshingly practical. Go is a young language (1.0 shipped in 2012, and 1.3 had just landed), and the talks reflected a community focused on building things rather than debating language features.

## Talks That Stuck With Us

**Rob Pike's keynote on the state of Go.** Rob reminded us that Go's design is as much about what was left out as what was included. The theme of *simplicity as a feature* ran through the rest of the conference. It's easy to forget, when you're deep in a codebase, that the constraints are doing you favors.

**Concurrency patterns.** Several talks dug into goroutines, channels, and the patterns that emerge from them. The recurring lesson: channels are great for orchestrating work and passing ownership of data, but a plain mutex is often the right tool for protecting simple shared state. Don't reach for a channel just because you can.

**Testing and tooling.** Talks on benchmarking, profiling with `pprof`, and the race detector were some of the most immediately useful for us. The race detector in particular is something we plan to run more aggressively in CI.

**Go internals.** Sessions on the runtime, the scheduler, and the garbage collector gave us a better mental model for diagnosing performance problems. Understanding *why* an allocation escapes to the heap makes it much easier to write code that behaves well under load.

## What We're Taking Back

Conferences are only worth it if something changes afterward. Here's our short list:

1. **Run `go test -race` in CI on every commit.** We've been running it sporadically. Several speakers shared war stories that convinced us the cost is small compared to the bugs it catches.
2. **Profile before optimizing.** We have a few services where we've made performance assumptions. We're going to put `pprof` on them and see whether we were right.
3. **Prefer small interfaces.** A recurring theme was that the best Go interfaces are tiny, often a single method. We're going to audit a few of our larger interfaces and see which can be broken up.
4. **Be deliberate with channels.** We'll review places where we used channels for convenience and consider whether a mutex would be clearer.
5. **Invest in error handling.** Go's explicit errors can feel verbose, but several talks showed how wrapping errors with context makes debugging production issues far less painful.

## The Community

The best part of GopherCon wasn't any single talk. It was the people. We met maintainers of libraries we depend on, engineers wrestling with the same deployment problems we are, and newcomers who were just beginning to explore the language. The hallway track, the dinners, and the hack sessions were where a lot of the real learning happened.

It's also worth noting how welcoming the event was. The organizers put real effort into making the conference approachable for people of all backgrounds and experience levels, and it showed. A language community lives or dies by its culture, and this one seems to be in good shape.

## Looking Ahead

If GopherCon 2014 is any indication, Go's future is bright. The ecosystem is maturing quickly, tooling keeps improving, and more companies are running Go in production at serious scale. We're excited to be part of that.

We'll be sharing more detailed write-ups on a few of the topics above in the coming weeks, particularly our experiments with the race detector and profiling. If you attended and want to compare notes, or if you're considering Go for your own stack, we'd love to hear from you.

Until next year, happy hacking.

*Were you at GopherCon? Tell us what your favorite talk was in the comments.*
