# Writing a test case

## Fields

| Field | Combined form | Engineering form | Rule |
|---|---|---|---|
| Id | yes | yes | `AREA-NN`, unique, not reused |
| Title | yes | yes | condition plus expected outcome |
| Verifies | yes | yes | requirement ids: `PRD-3`, `REQ-A2`, a screen state |
| Risk | yes | yes | the risk ids it covers: `R2` |
| Type | yes | yes | positive, negative, boundary, regression, non-functional |
| Priority | yes | optional | from the risk rating in `references/design.md`: P1 blocks release, P2 must be known before release, P3 can follow |
| Level | yes | yes | unit, integration, contract, end to end, SIT, UAT |
| Preconditions | yes | as fixture | exact state before step 1 |
| Test data | yes | as inputs | exact, synthetic values |
| Steps | yes | no | one action each |
| Expected: user | yes | no | what a person sees |
| Expected: system | yes | as assertions | what the system records |
| Cleanup | when state is left behind | as teardown | how to return to the starting state |
| Depends on | when blocked | when blocked | open question or other case |
| Test name | no | yes | the automated test's path and name |

## Title

1. State the condition and the outcome: "Sell more than the holding is rejected with `INSUFFICIENT-HOLDING`".
2. "Happy path buy" says which path but not what proves it. Prefer "Buy 10 units from a USD account debits the quoted total and credits 10 units".
3. Keep the id out of the wording and in its own field or prefix.

## Preconditions and test data

1. Write the state as values: role, account type, balance, existing records, feature switches, time of day when it matters.
2. Give data that produces a checkable result: quantity 10, unit price 1.42, fee 0.25%, so the expected total can be computed.
3. Say how to create the state when it is not obvious: a seed script, an admin action, a prior case.
4. Use synthetic data from the test environment. Refer to shared test accounts by an alias defined once in the suite ("ACC-USD-01"), so a real identifier never appears in a case.
5. Leave an empty field empty or write "none", since a dash is ambiguous.

## Steps

1. One action per step, written as an instruction: where, what, with which value.
2. Start from a state any tester can set up: "Sign in as ACC-USD-01 and open Buy."
3. A step that observes ("open the transaction history") belongs with the steps. What must be true there belongs in the expected result.
4. Forcing a failure is a step with a method: which stub, which switch, which value makes the dependency fail.
5. Five to eight steps is typical. Many more usually means two cases, or setup that belongs in preconditions.

Weak:

```
1. Request price lock
2. Confirm order
3. Check core and logs
```

Runnable:

```
1. Sign in as ACC-USD-01 and open Buy.
2. Enter quantity 10 and select the USD account. Press Get quote.
3. Press Confirm within the lock countdown.
4. Open Transaction history and open the newest entry.
```

## Expected results

1. Number the checks. Each is one observable fact, pass or fail.
2. Say where each is observed: which screen, message, email, table, log, or API response.
3. Give the value: the exact message text or reason code, the amount, the status.
4. When the case is about a failure, include what must not happen, such as an order being created or a second debit.
5. Write out calculations: `10 × 1.42 = 14.20; fee 0.25% = 0.04 (rounded half up); total 14.24`.

### User and system lists in the combined form

Expected, user (checked by product or QA):

1. The quote shows unit price 1.42, fee 0.04, total 14.24 USD.
2. After Confirm, the screen shows "Order completed" with a reference.
3. The holding increases by 10 units.
4. Transaction history shows the order with status Completed and total 14.24 USD.

Expected, system (checked by engineering):

1. The restriction check is called once before the hold is placed (request log, order reference).
2. One hold of 14.24 USD plus the configured buffer exists on ACC-USD-01 until the debit, then is released (core account history).
3. Exactly one debit of 14.24 USD is posted, keyed by the order reference.
4. The supplier order is placed only after the debit succeeds (timestamps in the order record).

A reviewer from product can confirm the first list without knowing an API code. An engineer can confirm the second without interpreting the screen. A failure in either list fails the case, and the record says which.

## Parent cases and variants

Group conditions that share preconditions and steps under one parent, and vary one thing per row.

```
BUY-04 Buy is rejected when the order is invalid   (parent: shared setup and steps 1 to 3)

| Id        | Varies              | Data                         | Expected, user                         | Expected, system                |
| BUY-04.1  | below minimum       | quantity 4                   | 1. "Minimum order is 5" (`MIN-ORDER`)   | 1. no hold 2. no debit 3. no order row |
| BUY-04.2  | at minimum          | quantity 5                   | 1. quote shown 2. order completes       | 1. one debit of 501.25                 |
| BUY-04.3  | insufficient balance| quantity 10, balance 1002.49 | 1. `INSUFFICIENT-BALANCE` message       | 1. no hold 2. no debit                 |
| BUY-04.4  | lock expired        | confirm at 16 s              | 1. `QUOTE-EXPIRED` message              | 1. no debit                            |
```

1. The parent contains what is shared: preconditions, steps, and cleanup. It has no result of its own; it passes when all its variants pass.
2. Each variant has an id under the parent's (`BUY-04.1`), the one thing it varies, its data, its own expected results, and its own run result. A failure is reported by variant id.
3. Number the checks inside each expected cell (`1. ... 2. ...`), one check per number, as above. Checks joined by commas or semicolons read as one, and a run cannot report which of them failed. Each variant writes out its own checks; "same as BUY-04.3" leaves the reader to guess what is checked. A variant whose result is wholly undecided is not a row yet: it goes in the open questions table with its reserved id.
4. A variant differs from its siblings in one input or state. Two changes at once belong to a decision table (`references/design.md`), with one variant per column.
5. Nest one more level when a second input varies across the same variants, for example each rejection for each of three currencies: `BUY-04.1.a` to `BUY-04.1.c`. Write the inner level as a second table or extra columns. Past two levels, split the parent.
6. Group the negative and boundary variants under the flow they belong to, so a reader sees the positive path and what breaks it together.
7. A variant whose steps differ from the parent's (forcing a dependency to fail, a different entry point) is its own case, not a row.
8. Coverage and run summaries count variants, since each is one condition.
9. In a tracker without nested items, the variant table goes in the parent case's description, and the run record lists results by variant id. Where the tracker has test parameters or data sets, use those.

## Negative and boundary cases

1. One invalid condition per case or variant, with the rest of the input valid, so the failure has one cause.
2. Give the exact message or reason code the user sees.
3. Check the absence of side effects: nothing saved, nothing charged, counters unchanged.
4. Test each limit just below, at, and just above its value (`references/design.md`).
5. For a dependency failure, state what the user sees, what is retried, and what is reversed.

## Run record

A case describes a test, and a run records one execution of it:

| Field | Content |
|---|---|
| Case | the id |
| Build | version or commit |
| Environment | SIT, UAT, staging |
| Date and tester | when and who |
| Result | pass, fail, blocked, not run |
| Failed check | which numbered check, user or system |
| Evidence | screenshot, log excerpt, response body, query result |
| Defect | link, on a failure |

1. Keep runs apart from the case text, so the case can be run again on the next build.
2. Blocked needs a reason and an owner. A blocked case is not a passed case.
3. The suite summary counts cases by result for each run. Sign-off refers to one run of the suite.

## In a tracker

1. One item per case, with the id at the start of the summary.
2. The parent item contains the scope, the out of scope list, the coverage table, the readiness checklist, and the run summary. A parent with no description leaves a reader to open every child.
3. Use labels or components for area, type, and level, so the suite can be filtered. Text in the description is not filterable.
4. Workflow status tracks the work on the item. Record the test result in its own field, or in the run record as a comment with evidence.
5. Link each case to the requirement and to defects with tracker links, since a title can change.
6. Readiness items (environment set up, access granted, a mapping agreed between teams) use a different type or a checklist on the parent.
7. Do not close a case that depends on an open question. Link the question as a blocker.

## Sources

- ISO/IEC/IEEE 29119-3:2021, Software testing, Part 3: Test documentation (test case specification): https://iteh.eu/catalog/standards/iso/b4f42a41-dd8f-446c-9674-238ba5dc90f1/iso-iec-ieee-29119-3-2021. The field list above follows its commonly cited elements (identifier, objective, preconditions, inputs, expected results, traceability); the standard's text was not consulted directly.
