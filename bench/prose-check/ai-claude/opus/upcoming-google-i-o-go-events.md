# Upcoming Google I/O Go Events

Every spring, Google I/O brings thousands of developers together to see what's next across Google's platforms. Most of the attention goes to Android, the web, and AI, but for teams like ours that run much of our infrastructure on Go, I/O is also a good time to take stock of the language and its ecosystem.

This year we're sending [NUMBER] engineers from our platform and infrastructure teams. We're also hosting a few Go-focused events of our own around the conference, both in person and online. Here's what we're planning and how you can join.

## Why Go at I/O Matters to Us

Go has been a core part of our stack for years. Our API gateway, event ingestion pipeline, and most of our internal developer tooling are written in it. We chose Go for the reasons many teams do:

- **Fast builds** that keep CI times reasonable as the codebase grows.
- **A straightforward concurrency model** that suits network-heavy services.
- **Single static binaries** that make deployment and container images simpler.
- **A small language** that new engineers can learn in days rather than months.

Because Go underpins so much of what we ship, changes to the language, toolchain, or cloud integrations affect our roadmap directly. Conferences like I/O are one of the best places to hear about those changes early and to talk with the people building them.

## What We're Watching For

We don't know the final I/O agenda yet, but these are the areas our team is most interested in:

**Language and standard library evolution.** Generics, range-over-function iterators, and steady standard library improvements have changed how we write Go over the past few releases. We want to learn where the language is heading and how other teams are adopting newer features in large, long-lived codebases.

**Tooling and performance.** Profile-guided optimization, improvements to `gopls`, and vulnerability scanning with `govulncheck` have all affected our day-to-day work. We're especially interested in practical guidance on getting PGO into production build pipelines.

**Go on Google Cloud.** Many of our services run on Cloud Run and GKE, so we follow updates to client libraries, observability integrations, and deployment patterns closely.

**Go for AI-powered applications.** More of our product features call model APIs, and we want to see how the Go ecosystem is evolving for building and serving those workloads reliably.

## Our Events

### I/O Watch Party & Go Lightning Talks

**When:** [DATE AND TIME]
**Where:** [OFFICE LOCATION] and livestreamed

We'll stream the keynote and any Go-related sessions, then follow with an evening of short talks from our engineers and guests from the local Go community. Proposed topics include:

- Lessons from migrating a large internal library to generics
- What we learned rolling out profile-guided optimization across our services
- Structured logging with `log/slog` at scale
- Building reliable retry and backoff logic for third-party APIs

Food and drinks are provided, and yes, there will be gopher stickers.

### Gopher Meetup Near the Venue

**When:** [DATE AND TIME]
**Where:** [VENUE NEAR SHORELINE AMPHITHEATRE]

If you're attending I/O in person, come find us after sessions end. This is an informal gathering with no slides and no agenda, just Go developers comparing notes on what they've seen during the day. It's a good chance to meet our engineers and ask about how we use Go in production.

### Post-I/O Recap (Online)

**When:** [DATE AND TIME]
**Where:** [LINK]

About a week after the conference, our attendees will host an hour-long online session summarizing the most relevant Go announcements and what they mean for teams building backend services. We'll leave plenty of time for Q&A, and we'll publish a written summary on this blog afterward.

## Call for Lightning Talks

We'd love to include voices from outside our company in the lightning talk lineup. If you have a five-to-ten-minute Go talk, whether it's a production war story, a library you've built, or a pattern that's worked well for your team, we want to hear it. Submit a short abstract at [SUBMISSION LINK] by [DEADLINE]. First-time speakers are especially welcome, and we're happy to help with a practice run.

## How to Join

All of our events are free. Space for the in-person watch party is limited, so please register at [REGISTRATION LINK]. The livestream and online recap are open to everyone.

Everyone attending is expected to follow our community code of conduct, which is available at [CODE OF CONDUCT LINK].

## See You There

Go's strength has always come from its community as much as its design. Conferences give us a chance to step away from our own codebase and learn from people solving different problems with the same tools. Whether you're a longtime gopher or just starting out with the language, we hope you'll join us.

If you have questions about any of these events, reach out at [CONTACT EMAIL]. See you at I/O!

---

*Note: Google hasn't published the I/O 2027 schedule yet, so I kept the post general and didn't name specific official sessions. Bracketed items are placeholders for your team's dates, links, and other details. The lightning talk topics are suggestions you can swap for your engineers' actual talks.*
