# Tool benchmarks

Measurements behind the optional extras in the README, taken on 2026-11-05 with Claude Code 2.1.318. Unless a section says otherwise, each number comes from headless `claude -p` runs on Sonnet 5.5 (`claude-sonnet-5-5`) with read-only tools (Bash, Edit, and Write disallowed), three runs per arm, and cost is the `total_cost_usd` that Claude Code reports at API prices. Three runs per arm is a small sample, so treat differences under about 10% as noise.

## rtk

From `rtk gain` over real sessions rather than an A/B test:

| Measure | Value |
|---|---|
| Commands filtered | 11,100 |
| Command output before and after filtering | 3.6M and 2.5M tokens |
| Tokens saved | 1.1M (30.4%) |
| grep output cut, then recalled by the agent | 623 cuts, 1 recall |
| `go test` output cut, then recalled | 15 cuts, 1 recall |

The recall rate is the useful check: the agent almost never had to fetch the output rtk removed.

## Search tools

### Do agents use them?

Claude Code hides MCP tools behind tool search until the model looks them up. Left alone, agents searched with Bash or Grep instead:

1. Eleven weeks of session history held about 3,900 Bash `grep`, `rg`, and `find` calls, against 282 fff calls, 8 semble calls, and 3 codebase-memory calls.
2. In 12 benchmark runs where fff, semble, or codebase-memory was available, the agent called them 0 times.
3. After setting `alwaysLoad: true` on fff, both runs of the same question used fff straight away, with no tool search and no Grep, at the same cost as Grep ($0.181 and $0.193 against $0.182).

### Targeted question in a 31k-line Rust service

One question that names its subject ("trace the market-data path from the socket to the consumer"), with the prompt telling the agent which search tool to use. Accuracy counts five file:line anchors per answer, 15 per arm.

| Search tool | Median cost | Correct anchors |
|---|---|---|
| Built-in Grep | $0.182 | 15 of 15 |
| fff | $0.179 | 14 of 15 |
| semble | $0.239 | 14 of 15 |
| codebase-memory | $0.224 | 13 of 15 |

### Vague questions in a 254k-line Rust workspace

Two questions that name no identifiers. The broad one asks how the system handles outputs that cannot keep up; the narrow one asks when a restarted run may resume. Every run in every arm found all five anchors. These runs also ended with a stop-hook exchange unrelated to search, which added a similar cost to each arm.

| Setup | Broad question | Narrow question |
|---|---|---|
| Built-in Grep only | $0.436 | $0.172 |
| Agent's own choice, fff on `alwaysLoad` | $0.336 | $0.162 |
| semble | $0.251 | $0.171 |
| codebase-memory | $0.264 | $0.218 |

### What follows

1. fff costs the same as Grep. Its value is that agents use it when it is always loaded, so `alwaysLoad` is set in the README install line.
2. semble and codebase-memory cut cost by about 40% on broad questions in a large codebase and break even or cost more on targeted ones. semble exposes two tools, so it is also set to `alwaysLoad`. codebase-memory exposes 17 and stays behind tool search.

## caveman

Same chat question with caveman off and on, answer length counted in words:

| Setup | Median answer | Median cost |
|---|---|---|
| caveman off | 435 words | $0.162 |
| caveman, June 2026 build | 439 words | $0.162 |
| caveman 4.0.1 | 389 words | $0.164 |

Output tokens did fall slightly with caveman on, but the drop was in thinking tokens, not in the answer. For a prompt that asked for an explanation meant for a teammate, caveman stepped aside as its own rules say it should, and its answers were no shorter (median 757 words against 653 with it off). The savings figure from `/caveman-stats` is a fixed 65% assumption from the upstream benchmark, not a measurement of your sessions.

## Plugin evals

`evals/run.sh` with two runs per case and a no-plugin baseline arm, Sonnet as both agent and judge:

| Check | With ai-setup | Without |
|---|---|---|
| Language or workflow skill loaded (rust, go, java, jvm, kotlin, cpp, spec-driven, software-design) | 16 of 16 runs | 0 of 16 |
| Spec written to `specs/<slug>/requirements.md` | 2 of 2 | 0 of 2 |
| Bug found in the code under review (rust, kotlin, cpp, design review) | 8 of 8 | 8 of 8 |
| No banned terms in new identifiers | 2 of 2 | 2 of 2 |
| PR description free of em dashes, attribution, and filler | 3 of 3 | 3 of 3 |

A full run costs about $2.60. The last two rows pass without the plugin too, so they guard against regressions rather than show a difference.

## Reproducing

The eval suite runs with `evals/run.sh`. The search and caveman comparisons ran against private repositories, so the harness is not in this repo; the method is enough to repeat them on your own code:

1. Run `claude -p "<question>" --model sonnet --output-format stream-json --verbose` from the repository root, with `--disallowedTools Bash Edit Write` to keep runs read-only.
2. Give each arm its search tool with `--allowedTools mcp__<server>` and block the others with `--disallowedTools mcp__<server>`. A forced arm adds a sentence to the prompt naming the tool.
3. Turn caveman off for the baseline with `--settings '{"enabledPlugins":{"caveman@caveman":false}}'`.
4. Read cost, turns, and tool calls from the final `result` event and the `tool_use` blocks, and score answers against anchors you found by hand first.
