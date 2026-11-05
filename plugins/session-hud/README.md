# session-hud

A Claude Code mod (a plugin of function hooks) that adds a usage row under the prompt and a TODO list every session shares.

**Install**

1. `/plugin marketplace add 0x67/ai-setup` (skip if ai-setup is already added)
2. `/plugin install session-hud@ai-setup`
3. Start a new session.

**Usage row**

1. Sits under the prompt, below the `? for shortcuts` line.
2. Shows context fill, the 5-hour and weekly rate limits with time to reset, session cost in API-equivalent dollars, and the count of open TODO items.
3. Percentages turn yellow at 60% and red at 85%. Bars show from 110 columns and drop out below that.
4. Rate limits show only on a subscription, after the first response of the session.

**TODO list**

1. Kept in `~/.claude-todo.md` as a markdown checklist (`- [ ] item`), so it can be edited by hand. Every session polls the file every 2 seconds.
2. The pane is hidden by default. `/todo` shows or hides it; `/todo show` and `/todo hide` do one or the other.
3. `/todo add <text>`, `/todo done <n>` (toggles), `/todo rm <n>`, `/todo clear` (drops done items). Pressing an item in the pane toggles it.
4. Item numbers follow the order in the file.

**Develop**

1. `claude --plugin-dir plugins/session-hud` loads it from the working copy and reloads on save.
2. `claude plugin test plugins/session-hud` runs the tests; `claude plugin validate plugins/session-hud` checks the manifest and module.
