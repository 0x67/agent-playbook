---
name: spec-driven
description: Use when writing, revising, or IMPLEMENTING spec artifacts (requirements.md, design.md, tasks.md, validation.md) under `specs/{slug}/` (legacy `plans/{slug}/` and `docs/plans/{slug}/` also recognized), or when the user invokes `/spec`, `/spec-driven`, says "write spec for", "phase N spec", "implement spec", "implement plan", "implement phase N", "requirements for", references `REQ-*` / `TASK-*` / `AC-*` ids, asks during design to "compare approaches", "A/B the options", "spike and benchmark", or run a "trial", or asks to "reconcile" or "resume" a spec. Covers spec writing (turn boundaries, Files-to-Read manifest, EARS REQs with symbol contracts, Source verification, adversarial pass, templates) and implementation (grounding, group order, per-TASK turns and validation, drift checks, regression review, spec-code sync, lat.md sync, reconcile). Skip for typo fixes, one-line edits, doc-only changes, single-test additions, or tasks whose requirements already sit complete in one document.
---

# Spec-Driven Workflow

Use it when scope is unclear or the work spans sessions. On a small task and on a three-module task that each came with a complete README, writing the spec first cost about twice as much for the same hidden-test results (`docs/benchmarks.md`), so implement those directly.

This skill enforces the canonical spec-driven workflow. `<skill-dir>` below is this skill's own directory; Claude Code prints it as the skill's base directory when the skill loads, and relay packets give it as an absolute path. Protocol bodies:

- `<skill-dir>/protocol.md`: **spec writing** (requirements, design, tasks, validation, adversarial pass).
- `<skill-dir>/implement.md`: **implementation** (group dispatch, per-TASK turns, validation gates, regression review, sync rules, final adversarial pass).
- `<skill-dir>/trial.md`: **approach trial**, optional inside spec writing: 2 to 5 candidate approaches spiked against one shared test and benchmark harness, scored on fixed weights, decided with evidence.

## On load

1. **Detect the phase.** Spec writing or implementation?
   - User says "write spec", "phase N spec", "requirements for", or there is no `tasks.md` yet under the slug → **spec writing phase**. Open `protocol.md`.
   - User says "implement spec", "implement phase N", "implement <slug>", or `tasks.md` already exists and is finalized → **implementation phase**. Open `implement.md`.
   - The user asks to "reconcile" or "resume <slug>", or a new session picks up a spec that already has `DONE` tasks → **implementation phase**, starting with the Reconcile section of `implement.md`.
   - Ambiguous → ask.

2. **Open the chosen protocol first.** Source of truth; this skill file is only the binding.

3. **Identify the spec slug.** Stable kebab-case, unique per task. If unclear, ask.

4. **Honor turn boundaries.**
   - Spec writing: one artifact per turn.
   - Implementation: one TASK per turn. Follow `tasks.md` Parallelizable groups α → β → γ → ... in order.

## Quick-reference rules

- One artifact per turn.
- Files-to-Read manifest before any Write.
- Re-Read inputs at the start of each artifact turn.
- EARS form for every REQ; stable `REQ-*` ids; per-REQ symbol contract.
- `design.md` ends with a Source verification block.
- Approach trial only when 2 to 5 approaches stay viable and the choice justifies spikes, or the user asks (`trial.md`).
- Meta-talk uses `[meta]` prefix; never bare "turn N" in spec output.
- Copy templates from `<skill-dir>/_template/<artifact>.md`; do not restructure.
- Traceability: user ask → REQ-* → TASK-* → code → validation.
- `tasks.md` records its `Base commit`; every TASK has a `Status` (TODO, DONE, BLOCKED, RETIRED) and starts with a drift check against that base.
- Rejected review findings live in `decision-log.md` under `## Rejected findings` and are not re-raised without new evidence.

## Templates

Located at `<skill-dir>/_template/`:

- `requirements.md`
- `design.md`
- `tasks.md`
- `validation.md`
- `trial.md` (only when an approach trial runs)

Use `cp <skill-dir>/_template/<artifact>.md <plan-folder>/<artifact>.md` to initialize.

## Subagent dispatch

When dispatching subagents, use the relay packet shape in `<skill-dir>/prompts/relay.md`. One subagent per artifact, fresh context each time.

## Vendor-portable variant

For tools that do not auto-load this skill (Copilot CLI BYOK, Cursor, plain SDK callers), see `<skill-dir>/prompts/system-portable.md`. Paste as the system prompt.

## When NOT to load

Do not load this skill for: typo fixes, one-line edits, doc-only changes, mechanical renames, single-test additions, formatting passes, dependency bumps, or anything without an architectural decision.
