---
name: orchestration-layers
description: Dispatch ladder and rules for multi-agent work - fable discipline, inline vs subagents vs Workflow(), composition, parallel fan-out with a warm prompt cache, subagent naming, model tiers, and model disclosure. Load before spawning subagents, fanning out in parallel, or authoring a Workflow.
---

# Orchestration layers (fable / subagents / Workflow)

fable-method and fable-judge are the discipline layer: they wrap every non-trivial task,
whatever runs it. Subagents dispatched from the main thread and dynamic Workflow() are the
dispatch mechanisms; pick one by the shape of the work. They nest, they do not compete.

## Discipline layer (always, mechanism-agnostic)

- Before any non-trivial multi-step task, apply the fable-method loop (classify -> define
  done -> evidence -> decide -> act -> prove). It runs BEFORE picking a dispatch mechanism.
- After completing substantive work, or whenever any agent or tool claims work is done, run
  a fable-judge pass before presenting it as finished. "Did that actually work?" = fable-judge.
  Universal exit gate for every mechanism below.
- fable skills missing (another agent, or the plugin removed): the inline loop in AGENTS.md
  replaces fable-method and fable-judge.

## Dispatch mechanism: cost-gated ladder

Escalate only when the cheaper tier can't hold the work. Minimal mechanism that fits.

1. Inline (main thread): trivial, single-file, one-shot, lookup.
2. Subagents from the main thread (Agent tool): when inline overflows and the shape is only
   discoverable by doing. The main thread orchestrates: it dispatches planning,
   implement, and review subagents one unit at a time, with a relay packet per unit, and
   verifies between dispatches.
3. Dynamic Workflow(): when the shape is known before dispatch and the fan-out is large
   (list fan-out, N-file migrate, multi-dimension review), and the user opted in.
   Deterministic control flow in JS, resumable, reproducible.

Tie-break when inline overflows: shape unknown -> subagents; shape known and opted in -> Workflow.

## Workflow() opt-in: strict, explicit-only

Dynamic Workflow() fires ONLY on explicit opt-in: the `ultracode` keyword, an explicit
"use a workflow" / "orchestrate this with subagents" ask, or a skill that calls it. Main
thread never reaches for Workflow() unprompted, even on an obvious big fan-out; offer it
and let the user opt in. Matches the Workflow tool's own built-in gate. Keeps token spend
predictable: a single Workflow can spawn dozens of agents.

## Composition (nest, do not compete)

- The main thread MAY hand a list it discovered to Workflow() for deterministic fan-out.
  Pattern: scout with subagents -> pipeline over the result.
- Workflow verify-stages ARE the fable-judge pattern (adversarial refute agents per
  finding). Bake fable-judge into the script's final stage.
- Relay packets AND Workflow agent prompts both carry the standing protocols: memory
  recall, comment rules (no REQ-*/TASK-*/em-dash), Code Simplicity Discipline (smallest
  change, no unrequested backwards-compat, no slop), search order.

## Parallel fan-out

Applies to every group of agents or runs started together: Agent tool calls from the main
thread or from a subagent, Workflow `parallel()` and `pipeline()` stages, headless
`claude -p` batches, and `claude plugin eval --concurrency`.

**What can run in parallel**

1. Only independent units: no shared files or functions, no shared schema or generated
   artifact, no dependency on another unit's interface. Compare each unit's files in scope
   before dispatch; anything shared runs serially.
2. Two to four at a time. More means merge and review noise.
3. Do not launch background work whose output you cannot retrieve. Use synchronous
   subagents or work directly.
4. After the group returns, reconcile each report against the changed files and the
   validation output, not against the summary alone.

**Warm the prompt cache first**

A prompt cache entry becomes available only after the first response that writes it starts
(Anthropic prompt caching docs). Agents launched in the same instant each write the whole
shared prefix (system prompt, tools, injected rules: about 42k tokens in a fresh Claude Code
session) at 1.25x or 2x the input price, instead of reading it at 0.1x or less.

1. Agent tool, main thread or orchestrating subagent: send one Agent call in its own message,
   then the rest of the group together in the next message.
2. Workflow: `await` one `agent()` before the `parallel()` or `pipeline()` stage that fans out
   the rest. In a pipeline, push the first item through alone, then the remainder.
3. Headless runs and evals: start one run, wait for its first output, then start the others.
   In an A/B comparison, warm each arm and give both arms the same concurrency.
4. Same agent type and model across the group, shared instructions first and per-agent details
   last, so every prompt shares the longest possible prefix.

## Subagent naming

This plugin's subagent types carry the plugin prefix: `ai-setup:planning-subagent`,
`ai-setup:implement-subagent`, `ai-setup:code-review-subagent`. Spawn those exact names. An
unmatched `subagent_type` silently falls back to `general-purpose` / `claude`, which is the
"wrong agent" failure.

## Model tier per handoff

Pick the tier by the work, not by habit. Pass it explicitly (`model:` on the Agent tool,
`opts.model` on Workflow `agent()`); each agent file's `model:` field is only its default.

| Work handed off | Tier | Default agent |
|---|---|---|
| Locate code, list files, one-file mechanical edit | `haiku` | Explore, quick lookups |
| Read-only research with a clear question | `sonnet` | `ai-setup:planning-subagent` |
| Implementation from a written spec or task | `opus` | `ai-setup:implement-subagent` |
| Review, adversarial verification, security-sensitive change | `opus` | `ai-setup:code-review-subagent` |
| Orchestration across work units | session model | the main thread |
| Hardest reasoning, only when the user asks for it | `fable` | any |

Move up one tier when a subagent returns FAILED twice on the same unit, or the unit changes an
interface other units depend on. Move down when the brief is a lookup.

## Model disclosure

Every subagent spawn discloses its model in user-visible output at dispatch: Agent tool,
Workflow `agent()`, every `parallel()` / `pipeline()` stage. One line per agent:
`<label> -> <alias> <version>`, adding `(inherited)` when it runs on the session model. The
version is what the alias resolves to now: an `ANTHROPIC_DEFAULT_<TIER>_MODEL` pin if one is
set, otherwise the latest model of that tier in the session's model list. Never write a version
from memory; if neither source gives one, write `(version unknown)`. No full model ID. No silent
spawns.
