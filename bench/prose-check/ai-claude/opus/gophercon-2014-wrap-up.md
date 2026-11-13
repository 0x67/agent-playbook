# GopherCon 2014 Wrap Up

Last week four of us from the platform team went to Denver for the first GopherCon. About 700 Go developers filled the conference hall for two days of talks and a day of hacking. We came home with full notebooks, some new ideas for our codebase, and far too many gopher stickers.

Over the past year we've moved more and more of our backend services from Ruby and Python to Go. Our ingestion pipeline, our internal job scheduler, and most of our new API endpoints are now written in Go. We've been happy with the results, but we've also had to work out many things on our own. GopherCon was a chance to compare notes with people who have run Go in production longer than we have.

## The Opening Keynote

Rob Pike opened with "Hello, Gophers!", a history of the language told through the changes to its hello world program. It sounds like a gimmick, but it worked. Watching that tiny program change over time showed the design decisions behind Go: the syntax shifted, semicolons disappeared, and the standard library took form. The recurring theme was that Go's simplicity is deliberate and hard-won.

## Running Go in Production

Peter Bourgon's "Best Practices for Production Environments" had the most immediate impact on our team. It drew on SoundCloud's experience, and several of his recommendations matched problems we've hit:

- **Configure with flags.** Command-line flags are explicit, self-documenting, and easy to inspect. We have a few services with layered config files that nobody fully understands anymore.
- **Vendor your dependencies.** Builds should be reproducible. Pulling `master` of someone else's repository at build time is not reproducible.
- **Prefer the standard library for testing.** The `testing` package and plain Go code go a long way before you need an assertion DSL.

Blake Mizerany's talk on dependencies made the same point from a different angle. Every import is a liability as well as an asset, and `go get` is convenient enough that it's easy to forget that. Dependency management came up in almost every hallway conversation we had. The community hasn't settled on an answer yet, and we expect it to be a big topic over the next year.

## Channels, Revisited

John Graham-Cumming's "A Channel Compendium" was a fast-paced tour of channel idioms from CloudFlare's codebase. Two patterns stood out:

- Closing a channel is a clean way to send a signal to any number of goroutines at once.
- Setting a channel to `nil` inside a `select` disables that case, which helps when merging streams:

```go
for a != nil || b != nil {
    select {
    case v, ok := <-a:
        if !ok {
            a = nil // stop selecting on a
            continue
        }
        out <- v
    case v, ok := <-b:
        if !ok {
            b = nil
            continue
        }
        out <- v
    }
}
```

In at least two places in our pipeline, we track whether an input is done with extra booleans. That code is getting simpler next sprint.

## The Hallway Track

As usual, some of the best conversations happened between sessions. We talked with engineers who deploy Go on everything from small ARM devices to large clusters. Many were excited about the upcoming Go 1.3 release and its runtime improvements. It was reassuring to hear that other teams have struggled with the same things we have:

- structuring large repositories
- deciding how much abstraction is too much
- teaching newcomers not to bring patterns over from other languages

The Saturday hack day was a highlight. With no fixed agenda, people paired up on open source projects, debugged each other's code, and sent fixes upstream. One of our engineers spent the afternoon chasing a race condition with someone who had hit the same bug months earlier.

## What We're Changing

We left Denver with a short, concrete list:

1. Vendor dependencies for every service so builds are reproducible.
2. Move service configuration to flags wherever practical.
3. Audit our channel-handling code for patterns we can simplify.
4. Run `go vet` and the race detector in CI for every project.

None of these is dramatic, but together they should make our services easier to build, deploy, and reason about.

## Thanks

Thank you to the organizers, speakers, and volunteers who made the first GopherCon happen. Running a first-year conference this size is hard, and it felt like a milestone for the Go community. Recordings of the talks should be posted soon, and we recommend them.

If you'd like to work with Go on problems like these, we're hiring. See you at GopherCon 2015.
