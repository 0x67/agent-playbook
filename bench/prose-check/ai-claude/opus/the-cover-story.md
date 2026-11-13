# The cover story

Last spring, our payments service had 92% test coverage. The dashboard was green, the badge on the README was green, and the number got its own slide in our quarterly review.

Then a refactor shipped that silently stopped applying regional tax to about 4% of invoices. Nobody noticed for eleven days.

The line that broke was covered. Three different tests executed it, and none of them checked the result.

This post is about how a number we were proud of became a cover story: a plausible account that let us stop asking harder questions. It's also about what we changed afterward.

## What coverage actually measures

Line coverage answers a narrow question: *did this line run while tests were executing?* It says nothing about whether any test would fail if the line did the wrong thing.

Here's a simplified version of the test that "covered" our tax logic:

```python
def test_invoice_generation():
    customer = make_customer(region="EU-DE")
    invoice = generate_invoice(customer, items=[make_item(price=100)])
    assert invoice is not None
    assert invoice.id.startswith("inv_")
```

Every line in `apply_regional_tax` ran. The test passed before the bug and after it. As far as the coverage tool could tell, nothing had changed.

When we audited the suite, we found this pattern everywhere:

- Tests that existed mainly to exercise code paths.
- Assertions on shape rather than substance.
- Heavy mocking, so the "covered" code ran against fakes that returned whatever made it pass.
- Error-handling branches covered by tests that triggered the error and then asserted only that *an* exception was raised.

This wasn't really laziness. It was a rational response to incentives. CI blocked merges below 85%, and the fastest way to get a PR through was to write a test that touched the new lines. Goodhart's law did the rest: once coverage became the target, it stopped being a good measure.

## What we changed

We didn't throw coverage out. It's still useful as a flashlight, but it makes a poor scoreboard. Uncovered code is a real signal that something has never been exercised. Covered code only tells you that signal is absent. We made four changes.

**1. We gate on diff coverage, not total coverage.** A repository-wide percentage is mostly noise. It drifts as files are deleted and code is generated, and it rewards padding easy modules. Now CI reports coverage for changed lines only, and reviewers see exactly which new branches have no test at all. The report starts a conversation; it doesn't block the merge.

**2. We run mutation testing on critical paths.** Mutation testing makes small changes to your code and reruns the tests. It might flip a `>` to `>=`, replace a return value with `None`, or delete a function call. If the tests still pass, the mutant "survived," which means nothing is checking that behavior. Running it across the whole monorepo was too slow, so we scoped it to payments, auth, and billing and run it nightly. The first run on the payments service had a 41% survival rate. That number was far more honest than 92%.

**3. We changed the review question.** Reviewers used to ask "is this tested?" Now they ask: *if this line were wrong, which test would fail?* If the author can't name one, the test isn't done. The wording change is small, but it moves attention from execution to assertion, and it has caught more issues than any tool we've added.

**4. We stopped putting the number on slides.** This change was cultural. When leadership celebrates a metric, teams optimize for it. We now report mutation scores for critical services and the count of incidents traced to untested behavior. Both are less flattering and both are more useful.

## Where we are now

Our overall line coverage has dropped slightly, to 88%, because we deleted a few hundred tests that asserted nothing meaningful. The mutation survival rate on payments is down to 12%. We've had two near-misses since the changes, and in both cases a test failed loudly before merge.

Coverage isn't bad. The problem is that any single number that's easy to compute and easy to celebrate will eventually be gamed, usually by well-meaning people doing exactly what the system asks of them. A green badge tells you a story, and it's worth checking whether that story is true.
