---
name: orchestration-layers
description: Dispatch ladder and rules for multi-agent work - fable discipline, inline vs Workflow() vs Conductor, composition, precedence, subagent naming and model disclosure, Fleet parallel scheduling with SQL todos. Load before spawning subagents for fan-out, running as Conductor or /fleet, or authoring a Workflow.
---

# Orchestration layers (fable / Conductor / Workflow)

Three tools, two layers. fable-* is the discipline layer (mechanism-agnostic, wraps
every non-trivial task); Conductor and dynamic Workflow() are in-session dispatch
mechanisms (pick one by scope shape). fable wraps whichever mechanism runs. Do not
treat as competitors; they nest.

## Discipline layer (always, mechanism-agnostic)

- Before any non-trivial multi-step task, apply the fable-method loop (classify ->
  define done -> evidence -> decide -> act -> prove). Runs BEFORE picking a dispatch
  mechanism. For tasks that run unattended or fan out subagents, use fable-loop.
- After completing substantive work, or whenever any agent/tool claims work is done,
  run a fable-judge pass before presenting it as finished. "Did that actually work?"
  = fable-judge. Universal exit gate for all mechanisms below.
- fable skills missing (another agent, or the plugin removed): the inline loop in
  AGENTS.md replaces fable-method and fable-judge. fable-loop has no inline twin;
  use Conductor for unattended fan-out.

## Dispatch mechanism: cost-gated ladder

Escalate only when the cheaper tier can't hold the work. Minimal mechanism that fits.

1. Inline (main thread): trivial, single-file, one-shot, lookup.
2. Dynamic Workflow(): when inline overflows AND the shape is known before dispatch
   (list fan-out, N-file migrate, multi-dimension review). Deterministic control flow
   in JS, resumable, reproducible.
3. Conductor subagents: when shape is only discoverable by doing, scope must be
   negotiated mid-flight, or SQL todos coordinate multiple work-units. Model-driven
   control flow, relay packet per artifact.

Tie-break when inline overflows: shape known -> Workflow; shape unknown -> Conductor.

## Workflow() opt-in: strict, explicit-only

Dynamic Workflow() fires ONLY on explicit opt-in: the `ultracode` keyword, an explicit
"use a workflow" / "orchestrate this with subagents" ask, or a skill that calls it.
Main thread never reaches for Workflow() unprompted, even on an obvious big fan-out;
offer it and let the user opt in. Matches the Workflow tool's own built-in gate. Keeps
token spend predictable: a single Workflow can spawn dozens of agents.

## Composition (nest, do not compete)

- Conductor MAY dispatch Workflow() for a deterministic sub-step: Conductor discovers
  the work-list adaptively, hands the known list to Workflow for deterministic fan-out.
  Pattern: scout inline -> pipeline over the result.
- Workflow verify-stages ARE the fable-judge pattern (adversarial refute agents per
  finding). Bake fable-judge into the script's final stage.
- Conductor relay packets AND Workflow agent prompts must both carry the standing
  protocols: memory recall, comment rules (no REQ-*/TASK-*/em-dash), Code Simplicity
  Discipline (smallest change, no unrequested backwards-compat, no slop), search order.

## Precedence when two fit: split by trigger

- fable-loop vs Conductor: fable-loop is outer for one-shot unattended runs
  (self-contained). Conductor is outer when scope negotiates with the user mid-flight
  or SQL todos coordinate multiple work-units. Never both outer; pick the outer, the
  other's fan-out+verify patterns fold in as sub-steps.
- Conductor vs Workflow: Workflow when the shape is known before dispatch; Conductor
  when the shape is only discoverable by doing. Hybrid: Conductor scouts, Workflow executes.

## Subagent naming

This plugin's subagent types carry the plugin prefix: `ai-setup:conductor`,
`ai-setup:planning-subagent`, `ai-setup:implement-subagent`, `ai-setup:code-review-subagent`.
Spawn those exact names. An unmatched `subagent_type` silently falls back to
`general-purpose` / `claude`, which is the "wrong agent" failure.

## Model tier per handoff

Pick the tier by the work, not by habit. Pass it explicitly (`model:` on the Agent tool,
`opts.model` on Workflow `agent()`); each agent file's `model:` field is only its default.

| Work handed off | Tier | Default agent |
|---|---|---|
| Locate code, list files, one-file mechanical edit | `haiku` | Explore, quick lookups |
| Read-only research with a clear question | `sonnet` | `ai-setup:planning-subagent` |
| Implementation from a written spec or task | `opus` | `ai-setup:implement-subagent` |
| Review, adversarial verification, security-sensitive change | `opus` | `ai-setup:code-review-subagent` |
| Orchestration across work units | session model | `ai-setup:conductor` |
| Hardest reasoning, only when the user asks for it | `fable` | any |

Move up one tier when a subagent returns FAILED twice on the same unit, or the unit changes an
interface other units depend on. Move down when the brief is a lookup.

## Model disclosure

Every subagent spawn discloses its model in user-visible output at dispatch: Agent tool,
Workflow `agent()`, Conductor delegation, every `parallel()` / `pipeline()` stage. One line per
agent: `<label> -> <alias> <version>`, adding `(inherited)` when it runs on the session model.
The version is what the alias resolves to now: an `ANTHROPIC_DEFAULT_<TIER>_MODEL` pin if one is
set, otherwise the latest model of that tier in the session's model list. Never write a version
from memory; if neither source gives one, write `(version unknown)`. No full model ID. No silent
spawns.

# Fleet Parallel Scheduling

Use when running as Conductor or `/fleet` with SQL todos:

- Query ready todos by dependency, not by list order.
- Dispatch multiple ready todos only when independent.
- Before dispatch, compare `Files/Functions in scope`, schemas, generated artifacts, public interface dependencies.
- Do not parallelize tasks that share files/functions, modify same schema/generated artifact, or depend on another task's interface.
- Prefer 2-4 parallel jobs. Too many = merge/review noise.
- If no result retrieval tool exists, do not launch background jobs whose output is needed. Use sync subagents or direct work.
- Parent owns SQL todo updates unless subagent proves it can update same todo database.
- After jobs return, trust SQL status as source of truth, then reconcile subagent summaries against changed files and validation.
- If deps missing or too coarse, add or refine `todo_deps` before dispatch.
- Every work-unit report must include parallel status:
  - `Parallel Group`: group id/name or `none`
  - `Parallel With`: sibling todo ids/titles or `none`
  - `Dependencies`: blocking or satisfied todo ids
  - `Serial Reason`: why not parallelized, when applicable
- Subagent return format must include same parallel status fields. Parent echoes them in user-facing work-unit summaries.
