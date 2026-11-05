# Spec-Driven Implementation Protocol

Companion to `protocol.md`. Covers the implementation phase that follows spec finalization. Vendor-neutral.

## When to use

A finalized spec exists at `specs/<slug>/` (requirements + design + tasks + validation, adversarial pass clean, AC-Z marked).

If the spec is not yet finalized, use `protocol.md` instead.

## Grounding (mandatory, do not skip)

Before the first code change:

1. Open `<skill-dir>/protocol.md` for context.
2. Open `specs/<slug>/{requirements,design,tasks,validation}.md`.
3. Open every `path:line` listed in `design.md` "## Source verification" block.
4. Quote 3-5 signatures back to the user. Proves grounding.
5. Memory recall: call `agentmemory/memory_recall` with concepts `[spec, <slug>, <key topic words>]`. If empty, use `memory_smart_search`.

## Search tool order (MANDATORY)

For any code/symbol/file search beyond opening files explicitly named in the spec, use this order. Falling back without stating the reason = work rejected.

1. **fff MCP** for exact text and file search: `mcp__fff__grep`, `mcp__fff__find_files`, `mcp__fff__multi_grep`. Always first choice.
2. **semble MCP** (`mcp__semble__search`) for semantic code search when intent is fuzzier than a literal grep.
3. **`codebase-memory` MCP** graph tools for callers, callees, routes, and types when it is connected.
4. **`LSP` tool** for definitions, references, hover, and diagnostics where a language server is connected (rust-analyzer, gopls, clangd, jdtls, kotlin-lsp).
5. **`lat locate`** / **`lat expand`** for architecture context if `lat.md/` exists in the workspace. Never `lat search`.
6. **Built-in `Read`** is allowed only for files whose paths are already known (from spec, from earlier search results, from `path:line` in Source verification).
7. **Shell `rg` / `find`** is the LAST fallback, used only when 1-4 are unavailable, fail, or genuinely lack the capability. State the fallback reason in the response.

Never invoke shell `fff`. The MCP tool names above are the project contract.

## Locating code: symbols not lines

Spec contracts (REQ Files, TASK Files, design interface specs) reference **symbols**, never line numbers. Line numbers in the spec are snapshots from spec authoring time and drift the moment the first TASK edits a file.

Rules:

1. **Open files by symbol.** Use `mcp__fff__grep "fn apply"` or `LSP` `goToDefinition`, not `Read path:LINE`. The `path:line` refs you see in `design.md` Source verification block are evidence of grounding at spec time, not navigation pointers.
2. **Do not trust line numbers in spec mid-implementation.** TASK-N's edits shift TASK-N+1's line refs. Re-locate each TASK's symbols when its turn begins.
3. **Source verification block staleness is acceptable.** Post-implementation, the line refs in design.md will be stale. That is by design; do not "sync" them. The block is read-only history of what was true when the spec was authored.
4. **Renames require an `Implementation correction` amendment.** If a TASK needs to rename a symbol referenced by REQ Files / TASK Files / design interface specs:
   - Update spec references to the new symbol in the SAME staged diff as the rename.
   - Add an `Implementation correction` paragraph (in `design.md` or `decision-log.md`) noting the rename and the reason.
   - Silent rename without spec update = work rejected.
5. **Per-TASK re-grounding uses symbol lookup.** When re-reading the TASK's Files block, search for each named symbol fresh. Do not assume line refs from an earlier TASK still hold.

If a referenced symbol cannot be found by search, that is a spec error (the symbol was renamed/removed in an earlier TASK without amendment). Stop and ask the operator before proceeding.

## Dispatch order

Follow `tasks.md` "Parallelizable groups" section verbatim:

- Group α → β → γ → δ → ε → ζ → η → θ (or whatever the spec uses).
- Single-implementer flow: do NOT parallelize unless the orchestrator explicitly dispatches; parallel groups then follow the Parallel fan-out rules in skill `orchestration-layers`, warm prompt cache included.
- Group order is binding. Skipping ahead breaks the dep graph and causes rework.

## Per-TASK rules

One TASK per response. Each TASK turn:

1. Drift check: `git log --oneline <Base commit>..HEAD -- <TASK files>`. Commits other than this spec's earlier TASKs mean the files changed after the spec was written: re-verify the TASK's symbols against the code (Source verification in `protocol.md`) before editing, and say so in the report.
2. Re-Read the files in the TASK's `Files` block.
3. Re-Read the linked REQ entries in `requirements.md`.
4. Apply edits.
5. Run the exact `Validation` commands from the TASK.
6. On failure: fix and re-run. Do not move on with a failing validation. If something outside the TASK blocks it, set its `Status` to `BLOCKED (<reason>)` and stop.
7. Set the TASK's `Status` to `DONE` in `tasks.md`.
8. Report: name the TASK, list files changed, paste validation output.
   **Do NOT commit.** Operator commits manually after reviewing the
   diff.

When the operator later asks to commit, use this format (one commit per
TASK, no amending across TASKs):

```
<conventional-commit-subject ≤50 chars>

Implements TASK-<id> from <slug>.

<optional body explaining non-obvious choices>
```

Examples:

```
feat(engine): apply by-value, remove redundant clone

Implements TASK-B2 from phase-4.9-replay-perf-venue-config.
```

```
fix(bootstrap): retry RingFull with returned event

Implements TASK-B3 from phase-4.9-replay-perf-venue-config.
```

## Comment hygiene (HARD GATE)

Source code comments must stand alone post-merge. Git log + PR
description carry process context. Comments do not.

**Banned in any code comment** (`//`, `///`, `//!`, `#`, `"""`,
JSDoc, runtime log strings, panic messages, doc strings, test names):

- `REQ-<digits>`, `TASK-<id>`, `AC-<id>`
- `phase <N>`, `Phase <N>`, `milestone <N>`
- "see TASK-…", "per design.md §…", "from requirements.md"
- "as decided in step …", "TODO from plan …"
- Any reference to a `specs/<slug>/` artifact by name or section

These belong in commit messages and PR descriptions, NEVER in code.

**Per-TASK validation gate (mandatory)**: before declaring a TASK
complete, run:

```bash
rg -n '\b(REQ|TASK|AC)-[A-Za-z0-9]+|\b[Pp]hase\s+[0-9]+(\.[0-9]+)?|milestone\s+[0-9]+' \
   <changed files>
```

Output MUST be empty. Any hit blocks the TASK. Fix the comment, re-run,
then move on.

**Cross-crate/module pointers OK** when the behavior depends on
specific code elsewhere:

```rust
// drain at sink pace, not source pace
// see pipeline-sinks::dispatcher for backpressure
// mirrors soupbintcp_replay::Reader
// SAFETY: caller holds slot lock
```

These reference code by stable identifier, not by spec process state.

**Bad examples** (would be caught by the gate):

```rust
/// Implementors: [`idx::IdxVenueLoader`] (see TASK-D2).
// TODO from the unified-pipeline-events plan
// See REQ-P0-005 for timestamp policy
// In milestone 4 we decided this should drain at the sink's pace
// Added in phase 4.9 per design.md §3.3
```

**Fixed versions**:

```rust
/// Implementors: [`idx::IdxVenueLoader`].
// TODO: handle backpressure once dispatcher emits ready signal
// timestamp policy: nanos since session midnight, see SessionContext
// drain at the sink's pace, not source pace
// (no comment needed: code self-explanatory after rename)
```

## Per-GROUP review

After every group α/β/γ/... completes:

1. Run the validation.md Regression guard end-to-end.
2. Banned terms check on changed files:
   ```
   rg "semantic|facade|golden|canonical|canonincal" <changed files>
   ```
   Document any matches as exceptions (third-party / domain quotes) or
   rename.
3. Code comments follow the Code Comments rules in AGENTS.md: no spec ids,
   no marketing prose, no em dashes, short.
4. Verify every spec-referenced symbol still resolves in the codebase
   after changes (`grep` / `rust-analyzer`).
5. If workspace uses lat.md: run `lat check`. Must exit 0.

If any check fails, fix before next group.

Review findings that get rejected (by design, false positive, out of scope) go into `decision-log.md` under `## Rejected findings`, one line each: the finding, its `path::Symbol`, the reason, and the evidence. Every later review gets that section as prior context and does not re-raise a listed finding unless it cites new evidence.

## Spec ↔ code sync

Spec is intent. Code follows spec. Two rules:

1. **Implementation reveals a spec error or omission.** AMEND the spec
   with a paragraph titled "Implementation correction" explaining
   what was wrong and why the change was needed. Same commit as the
   code change. Reviewer can see the rationale.

2. **Code diverges from spec without amendment.** That is a bug.
   Fix the code, not the spec. Silent sync is forbidden.

## lat.md sync

If workspace contains `lat.md/`:

- Add / change / remove behavior or architecture → update relevant
  lat.md section in the same commit.
- Pure refactor (no behavior or API change) → skip lat.md update.
- Run `lat check` at the end of every group.

If workspace lacks `lat.md/`: skip all lat.md steps.

## Commits

- **Do NOT auto-commit.** Operator commits manually after reviewing
  each TASK's diff. Implementer's job ends at "files staged + diff
  ready for review".
- When the operator explicitly asks for a commit:
  - Pre-commit hooks must run. Never pass `--no-verify`. If a hook
    fails, fix the underlying issue and create a NEW commit. Do not
    amend across hook failures.
  - One commit per TASK. Do not bundle multiple TASKs into one
    commit.
  - Use HEREDOC for multi-line commit bodies (see CLAUDE.md commit
    format).
- Do not push without explicit operator approval (separate from commit
  approval).

## Final step: adversarial pass

After all groups complete, run the spec-driven adversarial review
(same procedure as `prompts/relay.md` step 6):

1. Enumerate every external symbol (functions, types, paths) the spec
   references.
2. For each, verify it exists in the current codebase.
3. Report mismatches.
4. AC-Z in `validation.md` must pass.

If clean, declare the implementation phase complete and produce a
summary listing commits per TASK.

## Reconcile (resuming a spec)

Run this when work on a spec resumes in a new session, or when the user asks to reconcile or resume a spec. It brings `tasks.md` back in line with the code before any new TASK starts.

1. **DONE tasks:** re-run each one's `Validation` commands. A failure sets the TASK back to `TODO` with a one-line reconcile note.
2. **BLOCKED tasks:** re-check the recorded reason. Set the TASK to `TODO` when the reason no longer holds; otherwise keep it and ask the operator.
3. **TODO tasks:** run the drift check against `Base commit`. For files that changed, re-verify the TASK's symbols and amend its Scope with a reconcile note.
4. **Dead tasks and findings:** a TASK or rejected finding whose premise no longer holds (code removed, requirement dropped) becomes `RETIRED (<reason>)`, with an entry in `decision-log.md`.
5. **Report** a table of task, old status, new status, and evidence, then continue with the first `TODO` in group order.

## When stuck

- Cannot decide between two implementations → write both into
  `specs/<slug>/decision-log.md` and ask. Do not guess.
- Cannot find a symbol → grep / rust-analyzer / language-server-backed
  lookup before guessing. Symbol names from spec are starting points,
  not ground truth.
- Validation command in `tasks.md` is wrong → AMEND `tasks.md` with a
  one-line correction note explaining why. Do not silently change.
- Spec contradicts itself across artifacts → STOP. Ask the operator
  before continuing. Implementation cannot proceed on contradictory
  intent.

## Anti-patterns

- Multiple TASKs in one commit.
- Re-raising a rejected finding without new evidence.
- `--no-verify` to bypass pre-commit failures.
- Silent spec-to-code sync without "Implementation correction" note.
- Skipping the per-group review because "the next group is small".
- Spec-id references in source comments.
- Adversarial pass skipped because "everything compiled".
