# ai-setup

My setup for AI coding agents: engineering rules, language skills, a spec-driven workflow, and orchestration subagents. It installs as a Claude Code plugin. The skills and `AGENTS.md` also work in Cursor, Codex, Copilot, OpenCode and other agents that read `SKILL.md` or `AGENTS.md`.

## Contents

| Path | What it does | Works in |
|---|---|---|
| `AGENTS.md` | Engineering rules: comments, tests, code growth, simplicity, search order, terminology | any agent |
| `skills/golang`, `skills/rust`, `skills/tauri`, `skills/cpp` | Language skills with a routing table into `references/` and a post-write gate | any agent |
| `skills/spec-driven` | Spec writing and implementation protocol, with templates and relay prompts | any agent |
| `skills/orchestration-layers` | Dispatch ladder, model tier per handoff, model disclosure, parallel scheduling | Claude Code |
| `agents/` | `conductor`, `planning-subagent`, `implement-subagent`, `code-review-subagent` | Claude Code |
| `hooks/` | Injects `AGENTS.md` and a humanizer rule card at session and subagent start; reminds to load the Go, Rust, or C/C++ skill on the first edit; lat.md and memory reminders | Claude Code |

## Install

Claude Code:

```
/plugin marketplace add 0x67/ai-setup
/plugin install ai-setup@ai-setup
```

Skills, agents, and hooks show up with the plugin prefix, for example `ai-setup:golang` and `ai-setup:conductor`. Update with `claude plugin marketplace update ai-setup` followed by `claude plugin update ai-setup@ai-setup`.

Other agents get the skills through the [skills CLI](https://github.com/vercel-labs/skills), and the rules by copying `AGENTS.md` into a project or the tool's global rules file:

```
npx skills add 0x67/ai-setup
```

## Model tiers

Each subagent declares a default tier in its frontmatter: `planning-subagent` runs on sonnet, `implement-subagent` and `code-review-subagent` on opus, and `conductor` inherits the session model. `ai-setup:orchestration-layers` holds the table for choosing a tier per handoff. To pin the version an alias resolves to, set `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, or `ANTHROPIC_DEFAULT_FABLE_MODEL` in the `env` block of your Claude Code settings.

## Companions

The rules refer to these tools. None are bundled here; install them from their own repos.

| Project | Used for | Install |
|---|---|---|
| [blader/humanizer](https://github.com/blader/humanizer) | The full writing rules behind the injected card | `/plugin marketplace add blader/humanizer`, then `/plugin install humanizer@humanizer` |
| [Sahir619/fable-method](https://github.com/Sahir619/fable-method) | The fable-method and fable-judge loop the orchestration rules call for | `/plugin marketplace add Sahir619/fable-method`, then `/plugin install fable@fable-method` |
| [ksimback/tech-debt-skill](https://github.com/ksimback/tech-debt-skill) | Tech debt audits | `npx skills add ksimback/tech-debt-skill` |
| [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Terse chat replies | `/plugin marketplace add JuliusBrussee/caveman`, then `/plugin install caveman@caveman` |
| [claude-plugins-official](https://github.com/anthropics/claude-plugins-official) LSP plugins | `gopls-lsp`, `rust-analyzer-lsp`, `clangd-lsp` back the `LSP` tool the language skills prefer | `/plugin marketplace add anthropics/claude-plugins-official`, then `/plugin install clangd-lsp@claude-plugins-official` (same for the others); the language server must be on `PATH` |
| [lat.md](https://www.npmjs.com/package/lat.md) | `lat` CLI for `lat.md/` knowledge graphs | `npm i -g lat.md` |

The search order in `AGENTS.md` also names the fff, Semble, and codebase-memory MCP servers. Without them the agent falls back to its built-in search tools.

## License

MIT. `hooks/humanizer-card.md` condenses rules from [blader/humanizer](https://github.com/blader/humanizer) (MIT).
