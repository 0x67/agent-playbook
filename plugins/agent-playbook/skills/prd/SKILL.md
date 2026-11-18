---
name: prd
description: >
  Writes and reviews a product requirements document (PRD): objective, current
  process and metrics, success metrics, numbered user stories with testable
  "shall" requirements, out of scope, dependencies, open questions,
  non-functional requirements, and a phased rollout. Use on
  /prd, "write a PRD", "product requirements", "product brief", "one-pager",
  "feature brief", "define the scope", "what should we build", "review this
  PRD", or when a feature request has no agreed problem, user, or scope yet.
  Sits before the spec-driven skill (a PRD says what and why, a spec says how)
  and beside the ui-ux skill, which designs the flows and screens the PRD
  names. Skip for bug fixes, refactors, and tasks whose scope is already
  written down.
---

# PRD skill

A PRD records what to build, for whom, and why, in enough detail that an engineer, a designer, or a coding agent can start without guessing the scope. It stops before the how: architecture, schemas, and task lists belong to the spec (`spec-driven` skill), and layouts belong to the design (`ui-ux` skill).

## Routing table

Paths are relative to this skill's directory.

| Task | Read |
|---|---|
| writing or revising any section, sizing the document, wording requirements or metrics | `references/sections.md` |
| starting a new PRD | copy `_template/prd.md` |
| the level of detail and wording to aim for | `references/example.md` |

## Where it lives

`specs/<slug>/prd.md`, in the same folder the spec-driven skill uses, so the spec's `requirements.md` can cite it. Follow the repo's own location when it already keeps PRDs somewhere else (`docs/product-requirements-docs/`, a wiki, Confluence, Notion, Jira).

A team that already has a PRD template keeps it: its headings, its requirements table, its ticket column. Use `_template/prd.md` only where no template exists, and apply the rules below to either one. A PRD meant for people outside the repo goes where they read; keep a link to it in the spec folder.

## Before writing

1. Read what exists: the request, linked tickets, user feedback, analytics, the current behavior in code, and any earlier PRD or spec for the same area. List what you read at the top of your reply.
2. Find what the request leaves open. A request that leaves two or more scope-changing decisions open gets one round of at most four questions before the first draft. Ask about the problem, the user, the boundary, and how success is measured, in that order of priority. Skip what the material already answers.
3. With nobody to ask, write the draft anyway, mark each guess as an assumption in the document, and list the guesses in your reply.
4. Pick the size: a one-pager for one feature that one team releases in a sprint or two, the full template for anything that crosses teams or needs a rollout plan (`references/sections.md`).

## Core rules

- Start from the current process, its limitations, and the evidence for them. A PRD that opens with a feature list is a wishlist.
- State the system context: what the current release does in the area, the systems that feed or consume it, data that exists before the release, and other changes in the same release. A PRD for a later release says what it changes from that behavior, and each unknown goes to open questions.
- One PRD per feature. Split when parts could be released separately.
- Current metrics have a value and a source, or say "Not measurable". Each success metric has a baseline, a target with a comparison sign, and a window after launch.
- Out of scope is written down as a table of items with a rationale: the adjacent features a reader would expect, and where each is handled instead.
- Requirements sit under numbered user stories ("As a <role>, I want <capability>, so that <outcome>"). The story number is the id (`PRD-3`) and is not reused.
- Each requirement bullet is one behavior a user or a test can observe, written with "shall". Leave implementation to the spec unless a constraint forces it (a legal rule, an existing API, a platform limit).
- Limits, expiries, and counts have values. Words such as "fast", "simple", and "intuitive" need a number or a named behavior.
- Failure behavior is written beside success behavior: what is rejected, what goes to a person, what is retried, and what must never happen ("It shall not default to pass"). A failure that users or support see has a reason code and a plain-language message.
- Write stories for the roles around the end user too: reviewer, support agent, operations, data analyst, security, and users of assistive technology.
- The Notes column gives the reason for a deliberate choice a reader would question. It does not contain requirements.
- Walk the edge cases for each story (empty data, limits, permissions, a failed dependency, concurrent edits, a user who stops halfway, repeats, abuse) and record each outcome as a bullet or its own story.
- Non-functional requirements are a table by area, each with a number or a named standard.
- The rollout plan has phases with scope and measurable exit criteria, and a rollback rule.
- Open questions have a number, an owner, and the milestone by which the answer is needed. A decision made later moves into the requirements, and the change log records it.
- Define the terms the requirements rely on in a glossary and use each one the same way throughout.
- A rule with numbers (pricing, fees, limits, rounding) gets its formula and one worked example with real figures.
- User-facing messages that the requirement depends on are written out in full, with their placeholders: `Insufficient balance. You can sell up to {remaining_amount}`.
- A value that the business will change later (a limit, a margin, a window of days) is marked configurable in the requirement.
- Undecided details are marked `TBD` in place and repeated in open questions, so a reader of one section sees the gap.
- Scope removed after review is struck through and dated, and the change log says why. Sections changed after agreement get an "Updated on <date>" note in the heading.
- Never invent evidence. A missing number becomes a marked placeholder such as `[BASELINE: weekly exports per user]`, and the reply lists every placeholder.
- The document points to detail kept elsewhere (research, designs, dashboards) and does not copy it.

## Working with the ui-ux skill

A PRD for anything with an interface has an Experience section: the flows in order, the screens each flow touches, and the states each screen must handle. The `ui-ux` skill takes that list as its screen inventory.

- Write flows and states in words. Do not draw layouts or pick colors in the PRD.
- When the design exists, link it from the Experience section (the canvas, the Figma file, or the design system) and give the artboard or page for each flow.
- When design work finds a missing state, a flow the PRD did not name, or a requirement that cannot be met on a small screen, the PRD changes first: add the requirement or the open question, then the design follows.
- A change to scope made in the design and not in the PRD is a review finding.

Design work does not need a PRD. A restyle, a design system, or one screen with a clear brief goes straight to the `ui-ux` skill.

## Handing off to a spec

When the PRD is agreed, the spec-driven skill turns it into `requirements.md`. Each `REQ-*` cites the story (`PRD-*`) it comes from, and a story with no `REQ-*` is either out of scope or a gap to raise. Small features can skip the spec and go from the PRD to code; say which path you took.

## Handing off to test cases

The `test-cases` skill derives cases from the stories: each `shall` bullet gets a positive case, and each failure, limit, and reason code its own. Bullets that cannot be turned into a case are too vague; rewrite them here. State what is at stake when a story fails (money, personal data, a legal duty, a downstream system), so the test cases can rate impact without guessing.

## Review checklist

Flag in a PRD:

- No description of the current process and its limitations, or one that only restates the solution, such as "users need a dashboard".
- No system context, so a reader cannot tell what the product does today or which systems the change touches.
- A success metric with no baseline, target, or window; a current metric with no source.
- No out of scope section, one that lists only things nobody would expect, or items with no rationale.
- A requirement bullet that cannot be tested, or a story with no bullets.
- Requirements placed in the Notes column.
- Stories only for the end user when reviewers, support, or operations also use the feature.
- A failure with no stated behavior, or one the user sees with no reason code or message.
- No non-functional requirements for a feature that handles money or personal data; no rollback rule in the rollout plan.
- Vague quality words without a number.
- Implementation steps, schema, or library choices with no constraint behind them.
- Only the main path described; no edge cases, limits, or failure behavior.
- A calculation with no formula or worked example, or a limit with no statement of whether it is configurable.
- A feature that moves money, data, or access with no way to switch it off described.
- Invented statistics, quotes, or personas with no source.
- An interface feature with no flows or screen states listed.
- Open questions with no owner or milestone, or decisions still sitting in open questions.
- A term used with two meanings.
- Requirements that contradict each other or the non-goals.
- More than one feature in one document.

Report each finding with the section it is in and a concrete rewrite.
