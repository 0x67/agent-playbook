---
name: spec-driven
description: Use when writing, revising, or IMPLEMENTING spec artifacts (requirements.md, design.md, tasks.md, validation.md) under any `specs/<slug>/` folder (legacy `plans/<slug>/` and `docs/plans/<slug>/` also recognized), or when the user invokes `/plan`, `/spec`, `/spec-driven`, says "write spec for", "phase N spec", "implement spec", "implement plan", "implement phase N", "requirements for", or references `REQ-*` / `TASK-*` / `AC-*` ids. Two phases: (1) spec writing — enforces per-artifact turn boundaries, Files-to-Read manifest, EARS-form REQs with per-REQ symbol contracts, Source verification blocks in design.md, adversarial review pass, and template-driven structure; (2) implementation — enforces grounding, group dispatch order, per-TASK turn boundaries, per-task validation gates, per-group regression review, spec↔code sync direction, lat.md sync, and final adversarial pass. Skip for typo fixes, one-line edits, doc-only changes, or single-test additions.
---

# Spec-Driven Workflow

This skill enforces the canonical spec-driven workflow. `<skill-dir>` below is this skill's own directory; Claude Code prints it as the skill's base directory when the skill loads, and relay packets carry it as an absolute path. Two protocol bodies:

- `<skill-dir>/protocol.md`: **spec writing** (requirements, design, tasks, validation, adversarial pass).
- `<skill-dir>/implement.md`: **implementation** (group dispatch, per-TASK turns, validation gates, regression review, sync rules, final adversarial pass).

## When this skill is loaded

1. **Detect the phase.** Spec writing or implementation?
   - User says "write spec", "phase N spec", "requirements for", or there is no `tasks.md` yet under the slug → **spec writing phase**. Open `protocol.md`.
   - User says "implement spec", "implement phase N", "implement <slug>", or `tasks.md` already exists and is finalized → **implementation phase**. Open `implement.md`.
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
- Meta-talk uses `[meta]` prefix; never bare "turn N" in spec output.
- Copy templates from `<skill-dir>/_template/<artifact>.md`; do not restructure.
- Traceability: user ask → REQ-* → TASK-* → code → validation.

## Templates

Located at `<skill-dir>/_template/`:

- `requirements.md`
- `design.md`
- `tasks.md`
- `validation.md`

Use `cp <skill-dir>/_template/<artifact>.md <plan-folder>/<artifact>.md` to initialize.

## Subagent dispatch

When orchestrating subagents (Conductor or otherwise), use the relay packet shape in `<skill-dir>/prompts/conductor-relay.md`. One subagent per artifact, fresh context each time.

## Vendor-portable variant

For tools that do not auto-load this skill (Copilot CLI BYOK, Cursor, plain SDK callers), see `<skill-dir>/prompts/system-portable.md`. Paste as the system prompt.

## When NOT to load

Do not load this skill for: typo fixes, one-line edits, doc-only changes, mechanical renames, single-test additions, formatting passes, dependency bumps, or anything that ships without an architectural decision.
