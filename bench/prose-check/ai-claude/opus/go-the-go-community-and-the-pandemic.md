# Go, the Go Community, and the Pandemic

In March 2020, our engineering team went home for what we thought would be a few weeks. Like most of the industry, we ended up rebuilding how we collaborate, review code, onboard people, and stay connected. Looking back, one constant through that period was the language most of our backend runs on. Go, and the community around it, adapted to the disruption well, and how it did so taught us something about building durable software and durable teams.

## A Language That Was Already Built for Distance

Go was designed at Google to help large, distributed groups of engineers work on a shared codebase without stepping on each other. Many of its choices that look like minimalism are really about coordination:

- **`gofmt` ends formatting debates.** When code review moved entirely to async comments, nobody spent a thread arguing about brace placement. The formatter had settled that years ago.
- **A small language means a shared vocabulary.** An engineer who joined us remotely in 2020 could read almost any service in our monorepo within a week. Without that, onboarding by video call would have been much harder.
- **The toolchain is mostly self-contained.** `go build`, `go test`, and `go vet` behave the same on a laptop at a kitchen table as they do in CI. We lost very little time to environment problems as people set up home offices on whatever hardware they had.

None of this was designed with a pandemic in mind. It was designed for scale, and it turns out that organizational scale and physical distance cause many of the same problems.

## The Releases Kept Shipping

Early in the pandemic, the Go team said publicly that they expected work on Go to continue and that the release schedule would hold. It held. Go 1.15 shipped in August 2020, and Go 1.16 followed in February 2021. Go 1.16 added the `embed` package, turned module mode on by default, and brought native support for Apple Silicon, which arrived just as several of our engineers received new M1 laptops.

The big design work continued too. In June 2020, the Go team published an updated type parameters design draft along with an experimental playground for trying it. For the first time, anyone could write generic Go code and send feedback without building a custom toolchain. That proposal went through a long public review and eventually shipped as generics in Go 1.18. Much of that review happened in issue threads and mailing lists, where it didn't matter that nobody could meet in person.

For a company that depends on a language, predictability is a feature. We never had to wonder whether the next release would slip or whether a security fix would arrive. That let us keep our own upgrade cadence: we adopt each new Go release within one cycle, and we kept doing so throughout.

## The Community Moved Online

Gophers are a social bunch, and in-person events were the first thing the pandemic took. The community adapted quickly. GopherCon 2020 went fully virtual, as did GopherCon Europe and many regional conferences. Local meetups moved to video calls, which had an unexpected upside: our engineers could attend talks hosted on other continents. The Gophers Slack, which was already busy, became the default hallway track.

Some things were lost. A video talk doesn't replace a conversation over coffee after a session, and several of our engineers said they missed the serendipity of conferences. But the community kept learning and sharing, and a lot of what was built then, including recorded talks, online study groups, and remote-friendly meetups, has continued.

## What We Took Away

Several lessons from that period are still part of how we work:

1. **Lean on tooling to remove friction.** Every argument a tool can settle is one fewer async thread. Beyond `gofmt`, we now enforce `go vet` and `staticcheck` in CI and treat their output as non-negotiable.
2. **Readable code is a remote-work strategy.** We deliberately favor plain, explicit Go over clever abstractions, because the next reader may be a new hire in a different time zone with no one to ask.
3. **Depend on stable infrastructure.** The module proxy and checksum database, introduced in Go 1.13, kept our builds reproducible and fast when we couldn't count on anything else.
4. **Invest in the community you depend on.** We sponsored virtual events, encouraged engineers to give talks remotely, and upstreamed fixes we would otherwise have kept in a fork. A healthy ecosystem is not something you can take for granted.

## Looking Forward

The pandemic tested every team and every tool we rely on. Go held up because it was built around simplicity, stability, and collaboration at a distance. The community held up because the people in it decided to keep showing up, even when that meant a webcam instead of a conference hall.

We're grateful to the Go team and to the gophers around the world who kept things moving. If you're one of them, thank you. And if you'd like to write Go with a team that cares about these things, we're hiring.
