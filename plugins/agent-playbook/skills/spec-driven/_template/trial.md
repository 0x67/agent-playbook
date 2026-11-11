# <Spec Name>: Approach Trial

| Field        | Value                                   |
| ------------ | --------------------------------------- |
| Status       | Framing / Running / Decided             |
| Requirements | REQ-A1, REQ-A2, ...                     |
| Decision     | <candidate id, filled when decided>     |

## 1. Question

<the decision in one sentence>

## 2. Candidates

| ID  | Approach                                          | Hypothesis                       |
| --- | ------------------------------------------------- | -------------------------------- |
| A   | <shape, key types and functions, dependencies>    | <why it could win>               |
| B   | ...                                               | ...                              |

2 to 5 rows. Cut before the trial:

- <approach>: <one-line reason>

## 3. Gates

- Shared tests pass: `<command>`
- <hard limit from a REQ or the user>

## 4. Criteria

| Criterion                         | Weight | Measured by                                              |
| --------------------------------- | ------ | -------------------------------------------------------- |
| Performance: <metric>             | <n>    | `<benchmark command>`, median and spread of <N> runs     |
| Readability and maintainability   | <n>    | `software-design` review checklist, blind side by side   |
| Change cost                       | <n>    | diff against base, new dependencies, reversal effort     |
| Operability                       | <n>    | failure modes, error clarity, observability              |

Weights sum to 100 and are fixed before any spike. Budget per candidate: <cap>. Stop rule: <rule>.

## 5. Harness

- Trial base: `trial/<slug>/base`
- Common entry point: `<signature, interface, command, or endpoint>`
- Benchmark: `<command>`; inputs <...>; seed <...>; warm-up <...>; runs <N>
- Machine and build: <CPU, OS, toolchain version, build mode and flags>

## 6. Results

| Candidate | Gates | <metric> median (spread) | Readability findings | Diff +/- | New deps | Weighted |
| --------- | ----- | ------------------------ | -------------------- | -------- | -------- | -------- |
| A         | pass  | ...                      | ...                  | ...      | ...      | ...      |
| B         | ...   | ...                      | ...                  | ...      | ...      | ...      |

Raw output: `artifacts/trial/<candidate-id>/`

## 7. Decision

- Winner: <ID>, because <evidence>
- Runner-up: <ID>, gap <...>
- Revisit if: <condition>
- Cleanup: losing branches deleted <yes / no>; harness kept as a regression check <yes / no>
