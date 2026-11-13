# Announcing the 2021 Go Developer Survey

Every year we ask the people who write Go every day how things are going. What's working? What's frustrating? What do you wish existed? Today we're opening the **2021 Go Developer Survey**, and we'd like to hear from you.

**[Take the 2021 Go Developer Survey →](#)**

The survey takes about 15 minutes and will be open until **[closing date]**.

## Why this survey matters

Go is used by a very wide range of developers. Some build cloud infrastructure, some write command-line tools, and some ship web services, data pipelines, or embedded systems. Some have written Go since before 1.0, and some wrote their first `func main()` last week. No single team can see all of that firsthand. Bug reports, mailing lists, and conference conversations tell us a lot, but they mostly reflect the people who already speak up.

The annual survey fills in the rest of the picture. It shows us where developers spend their time, which parts of the toolchain cause friction, and which problems are common rather than just loud. Past results have directly shaped our priorities:

- **Dependency management.** Survey feedback helped us understand where developers struggled with the move to modules. That guided improvements to `go get`, `go mod tidy`, and module-aware error messages.
- **Editor tooling.** Developers repeatedly said that a consistent editor experience mattered to them. That pushed us to invest heavily in `gopls`, the Go language server, so that autocompletion, navigation, and refactoring work well in every major editor.
- **Generics.** Year after year, the lack of generics ranked among the biggest challenges respondents reported. That signal, along with years of design discussion, helped bring type parameters to the language.

When you take the survey, you're helping decide what we work on next.

## What's new this year

Most of the survey will be familiar, because tracking the same questions over time lets us measure whether things are actually improving. We've also added sections that reflect where Go is heading:

- **Generics readiness.** Type parameters are coming in Go 1.18. We want to know how you plan to use them, what concerns you have, and what documentation or tooling would help you adopt them.
- **Fuzzing.** Native fuzz testing is also arriving in the standard toolchain. We're curious how many of you already fuzz your code, with what tools, and what would make fuzzing part of your normal workflow.
- **Security and the software supply chain.** Teams are paying more attention to how dependencies are vetted and how vulnerabilities are found and fixed. We'd like to understand your current practices and where Go could do more to help.
- **Onboarding.** We're adding questions about the first few weeks with Go: what helped, what confused you, and what you wish someone had told you sooner.

## Who should take it

**Everyone who uses Go, or has used it.** We especially want to hear from:

- Developers who are new to Go, because your first impressions show us problems that experienced users have learned to work around.
- People who use Go only occasionally or as a secondary language.
- Anyone who tried Go and moved on. Knowing why Go *didn't* work for you is just as valuable as knowing why it did.
- Developers working outside the large tech hubs, in smaller companies, in academia, or on hobby projects.

If you know a teammate, friend, or community group that writes Go, please share the link. Broad participation is what makes the results meaningful.

## Your time and your privacy

We know your time is valuable, so we've kept the survey as short as we can while still getting useful data. Most people finish in about 15 minutes. Every question is optional, so skip anything that doesn't apply to you or that you'd rather not answer.

The survey is anonymous. We don't ask for your name or contact information. Responses are analyzed in aggregate, and nothing we publish will identify an individual respondent. Free-text answers are read by members of the team to find themes, and they are never published in a way that ties them back to you.

## What happens next

After the survey closes, we'll spend a few months analyzing the results. Then we'll publish a full write-up here on the blog, including charts, year-over-year trends, and a discussion of what we're changing in response. You can find results from previous years in our blog archive if you'd like to see how earlier feedback turned into concrete work.

## Thank you

Go exists because of its community: the people who file issues, review proposals, maintain libraries, answer questions, and write code with it every day. This survey is one of the most direct ways we have to listen to all of you at once.

Please take 15 minutes, tell us what you think, and pass it along.

**[Take the 2021 Go Developer Survey →](#)**

*Happy coding, and thank you for helping us make Go better.*
