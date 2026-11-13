# Contributors Summit

Last month, roughly sixty people gathered in a converted warehouse for two days to talk about a codebase most of them had only ever seen through a terminal. Some had been contributing for six years. A few had merged their first pull request the week before. This was our first Contributors Summit. Here's why we ran it, what we heard, and what we're changing as a result.

## Why we did it

Our open-source project has grown faster than the processes around it. Over the past two years, monthly active contributors roughly tripled, while the core maintainer team grew by only two people. Nearly all collaboration happens asynchronously across GitHub, our forum, and chat.

That works fine for code. It works less well for what surrounds code: shared context, trust, and a sense of where the project is heading. We kept seeing the same symptoms:

- Pull requests stalled because nobody felt empowered to make a call.
- Design debates circled for weeks in comment threads.
- Contributors drifted away after a frustrating first experience.

We didn't expect one event to fix that. We did hope it would help us understand it.

## The format

We kept scheduled talks to a minimum. The first morning had three short sessions:

- a state-of-the-project overview
- a tour of the architecture's rougher edges
- a candid talk from a maintainer titled "Things I Got Wrong in Code Review"

After that, the agenda lived on a whiteboard. Anyone could propose a session, people voted with sticky dots, and the top-voted topics got rooms.

We reserved the second afternoon for pairing. Contributors brought issues they were stuck on and worked through them with maintainers. By the end of the day, 23 pull requests had been opened and 14 merged.

## What we heard

Four themes came up again and again.

**Review latency is the biggest pain point.** Nearly every session came back to this. The median time to first review on external PRs was over five days, and larger changes often waited more than two weeks. Contributors said the wait itself wasn't the worst part. The worst part was not knowing whether anyone had seen their work at all.

**The plugin API feels unstable.** Several attendees maintain plugins outside the main repository, and they described every upgrade as a recurring tax. Small, unannounced signature changes kept breaking their builds. Nobody asked for a frozen API. They asked for predictability.

**Decisions are hard to find.** Major design choices often get made in long issue threads or chat conversations that are effectively unsearchable. Newer contributors had no way to learn why things were built the way they were, so the same questions and the same debates kept resurfacing.

**Onboarding stops too early.** Our "good first issue" labels got people through the door, but nothing guided them toward a second or third contribution. Many people described hitting a cliff right after their first merged PR.

## What we're changing

We left with a long list. We've narrowed it to commitments we can actually keep:

- **A triage rotation.** Each week, one maintainer is on point to give every new PR an initial response within two business days. Sometimes that response will just be "we've seen this, and here's who will review it."
- **An RFC process.** Changes to public APIs or core architecture will go through a lightweight RFC in a dedicated repository. Accepted RFCs become the searchable record of why decisions were made.
- **A plugin API stability policy.** We're publishing a policy that defines which interfaces are stable, how deprecations work, and how much notice plugin authors get before a breaking change.
- **A contributor ladder.** We're documenting concrete paths from first-time contributor to reviewer to maintainer. We're also adding "next step" issue labels for people who've already landed a change.

We'll share numbers on how these are going in a follow-up post early next year.

## The part that doesn't fit in a changelog

Some of the most valuable moments happened outside the sessions. In one hallway conversation, two contributors discovered they'd been solving the same problem in separate forks. At one dinner, a longtime maintainer and a first-timer spent an hour happily arguing about error handling.

Open source runs on code, but relationships are what keep it going. We plan to make the summit an annual event, and we're exploring smaller regional meetups in between, with remote participation built in from the start.

If you contribute to the project, or want to, we'd love to see you at the next one. In the meantime, open that PR. Someone will get back to you within two business days.
