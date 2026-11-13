# Introducing the Developer Experience Working Group

Every engineering team has a story about the afternoon that disappeared. A build that wouldn't reproduce locally. A test suite that failed on the third retry for reasons nobody could explain. A setup doc that was accurate two reorganizations ago. None of these problems is catastrophic on its own, but together they form a tax on every engineer, every day. Today we're announcing a group dedicated to reducing it: the **Developer Experience Working Group**.

## Why now

As our company has grown, so has the surface area of our engineering work. More services, more languages, more tooling, more teams. Each team has made sensible local decisions, and many have built excellent internal tools. But the sum of those decisions has produced friction that no single team owns.

When we ran our most recent internal engineering survey, a few themes came up again and again:

- **Slow feedback loops.** CI times and flaky tests were the most common complaint, especially for engineers working across multiple repositories.
- **Inconsistent onboarding.** New hires reported that getting to a first meaningful pull request ranged from a few days to more than two weeks, depending on the team.
- **Fragmented tooling.** Engineers often didn't know which internal tools existed, which were supported, and which were quietly abandoned.
- **Hard-to-find knowledge.** Documentation exists, but it is scattered across wikis, READMEs, and chat threads.

These aren't problems you fix with a hackathon. They need sustained attention, shared ownership, and someone accountable for measuring whether things actually get better.

## What the working group is

The Developer Experience Working Group is a cross-functional team of engineers from platform, product, infrastructure, security, and support. Membership rotates every two quarters so the group stays connected to day-to-day engineering work rather than drifting into an ivory tower. A small core team provides continuity, runs the weekly triage, and keeps the roadmap honest.

The group is not a gatekeeper. We don't approve or reject tooling choices, and we're not here to impose a single way of working. Our job is to find the friction, prioritize it with data, and either fix it ourselves or help the owning team do so.

## How we'll work

We've set a few principles for ourselves up front.

**Measure before we build.** We're establishing a baseline for a handful of metrics: CI duration, flaky test rate, time to first pull request for new hires, and the time it takes to get a local environment running from scratch. We'll also keep running a short quarterly survey so that numbers are paired with how the experience actually feels.

**Work in the open.** The group's roadmap, meeting notes, and metrics dashboard will be visible to everyone in the company. Anyone can file a friction report, and every report gets a response, even if the response is "not now, and here's why."

**Fix the paved road first.** We'd rather make the default path excellent than build elaborate escape hatches. If the standard way to create a service, run tests, or deploy is fast and reliable, most teams will happily use it.

**Treat internal tools like products.** Internal tools deserve owners, documentation, release notes, and a way to collect feedback. We'll help teams adopt that mindset and retire tools that no longer earn their keep.

## What's on the roadmap

For the first two quarters, we're focusing on four areas:

1. **CI reliability and speed.** We'll quarantine and triage the flakiest tests, introduce better caching, and publish per-repository CI dashboards.
2. **One-command setup.** The goal is for a new engineer to go from a fresh laptop to a running local environment with a single documented command.
3. **A unified service catalog.** A searchable index of services, owners, runbooks, and internal tools, so "who owns this?" has a fast answer.
4. **Documentation standards.** Lightweight templates and ownership rules that keep docs close to the code and make staleness visible.

## How you can get involved

If you work here, the best thing you can do is tell us what hurts. File a friction report in the `#dx-feedback` channel or through the intake form, and be specific: what you were trying to do, what got in the way, and roughly how much time it cost you. Concrete examples help us prioritize far better than general frustration does.

We'll share progress here on the engineering blog every quarter, including the things that didn't work. Our hope is simple: that a year from now, fewer of your afternoons disappear.
