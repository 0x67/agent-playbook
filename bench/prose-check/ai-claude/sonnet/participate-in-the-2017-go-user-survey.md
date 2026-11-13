# Participate in the 2017 Go User Survey

Every year, the Go community gets a chance to tell the people building the language what is working, what is painful, and what should come next. The 2017 Go User Survey is that chance, and we at our engineering team want to encourage every Go developer, whether you write it daily or have only tried it once, to take part.

## Why the survey matters

Language design is full of tradeoffs, and the Go team can't make good ones by guessing. The survey is one of the few structured ways maintainers learn how Go is actually used in the wild: which tools people rely on, where the learning curve bites, which platforms matter, and which missing features cause real friction.

Past surveys have had visible effects. Feedback about dependency management, for example, helped push the conversation around vendoring and package tooling forward. Responses about error handling, generics, and debugging have shaped what the community discusses and what the core team prioritizes. When thousands of developers describe the same pain point independently, it becomes hard to ignore.

## Why we care at our company

We run Go in production. It powers several of our internal services, our deployment tooling, and a growing share of our data pipelines. We chose it for its fast compile times, simple concurrency model, static binaries, and a standard library that lets a small team ship reliable network services without a pile of dependencies.

That doesn't mean our experience has been friction-free. A few themes come up repeatedly in our own retrospectives:

- **Dependency management.** Reproducible builds across many services remain harder than they should be.
- **Error handling.** Explicit errors make control flow clear, but the boilerplate adds up, and attaching context consistently takes discipline.
- **Debugging and profiling.** The tooling has improved, but production debugging of concurrent programs can still be difficult.
- **Onboarding.** New engineers pick up syntax in days, but idiomatic design (interfaces, channels, package layout) takes longer.

These are the kinds of issues the survey is designed to measure. If you've hit the same ones, your response adds weight to them.

## What the survey asks

The survey is short, typically taking about ten to fifteen minutes. It covers:

- How long you've used Go and how you use it (work, open source, hobby)
- Which operating systems, editors, and deployment environments you use
- Which tools and libraries are part of your workflow
- What challenges most limit your productivity
- How you feel about the community, documentation, and the pace of change

Most questions are multiple choice, with a handful of open-text fields. Those free-text answers are often the most valuable, so don't hesitate to be specific. "Vendoring is awkward" is useful; "pinning a transitive dependency across twelve services takes us a day" is far more useful.

## Tips for giving useful answers

1. **Be concrete.** Describe real situations rather than abstract preferences.
2. **Think about your whole team.** If you lead a group, consider the problems your colleagues raise, not only your own.
3. **Mention what's going well.** Maintainers need to know what to protect, not just what to fix.
4. **Don't skip the open-text boxes.** Even a sentence or two can surface an issue that no multiple-choice option anticipated.
5. **Share it.** Participation is only representative if it includes people outside the usual circles. Pass the link to colleagues, local meetup groups, and newer Go developers.

## A note on representativeness

Surveys are only as good as their respondents. If only experienced backend engineers answer, the results will skew toward their concerns, and the needs of beginners, students, systems programmers, and people using Go in unusual domains will be underweighted. If you know someone who fits one of those groups, ask them to take part. A broader sample leads to better decisions.

## How to participate

Look for the official 2017 Go User Survey link on the Go blog and the project's community channels, and complete it before the deadline announced there. Results are typically summarized publicly afterward, so you'll be able to see how your answers compare with the wider community's and how they inform the language's direction.

We'll be filling it out as a team, and we'll share our own takeaways internally once the results are published. If you use Go in any capacity, please take a few minutes to add your voice. The language gets better when the people who use it speak up.
