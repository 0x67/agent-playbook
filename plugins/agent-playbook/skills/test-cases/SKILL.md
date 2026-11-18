---
name: test-cases
description: >
  Writes and reviews test cases in two forms: a combined product and
  engineering case (what the user sees, checked by product or QA, beside what
  the system records, checked by engineering) and an engineering-only test
  design that maps requirements to automated tests. Use on /test-cases, "write
  test cases", "test plan", "test scenarios", "UAT cases", "SIT cases", "QA
  checklist", "acceptance tests", "regression suite", "test matrix",
  "coverage matrix", "risk-based testing", "what could go wrong", "review these test cases", or when turning a PRD, spec,
  ticket, or design into tests. Works alone from a ticket or the code, and together with
  the prd, spec-driven, and ui-ux skills when their documents exist. Not for writing test code itself: the language skill's testing page
  covers that.
---

# Test cases skill

A test case is an instruction another person can run without asking the author anything, with a result that two people would judge the same way. This skill covers how to derive cases, how to write them, and how to record a run; test code is covered by the language skills.

## Routing table (mandatory)

Paths are relative to this skill's directory.

| Task | Read |
|---|---|
| writing or reviewing any case: fields, steps, expected results, data, run records, tracker layout | `references/writing.md` |
| deciding which cases to write: context around the change, risk ranking, partitions, boundaries, decision tables, state transitions, coverage, test levels | `references/design.md` |
| a combined product and engineering suite | copy `_template/product-engineering.md` |
| an engineering-only test design | copy `_template/engineering.md` |

## Pick the form

| Form | Readers | Use when | Output |
|---|---|---|---|
| Product and engineering | product, QA, operations, engineers | UAT, SIT, a release sign-off, anything a non-engineer runs or approves | cases with a user-visible result and a system result kept apart |
| Engineering only | engineers, reviewers, coding agents | planning automated tests for a change, a spec's validation, a regression suite | a table that maps each requirement to named tests at a level |

One feature often needs both. The engineering design automates what it can; the combined suite covers what a person must see, what crosses systems, and what needs sign-off. A case automated in the engineering design is cited from the combined suite, and is not written twice.

## Where it lives

`specs/<slug>/test-cases.md`, beside the PRD and spec. An engineering-only design for a spec goes into that spec's `validation.md` tables. A team that runs cases from a tracker (Jira, a test management tool) keeps them there, one case per item, with the suite summary and coverage table on the parent item; keep a link in the spec folder.

## Before writing

1. Find the source of truth, in this order: the PRD's user stories (`PRD-*`), the spec's requirements (`REQ-*`, `AC-*`), the design's screen states, the ticket, the code. Read it. With none of them, write down the behavior you inferred from the code and have it confirmed before anyone runs the cases.
2. Learn the area around the change (`references/design.md`): current behavior, the systems one step upstream and downstream, data that already exists, how the environments differ from production, other changes in the same release, and past incidents. A PRD for a future release describes only the change; when current behavior is not written down, read the code or ask, mark what you inferred, and raise each unknown as an open question.
3. List what is in scope and what is out, using the PRD's out of scope table when there is one.
4. List where the change can go wrong and rate each place for likelihood (likely, possible, rare, edge) and impact (nit, minor, major, critical, catastrophic). Together they set the priority and how deep to test (`references/design.md`).
5. Derive the conditions to test before writing any case (`references/design.md`), and show the list: it is cheaper to correct than finished cases.
6. Separate what is not a test: environment readiness, access requests, and agreements between teams are a checklist that must be complete before the run starts.
7. Decide where each condition is tested. The lowest level that can prove it is the right one.

## Core rules

- Each case tests one condition and has one reason to fail. A loop in prose ("for each currency", "for each code") hides how many conditions there are and which one failed.
- Conditions that share setup and steps are grouped under a parent case as variants: the parent has the shared preconditions and steps, and each variant is a row with its own id (`BUY-04.1`), data, expected result, and run result. The negative and boundary cases of a flow usually sit under that flow's parent this way. Variants nest one level further when a second input varies (`BUY-04.1.a`); deeper than that, split the parent.
- The title states the condition and the expected outcome: "Buy below the 5-unit minimum is rejected with `MIN-ORDER`".
- Ids are unique, follow one scheme (`AREA-NN`), and are never reused. Every case in the suite has one.
- Each case cites what it verifies by id: `PRD-3`, `REQ-A2`, a screen state. A case that does not verify anything written down is a question for the requirement's owner first.
- Preconditions and test data are exact: which account, which role, what balance, which values. "A user with sufficient balance" is not runnable.
- Test data is synthetic. Real customer identifiers, account numbers, and credentials never go into a case or a ticket.
- A step is one action, with where it happens and what is entered. "Check the logs" is not a step; "In the order service log, find the entry for order reference X" is.
- An expected result is a numbered list of separate checks, each one pass or fail and each saying where to look. Clauses joined by semicolons in one paragraph are several checks written as one.
- In the combined form, the user-visible result and the system result are separate lists. Product signs off on the first; engineering on the second.
- Calculated values are worked out in the case: the inputs, the formula, and the expected number.
- An expected result that is undecided, or that rests on current behavior nobody has confirmed, blocks the case. It cannot pass, and its item cannot be closed, until the open question is answered.
- A blocked case still lists every check that is decided, in both expected lists, and marks only the undecided check as blocked with its question id. A case or variant with no decided check is not written as a case yet: list it in the open questions table with the id it will get (`BUY-05.2, pending Q2`), and add it when the answer comes.
- Each requirement has a positive case, and each stated failure, limit, and reason code has its own case. Count boundaries on both sides.
- Each behavior the change touches has regression cases for what must stay the same around it.
- Priority comes from the risk rating: a critical or catastrophic failure has cases even when it is rare, while a rare nit has none and goes in the coverage table as an accepted risk.
- A run is recorded apart from the case: build, environment, date, who ran it, pass, fail, or blocked, evidence, and the defect link on a failure. A tracker status of Done means the work item is closed, which is a different fact from the test passing.
- An automated test must be able to fail from a product bug (the Useless Test Ban in `AGENTS.md`).

## Together with the other skills

| Source | Becomes |
|---|---|
| PRD current process and system context | the Context table and the regression cases |
| PRD user story bullet (`shall`) | at least one positive case citing the story |
| PRD failure bullet, reason code, "shall not" | one negative case each |
| PRD limits, expiries, counts | boundary cases on both sides of each value |
| PRD non-functional requirements | performance, accessibility, compatibility, and degradation cases |
| PRD rollout plan | the cases that make up each phase's exit criteria, and a rollback case |
| ui-ux screen states (empty, loading, error, partial) | one case per state, with how to reach it |
| ui-ux component states and variants | visual and keyboard checks on the state sheet |
| spec `REQ-*` and `AC-*` | rows in the engineering design, then in `validation.md` |

1. When the PRD or spec changes, update the cases that cite the changed id in the same change.
2. A condition found while deriving cases that no requirement covers goes back to the PRD or spec as an open question. Do not settle it inside a test case.
3. The coverage table lists every requirement id with its cases. A requirement with none is either out of scope, with the reason, or a gap.

Without a PRD or spec the skill still works: state the behavior under test at the top of the suite, mark it as inferred, and cite tickets or code paths in place of requirement ids.

## Review checklist

Flag in a suite:

- A suite for a future release with no record of current behavior, neighboring systems, or environments, and no regression cases.
- No risk ranking, or priorities that ignore it: a rare critical failure with no case while nits have several.
- A case with several conditions, a loop in prose ("for each") where a variant table belongs, or an expected result that is one run-on sentence.
- A parent case whose variants lack their own ids, expected results, or run results, or whose variants do not share its steps.
- Steps that cannot be followed without the author: "place order", "check core and logs", "verify it works".
- Preconditions or data with no values; real customer data or credentials.
- Internal checks (API codes, field names, ledger entries) mixed into what a product reviewer is asked to confirm, or a combined case with no user-visible result at all.
- An expected result containing `TBD`, a case or variant row with no decided check ("blocked" in every cell), or a case marked done while it depends on an open item.
- Closed items with no run record: no build, date, result, or evidence.
- Cases with no id, duplicate ids, or ids in more than one scheme; a case filed under the wrong area or type.
- Readiness and agreement items counted as test cases.
- Requirements cited by section title where an id exists.
- Only positive cases; a limit tested on one side; a reason code with no case.
- A missing coverage table, or a requirement that lacks both a case and a reason.
- A parent item with a hundred children and no summary of scope, coverage, or results.
- The same check repeated in several cases, or an end-to-end case for what a unit test can prove.
- An automated test that cannot fail, or whose name claims more than it asserts.

Report each finding with the case id and a rewritten version.
