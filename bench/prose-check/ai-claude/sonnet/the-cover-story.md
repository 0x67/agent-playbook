# The cover story

Every outage has two stories. The first is the one you tell while it's happening: "elevated error rates on the checkout service, investigating." The second is the one you learn weeks later, after the dashboards have cooled and someone finally reads the logs end to end. This post is about a time those two stories diverged, and about what we changed so they diverge less often.

## The incident that wasn't what it said

Last spring, our payments API began returning intermittent 502s. Error rates climbed to about 4% over twenty minutes, then dropped back to normal without anyone doing anything. Within the hour, we had a tidy explanation: a noisy neighbor on a shared node had starved our pods of CPU. The graphs agreed. CPU throttling spiked right when the errors did. We wrote it up, filed a ticket to tune resource limits, and moved on.

Two weeks later it happened again. Same shape, same throttling spike, and this time we had already "fixed" the limits.

That was the moment we realized our first explanation had been a cover story. Not a lie. Nobody was hiding anything. It was a story that fit the evidence we happened to look at, told with more confidence than that evidence deserved.

## How cover stories form

Looking back, the pattern was predictable, and we think it's common to most teams.

**The first plausible cause wins.** Under pressure, the explanation that arrives first gets the most airtime. Everything afterward is interpreted as confirmation. CPU throttling was real, so it felt like the cause. It was actually a symptom: retries from a failing dependency were burning CPU.

**Correlation is cheap on a dashboard.** When you plot enough metrics on the same time axis, something will line up. We had 40 panels on our service overview. Of course one of them spiked.

**Recovery looks like proof.** When errors dropped on their own, we read that as the noisy neighbor leaving. In truth, a downstream connection pool had simply drained and refilled. Self-healing systems are wonderful for uptime and terrible for forensics, because they erase the scene.

**Postmortems reward closure.** A document with a clear root cause and three action items feels finished. "We don't know yet" feels like failure, so it gets edited into something more satisfying.

## What the logs actually said

On the second occurrence, someone (credit to our teammate Priya) skipped the dashboards and traced a single failed request across services. The 502 came from our gateway, which had timed out waiting on the fraud-scoring service. Fraud scoring was slow because it was waiting on a database connection. The pool was capped at 20, and a batch job that ran every few hours had started holding connections longer after a schema change.

The CPU throttling was our own gateway retrying aggressively into a slow dependency. We had been staring at the smoke and calling it the fire.

## What we changed

We didn't adopt a grand new process. We made a few small commitments.

1. **Separate "what we observed" from "what we believe."** Every incident doc now has two distinct sections. Observations are timestamps, graphs, and log lines. Beliefs are hypotheses, each with a confidence level and the evidence that would disprove it.

2. **Require one end-to-end trace before declaring a cause.** Aggregate metrics can suggest where to look, but a root cause needs at least one concrete request followed from entry to failure.

3. **Keep the incident open until it can be reproduced or explained.** Self-resolving incidents get a "recurrence watch" status instead of being closed. If the same signature shows up again, we reopen the original rather than starting fresh, which preserves the history of what we got wrong.

4. **Ask "what would this explanation fail to predict?"** If our theory is noisy neighbors, why did only the payments path degrade? A story that can't answer follow-up questions is a draft.

5. **Trim the overview dashboard.** We cut it from 40 panels to 12, organized around request flow rather than infrastructure layers. Fewer coincidences to be fooled by.

## The takeaway

We still write quick, confident summaries during incidents, because teammates and customers need something to hold onto. But we now label them as what they are: working theories, provisional by default.

The goal isn't to distrust every explanation. It's to keep the cost of revising one low. The worst part of our spring incident wasn't the wrong diagnosis; it was how hard we'd made it to say, two weeks later, "we got this wrong."

A good postmortem doesn't just tell you what broke. It tells you how you came to believe what you believed, and where that belief was thinnest. That's the real cover story worth uncovering.
