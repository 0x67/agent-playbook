# <Change> test design

| | |
|---|---|
| Verifies | <spec, REQ ids, ticket; "inferred from code" when none> |
| Owner | <name> |
| Run with | <the exact test commands> |

## Context

| Area | Known | Source | Unknown, owner |
|---|---|---|---|
| Current behavior | <what the code does today in the changed area> | <`path::Symbol`, earlier spec> | <question, owner> |
| Callers and consumers | <what calls this code and what reads its output> | | |
| Existing data | <rows, messages, or files created before the change> | | |
| Environments | <how test configuration and stubs differ from production> | | |

## Risks

| Id | What can go wrong | Likelihood | Impact | Reason | Priority |
|---|---|---|---|---|---|
| <R1> | <the failure> | likely, possible, rare, edge | nit, minor, major, critical, catastrophic | <the worst plausible outcome> | <P1, P2, P3, accepted> |

Write the conditions for P1 risks first.

## Conditions

| Id | Verifies | Risk | Level | Technique | Input or state | Expected | Test name | Fails before the change |
|---|---|---|---|---|---|---|---|---|
| <ORD-01> | <REQ-A1> | <R1> | unit | boundary | <quantity 4, minimum 5> | <error `MIN-ORDER`, nothing saved> | <`orders::tests::rejects_order_below_minimum`> | yes |

Rows that share a fixture and differ in input are one table-driven test: give them ids under one parent (`ORD-01.1`, `ORD-01.2`) and the same test name with the row label.

## Fakes and fixtures

| Dependency | Replaced by | At which boundary | Why |
|---|---|---|---|
| <payments API> | <recorded stub> | <HTTP client> | <no sandbox for failure codes> |

## Coverage

| Requirement | Conditions | Notes |
|---|---|---|
| <REQ-A1> | <ORD-01, ORD-02> | <or "none" with the reason> |

## Not automated

| Condition | Why | Covered by |
|---|---|---|
| <what a person must see or sign> | <reason> | <case id in the combined suite> |

## Open questions

| # | Question | Owner | Blocks |
|---|---|---|---|
| 1 | <undecided behavior found while deriving conditions> | <name> | <condition ids> |
