# agent-playbook

My setup for AI coding agents: engineering rules, language skills, a spec-driven workflow, and orchestration subagents. It installs as a Claude Code plugin. The skills and `AGENTS.md` also work in Cursor, Codex, Copilot, OpenCode and other agents that read `SKILL.md` or `AGENTS.md`.

I use this setup in my own daily work, and it took shape over a long stretch of real projects before it moved into this repo. The version references (each skill's release ladder, the JVM tool compatibility table, and the crate versions behind the low-latency pages) are checked weekly: a scheduled agent reads the official release notes, a reviewer on the highest model tier available re-checks every change against its source, and the result arrives as a pull request that I review before merging.

## Contents

| Path | What it does | Works in |
|---|---|---|
| `AGENTS.md` | Engineering rules: comments, tests, code growth, simplicity, search order, terminology | any agent |
| `skills/golang`, `skills/rust`, `skills/tauri`, `skills/cpp`, `skills/java`, `skills/kotlin` | Language skills with a routing table into `references/` and a post-write gate | any agent |
| `skills/jvm` | JVM platform shared by Java and Kotlin: Gradle, Maven, JUnit, Mockito, MockK, Spring, profiling, version compatibility, jdtls and kotlin-lsp navigation | any agent |
| `skills/software-design` | Language-agnostic naming, function size, modularity, and architecture (SOLID, layered, MVC, hexagonal, DDD, CQRS, microservices) | any agent |
| `skills/low-latency` | Hot-path rules for any language (measure first, one writer, no per-message allocation, overflow policy, wait strategy, thread placement), with Rust pages for disruptor, crossbeam and rtrb, bytes and zerocopy, io-uring, measurement (criterion, hdrhistogram, loom, Miri), and CPU pinning | any agent |
| `skills/spec-driven` | Spec writing and implementation protocol, with templates and relay prompts | any agent |
| `skills/orchestration-layers` | Dispatch ladder, model tier per handoff, model disclosure, parallel scheduling | Claude Code |
| `agents/` | `planning-subagent`, `implement-subagent`, `code-review-subagent` | Claude Code |
| `hooks/` | Injects `AGENTS.md` and a humanizer rule card at session and subagent start; reminds to load the Go, Rust, C/C++, Java, Kotlin, or JVM skill the first time matching code comes up (a read, an edit, a build command, or search results), plus the low-latency skill and its matching pages when a Rust repo's `Cargo.toml` depends on a latency crate; in repos with `lat.md/`, injects the sections matching each prompt and runs lat's end-of-session check only when the session changed files; memory-search reminder | Claude Code |
| `plugins/session-hud` | Separate plugin in the same marketplace: a usage row under the prompt (context, rate limits, cost) and a TODO list shared by every session, see its [README](plugins/session-hud/README.md) | Claude Code |

## Install (Claude Code)

1. Add the marketplaces, then install agent-playbook:

   ```
   /plugin marketplace add blader/humanizer
   /plugin marketplace add Sahir619/fable-method
   /plugin marketplace add 0x67/agent-playbook
   /plugin install agent-playbook@0x67
   ```

   agent-playbook declares [humanizer](https://github.com/blader/humanizer) and [fable-method](https://github.com/Sahir619/fable-method) as dependencies, so the install also brings in `humanizer@humanizer` and `fable@fable-method`. Claude Code installs dependencies only from marketplaces you have added, which is why those two lines come first. If you skip them, agent-playbook installs but does not load; adding the two marketplaces afterwards installs the missing plugins and fixes it.
2. Start a new session. Nothing else to configure: the hooks inject `AGENTS.md` and the humanizer rule card, and skills and subagents show up with the plugin prefix (`agent-playbook:golang`, `agent-playbook:planning-subagent`).
3. Optional: add any of the extras below.

Update with `claude plugin marketplace update 0x67` and `claude plugin update agent-playbook@0x67`.

## Other agents

Cursor, Codex, Copilot, OpenCode and the rest get the skills through the [skills CLI](https://github.com/vercel-labs/skills), and the rules by copying `AGENTS.md` into a project or the tool's global rules file:

```
npx skills add 0x67/agent-playbook
```

Hooks and subagents are Claude Code only, so nothing injects the rules automatically, and the humanizer and fable plugins are not there. `AGENTS.md` covers both gaps: its own writing rules apply without the humanizer skill, and it spells out the fable loop inline for when the fable skills are missing.

## Optional extras

Each extra is used when present. Nothing breaks without it. [docs/benchmarks.md](docs/benchmarks.md) has measured token and cost numbers for rtk, the search tools, lat.md, and caveman.

| Extra | What it adds | Install (macOS; other platforms in each project's docs) | Without it |
|---|---|---|---|
| [fff](https://github.com/dmtrKovalenko/fff) MCP | Exact text and file search, first in the `AGENTS.md` search order | `brew install dmtrkovalenko/fff/fff-mcp`, then `claude mcp add-json -s user fff '{"type":"stdio","command":"fff-mcp","args":["--no-update-check"],"alwaysLoad":true}'` (`alwaysLoad` keeps its three tools out of tool search, so agents use them without a lookup first) | Built-in Grep and Glob; the agent says why |
| [Semble](https://github.com/MinishLab/semble) MCP | Semantic code search | `uv tool install 'semble[mcp]'`, then `claude mcp add-json -s user semble '{"type":"stdio","command":"semble","args":[],"alwaysLoad":true}'` (needs [uv](https://docs.astral.sh/uv/); launched through `uvx` instead, each running server holds uv's cache lock, so `uv cache prune` cannot run while sessions are open) | Text search only |
| [codebase-memory](https://github.com/DeusData/codebase-memory-mcp) MCP | Callers, callees, routes, and types from a code graph before multi-file reads | Install the `codebase-memory-mcp` binary per its README, then `claude mcp add -s user codebase-memory -- codebase-memory-mcp` | More file reads |
| LSP plugins from [claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | `gopls-lsp`, `rust-analyzer-lsp`, `clangd-lsp`, `jdtls-lsp`, `kotlin-lsp` back the `LSP` tool the Go, Rust, C/C++, and Java/Kotlin skills prefer | `/plugin marketplace add anthropics/claude-plugins-official`, then `/plugin install clangd-lsp@claude-plugins-official` (same for the others); the language server must be on `PATH` | Grep-based code navigation |
| [open-code-review](https://github.com/alibaba/open-code-review) CLI | Per-language review checklists and file selection that `code-review-subagent` uses on big diffs (more than 800 changed lines or 25 files), through `ocr delegate`, which needs no model of its own | `npm install -g @alibaba-group/open-code-review` | Big diffs get the subagent's own checklist only |
| [rtk](https://www.rtk-ai.app/) | Compresses shell command output before it reaches the model | `brew install rtk`, then `rtk init -g --hook-only` (`--agent cursor` and others for other tools) | Full command output, more tokens |
| [lat.md](https://www.npmjs.com/package/lat.md) | `lat` CLI for `lat.md/` architecture graphs | `npm i -g lat.md` | The lat reminder stays silent in repos without `lat.md/` |
| [caveman](https://github.com/JuliusBrussee/caveman) | Terse chat replies | `/plugin marketplace add JuliusBrussee/caveman`, then `/plugin install caveman@caveman`; its `[CAVEMAN]` status line badge is optional, and the mode works without it | Normal replies; nothing in agent-playbook depends on it |
| session-hud (this repo) | Usage row under the prompt and a shared TODO pane (`/todo`) | `/plugin install session-hud@0x67` | The built-in status line and `/usage` |
| [tech-debt-skill](https://github.com/ksimback/tech-debt-skill) | Tech debt audits | `npx skills add ksimback/tech-debt-skill` | Nothing; agent-playbook does not reference it |

## Model tiers

Each subagent declares a default tier in its frontmatter: `planning-subagent` runs on sonnet, `implement-subagent` and `code-review-subagent` on opus. `agent-playbook:orchestration-layers` holds the table for choosing a tier per handoff. To pin the version an alias resolves to, set `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, or `ANTHROPIC_DEFAULT_FABLE_MODEL` in the `env` block of your Claude Code settings.

## Evals

`evals/` holds a `claude plugin eval` suite with one case per skill trigger and standing rule. Each case runs with and without the plugin, so the report shows what the plugin changes. Run `evals/run.sh`, adding `--case <name>`, `--runs <n>`, or `--model <alias>` as needed. Eval sandboxes load only the plugin under test, and agent-playbook will not load without its humanizer and fable dependencies, so the script evals a temporary copy with those dependencies removed. Results go to `evals/results/`, which git ignores. Cases run one at a time by default; with `--concurrency` above 1, cases that start together each pay the shared prompt prefix as a cache write instead of reading it, so the run costs more.

## License

MIT. `hooks/humanizer-card.md` condenses rules from [blader/humanizer](https://github.com/blader/humanizer) (MIT).
