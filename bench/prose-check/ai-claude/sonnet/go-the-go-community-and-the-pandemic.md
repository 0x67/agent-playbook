# Go, the Go Community, and the Pandemic

When the world moved indoors in the spring of 2020, few of us on the engineering team expected that a programming language would become one of the steadier things in our working lives. Yet looking back, Go and the community around it offer a useful case study in how technical choices and human networks hold up under stress. This post reflects on what we saw, what we learned, and what we changed.

## A language built for distributed teams

Go was designed at Google to help large groups of engineers work on large codebases without stepping on each other. That design goal turned out to matter far more once everyone was remote.

A few properties made the difference for us:

- **One obvious style.** `gofmt` ended formatting debates before they started. When you can't lean over a desk to settle a disagreement, having the tooling settle it is a gift.
- **Readable by default.** Go's small feature set means a reviewer can understand unfamiliar code quickly. Asynchronous code review depends on this. A pull request that takes thirty minutes to decode across time zones is a pull request that blocks a teammate for a day.
- **Fast, boring builds.** Short compile times kept feedback loops tight when we couldn't pair in person. Fast CI meant fewer context switches and fewer "I'll check back tomorrow" stalls.
- **Easy onboarding.** We hired and onboarded several engineers entirely remotely. Most were productive in Go within their first couple of weeks, which we attribute largely to the language's small surface area and the quality of its standard library and documentation.

None of this was new. But properties that feel like conveniences in an office become load-bearing in a distributed setting.

## The community moved online, and widened

The Go community has always been strong in person. GopherCon, regional conferences, and local meetups were central to how many people learned and made connections. In 2020, nearly all of that was cancelled or went virtual.

What happened next was interesting. Virtual events lowered barriers: no flights, no hotel costs, no visa hurdles. Attendance at online talks and meetups often reached people who had never been able to attend in person. Recordings made talks searchable and reusable. Slack workspaces, forums, and Discord servers became the hallway track.

There were real losses too. Spontaneous conversations, mentorship over coffee, and the feeling of being in a room full of people who care about the same things are hard to replicate on a video call. Many maintainers and organizers worked hard to recreate some of that, with mixed but admirable results. We came away convinced that the best future is hybrid: in-person gatherings for connection, with online access for reach.

## Open source under pressure

The pandemic also tested open source sustainability. Maintainers were juggling childcare, health concerns, and disrupted jobs, while demand for their work often went up as more software moved online.

The Go project continued to ship on its regular cadence, with releases arriving on schedule through the period. That predictability mattered. Our own upgrade process was simple because the release rhythm was dependable and the compatibility promise meant upgrades rarely broke anything. During a time when so much felt uncertain, being able to treat our toolchain as stable ground was a real benefit.

It also reminded us of our own responsibility. We increased our contributions: filing better bug reports, sending small fixes upstream, and sponsoring maintainers of libraries we depend on. If your business runs on open source, the pandemic was a good prompt to ask what you're giving back.

## What we changed

Several practices from that period stuck:

1. **Write things down.** Design docs and decision records replaced hallway conversations. Go's emphasis on simplicity made these easier to write and easier to follow.
2. **Invest in tooling.** We tightened linting, testing, and CI so that quality didn't depend on anyone's availability.
3. **Build community deliberately.** We started an internal Go reading group and began hosting small virtual talks, open to the public, that continue today.
4. **Protect maintainers.** We budgeted time and money for the open source projects we rely on.

## Closing thoughts

A language can't solve a crisis, and a community can't replace being together. But Go's emphasis on clarity, stability, and shared convention gave distributed teams a common footing, and the people around it showed remarkable generosity in adapting. As we plan for whatever comes next, we're carrying forward the lessons: favor simplicity, communicate in writing, and keep investing in the people who make the tools we depend on.

If you have your own stories from this period, we'd love to hear them. Reach out to the team or join us at our next community talk.
