# Deciding which cases to write

Learn the area around the change and rank where it can fail, then derive the conditions and write one case per condition. The techniques are the black-box techniques of the ISTQB Foundation Level syllabus (equivalence partitioning, boundary value analysis, decision tables, state transitions), followed by coverage and level rules.

## Know the area first

A requirement for a future release describes a change. The cases also need the behavior it changes and what sits around it, at this depth:

1. Current behavior of the changed area: what a user does today and what the system does, with the source (the released product, the code, the current PRD or spec, an operations runbook). Behavior read from code counts as inferred until its owner confirms it.
2. One step out in each direction: what calls or feeds the area, and what consumes its data or events (other services, reports, batch jobs, notifications, reconciliation).
3. Data that already exists: records created before the change, work in flight when it is released, and the migration between the two.
4. Environments: how each test environment differs from production in configuration, feature switches, versions of other systems, and stubs.
5. Other changes in the same release that touch the area.
6. History: incidents and defects in the area, and what support hears about it.

Read further out where the impact is high. A change near money, personal data, or shared records justifies reading the systems two steps away.

When the only source is a PRD for a future release:

1. Fill the suite's Context table with what is known, its source, and each unknown with an owner.
2. Raise each unknown as an open question. A plausible guess about current behavior hides a gap that the PRD owner can close.
3. Mark a case blocked when its expected result depends on an unanswered question about current behavior.
4. Give each behavior the PRD changes regression cases for what must stay the same around it: the flows that share its screens, data, or rules.

## Rank where it can fail

Before deriving conditions, list the places the change can go wrong: each step of the flow, each system it touches, each item in the Context table. Rate each on two scales.

| Likelihood | Means |
|---|---|
| Likely | the main path, new or changed code, or an area with past defects |
| Possible | a valid path that fewer users take: another role, account type, or locale |
| Rare | an unusual combination: a second session, a retry, a slow dependency |
| Edge | a limit, a race, a clock or time zone change, or a failure between two steps |

| Impact | Means | Example |
|---|---|---|
| Nit | cosmetic, nobody is slowed down | a misaligned label |
| Minor | a workaround exists, or a few users lose time | a filter resets after a refresh |
| Major | a feature fails for some users with no workaround | one account type cannot place a buy |
| Critical | money, personal data, security, or a legal duty is affected, or most users are blocked | a wrong amount is debited |
| Catastrophic | irreversible, or spreads past this product: records lost with no recovery, a data breach, a regulatory breach, harm to the customers of other systems | a batch posts every order to the ledger twice |

Likelihood and impact together set the priority (P1 blocks release, P2 must be known before release, P3 can follow):

| Impact | Likely | Possible | Rare | Edge |
|---|---|---|---|---|
| Catastrophic | P1 | P1 | P1 | P1 |
| Critical | P1 | P1 | P1 | P2 |
| Major | P1 | P2 | P2 | P3 |
| Minor | P2 | P3 | P3 | accepted |
| Nit | P3 | P3 | accepted | accepted |

1. Rate impact for the worst outcome that can plausibly happen, and write the reason: "Critical: a wrong fee posts to the ledger, and reconciliation only runs nightly."
2. Product rates impact, from what users and the business lose. Engineering rates likelihood, from the code, the size of the change, and the history. Record who rated each.
3. Depth follows priority. Give a P1 risk every technique on this page that applies, with cases at each level it crosses: a unit test for the rule, and an end-to-end or SIT case for the wiring. For a P3 risk, one case at the lowest level that proves it is enough.
4. "Accepted" means no case. The coverage table lists accepted risks with the person who accepted each.
5. Write and run cases in priority order, so a run that is cut short still covers the worst failures.

## From a requirement to conditions

For each requirement statement:

1. Underline the inputs, the limits, the roles, the states, and the outcomes.
2. Write the positive condition: valid input, allowed role, expected outcome.
3. Write one condition per stated failure, limit, and reason code.
4. Apply the techniques below to find the conditions the statement implies but does not list.
5. Record a question for anything the statement leaves undecided.

A requirement such as "A one-time passcode shall expire after five minutes and shall be limited to five requests per number per hour" gives: code accepted within five minutes, code rejected after five minutes, fifth request in an hour accepted, sixth rejected, and the counter resetting after the hour.

## Equivalence partitioning

1. Split each input into groups the system treats the same way: valid quantities, quantities below the minimum, non-numeric input.
2. Test one value from each group. More values from the same group add cost and no information.
3. Include invalid groups and the group "absent" (empty, null, missing field).
4. Partition outputs and states too: each account status, each role, each currency that follows a different rule.
5. When three currencies follow one rule, one case covers the rule and one cheap check per currency covers configuration. When each has its own rounding or limit, each is its own partition.

## Boundary value analysis

1. For each limit, test just below, at, and just above: with a minimum of 5, test 4, 5, and 6.
2. Limits include lengths, counts, amounts, dates, timeouts, and rate limits.
3. Time limits need a way to move time: a configurable duration or a clock the test controls. State which.
4. Check both ends of a range, and the empty and maximum sizes of a list.
5. Decimal limits need the smallest step: with two decimals and a minimum of 5.00, test 4.99.

## Decision tables

Use when several conditions combine into an outcome (role, account restriction, balance, feature switch).

| | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| Account restricted | no | no | yes | yes |
| Balance sufficient | yes | no | yes | no |
| Outcome | order placed | `INSUFFICIENT-BALANCE` | `ACCOUNT-RESTRICTED` | `ACCOUNT-RESTRICTED` |

1. One column is one case, or one variant under a parent case when the columns share steps.
2. Merge columns only where the requirement says a condition does not matter, and write that down.
3. The table shows which check takes precedence when two fail, and a requirement that does not say so leaves an open question.
4. With many conditions, cover each pair of values at least once and add the combinations the business names as risky.

## State transitions

Use when the thing under test has statuses (an order, an application, a session).

1. List the states and the events that move between them.
2. Write a case for each valid transition.
3. Write cases for the invalid ones that matter: cancel after completion, a second submit, an event arriving twice or out of order.
4. Cover time-driven transitions (expiry, timeout) and what happens to work in flight.
5. Cover interruption: the user leaves halfway and returns, a dependency fails between two steps, and what is reversed.

## Experience-based additions

After the systematic techniques, add cases from known weak spots:

1. Double submit and retry after a timeout: the action must take effect once.
2. The same record changed from another session or by another person.
3. The dependency that is slow, down, or returns an unclear answer.
4. Data created before the change, and migration of in-flight work.
5. Permissions: each role against each action, including a direct request that skips the screen.
6. Long, empty, and unusual text; other locales; keyboard-only and screen-reader use.
7. Whatever failed in production last time in this area.

## Coverage

| Requirement | Cases | Notes |
|---|---|---|
| PRD-1 | AUTH-01, AUTH-02, AUTH-07 | |
| PRD-2 | DOC-01 to DOC-06 | upload on desktop is manual only |
| PRD-3 | none | out of scope for this release |

1. List every requirement id, including those with no case and why.
2. Each case appears under at least one requirement. A case under none is a missing requirement or an unneeded case.
3. Coverage counts conditions. Many cases on one partition still cover one condition.
4. Report coverage with the run: requirements with all cases passed, with a failure, and not yet run.
5. Coverage includes the Risks table. A P1 or P2 risk with no case is a gap, and an accepted risk names who accepted it.

## Choosing the level

| Level | Proves | Typical cases |
|---|---|---|
| Unit | one rule in isolation | calculations, rounding, validation, state machine transitions, mapping tables |
| Integration | this code with one real dependency | queries, message handling, an API client against a stub or sandbox |
| Contract | the agreed request and response format between two services | request and response fields, error codes |
| End to end | a user flow through the deployed system | the main paths, one or two failure paths that cross services |
| SIT | several systems together in a shared environment | flows that cross teams, reconciliation, cutover |
| UAT | the business accepts the behavior | what a product owner or operator must see and sign |

1. Test each condition at the lowest level that can prove it. Rounding belongs in a unit test; a UAT case with a calculator is the expensive way to check it.
2. Keep end-to-end and manual cases for what only they can show: wiring between systems, what the user sees, and operations procedures.
3. A manual case that is run on every release is a candidate for automation. Cite the automated test from the manual suite and remove the manual steps.
4. Non-functional conditions need their own method: a load test for capacity, an audit against the stated standard for accessibility, a failover drill for degradation.

## Engineering-only design

1. One row per condition: id, requirement, level, technique, input, expected, test name.
2. Give the test the name of the behavior it proves: `rejects_order_below_minimum`, not `test_order_3`.
3. Say what is faked and at which boundary. A test that fakes the thing it claims to prove is not coverage.
4. Group table-driven cases under one test where the language supports it, with one row per partition or boundary.
5. Mark which rows must fail before the change and pass after it. That is the evidence the test can fail.
6. Leave out tests that restate the language or a library (the Useless Test Ban in `AGENTS.md`).
7. For a spec, copy the rows into the matching level of `validation.md`.

## Sources

- ISTQB Certified Tester Foundation Level syllabus v4.0, chapter 4 (test analysis and design) and section 5.2 (risk management: risk likelihood, risk impact, product risk analysis): https://www.istqb.org. The priority matrix above is this skill's own mapping onto its P1 to P3 scale.
