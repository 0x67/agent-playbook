# <PRD id> <Feature name>

| | |
|---|---|
| Target release | <quarter or date> |
| Epic | <epic or ticket link> |
| Platform | <apps and surfaces affected> |
| Document status | draft, in review, agreed, released |
| Document owner | <name> |
| Designer | <name> |
| Tech lead | <name or team> |
| Stakeholders involved | <teams that must review> |

## Objective

<What this replaces or adds, for whom, and the scope of the first release.>

<The target outcome as a measurable result, the standard that must not weaken, and the existing processes this PRD does not change.>

## Current process and limitations

<How it works today, step by step, and where it fails: the rework, the waiting, what nobody can measure. Give the cause of each limitation.>

## System context

| Area | Today | Source |
|---|---|---|
| Current behavior | <what the released product does in this area> | <earlier PRD, spec, code path> |
| Upstream and downstream | <systems that feed this area or consume its data> | <owning team> |
| Existing data | <records created before release, work in flight> | <source> |
| Same release | <other changes that touch this area> | <PRD or ticket> |

## Current metrics

| Metric | Current | Source |
|---|---|---|
| <what is measured> | <value, or "Not measurable"> | <log, queue, dashboard, ticket taxonomy> |

## Success metrics

| Metric | Baseline | Target (<window after launch>) |
|---|---|---|
| <metric> | <current value, or a dash when new> | <threshold with a comparison sign> |

## User stories

| User story | Requirement | Notes |
|---|---|---|
| **1.** As a <role>, I want <capability>, so that <outcome>. | <ul><li>The system shall <observable behavior>.</li><li><Limit, expiry, or count, with its value or "configured".></li><li><Failure behavior and its reason code `REASON-CODE`.></li></ul> | <Why a deliberate choice was made, when a reader would expect the opposite.> |

## Experience

<Only for features with an interface. Flows in order, the screens each one touches, and the states each screen must handle: ideal, empty, loading, error, partial, with a link to the design once it exists.>

| Flow | Screens | States to design | Design link |
|---|---|---|---|
| <flow> | <screens> | <states> | <artboard or page> |

## Out of scope

| Item | Rationale |
|---|---|
| <adjacent thing a reader would expect> | <why it is out, and where it is handled> |

## Dependencies and assumptions

| Type | Detail | Owner |
|---|---|---|
| Dependency | <service, contract, interface, or team delivery this waits on> | <team> |
| Assumption | <what this PRD takes as given> | <team that confirms it> |

## Open questions

| # | Question | Owner | Needed by |
|---|---|---|---|
| 1 | <question> | <team or name> | <milestone: design sign-off, development start, pre-launch> |

## Non-functional requirements

| Area | Requirement |
|---|---|
| Performance | <latency at a stated percentile> |
| Availability | <target and where it is measured> |
| Degradation | <behavior when a dependency is down> |
| Capacity | <concurrent and peak load> |
| Security | <encryption, access, logging> |
| Retention | <what is kept, how long, what is purged> |
| Auditability | <what must be reconstructible, from which record> |
| Accessibility | <standard and level> |
| Localisation | <languages> |
| Compatibility | <platform and browser versions> |
| Observability | <dashboards and alerts> |

## Rollout plan

| Phase | Scope | Exit criteria |
|---|---|---|
| 1: Internal | <who gets it, on which platform> | <measurable conditions to move on> |

<Where traffic returns to on rollback, and what happens to work in flight.>

## Glossary

| Term | Definition |
|---|---|
| <term used in the requirements> | <one definition, used the same way throughout> |

## Change log

- <YYYY-MM-DD> <what changed and why>
