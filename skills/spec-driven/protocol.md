# Spec-Driven Workflow Protocol

Canonical workflow body. Vendor-neutral (Claude Code, Copilot CLI, VS Code Copilot, others). Sibling bindings reference this file.

## When to use

- Non-trivial implementation (>1 file, >100 LOC, or cross-crate).
- Architectural decisions worth recording.
- Tasks delegated to subagents.
- Multi-step work spanning multiple sessions.

Skip for: typo fixes, one-line edits, doc-only changes, mechanical renames, single-test additions.

## Artifact layout

Per task slug, isolated folder under `specs/` (or `docs/specs/` if the project uses that path). Legacy alias `plans/` still recognized for older repos.

```
specs/<slug>/
  README.md         overview, motivation, outcomes, non-goals, x-refs
  requirements.md   REQ-* in EARS form with stable ids
  design.md         architecture, interfaces, invariants, error strategy, validation map
  tasks.md          TASK-* with files, outcome, validation, deps; dep graph
  validation.md     ladder, AC table, regression guard
  trial.md          only when an approach trial ran (`<skill-dir>/trial.md`)
  decision-log.md   only if decisions diverge from design or review findings are rejected
  artifacts/        preserved logs and evidence
```

`<slug>` must be stable kebab-case, unique per task. Never share root-level `requirements.md`/`design.md`/`tasks.md`.

## Mandatory pre-spec checklist

Before writing the first artifact, produce a Files-to-Read manifest:

1. List files to open at `path::Symbol` granularity.
2. Open each listed file.
3. Quote 3-5 relevant signatures back in the response.
4. Proceed to artifact write only after manifest is present.

Without this manifest, the model writes from inference, not evidence.

## Search tool order (MANDATORY)

For any code/symbol/file search during manifest-building or artifact authoring, use this order. Falling back without stating the reason = artifact rejected.

1. **fff MCP** for exact text and file search: `mcp__fff__grep`, `mcp__fff__find_files`, `mcp__fff__multi_grep`. Always first choice.
2. **semble MCP** (`mcp__semble__search`) for semantic code search when intent is fuzzier than a literal grep.
3. **`codebase-memory` MCP** graph tools for callers, callees, routes, and types when it is connected.
4. **`LSP` tool** for definitions, references, hover, symbols, and diagnostics where a language server is connected (rust-analyzer, gopls, clangd, jdtls, kotlin-lsp).
5. **`lat locate`** / **`lat expand`** for architecture context if `lat.md/` exists in the workspace. Never `lat search`.
6. **Built-in `Read`** is allowed only for files whose paths are already known (from prior search results, from a Source verification block, from explicit operator instruction).
7. **Shell `rg` / `find`** is the LAST fallback when 1-4 are unavailable, fail, or genuinely lack the capability. State the fallback reason in the response.

Never invoke shell `fff`. The MCP tool names above are the project contract.

## Per-artifact turn boundaries

One artifact per turn. Each turn starts by re-opening its inputs:

| Turn | Reads                              | Writes                  |
| ---- | ---------------------------------- | ----------------------- |
| 1    | code + prior-art                   | Files-to-Read manifest  |
| 2    | manifest + code                    | requirements.md         |
| 3    | requirements.md + code             | design.md               |
| 3t   | requirements.md + design.md + code | trial.md (optional)     |
| 4    | requirements.md + design.md + code | tasks.md                |
| 5    | all prior artifacts                | validation.md           |
| 6    | all artifacts + code               | adversarial review pass |

Stops output-budget drift across artifacts. Re-grounding per turn catches hallucinations early.

Turn 3 loads skill `software-design` (`agent-playbook:software-design` in Claude Code) before writing `design.md`: module boundaries, dependency direction, names for new types and APIs, and the architecture style follow it and the repo's existing structure.

Turn 3t is optional. When 2 to 5 approaches stay viable after reading the code and the choice is worth spikes (a performance budget, a decision costly to reverse, a readability dispute), or the user asks for a comparison, follow `<skill-dir>/trial.md`: frame the candidates, gates, and fixed weights; spike each candidate against one shared harness; measure; record the decision in `trial.md`; then finish `design.md` with the winner. Skip it for everything else.

Turn 4 records `git rev-parse --short HEAD` as `Base commit` in the `tasks.md` header and starts every TASK at `Status: TODO`. Implementation compares against that base to catch files that changed after the spec was written.

## Per-REQ symbol contract

Each REQ must name the `crate::path::Symbol` (or `path/to/file.rs::SymbolOrFn`) it touches. Symbols not present in code fail review. EARS form is mandatory.

```
### REQ-X1: <short title>

**Where** <trigger or condition>,
**the system shall** <observable behavior>,
**so that** <user-visible outcome>.

Files:
- `path/to/file.rs::SymbolOrFn`
- `path/to/other.rs::OtherFn`

Severity: Critical | High | Medium | Low
```

REQ ids are stable across renames. New REQs append; never renumber.

## Symbols vs line numbers (contract rule)

Anything load-bearing references a **symbol**, never a line number.

| Reference kind                              | Stable across edits? | Allowed location                                                              |
| ------------------------------------------- | -------------------- | ----------------------------------------------------------------------------- |
| `crate::module::Symbol`, `path::Symbol`     | Yes (until rename)   | REQ Files, TASK Files, design interface specs, anything normative             |
| `path:LINE`                                 | No (drifts per edit) | Source verification block ONLY: forensic evidence of grounding at spec time  |
| Code snippet quotes                         | No (drifts per edit) | Design illustration only; not a navigation pointer                            |

Implementers locate code by symbol (`mcp__fff__grep`, `LSP` `goToDefinition`, equivalent), never by line. Source verification block staleness post-implementation is acceptable: it is a snapshot, not a contract.

**Renames are the only failure mode.** If a referenced symbol is renamed mid-implementation:

- Update REQ Files / TASK Files / design references to the new symbol in the same commit as the rename.
- Add an `Implementation correction` paragraph (in design.md or `decision-log.md`) noting the rename and why.
- Silent symbol drift (rename without spec update) is forbidden.

## Meta-context tagging

Project vocab collides with process vocab. Tag accordingly:

- `REQ-*`, `TASK-*`, `AC-*`, `phase N`: always artifact ids.
- For conversation/process refs, prefix with `[meta]` or use "iteration"/"round".
- Never use bare "turn N" in spec output (collides with REQ/TASK numbering).

## Source verification checkpoint

`design.md` must end with:

```
## Source verification

- path/to/file.rs:LINE: claim quoted from code
- path/to/other.rs:LINE: claim quoted from code
- ...
```

Forces re-opening files at the end of the artifact. Reviewer scans this section first. Missing or fabricated entries fail review.

## Adversarial pass

After validation.md complete, a separate turn:

> Review your own spec. List every external symbol referenced (functions, types, files, paths). Verify each exists in the codebase. Report mismatches.

Catches fabricated symbol names before integration. Cheap; one turn.

## Memory bridges

After each artifact, save a durable memory entry:

```
type: project
concepts: [spec, <slug>, <artifact-name>]
files: [<paths touched>]
content: 1-line summary + key decisions
```

Enables cross-session continuity. Subsequent sessions load these before starting.

## Validation gates

Don't advance to the next artifact until the prior one passes:

- `design.md` requires `requirements.md` present with at least one REQ.
- `tasks.md` requires `design.md` with interfaces, error matrix, validation map, and a chosen approach (no `pending trial` left; when `trial.md` exists, its Decision section is filled).
- `validation.md` requires `tasks.md` with dep graph and per-task validation.
- Every REQ traces to at least one AC entry.
- Every TASK traces to at least one REQ and one validation step.
- Every behavior change traces: user ask → REQ-* → TASK-* → code → validation.

Reject plans missing this chain.

## Subagent handoff rules

When dispatching subagents, the handoff packet must include:

- task slug
- artifact under work (`current_artifact`)
- linked REQ-* ids
- linked design constraints or invariants
- in-scope and off-limits files
- acceptance criteria
- exact validation command
- edge cases and failure modes to protect
- pointer to this protocol file

If task is small and no files are written under `specs/<slug>/`, include a lightweight spec inline with the same fields.

## Templates

Copy from `<skill-dir>/_template/<artifact>.md` when initializing a new `specs/<slug>/`. Fill blanks; don't restructure.

## Banned shortcuts

- Skipping the Files-to-Read manifest.
- Writing multiple artifacts in a single turn.
- Inferring symbol names from convention rather than reading.
- "TBD" or "see code" in REQ Files lists.
- Long prose where a table would suffice.
- Restructuring templates instead of filling them.
- Closing a workstream without a Source verification block.
