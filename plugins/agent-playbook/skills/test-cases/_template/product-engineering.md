# <Feature> test cases

| | |
|---|---|
| Verifies | <PRD id, spec, or ticket; "inferred from code" when none> |
| Environments | <SIT, UAT> |
| Owner | <name> |
| Product reviewer | <name> |
| Engineering reviewer | <name> |
| Status | draft, reviewed, in run, signed off |

## Scope

<What this suite covers, and what it leaves out with the reason.>

## Context

What the suite takes as true about the product today. An unknown blocks the cases that depend on it.

| Area | Known | Source | Unknown, owner |
|---|---|---|---|
| Current behavior | <what users and the system do today in the changed area> | <released app, code path, earlier PRD> | <question, owner> |
| Upstream and downstream | <systems that feed this area or consume its data> | | |
| Existing data | <records created before the change, work in flight, migration> | | |
| Environments | <how SIT and UAT differ from production: configuration, switches, versions, stubs> | | |
| Same release | <other changes that touch this area> | | |
| History | <past incidents and defects in this area> | | |

## Risks

| Id | What can go wrong | Where | Likelihood | Impact | Reason | Rated by | Priority | Cases |
|---|---|---|---|---|---|---|---|---|
| <R1> | <the failure> | <screen, service, job> | likely, possible, rare, edge | nit, minor, major, critical, catastrophic | <the worst plausible outcome> | <product for impact, engineering for likelihood> | <P1, P2, P3, accepted> | <AREA-03, AREA-04> |

## Readiness checklist

Complete before the run starts. These are not test cases.

- [ ] <environment, access, test accounts, stubs, agreed mappings>

## Test accounts and data

| Alias | Description | State before the run |
|---|---|---|
| <ACC-USD-01> | <role and account type, synthetic> | <balance, holdings, restrictions> |

## Coverage

| Requirement | Cases | Notes |
|---|---|---|
| <PRD-1> | <AREA-01, AREA-02> | <or "none" with the reason> |

## Cases

### <AREA-01> <Condition and expected outcome>

| | |
|---|---|
| Verifies | <PRD-1, second bullet> |
| Risk | <R1> |
| Type | positive, negative, boundary, regression, non-functional |
| Priority | P1, P2, P3 |
| Level | SIT, UAT, end to end |
| Automated by | <test name, or "manual"> |
| Depends on | <open question or case, or "none"> |

**Preconditions**

1. <Exact state: account alias, role, balance, switches.>

**Test data**

<Exact input values, and the worked calculation when a number is expected.>

**Steps**

1. <An action with where it happens and which value is entered.>

**Expected, user** (product or QA confirms)

1. <What is seen, where, with the exact text or value.>

**Expected, system** (engineering confirms)

1. <What is recorded, where to observe it, with the exact value.>

**Variants** (only for a parent case; the lists above then describe the shared flow)

| Id | Varies | Data | Expected, user | Expected, system |
|---|---|---|---|---|
| <AREA-01.1> | <the one input or state that differs> | <values> | <1. exact text or value 2. ...> | <1. what is recorded 2. what is not> |

**Cleanup**

<How to return to the starting state, or "none".>

## Run record

| Case | Build | Environment | Date | Tester | Result | Failed check | Evidence | Defect |
|---|---|---|---|---|---|---|---|---|
| <AREA-01 or AREA-01.1> | <version> | <UAT> | <YYYY-MM-DD> | <name> | pass, fail, blocked, not run | <user 2, system 3> | <link> | <link> |

## Run summary

| Run | Build | Passed | Failed | Blocked | Not run | Signed off by |
|---|---|---|---|---|---|---|
| <1> | <version> | <n> | <n> | <n> | <n> | <product, engineering> |
