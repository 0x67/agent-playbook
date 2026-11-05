# session-hud

A Claude Code mod (a plugin of function hooks) that adds a usage row under the prompt, an agents pane for subagents and workflow runs, and a TODO list every session shares.

**Install**

1. `/plugin marketplace add 0x67/agent-playbook` (skip if the 0x67 marketplace is already added)
2. `/plugin install session-hud@0x67`
3. Start a new session.

**Usage row**

1. Sits under the prompt, below the `? for shortcuts` line.
2. Shows context fill, the 5-hour and weekly rate limits with time to reset, session cost in API-equivalent dollars, the number of agents running, and the count of open TODO items.
3. Percentages turn yellow at 60% and red at 85%. Bars show from 110 columns and drop out below that.
4. Rate limits show only on a subscription, after the first response of the session.

**Agents pane**

1. Tracks every subagent the session starts: Agent tool spawns from the main thread or from another subagent, and each `agent()` of a Workflow run. Teammates are left out.
2. Hidden by default. `/orch` shows or hides it; `/orch clear` drops finished agents, `/orch reset` drops all, `/orch log` prints where the run log lives.
3. Agents are grouped by run: a Workflow run under its `meta.name`, Agent tool spawns under "Main thread" or under the subagent that spawned them. Newest run first.
4. Each row shows status, the spawn's description, model, elapsed time, and the tool in use while running or the total tokens once done. Types show from 84 columns.
5. A verdict badge comes from the agent's final answer: a line that is `APPROVED`, `NEEDS_REVISION`, `FAILED`, `VERIFIED`, `VERIFIED WITH CAVEATS`, `REFUTED`, `PASS`, or the spec-driven `DONE` and `BLOCKED` (optionally after `Verdict:` and markdown emphasis), or a JSON `"verdict"` field from a Workflow schema. A word inside a sentence does not count.

**Run log**

1. Each finished agent appends one JSON line to `~/.claude-orch-log/<date>-<session>.jsonl`: time, working directory, run name, agent id and description, type, model, status, verdict, duration, and the four token counts.
2. One file per session and day, so concurrent sessions never write the same file.
3. Example: `cat ~/.claude-orch-log/*.jsonl | jq -s 'group_by(.model) | map({model: .[0].model, runs: length, output: (map(.output_tokens) | add)})'`.

**TODO list**

1. Kept in `~/.claude-todo.md` as a markdown checklist (`- [ ] item`), so it can be edited by hand. Every session polls the file every 2 seconds.
2. The pane is hidden by default. `/todo` shows or hides it; `/todo show` and `/todo hide` do one or the other.
3. `/todo add <text>`, `/todo done <n>` (toggles), `/todo rm <n>`, `/todo clear` (drops done items). Pressing an item in the pane toggles it.
4. Item numbers follow the order in the file.

**Develop**

1. `claude --plugin-dir plugins/session-hud` loads it from the working copy and reloads on save.
2. `claude plugin test plugins/session-hud` runs the tests; `claude plugin validate plugins/session-hud` checks the manifest and module.
