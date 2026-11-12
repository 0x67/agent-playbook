---
name: orchestration-layers
description: Dispatch ladder and rules for multi-agent work - the verify-before-done loop, inline vs subagents vs Workflow(), composition, parallel fan-out with a warm prompt cache, subagent naming, model tiers, and model disclosure. Load before spawning subagents, running agents in parallel, or authoring a Workflow.
---

# Orchestration layers (discipline / subagents / Workflow)

The loop in `AGENTS.md` is the discipline layer: it wraps every non-trivial task,
whatever runs it. Subagents dispatched from the main thread and Workflow() are the
dispatch mechanisms; pick one by the kind of work, and nest them when the work needs more than one.

## Discipline layer (always, mechanism-agnostic)

- Before any non-trivial multi-step task: classify the ask, define done and how to check it,
  read the evidence, then pick a dispatch mechanism.
- After substantive work, or whenever an agent or tool claims work is done, check every claim
  against the diff and the command output before presenting it as finished. This is the exit
  gate for every mechanism below.

## Dispatch mechanism: cost-gated ladder

Escalate only when the cheaper tier can't hold the work. Minimal mechanism that fits.

1. Inline (main thread): trivial, single-file, one-shot, lookup.
2. Subagents from the main thread (Agent tool): when inline overflows and the structure of the work is only
   discoverable by doing, and only for independent, read-heavy units. A few related questions
   in one prompt stay inline: one subagent per question cost about twice as much with no steady
   gain (`docs/benchmarks.md`). The main thread dispatches planning and
   implement subagents one unit at a time, with a relay packet per unit, runs `/code-review`
   on the result, and verifies between dispatches.
3. Dynamic Workflow(): when the structure is known before dispatch and the fan-out is large
   (list fan-out, N-file migrate, multi-dimension review), and the user opted in.
   Deterministic control flow in JS, resumable, reproducible.

Tie-break when inline overflows: shape unknown -> subagents; shape known and opted in -> Workflow.

## Workflow() opt-in: strict, explicit-only

Dynamic Workflow() fires ONLY on explicit opt-in: the `ultracode` keyword, an explicit
"use a workflow" / "orchestrate this with subagents" ask, or a skill that calls it. Main
thread never reaches for Workflow() unprompted, even on an obvious big fan-out; offer it
and let the user opt in. Matches the Workflow tool's own built-in gate. Keeps token spend
predictable: one Workflow can spawn dozens of agents.

## Composition (nest, do not compete)

- The main thread MAY hand a list it discovered to Workflow() for deterministic fan-out.
  Pattern: scout with subagents -> pipeline over the result.
- Workflow verify stages are the exit gate: adversarial refute agents per finding in the
  script's final stage.
- Relay packets AND Workflow agent prompts both include the standing protocols: memory
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
session) at 1.25x or 2x the input price. A read is 0.1x or less.

1. Agent tool, main thread or orchestrating subagent: send one Agent call in its own message,
   then the rest of the group together in the next message.
2. Workflow: `await` one `agent()` before the `parallel()` or `pipeline()` stage that starts
   the rest. In a pipeline, push the first item through alone, then the remainder.
3. Headless runs and evals: start one run, wait for its first output, then start the others.
   In an A/B comparison, warm each arm and give both arms the same concurrency.
4. Same agent type and model across the group, shared instructions first and per-agent details
   last. Every prompt then shares the longest possible prefix.

## Subagent naming

This plugin's subagent types use the plugin prefix: `agent-playbook:planning-subagent` and
`agent-playbook:implement-subagent`. Spawn those exact names. An
unmatched `subagent_type` silently falls back to `general-purpose` / `claude`, which is the
"wrong agent" failure.

## Model tier per handoff

Pick the tier by the work, not by habit. Pass it explicitly on every spawn (`model:` on the
Agent tool, `opts.model` on every Workflow `agent()`). A spawn without one falls back to the agent
file's `model:`, then to `CLAUDE_CODE_SUBAGENT_MODEL`, then to the session model, which may be Opus
or Fable. Set `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` in settings so that fallback is cheap.

| Work handed off | Tier | Default agent |
|---|---|---|
| Locate code, list files, one-file mechanical edit, preflight checks, a gate that runs commands and reports | `haiku` | Explore, quick lookups |
| Read-only research with a clear question | `sonnet` | `agent-playbook:planning-subagent` |
| Implementation from a written spec or task, fix from confirmed findings | `sonnet` | `agent-playbook:implement-subagent` |
| Review of one slice or lens of a diff, verification of one finding | `sonnet` | `general-purpose` with an explicit brief |
| Code review of a diff | the skill's own | built-in `code-review` skill (`/code-review <level>`) |
| Final adversarial pass over the merged diff, security-sensitive change | `opus` | `general-purpose` with an explicit brief |
| Orchestration across work units | session model | the main thread |
| Hardest reasoning, only when the user asks for it | `fable` | any |

Raise a unit to `opus` when it changes an interface other units depend on, touches money,
concurrency, auth, or a data migration, or returned FAILED twice on `sonnet`. Reviewers of a diff
that touches money, auth, or security also run on `opus`; their verifiers stay on `sonnet`. Move
down when the brief is a lookup.

## Model disclosure

Every subagent spawn discloses its model in user-visible output at dispatch: Agent tool,
Workflow `agent()`, every `parallel()` / `pipeline()` stage. One line per agent:
`<label> -> <alias> <version>`, adding `(inherited)` when it runs on the session model. For the
version, use an `ANTHROPIC_DEFAULT_<TIER>_MODEL` pin if one is
set, otherwise the latest model of that tier in the session's model list. Never write a version
from memory; if neither source gives one, write `(version unknown)`. Do not write a full model ID or spawn
silently.
