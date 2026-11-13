# Go at Google I/O and Gopher SummerFest

This summer a few of us left our desks for two very different Go events. The first was Google I/O: a huge keynote stage, polished demos, and thousands of attendees. The second was Gopher SummerFest, a community meetup with folding chairs, lightning talks, and more pizza than any of us should have eaten. Seeing both in the same season was useful. One showed where Go is heading at scale, and the other showed how people actually use it day to day.

Here's what we saw, what we learned, and what we've changed since.

## Why We Went

Most of our backend runs on Go. That includes the API gateway, the event pipeline, and nearly every internal tool someone has built on a Friday afternoon. Go has worked well for us, but a stable language can make a team complacent. We wanted to check our habits against what other teams are doing and bring back ideas we could use.

## Google I/O: Go in the Big Room

The Go sessions at I/O kept returning to one idea: **simplicity is what lets you operate at scale.** Speakers described large codebases and large teams, and the advice was mostly about keeping things uniform:

- **Tooling is the culture.** `gofmt`, `go vet`, and the standard test runner aren't conveniences. They let thousands of engineers read each other's code without arguing about style. Several speakers pointed out that the best Go code at large companies looks boring, and that's the goal.
- **Small binaries, simple deploys.** Go compiles to a single static binary, so a container image can hold little more than your program. Faster cold starts and a smaller attack surface came up repeatedly in talks about cloud deployment.
- **Concurrency is a design tool, not a performance trick.** The best talks didn't treat goroutines and channels as a way to go faster. They used them to describe how a system is structured: independent pieces that communicate clearly.

We left with a reminder more than a list of new features. Go's strengths are things we already have, and we should stop working around them.

## Gopher SummerFest: Go in the Small Room

SummerFest felt more like a long, friendly code review. The lightning talks were short and specific, often given by engineers at startups describing a production incident and what they learned from it.

The most common topic was **goroutine leaks**. At least three speakers had a version of the same story: memory slowly climbs, nobody can explain it, and eventually someone finds thousands of goroutines blocked on a channel nobody will ever read. One speaker showed a pattern so common that two of us recognized it from our own code:

```go
// If ctx is cancelled first, the goroutine blocks forever on send.
func lookup(ctx context.Context, key string) (string, error) {
	ch := make(chan string)
	go func() { ch <- slowLookup(key) }()

	select {
	case v := <-ch:
		return v, nil
	case <-ctx.Done():
		return "", ctx.Err()
	}
}
```

The fix is one character of intent: `make(chan string, 1)`. With a buffer, the goroutine can always complete its send and exit, even if nobody is listening anymore. The lesson that stuck with us was broader than this bug: every goroutine you start needs a clear plan for how it ends.

Other highlights from the hallway track:

- **Profile before guessing.** Several people showed `pprof` flame graphs that contradicted what the team had assumed. The slow part was rarely the part they expected.
- **Table-driven tests scale well.** A simple slice of test cases plus a loop with `t.Run` stays readable as a test file grows into the hundreds of cases.
- **`context` should go everywhere.** Pass it as the first argument and respect its cancellation, even in code where it doesn't seem to matter yet.

## What We Brought Back

Conference energy fades quickly, so we made a few concrete changes within two weeks of getting home:

1. **`pprof` endpoints on every service**, behind internal authentication. Profiling is now something anyone can do in a few minutes, not a special project.
2. **Goroutine leak detection in tests.** Our test helpers now fail if a test leaves goroutines running. This caught four real leaks in the first week.
3. **A table-driven testing guide** added to our internal style docs, with examples taken from our own codebase.
4. **A monthly Go lunch.** It's a small internal version of SummerFest: two or three short talks, no slides required, and plenty of food.

## Closing Thoughts

Google I/O showed us that Go's design holds up at very large scale. SummerFest showed us that the community around it is generous, practical, and happy to share its mistakes. Both reminded us that the best way to get better at Go is to keep it simple, measure what matters, and learn from other people's incidents before they become yours.

If this kind of work sounds interesting, we're hiring, and we'd be glad to save you a seat at the next Go lunch.
