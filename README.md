# agent-playbook

My setup for AI coding agents: engineering rules, language skills, a spec-driven workflow, and orchestration subagents. It installs as a Claude Code plugin. The skills and `AGENTS.md` also work in Cursor, Codex, Copilot, OpenCode and other agents that read `SKILL.md` or `AGENTS.md`.

I use this setup in my own daily work, and it took shape over a long stretch of real projects before it moved into this repo. The version references (each skill's release ladder, the JVM tool compatibility table, and the crate versions behind the low-latency pages) are checked weekly: a scheduled agent reads the official release notes, a reviewer on the highest model tier available re-checks every change against its source, and the result arrives as a pull request that I review before merging.

## Contents

The agent-playbook plugin lives in `plugins/agent-playbook/`, and the paths in this table are relative to it. The repo root holds only the marketplace, so claude.ai can sync each plugin on its own.

| Path | What it does | Works in |
|---|---|---|
| `AGENTS.md` | Engineering rules: comments, tests, code growth, simplicity, search order, terminology | any agent |
| `skills/golang`, `skills/rust`, `skills/tauri`, `skills/cpp`, `skills/java`, `skills/kotlin` | Language skills with a routing table into `references/` and a post-write gate | any agent |
| `skills/jvm` | JVM platform shared by Java and Kotlin: Gradle, Maven, JUnit, Mockito, MockK, Spring, profiling, version compatibility, jdtls and kotlin-lsp navigation | any agent |
| `skills/software-design` | Language-agnostic naming, function size, modularity, and architecture (SOLID, layered, MVC, hexagonal, DDD, CQRS, microservices) | any agent |
| `skills/conventional-commits` | Conventional Commits headers for commits and PR titles, one-line commits with no AI attribution, and a PR body layout; the repo's commitlint config, PR template, and history take precedence | any agent |
| `skills/low-latency` | Hot-path rules for any language (measure first, one writer, no per-message allocation, overflow policy, wait strategy, thread placement), with Rust pages for disruptor, crossbeam and rtrb, bytes and zerocopy, io-uring, measurement (criterion, hdrhistogram, loom, Miri), and CPU pinning | any agent |
| `skills/spec-driven` | Spec writing and implementation protocol, with templates and relay prompts | any agent |
| `skills/orchestration-layers` | Dispatch ladder, model tier per handoff, model disclosure, parallel scheduling | Claude Code |
| `agents/` | `planning-subagent`, `implement-subagent` | Claude Code |
| `hooks/` | Injects `AGENTS.md` and a humanizer rule card at session and subagent start; reminds to load the Go, Rust, C/C++, Java, Kotlin, or JVM skill and run its post-write gate the first time matching code is edited or built, and points at the low-latency skill and its matching pages on the first read in a Rust repo whose `Cargo.toml` depends on a latency crate; asks you before risky moments: a new dependency with a malware or known-vulnerability advisory (OSV), a skill, plugin, or MCP install (SkillSpector), a commit that adds a secret (gitleaks), a risky workflow edit (zizmor), and any push, publish, or deploy; in repos with `lat.md/`, injects the sections matching each prompt and runs lat's end-of-session check only when the session changed files; memory-search reminder | Claude Code |
| `../session-hud` | Separate plugin in the same marketplace: a usage row under the prompt (context, rate limits, cost) and a TODO list shared by every session, see its [README](plugins/session-hud/README.md) | Claude Code |
| `../vetted-skills` | Separate plugin in the same marketplace: better-writing, better-typography, Waza `ui`, and Kami, each copied from a pinned commit after a SkillSpector scan, see [Vetted third-party skills](#vetted-third-party-skills) | Claude Code, claude.ai |

## Install (Claude Code)

The hooks need `sh`, `python3`, `jq`, and `git` on `PATH`. Without `jq` the language reminder stays silent; everything else still works. The dependency check calls the public OSV API (`api.osv.dev`) and needs network access; when it is unreachable the check is skipped.

1. Add the marketplaces, then install agent-playbook:

   ```
   /plugin marketplace add blader/humanizer
   /plugin marketplace add 0x67/agent-playbook
   /plugin install agent-playbook@0x67
   ```

   agent-playbook declares [humanizer](https://github.com/blader/humanizer) as a dependency, so the install also brings in `humanizer@humanizer`. Claude Code installs dependencies only from marketplaces you have added, which is why that line comes first. If you skip it, agent-playbook installs but does not load; adding the humanizer marketplace afterwards installs it and fixes that.
2. Start a new session. Nothing else to configure: the hooks inject `AGENTS.md` and the humanizer rule card, and skills and subagents show up with the plugin prefix (`agent-playbook:golang`, `agent-playbook:planning-subagent`).
3. Optional: add any of the extras below.

Update with `claude plugin marketplace update 0x67` and `claude plugin update agent-playbook@0x67`.

## Other agents

Cursor, Codex, Copilot, OpenCode and the rest get the skills through the [skills CLI](https://github.com/vercel-labs/skills), and the rules by copying `AGENTS.md` into a project or the tool's global rules file:

```
npx skills add 0x67/agent-playbook
```

Hooks and subagents are Claude Code only, so nothing injects the rules automatically, and the humanizer plugin is not there. `AGENTS.md` covers that gap: its own writing rules apply without the humanizer skill.

## Optional extras

Each extra is used when present. Nothing breaks without it. [docs/benchmarks.md](docs/benchmarks.md) has measured token and cost numbers for every part of the setup, including what did not pay off.

| Extra | What it adds | Install (macOS; other platforms in each project's docs) | Without it |
|---|---|---|---|
| [fff](https://github.com/dmtrKovalenko/fff) MCP | Exact text and file search, first in the `AGENTS.md` search order | `brew install dmtrkovalenko/fff/fff-mcp`, then `claude mcp add-json -s user fff '{"type":"stdio","command":"fff-mcp","args":["--no-update-check"],"alwaysLoad":true}'` (`alwaysLoad` keeps its three tools out of tool search, so agents use them without a lookup first) | Built-in Grep and Glob; the agent says why |
| [Semble](https://github.com/MinishLab/semble) MCP | Semantic code search | `uv tool install 'semble[mcp]'`, then `claude mcp add-json -s user semble '{"type":"stdio","command":"semble","args":[],"alwaysLoad":true}'` (needs [uv](https://docs.astral.sh/uv/); launched through `uvx` instead, each running server holds uv's cache lock, so `uv cache prune` cannot run while sessions are open) | Text search only |
| [codebase-memory](https://github.com/DeusData/codebase-memory-mcp) MCP | Callers, callees, routes, and types from a code graph before multi-file reads | Install the `codebase-memory-mcp` binary per its README, then `claude mcp add -s user codebase-memory -- codebase-memory-mcp` | More file reads |
| LSP plugins from [claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | `gopls-lsp`, `rust-analyzer-lsp`, `clangd-lsp`, `jdtls-lsp`, `kotlin-lsp` back the `LSP` tool the Go, Rust, C/C++, and Java/Kotlin skills prefer | `/plugin marketplace add anthropics/claude-plugins-official`, then `/plugin install clangd-lsp@claude-plugins-official` (same for the others); the language server must be on `PATH` | Grep-based code navigation |
| [rtk](https://www.rtk-ai.app/) | Compresses shell command output before it reaches the model. Claude Code already cuts outputs over about 30 KB to a short preview, and rtk can shrink such an output back under that limit so more of it lands in context; an A/B run in [docs/benchmarks.md](docs/benchmarks.md) cost 46% more for that reason | `brew install rtk`, then `rtk init -g --hook-only` (`--agent cursor` and others for other tools) | Full command output, more tokens |
| [lat.md](https://www.npmjs.com/package/lat.md) | `lat` CLI for `lat.md/` architecture graphs | `npm i -g lat.md` | The lat reminder stays silent in repos without `lat.md/` |
| [caveman](https://github.com/JuliusBrussee/caveman) | Terse chat replies. Measured: answers about 10% shorter, no cost saving, and about 5.9k extra prompt tokens per session | `/plugin marketplace add JuliusBrussee/caveman`, then `/plugin install caveman@caveman`; its `[CAVEMAN]` status line badge is optional, and the mode works without it | Normal replies; nothing in agent-playbook depends on it |
| [gitleaks](https://github.com/gitleaks/gitleaks) | Stops a commit that adds a key or token: the `security-guard` hook asks you first | `brew install gitleaks` | Commits are not scanned for secrets |
| [SkillSpector](https://github.com/NVIDIA/skillspector) | Scans a skill repo, plugin marketplace, or new `SKILL.md` before it is installed, and asks you when it is not rated safe | `uv tool install git+https://github.com/NVIDIA/skillspector.git` | Skill and plugin installs are not scanned; `claude mcp add`, `curl \| sh`, and git-URL installs still ask |
| [zizmor](https://github.com/zizmorcore/zizmor) | Checks GitHub Actions workflow edits for injection and permission problems before they are written | `brew install zizmor` | Workflow edits are not checked |
| [better-writing and better-typography](https://github.com/jakubkrehel/skills) | Reviews of interface copy (buttons, errors, empty states, plurals, capitalization) and of how text renders (type scale, line-height, weights, `tabular-nums`, wrapping). Neither overlaps with humanizer, which covers prose. Measured: no gain on common UI problems, about 45% more cost ([docs/benchmarks.md](docs/benchmarks.md)) | `/plugin install vetted-skills@0x67` (pinned at commit `1eb03d2`, where SkillSpector rates both skills safe; the plugin also adds Waza `ui` and Kami). Other agents: `npx skills add jakubkrehel/skills --skill better-writing --skill better-typography`; the full repo scans HIGH because of other skills, so install only these two. Once installed they load on their own for UI copy and typography work, or on demand with `/better-writing` and `/better-typography` | General UI review from the model alone |
| [Kami](https://github.com/tw93/Kami) | Typesets documents from templates into PDF, PNG, and editable PowerPoint: resumes, one-pagers, long documents, letters, slide decks, social cards, and landing pages. Not measured here | `/plugin install vetted-skills@0x67` (pinned at commit `e82bb39`), or upstream with `/plugin marketplace add tw93/Kami`, then `/plugin install kami@kami`. SkillSpector rates it CRITICAL at `e82bb39`; the findings read on 2026-11-09 were CJK text, HTML template comments, cleanup of its own temp files, and install hints. It checks GitHub for a newer release once a day, and downloads CJK fonts and a math renderer the first time they are needed. PDF output needs WeasyPrint, and math needs Node.js 20 or 22 | Documents as plain Markdown or HTML, with no layout system |
| [Waza `ui`](https://github.com/tw93/Waza) | Builds and restyles pages and components, and polishes them from screenshots of the rendered UI. Not measured here | `/plugin install vetted-skills@0x67` (pinned at commit `5821754`, where SkillSpector rates `ui` safe), or upstream with `/plugin marketplace add tw93/Waza`, then `/plugin install waza-ui@waza`. Install only the skills you want: the `waza` bundle also adds its own rules, and its `read` skill can send search queries to DeepSeek when `DEEPSEEK_API_KEY` is set | UI work from the model alone |
| session-hud (this repo) | Usage row under the prompt and a shared TODO pane (`/todo`) | `/plugin install session-hud@0x67` | The built-in status line and `/usage` |
| [tech-debt-skill](https://github.com/ksimback/tech-debt-skill) | Tech debt audits | `npx skills add ksimback/tech-debt-skill` | Nothing; agent-playbook does not reference it |

## Model tiers

Each subagent declares a default tier in its frontmatter: `planning-subagent` runs on sonnet and `implement-subagent` on opus. Code review uses the built-in `/code-review` skill. `agent-playbook:orchestration-layers` holds the table for choosing a tier per handoff. To pin the version an alias resolves to, set `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, or `ANTHROPIC_DEFAULT_FABLE_MODEL` in the `env` block of your Claude Code settings.

## Vetted third-party skills

`plugins/vetted-skills` holds copies of four third-party skills taken from fixed commits, so Claude Code and claude.ai load the exact version that was scanned. `scripts/vendor-skills.json` lists each skill's repo, folder, and commit.

1. `scripts/vendor-skills.py` downloads each pinned commit, scans the skill folder with `skillspector scan --no-llm`, and replaces the copy only when SkillSpector recommends SAFE.
2. A skill rated above that needs an `accepted` block with the same commit, the accepted severity, and the review date. Kami has one for its CRITICAL rating.
3. `--bump` moves every pin to the head of the upstream default branch first, so Kami fails after a bump until someone reviews the new commit. `--only <name>` limits the run to one skill.
4. The script also lists frontmatter that claude.ai ignores or strips, such as extra keys or angle brackets in a description.

In claude.ai, add this repo under Customize, Add marketplace, Add from a repository, then install `agent-playbook` and `vetted-skills`. claude.ai syncs on each push to `main`. Only the skills work in chat; hooks and subagents do not run there.

## Evals

`plugins/agent-playbook/evals/` holds a `claude plugin eval` suite with one case per skill trigger and standing rule. Each case runs with and without the plugin, so the report shows what the plugin changes. Run `plugins/agent-playbook/evals/run.sh`, adding `--case <name>`, `--runs <n>`, or `--model <alias>` as needed. Eval sandboxes load only the plugin under test, and agent-playbook will not load without its humanizer and fable dependencies, so the script evals a temporary copy with those dependencies removed. Results go to `plugins/agent-playbook/evals/results/`, which git ignores. Cases run one at a time by default; with `--concurrency` above 1, cases that start together each pay the shared prompt prefix as a cache write instead of reading it, so the run costs more.

## License

MIT. `plugins/agent-playbook/hooks/humanizer-card.md` condenses rules from [blader/humanizer](https://github.com/blader/humanizer) (MIT).
