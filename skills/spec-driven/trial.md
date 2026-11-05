# Approach Trial

Optional step inside spec writing. When the design has several viable approaches and reading the code cannot settle the choice, build 2 to 5 of them as throwaway spikes, run every spike against the same tests and benchmarks, and choose with evidence. Output: `specs/<slug>/trial.md` from `<skill-dir>/_template/trial.md`, plus raw results under `specs/<slug>/artifacts/trial/`.

A trial costs a spike per candidate. Most designs never need one.

## When to run

Run only when both hold:

1. After the Files-to-Read manifest and `requirements.md`, two or more approaches remain viable and the evidence in the code does not pick one.
2. The choice is worth the spikes. At least one of:
   - a performance budget in a REQ, or a hot path where latency, throughput, memory, allocations, startup, or binary size decide the design;
   - the choice is costly to reverse: a public API, a wire or storage format, the concurrency model, a new dependency or framework;
   - a real dispute about readability or maintainability that side-by-side code would settle.

Also run when the user asks for one ("trial", "A/B", "compare approaches", "benchmark the options", "spike these").

Skip when one approach is clearly right from evidence, the change is small and easy to reverse, candidates differ only in taste, or nothing measurable separates them. A design that considered a trial and skipped it says so in one line in its Rationale: `No trial: <reason>`.

Candidate count: 2 to 5. With fewer than 2 viable approaches there is nothing to trial. With more than 5, shortlist to 5 by reasoning first and list each cut approach with a one-line reason.

## Where it sits in the turn order

| Turn | Reads | Writes |
|---|---|---|
| 3 | requirements.md + code | `design.md` with the approach marked `pending trial` and the candidates listed in Rationale |
| 3t-frame | requirements.md + design.md + code | `trial.md` sections 1 to 5 (question, candidates, gates, criteria, harness), before any spike |
| 3t-run | trial.md + code | spikes, results, and `trial.md` sections 6 and 7 |
| 3 (finish) | trial.md + design.md | `design.md` with the winner and a link to `trial.md` |
| 4 | requirements.md + design.md + code | `tasks.md` |

One artifact per turn still holds. `tasks.md` waits until `trial.md` has a decision.

## 1. Frame (before any code)

- **Question:** the decision in one sentence.
- **Candidates:** 2 to 5 rows, each with a short sketch (shape, key types and functions, dependencies) and a hypothesis for why it could win. Include the most direct implementation, or the current code, as a baseline when it is credible.
- **Gates:** must-pass conditions. The shared test suite is always one; add hard limits from REQs and the user ("no new dependency", "p99 under 5 ms", "no API break"). A candidate that fails a gate is out regardless of score.
- **Criteria and weights:** a table of criteria, weights that sum to 100, and how each is measured. Fix the weights now; never change them after seeing results. Typical criteria:

  | Criterion | Measured by |
  |---|---|
  | Performance | the benchmark metric the REQ names (median and spread) |
  | Readability and maintainability | `software-design` review checklist findings, nesting depth, size of the public surface |
  | Change cost | diff size against base, new dependencies, migration or reversal effort |
  | Operability | failure modes, error clarity, observability hooks |

- **Budget:** effort cap per candidate and a stop rule. A candidate that cannot pass the shared tests within budget is recorded as failed, not extended.
- **Checkpoint:** attended sessions show the frame and wait for an OK when the budget is large or the weights are a judgment call. Unattended runs proceed and flag the weights in the report.

## 2. Harness (once, before the spikes)

Build on a trial base branch `trial/<slug>/base` cut from the work branch:

- **Common entry point** every candidate must expose: a function signature, interface, CLI command, or endpoint.
- **Shared tests:** the acceptance tests for the REQs in scope, written against that entry point.
- **Benchmark:** the same inputs, fixed seeds, warm-up, and repeated runs for every candidate. Use the tool the language skill's performance reference names:

  | Stack | Tool |
  |---|---|
  | Go | `go test -bench . -count 10`, compared with `benchstat` |
  | Rust | criterion |
  | Java, Kotlin | JMH |
  | C, C++ | Google Benchmark |
  | whole programs, CLIs | `hyperfine` |
  | services, only when the REQ is about the service | a fixed-rate load generator (k6, wrk2, vegeta) |

## 3. Spikes

- One branch and worktree per candidate: `trial/<slug>/<candidate-id>` off the trial base. In Claude Code, dispatch one `agent-playbook:implement-subagent` per candidate in parallel with `isolation: "worktree"`, the same model tier for all, and identical packets apart from the candidate sketch. Other tools: one worktree at a time.
- A spike is the smallest implementation that passes the shared tests and runs the benchmark. It compiles warning-free and touches nothing outside the trial scope. It is not polished.
- Equal effort for every candidate. Tuning the favorite and not the others invalidates the trial.
- Inside a worktree, code navigation follows the AGENTS.md worktree rule: query the main checkout's `codebase-memory` index and read changed files directly.

## 4. Measure

- Run benchmarks one candidate at a time on the same machine, with the same build mode and flags and an otherwise idle system. Never run candidates in parallel. Save raw output to `artifacts/trial/<candidate-id>/`.
- Report median and spread. Call a difference real only when the tool's statistics support it (benchstat p-value, criterion change detection, JMH error intervals that do not overlap). Otherwise write "no measurable difference".
- Readability: one reviewer (`agent-playbook:code-review-subagent`, one tier for all candidates) scores every candidate in a single pass against the `software-design` review checklist. It sees the diffs side by side, labeled A, B, C rather than by approach name, so the label does not anchor the score.
- Collect for each candidate: diff stats against base, new dependencies, public API additions.

## 5. Decide

- Gates first, then the weighted score: each criterion scored 1 to 5 with the evidence in the cell (numbers, findings), multiplied by its weight.
- Winner: the highest weighted total among candidates that pass every gate. When the top two are within 10% of each other, or performance shows no measurable difference, choose the simpler one under Code Simplicity Discipline: smaller diff, fewer dependencies, smaller public surface.
- Record the winner, the evidence that decided it, the runner-up and the gap, and what would change the decision ("revisit B if load passes X").
- Update `design.md` Rationale with the winner, one line of reasoning, and a link to `trial.md`. If the result overturns an earlier design decision, add a `decision-log.md` entry.
- Attended sessions show the results table and wait for confirmation before `tasks.md` when the choice is user-visible or costly to reverse. Unattended runs proceed and flag it.

## 6. Clean up

- Delete the losing branches and worktrees. Keep the raw benchmark output under `artifacts/trial/`.
- The winning spike is a reference, not the implementation. `tasks.md` plans the real work; spike code is reused only after it passes normal review and the language gate.
- Keep the harness when a REQ carries a performance budget: it becomes a regression check in `validation.md`.

## Banned shortcuts

- Choosing or changing weights after seeing results.
- Comparing numbers across machines, build modes, input sizes, or toolchain versions.
- Declaring a winner on a difference inside the noise.
- Unequal effort across candidates.
- A trial with one candidate, or without shared tests.
- Shipping spike code without review.
- Trials for trivial, easily reversed, or taste-only choices.
