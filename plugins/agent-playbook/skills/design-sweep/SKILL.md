---
name: design-sweep
description: >
  Reviews the design friction log (.agents/friction.md) with fresh context, groups the entries by design
  cause, and proposes redesign options without changing code; after the user approves, files one issue per
  group. Use on /design-sweep, "sweep the friction log", "review .agents/friction.md", "what design problems
  have agents hit", or from a scheduled routine.
---

# Design sweep

Agents add a line to `.agents/friction.md` when a design problem outside their task gets in the way (the Bugs and Design Friction rule in `AGENTS.md`). This skill turns those lines into decisions and does not change code.

## Entry format

```markdown
- 2026-11-14 `shop/receipt.py::format_line` receipt text is built in three copied functions; added the currency to each copy
```

## Steps

1. Open the log at the main checkout's root, the first path in `git worktree list`. If the file is missing or has no entries above `## Swept`, say so and stop.
2. Start from fresh context. In a session that already holds other work, dispatch `agent-playbook:planning-subagent` with the log path and steps 3 to 5; otherwise run them inline.
3. Check each entry against the current code by symbol, with search rather than line numbers. An entry whose path or symbol is gone, or whose problem has been fixed, is stale: list it and leave it out of the groups.
4. Group the rest by design cause: one type, one module boundary, or one rule copied to several places. One entry can be a group.
5. For each group, write the cause in one sentence, the entries, 2 or 3 options with their cost (files and modules touched, risk, migration steps, whether callers change), and a recommendation. Load skill `software-design` for the options when it is installed.
6. Write the report to `.agents/design-sweep-YYYY-MM-DD.md` with bold section headings and numbered lists. Show the user a short summary: each group with its recommendation, and the stale entries.
7. Stop. The user picks which groups become issues.

## Filing issues

1. File only the groups the user named. Creating an issue is an outward action.
2. On a GitHub remote, use `gh issue create --title "<what to change>" --body-file <file>`. In a repo that tracks work in Jira (ticket keys in branch names or commit messages, or the user says so), use the Atlassian MCP `createJiraIssue`.
3. The body has bold section headings with numbered lists: **Problem**, **Evidence** (the entries with their paths), **Options** (with cost), and **Recommendation**. Load the `humanizer` skill in embedded mode before writing it when the skill is installed.
4. Move filed entries under `## Swept` in the log with the date and the issue link, and delete the stale entries.

## Running on a schedule

`/schedule` can run `/design-sweep` weekly for a repo. A scheduled run stops at step 7 and leaves the report for the user; it never files issues on its own.
