# PRD sections

How to size a PRD and what each section of `_template/prd.md` has to contain. `references/example.md` shows the sections filled in.

## An existing team template

Many teams already write PRDs from a wiki template: Objective, Success metrics, Assumptions, Milestones, a Requirements table (requirement, user story, importance, ticket, notes), Out of scope, Design, Open questions, Reference links. Keep that template and its column names. The usual gaps to fill inside it:

1. Objective and Success metrics left empty while Requirements runs for pages.
2. Out of scope left empty.
3. Requirements written as feature names with no testable statements.
4. Decisions recorded only as strikethrough, with no date or reason.
5. `TBD` items in the body that are missing from Open questions.

## Sizing

| Size | When | Sections |
|---|---|---|
| One-pager | one feature, one team, no staged rollout | header, Objective, System context, Success metrics, User stories, Experience, Out of scope, Open questions |
| Full | crosses teams, changes money or personal data, needs a staged rollout, or has legal or security limits | all sections of the template |

A full PRD for a large feature runs to a dozen or more stories. Past about twenty, split the feature. Delete a template section that does not apply.

## Header

1. The id and title identify the PRD in tickets and specs.
2. Fill owner, designer, and tech lead with the people who answer questions, and list the teams that must review.
3. Status is one of draft, in review, agreed, released.

## Objective

1. First paragraph: what the feature replaces or adds, for whom, and what the first release includes.
2. Second paragraph: the target outcome as a number, the standard that must not weaken while reaching it, and the existing processes this PRD does not change.
3. State the failure policy when it shapes the whole feature, for example that cases the system cannot decide go to a manual queue and are never silently rejected.

## Current process and limitations

1. Describe today's process in the order a user goes through it.
2. For each limitation give its cause: data is retyped, so transcription errors recur; no state is saved, so an interrupted user starts again.
3. Include what cannot be measured today. A missing measurement is a limitation and usually becomes a requirement.
4. Check the section by removing the proposed feature from it. If a sentence stops making sense ("users need a CSV export button"), it describes a solution; rewrite it as the situation.

## System context

What the change touches in the product as it stands, so design, the spec, and the test cases start from the same picture.

1. The current release's behavior in the area, with a link to the earlier PRD, spec, or code. A PRD for a later release states what it changes from that behavior.
2. The systems one step upstream and downstream: what feeds the area, and what consumes its data or events (other services, reports, batch jobs, notifications).
3. Data that exists before the release, and work in flight when it goes live.
4. Other changes planned for the same release that touch the area.
5. An unknown goes to Open questions with an owner. A description of the current system written from memory or guesswork misleads every document built on it.

## Current metrics and success metrics

1. Current metrics have a value and a source (a case log, a review queue, analytics, the ticket taxonomy). Write "Not measurable" where that is the truth.
2. Success metrics repeat the baseline and add a target with a comparison sign (`≤ 1 business day`, `≥ 80%`) and a window ("90 days post-launch").
3. A metric that does not exist yet has an empty baseline.
4. Include a metric for the risk the feature introduces (fraud blocked, error rate, support contacts) beside the metrics for its benefit.
5. Never invent a baseline. An unknown one becomes a placeholder such as `[BASELINE: weekly exports per user]`, and measuring it becomes a requirement.

## User stories

The table has three columns.

### The story

1. Number the stories. The number is the id (`PRD-3`) that specs, tickets, and designs cite, and it is not reused after a story is removed.
2. Use the form "As a <role>, I want <capability>, so that <outcome>."
3. Write stories for the roles around the end user as well: the reviewer or compliance officer, the support agent, the operations officer who tunes settings, the data analyst, the security engineer, and the user of assistive technology.
4. One capability per story. A story with "and" in its capability is two stories.

### The requirement bullets

1. Each bullet is one behavior that can be observed and tested, written with "shall": "A one-time passcode shall expire after five minutes."
2. Give limits, expiries, and counts their values, or say "configured" and make the configuration a requirement.
3. Write the failure behavior next to the success behavior: what is rejected, what is routed to a person, what is retried.
4. A failure the user or support will see gets a reason code (`DOC-EXPIRED`) and a plain-language message. Product, operations, and support share one list of codes.
5. Say what must not happen as well: "It shall not default to pass." "Device-reported time shall not be used for any signing record."
6. Say what is stored, for how long, and who can see it, when the feature handles personal data or decisions that may be disputed.
7. A calculation needs its formula and one worked example with real figures, plus the rounding rule.
8. Describe behavior only. Specify a mechanism only when a constraint forces it.
9. Words such as "fast", "simple", and "intuitive" need a number or a named behavior.

### The notes

1. Use Notes for the reason behind a deliberate choice that a reader would otherwise question: "Duplicate-contact handling deliberately blocks rather than merges."
2. One or two sentences. Requirements do not go in Notes.
3. Leave the cell empty when the bullets need no explanation.

### Cases to walk for each story

Record the outcome of each as a bullet under the story, or as its own story when it is large:

1. No data yet, and data the user deleted.
2. Very large and very long: 10,000 rows, a 300-character name, a 2 GB file.
3. Permissions: a role that can see but not act, a link opened by someone signed out.
4. A dependency that is slow, down, or returns an unclear result. State whether the feature proceeds, waits, or blocks.
5. The same thing changed from another tab or by another person.
6. The user stops halfway by closing the tab, losing the network, or pressing back, and comes back later.
7. Repeats: double submit, retry after a timeout, a second application after a rejection.
8. Time: time zones, expiry while the page is open, device time against server time.
9. Locale and accessibility: long translations, screen readers, keyboard-only use.
10. Abuse: rate limits, replayed links, a request that skips a step.
11. Existing users and data created before this feature.

## Experience

1. List flows as numbered steps from the user's side: where they start, what they do, where they end up.
2. For each screen, give the states it must handle: ideal, empty (first use, user cleared it, no results), loading, error, partial.
3. Describe them in words. Wireframes and visuals belong in the design, linked from the table.

## Out of scope

1. List what a reasonable reader would assume is included and is not, each with a rationale.
2. The rationale says where the item is handled instead: a separate initiative, an existing process that this PRD does not change, a later phase.
3. This section matters most when a coding agent reads the PRD: an agent builds adjacent features unless the document rules them out.

## Dependencies and assumptions

1. A dependency is something another party must deliver: a contracted service, an interface, a test environment, a data pipeline.
2. An assumption is something taken as true: the user has a camera, the review team is staffed for the volume.
3. Each row has an owner who delivers or confirms it.

## Open questions

1. Number them. Each has an owner and the milestone by which the answer is needed (design sign-off, development start, pre-launch).
2. When a question is answered, move the answer into the requirements and record it in the change log.
3. Mark an undecided detail `TBD` where it occurs and repeat it here.

## Non-functional requirements

One row per area, each with a number or a named standard:

1. Performance: latency at a stated percentile, per kind of step.
2. Availability: the target and where it is measured.
3. Degradation: what the user sees when each dependency is down, and which dependency must block instead of proceeding.
4. Capacity: concurrent load and daily peak.
5. Security: encryption, role restrictions, access logging.
6. Retention: what is kept for how long, and what is purged when.
7. Auditability: which decisions must be reconstructible, and from which record.
8. Accessibility: the standard and level, for each platform.
9. Localisation: the languages, and where the user chooses.
10. Compatibility: supported platform and browser versions.
11. Observability: what is on a dashboard and what raises an alert.

Leave out an area that does not apply.

## Rollout plan

1. Phases move from internal users to a small share of real users to everyone, then to retiring the old path.
2. Each phase states its scope (who, which platform, what share) and exit criteria that can be measured.
3. The final phases tie back to the success metrics: targets met for a stated number of consecutive days.
4. State the rollback rule: where traffic returns to, and what happens to work already in flight.
5. Anything that moves money, data, or access needs an off switch. Say who can use it, at what level, and what the user sees meanwhile.

## Glossary

1. Define each term the requirements rely on, once, and use it the same way throughout.
2. A term with two meanings in the organization gets the one this PRD uses.
3. A one-pager with plain vocabulary can skip it.

## Change log

1. Record each change to scope after agreement, with the date and the reason.
2. Removed scope is struck through and dated in place. A section changed after agreement gets "Updated on <date>" in its heading.
3. Update the PRD when scope changes during design or build. A PRD that no longer matches the released feature misleads the next reader.

## For a coding agent

1. Predictable headings and story numbers that do not change let the agent cite them.
2. Out of scope, failure behavior, and constraints must be explicit. An agent cannot ask a colleague in the corridor.
3. Leave out step-by-step implementation plans. They go stale with the first code change; the spec's `tasks.md` contains them.
4. Hand the agent one story or one small group at a time, and not the whole document as one task.

## Sources

- "Sample PRD: Digital Account Opening v1.0", a fictional sample that is free to share, excerpted in `references/example.md`.
- Plane, "How to write a PRD that engineers actually read": https://plane.so/blog/how-to-write-a-prd-that-engineers-actually-read
- MakerKit, "Vibe coding with PRDs: how to keep AI coding agents on track": https://makerkit.dev/blog/vibe-coding/prds-for-ai-coding-agents
