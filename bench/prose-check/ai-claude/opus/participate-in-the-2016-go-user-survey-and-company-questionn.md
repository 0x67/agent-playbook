# Participate in the 2016 Go User Survey and Company Questionnaire

Over the last few years, Go has moved from an experiment in a corner of our codebase to the language behind a large share of our backend services. Our API gateway, internal deployment tooling, and several data pipelines are written in it. Many of us now reach for Go by default when starting a new service. So we were glad to see that the Go team has launched its first official **Go User Survey**, along with a separate **Company Questionnaire** for organizations using Go in production.

We're filling both out, and we'd like to encourage you to do the same. Here's why we think it matters and how to make your answers count.

## What's Being Asked

There are two parts:

- **The Go User Survey** is for individual developers. It asks how you use Go, what you build with it, which tools and libraries you depend on, where you get stuck, and what you'd like to see improved. You don't need to be an expert or use Go at work to take part. If you've written Go, your perspective is useful.
- **The Company Questionnaire** is for organizations. It asks how Go is used inside your company, how adoption happened, and what has helped or hindered it. One person who can speak for your team or organization is enough.

Both are linked from the official Go blog at [blog.golang.org](https://blog.golang.org). They don't take long to complete.

## Why This Matters

Go's design has always favored deliberate, conservative change. That's a big part of why we trust it for production systems. Code we wrote years ago still compiles, and upgrading the toolchain is usually uneventful. But deliberate change depends on good information about how the language is used.

Until now, much of that information came from indirect sources: issue trackers, mailing lists, conference talks, and conversations on social media. Those channels are valuable, but they over-represent certain voices. People who file issues or post on forums are a small slice of the people writing Go every day. A structured survey reaches the larger group of developers who rarely comment publicly.

Your answers can help shape decisions about:

- **Tooling priorities.** Debugging, profiling, editor integration, and dependency management all compete for limited engineering time.
- **Documentation and learning resources.** Knowing where newcomers struggle helps the community build better onboarding material.
- **Ecosystem gaps.** Knowing which domains people use Go for, and which ones they avoid, shows where libraries are missing.
- **Community health.** Knowing who uses Go, and where, helps make sure the community is welcoming to everyone.

## Why We're Participating as a Company

We get a great deal of value from Go and its open source ecosystem, and we don't pay for most of it. Contributing code upstream is one way to give back. Giving clear, honest feedback is another, and it costs almost nothing.

There's also a practical reason. Some problems our teams hit regularly are probably common in production environments: managing dependencies across many repositories, building consistently in CI, and diagnosing latency in long-running services. If companies like ours don't report these issues, it's harder for the people building Go to see how widespread they are.

We asked our Go developers to take the individual survey on their own, without coordination, so their answers reflect real day-to-day experience. A few of our tech leads are working together on the company questionnaire.

## Tips for Giving Useful Feedback

From our experience running internal developer surveys, a few things make responses much more useful:

1. **Be specific.** "Dependency management is hard" is less helpful than "We vendor dependencies across a dozen services and keeping versions consistent takes manual work every release."
2. **Describe the problem, not just your preferred fix.** A clear description of the pain point leaves room for solutions you might not have thought of.
3. **Mention what works well.** Knowing what to keep matters as much as knowing what to change.
4. **Answer even if you're new.** Beginner feedback is especially valuable because experienced developers often forget what was hard at first.
5. **Use the free-text fields.** Multiple-choice answers show trends. Written comments explain them.

## How to Participate

Visit the [official Go blog](https://blog.golang.org) for links to the user survey and the company questionnaire. Set aside a few minutes, answer honestly, and share the links with colleagues, local meetup groups, or anyone else you know who writes Go. The more people who respond, the more representative the results will be.

Go has served us well. Taking a few minutes to help guide where it goes next is time well spent. We'll see you in the results.
