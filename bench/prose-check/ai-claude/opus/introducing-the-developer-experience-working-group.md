# Introducing the Developer Experience Working Group

Every engineer here has a story about a lost afternoon. Maybe a flaky integration test failed three times before passing on the fourth. Maybe a local environment refused to build after a dependency bump, or a deploy sat in a queue for forty minutes with no explanation. Each of these moments is a small annoyance. Across a growing engineering organization, they add up to one of the largest hidden costs we pay.

Today we're announcing the **Developer Experience Working Group (DXWG)**, a cross-team effort to find those costs, measure them honestly, and pay them down.

## Why Now

Over the past two years, our engineering organization has roughly doubled. Our tooling grew with it, but not always deliberately. Services adopted different build setups. Our CI pipeline accumulated steps that made sense at the time and that nobody has revisited since. Onboarding documentation went out of date faster than anyone could fix it.

In our most recent internal survey, engineers reported spending an average of five to six hours per week "fighting the tools." New hires told us it took more than two weeks to ship their first meaningful change. These numbers don't reflect a failure by any one team. They're what happens when shared infrastructure has no shared owner.

The DXWG will be that owner.

## What We're Focusing On

We've chosen a deliberately small set of priorities for our first two quarters:

1. **Faster feedback loops.** Our median CI run for the main monorepo takes about 22 minutes. We want to cut that in half by parallelizing test suites, caching more aggressively, and running only the tests affected by a given change.

2. **Reliable tests.** Flaky tests erode trust in the entire pipeline. We'll build a flakiness dashboard, automatically quarantine tests that fail nondeterministically, and route them to the owning teams with enough context to fix them.

3. **A working laptop on day one.** We're consolidating local environment setup into a single, versioned bootstrap script with containerized dependencies. The goal is that a new engineer can clone, build, and run the core services on their first day without asking for help in chat.

4. **Documentation that stays current.** We'll move key runbooks and setup guides into the repositories they describe. When someone changes the code, the docs that need updating will be right there in the same review.

## How We'll Work

The working group isn't a new team, and it doesn't replace our platform or infrastructure teams. It's a rotating group of engineers from across product and platform teams, each contributing about 20 percent of their time for a six-month term. The rotation matters. We want the people shaping our tools to be the people who use them every day, and we want that perspective to keep refreshing.

We'll work in the open. Our roadmap, meeting notes, and metrics will live in the DXWG space on the internal wiki, and we'll post a short update in the engineering channel every two weeks. Before we make a decision that affects how you work, such as changing a lint rule, deprecating a script, or altering CI configuration, we'll publish a brief proposal and leave time for feedback.

We'll also measure what matters. Alongside build times and flakiness rates, we'll repeat the developer survey every quarter. Some of the most important signals, like frustration, confusion, and lost focus, never show up on a dashboard.

## What This Isn't

The DXWG won't mandate a single editor, ban your favorite shell aliases, or force every team's tooling into one mold. Our goal is to make the paved road good enough that people *want* to use it, not to close the side streets. Teams with different needs will keep the flexibility to meet them.

## Get Involved

Specific feedback helps us most. If something slows you down, tell us, and include as much detail as you can. "The billing service integration suite takes 14 minutes and fails about once a day" gives us far more to act on than "CI is slow."

Here's how to reach us:

- File an issue with the **`dx-friction`** label in our tracker
- Drop by our open office hours every other Thursday
- Apply for the next rotation, which opens in the spring

Good developer experience compounds. Every minute we save, every confusing error message we clarify, and every flaky test we fix gives time back to the work that matters most: building great software for our users. We're excited to get started, and we'd love your help.
