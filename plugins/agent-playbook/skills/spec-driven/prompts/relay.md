# Relay: Spec-Driven Dispatch

When the orchestrator (the main thread, or a subagent that dispatches others) sends subagents spec work, the handoff packet must conform to this shape. Pass it verbatim into the subagent prompt.

## Relay packet fields

```
spec_slug:          <kebab-case-slug>
current_artifact:   manifest | requirements | design | trial | tasks | validation | adversarial
protocol_path:      <skill-dir>/protocol.md
template_path:      <skill-dir>/_template/<artifact>.md
prior_artifacts:    [<absolute paths to completed artifacts in this spec>]
files_in_scope:     [<absolute paths the subagent must Read first>]
reqs_in_scope:      [REQ-A1, REQ-A2, ...]
vocabulary_guard:   "REQ-*/TASK-*/AC-*/phase N = artifact ids; meta-talk uses [meta] prefix"
validation_command: <exact shell command that will verify the work>
edge_cases:         [<list of failure modes the subagent must protect>]
off_limits_files:   [<paths the subagent must NOT touch>]
code_rules:         "comment rules (no REQ-*/TASK-*/AC-*/phase/em dash); Code Growth Discipline; Useless Test Ban; Code Simplicity Discipline (smallest change, no speculative abstraction, no unrequested backwards-compat shims, no slop)"
```

## Dispatch order

One subagent per artifact, fresh context each time. The orchestrator verifies between dispatches.

| Step | Subagent kind                | current_artifact | Pre-conditions                                |
| ---- | ---------------------------- | ---------------- | --------------------------------------------- |
| 1    | planning / explore           | manifest         | task slug exists; user intent captured        |
| 2    | implement / write            | requirements     | manifest accepted                             |
| 3    | implement / write            | design           | requirements.md present + passes review       |
| 3t   | implement / write (optional) | trial            | design.md marks the approach `pending trial`; spikes follow `<skill-dir>/trial.md` |
| 4    | implement / write            | tasks            | design.md present + passes review             |
| 5    | implement / write            | validation       | tasks.md present + passes review              |
| 6    | code-review / adversarial    | adversarial      | all four artifacts present                    |

## Subagent prompt template

```
You are working on spec <spec_slug>. Current artifact: <current_artifact>.

Protocol: read <skill-dir>/protocol.md first.
Template: copy from <skill-dir>/_template/<artifact>.md.

Prior artifacts (read before writing):
  <prior_artifacts list>

Files in scope (read before writing):
  <files_in_scope list>

REQs in scope: <reqs_in_scope>

Vocabulary guard: <vocabulary_guard>

Off-limits files (do NOT touch): <off_limits_files>

Edge cases to protect: <edge_cases>

Code rules (apply when writing any code): <code_rules>

Validation command (must pass before declaring done):
  <validation_command>

Memory recall: call agentmemory/memory_recall with concepts [spec, <spec_slug>]
before starting. Save durable facts at end with memory_save (type=project,
concepts=[spec, <spec_slug>, <current_artifact>]).

Write exactly one artifact (current_artifact). Do not write others.
Do not skip the Source verification block (if current_artifact = design).
Do not paraphrase code; quote it.
```

## Verification gates

Between each dispatch, the orchestrator performs:

1. **File present**: artifact file exists at expected path.
2. **Required sections**: artifact contains its mandatory headings (see templates).
3. **Symbol check**: every `path::Symbol` reference in the new artifact maps to an actual file/symbol in the workspace.
4. **Traceability**: every REQ traces forward; every TASK traces to at least one REQ; every AC traces to at least one REQ.

Failure at any gate → re-dispatch the same subagent with the gate failure as context. Do NOT proceed to the next artifact.

## After all artifacts complete

Final adversarial pass (step 6) reviews the spec against the codebase:

- Enumerate every external symbol referenced in the spec.
- For each, verify existence with grep / rust-analyzer / equivalent.
- Report mismatches.
- If clean, declare spec ready for implementation phase.

## Parallel dispatch caveat

Per the Parallel fan-out rules in skill `orchestration-layers`, spec-writing tasks are inherently
serial (requirements → design → tasks → validation). Parallel opportunity
only exists during the implementation phase derived from tasks.md, not
during spec writing itself. Do not parallelize the dispatch order above.
