# Engineering rules

Standing rules for coding agents. Claude Code gets this file at every session and subagent start through the ai-setup plugin; other tools read it as `AGENTS.md`. The user's own instructions override anything here.

# Written Output (humanizer)

Text that ends up in an artifact or in front of other people is plain human prose: code comments, doc comments, docs and markdown, specs, PR descriptions, commit messages, Jira comments, Slack and email drafts, published artifacts. Drafts shown in chat for the user to paste elsewhere count too. In Claude Code a condensed rule card arrives at every session and subagent start. Load the full `humanizer` skill (`humanizer:humanizer` as a Claude Code plugin) in embedded mode (final text only) before writing PR bodies, docs, specs, Jira comments, or other prose longer than a short paragraph.

- Keep all technical substance: identifiers, paths, numbers, types, error text.
- The user's own formats and writing samples override humanizer patterns.
- Never rewrite code, commands, paths, or data.

# Code Comments

Plain clauses a person would write, following the humanizer rules above. Keep all technical substance (identifiers, paths, numbers, types).

- No phase/plan refs: no "milestone 3", "TODO from plan X", "as decided in step 2", or `REQ-*` / `TASK-*` / `AC-*` ids. Comments stand alone post-merge; git log/PR holds process.
- No restating code. Skip comment if code self-explanatory.
- Cross-crate/module links encouraged when behavior depends elsewhere: `// see pipeline-sinks::pg::raw`, `// mirrors soupbintcp_replay::Reader`.
- Short > long. One line preferred. Multi-line only when truly needed.
- Doc comments (`///`, `//!`, `"""`, JSDoc) follow same rules. No marketing prose.
- No em dash characters in comments.

Good: `// drain at the sink's pace, not the source's` · `// SAFETY: caller holds the slot lock`
Bad: `// In milestone 4 we decided this should drain at the sink's pace` · `// This function is responsible for draining the buffer` · `// See REQ-P0-005 for timestamp policy`

# Spec-Driven Workflow

Skill `spec-driven` (`ai-setup:spec-driven` in Claude Code; protocol files ship inside it) loads on `/plan`, `/spec`, `REQ-*`, `TASK-*`, or spec paths and carries the rules, templates, artifact layout, and relay packet shape. Specs live in `specs/<task-slug>/` (legacy `plans/<task-slug>/` recognized). Small tasks without a spec folder: give subagents a lightweight inline spec with the same relay fields.

# Project Terminology Guard

- Do not introduce `semantic`, `facade`, `golden`, `canonical`, or `canonincal` as project-authored code terms: identifiers, test names, module/file names, fixtures, generated project-owned outputs, API names.
- Prefer by context: `normalized`, `contract`, `payload`, `market_event`, `boundary`, `adapter`, `api`, `mapping`, `domain`, `typed`, `expected`, `reference`, `snapshot`, `stable`, `allowed`.
- Comments and docs may use banned terms only when precise. Prefer alternatives.
- Exceptions: external package/API names, tool feature names, upstream quotes, third-party generated or bundled files; precise DB/storage `canonical` wording and domain terms like `golden cross` when renaming would obscure meaning or break schema compatibility.
- Reviewers flag new project-authored identifier or test occurrences unless an exception is documented.

# Memory and Search

Before planning, implementation, review, or investigation:

1. Native auto memory: scan the `MEMORY.md` index for task, file, module keywords and open matching files. Save durable facts there, one fact per file, linked with `[[name]]`.
2. Architecture: `lat locate` / `lat expand` when `lat.md/` exists.
3. Semantic code search: Semble MCP; if missing, `uvx --from "semble[mcp]" semble search "query" .`.
4. Exact text/file search: fff MCP tools (`mcp__fff__grep`, `mcp__fff__find_files`, `mcp__fff__multi_grep`). Never shell `fff`. Not exposed: Grep, `rg`, or `find`; state reason.
5. Code structure (callers, callees, routes, types) where the `codebase-memory` MCP is connected: its graph tools before multi-file reads.
6. Rust symbols: rust-analyzer tools.

Preferred tool missing, failing, or lacking capability: use regular tools, state reason. `grep`/`find` fine for logs and configs.
Subagent prompts repeat this block: memory recall, search order, fff MCP tool names, no shell fff, fallback rule.

# Language Rules

Before reading, editing, or reviewing Go or Rust, and before any `go` or `cargo` command, load skill `golang` / `rust` (`ai-setup:golang` / `ai-setup:rust` in Claude Code) and follow its routing table into `references/`. Run its post-write gate before reporting done.

# Worktree Commit Handoff

Work in a git worktree or on a branch other than the user's workspace branch:

- Track source branch and target workspace branch when known.
- Uncommitted: give exact proposed commit message; say no hash exists yet.
- Committed: give hash, source branch, full commit message, `git cherry-pick <hash>`.
- Include at each work-unit pause and at final completion.

# Agents and Orchestration (Claude Code)

Full ladder, composition, precedence, tier table, and Fleet scheduling: skill `ai-setup:orchestration-layers`. Load it before subagent fan-out, Conductor, or Workflow. Always on:

- Non-trivial multi-step task: fable-method loop first; fable-judge pass before presenting work as finished (fable plugin).
- Cheapest mechanism that fits: inline, then Workflow (shape known), then Conductor (shape unknown).
- Workflow() only on explicit opt-in: `ultracode`, "use a workflow", "orchestrate this with subagents", or a skill calls it. Otherwise offer.
- Subagent types carry the plugin prefix: `ai-setup:conductor`, `ai-setup:planning-subagent`, `ai-setup:implement-subagent`, `ai-setup:code-review-subagent`. Never a guessed name.
- Hand off at the tier the work needs (table in `ai-setup:orchestration-layers`). Disclose every spawn at dispatch as `<label> -> <alias> <version>`, with the version taken from an env pin or the session's model list, never from memory. No silent spawns.
- Relay packets carry the standing protocols: memory recall, comment rules, Code Simplicity Discipline, search order.

---

# Code Growth Discipline (all projects)

Pre-write gates. Apply before writing, not during review.

- New code: sketch module layout first. One concern per file. Projected >600 non-test LOC or a second concern: start as mod dir with children, never "split later".
- Feature work: if the result would be too coupled or push a file past ~800 non-test LOC, split first (pure moves + `pub use` re-exports, gates green) as its own commit, then implement on the clean layout.
- Cohesive single impl block: fine at any size. Trigger is mixed concerns, not LOC.
- Test mod >40% of file: move to sibling `tests.rs`.
- Split mechanics: inherent impls split across files freely; one trait impl per file; child modules see parent-private fields, siblings need `pub(super)`; move by exact line-range extraction, never retype or dedent; keep external paths via `pub use`.
- Hot path: concrete non-generic per-message fn callable across a crate/repo boundary gets `#[inline]` at write time. Generic fns: nothing. `#[inline(always)]`: only with a cited measured delta.
- A gate must compile what it validates: feature-gated code needs `--features` in every command; green without compiling the target is false green.

# Useless Test Ban (all projects)

A test must be able to fail from a project bug. Never write:

- Derive/stdlib restatement: thiserror `#[error]` string equality, `#[derive(Default)]` variant choice, `#[from]` conversion, derived Clone/Debug/Eq works, plain serde roundtrip with no custom impl.
- Field echo: constructor-stores-argument, struct-literal readback, constant restated.
- Duplicate coverage: branch already covered; name the covering test and skip.
- Mock-call-count-only asserts with no observable output checked.
- False confidence: assertion weaker than the test name claims. Verify the actual contract or delete the test.
- Copy-pasted test doubles/encoders: one shared `tests/support` module per crate.
- Re-proving a generic contract per implementation: write one generic assert helper, call it per impl.

Exception: wire/on-disk layout pins (size, alignment, discriminant, padding, format magic) are contract gates. Keep those.

# Code Simplicity Discipline (all projects)

Pre-write gates, same standing as Code Growth Discipline. Apply before writing, not during review.

- No overcomplicated or overlong code. Smallest change that meets the ask. No speculative abstraction: no trait for one impl, generic for one type, builder for two fields, config knob for one value, indirection layer "for later". One concern per fn; if it needs section comments, split it. Plain `match`/`if`/iterator chain beats layered helpers.
- No backwards compatibility unless user asks. Rename or change signature and fix every call site. No `#[deprecated]` shims, `_v2` twins, old-name re-exports, dual code paths, "legacy" flags, or migration adapters. Breaking inside workspace is fine; git history holds old shape.
- No slop, no anti-patterns. Slop: dead code, unused params/imports, `#[allow]` to silence instead of fix, `.clone()` to dodge borrow, `unwrap()`/`expect()` on lib path, stringly-typed state, bool-param flags, `Box<dyn>` where generic fits, newtype with no invariant, re-validating already-typed input, comment narrating code, TODO placeholder instead of finishing, catch-all error swallow. Delete on sight in touched code.

Review rule: any of above in diff = NEEDS_REVISION. Relay packets carry this section.
