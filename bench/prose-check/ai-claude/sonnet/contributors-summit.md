# Contributors Summit

Last month, we hosted our first-ever Contributors Summit: two days, forty-two people from eleven countries, and one very overworked espresso machine. We'd been talking about running something like this for years. Our open source projects have grown from side experiments into infrastructure that thousands of teams depend on, and the people who make that possible rarely get to sit in the same room. This post is a look at how we planned the event, what we learned, and what we're changing as a result.

## Why we did it

Most of our collaboration with outside contributors happens asynchronously. Pull requests, issue threads, and the occasional video call carry a surprising amount of weight, but they flatten something important: context. A reviewer who asks for a refactor in a comment may not realize the contributor is working around a constraint in their production environment. A contributor who abandons a PR after three rounds of feedback may never tell us why.

We wanted to close that gap. The goal wasn't a conference with talks to passively absorb. It was a working session, where maintainers, regular contributors, and a few first-timers could argue about design, pair on stubborn bugs, and put faces to usernames.

## How we structured it

We borrowed heavily from unconference formats. Day one opened with a short session where anyone could propose a topic on a whiteboard, and we voted with sticky dots. By ten o'clock we had a schedule of twelve sessions that nobody on our team had planned.

A few ground rules shaped the format:

- **No slides longer than five minutes.** If a session needed a presentation, it had to leave the majority of its time for discussion.
- **Every session produces a written artifact.** Notes, a decision, a draft RFC, or a list of open questions. Nothing evaporates when the room empties.
- **Maintainers listen first.** We asked our own engineers to hold their opinions until contributors had spoken. It was harder than it sounds.

Day two was mostly hands-on. We set up a "contribution clinic" where newer contributors paired with maintainers on real issues, and a parallel track for tackling long-standing design debates.

## What we heard

Some of the feedback confirmed what we suspected. Much of it didn't.

**Review latency is the biggest friction.** We knew our response times varied, but we underestimated how much a slow first response discourages newcomers. Several contributors said they'd stopped sending larger changes because the wait made the investment feel risky. One person described it as "shipping into a void."

**Our contribution docs assume too much.** Our setup guide worked flawlessly if you already used our preferred tooling. For everyone else, it was a maze. During the clinic, two first-time contributors spent most of the morning just getting the test suite to run. Watching that happen in real time was more instructive than any survey.

**Contributors want a path to ownership.** Several long-time contributors asked how they could take on more responsibility. We had an informal answer, but nothing written down. Ambiguity here quietly pushes talented people away.

**Good-first-issue labels are often misleading.** What we considered beginner-friendly frequently required deep knowledge of internal architecture. We'd labeled issues based on how small the diff was, not how much context was needed.

## What we're changing

We left with a short list of commitments, and we want to hold ourselves to them publicly:

1. **A first-response target.** Every new pull request will get a human acknowledgment within three business days, even if it's just "we've seen this, a full review is coming."
2. **Rewritten onboarding docs.** We're rebuilding the contributor guide around a containerized dev environment, tested by someone who has never touched the project.
3. **A documented maintainer ladder.** We're drafting a clear, public path from contributor to reviewer to maintainer, including what we expect at each stage.
4. **Relabeling issues.** We're auditing every good-first-issue and rating it by required context, not diff size.
5. **A lightweight monthly sync.** An open, recorded call where anyone can raise a topic, so the momentum from the summit doesn't fade.

## A few personal notes

The best moments weren't on the schedule. A contributor in Lagos and one in Warsaw discovered they'd been independently fixing the same performance issue for months. Two people who had traded terse review comments for a year turned out to be natural collaborators once they shared a table. Our team left with a renewed sense of who we're building for.

We also made mistakes. We under-provisioned for accessibility needs, and our remote option was an afterthought rather than a first-class experience. Next time, we'll plan both from the start, and we'll likely run a regional event to make attendance easier.

## Thank you

To everyone who traveled, took time off, or stayed up late to join us remotely: thank you. Open source runs on goodwill and curiosity, and you brought plenty of both.

If you'd like to follow our progress on the commitments above, watch the tracking issue in our community repository. And if you couldn't make it this time, the notes from every session are published there too. We'd love to see you at the next one.
