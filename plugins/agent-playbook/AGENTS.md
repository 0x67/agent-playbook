# Engineering rules

Standing rules for coding agents. Claude Code gets this file at every session and subagent start through the agent-playbook plugin; other tools read it as `AGENTS.md`. The user's own instructions override anything here.

# Written Output (humanizer)

Text that ends up in an artifact or in front of other people is plain human prose: code comments, doc comments, docs and markdown, specs, UI strings, PR descriptions, commit messages, Jira comments, Slack and email drafts, published artifacts. Drafts shown in chat for the user to paste elsewhere count too. In Claude Code a condensed rule card arrives at every session and subagent start. Load the full `humanizer` skill (`humanizer:humanizer` as a Claude Code plugin) in embedded mode (final text only) before writing PR bodies, docs, specs, Jira comments, or other prose longer than a short paragraph. Where the skill is not installed, the card and the bullets below are the whole rule set; write without it.

- Keep all technical substance: identifiers, paths, numbers, types, error text.
- Do not add a fact, detail, or example the source lacks, even when a rewrite would read better with one.
- The user's own formats and writing samples override humanizer patterns.
- Never rewrite code, commands, paths, or data.

# Code Comments

Plain clauses a person would write, following the humanizer rules above. Keep all technical substance (identifiers, paths, numbers, types).

- No phase/plan refs: no "milestone 3", "TODO from plan X", "as decided in step 2", or `REQ-*` / `TASK-*` / `AC-*` ids. Comments must read alone post-merge; git log/PR holds process.
- No restating code. Skip comment if code self-explanatory.
- Cross-crate/module links encouraged when behavior depends elsewhere: `// see pipeline-sinks::pg::raw`, `// mirrors soupbintcp_replay::Reader`.
- Short > long. One line preferred. Multi-line only when truly needed.
- Doc comments (`///`, `//!`, `"""`, JSDoc) follow same rules. No marketing prose.
- No em dash characters in comments.

Good: `// drain at the sink's pace, not the source's` · `// SAFETY: caller holds the slot lock`
Bad: `// In milestone 4 we decided this should drain at the sink's pace` · `// This function is responsible for draining the buffer` · `// See REQ-P0-005 for timestamp policy`

# Spec-Driven Workflow

Skill `spec-driven` (`agent-playbook:spec-driven` in Claude Code; protocol files are bundled in it) loads on `/spec`, `REQ-*`, `TASK-*`, or spec paths and holds the rules, templates, artifact layout, and relay packet shape. Specs live in `specs/<task-slug>/` (legacy `plans/<task-slug>/` recognized). Small tasks without a spec folder: give subagents a lightweight inline spec with the same relay fields.

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
3. Semantic code search: Semble MCP; if missing, `semble search "query" .` (or `uvx --from "semble[mcp]" semble search "query" .` when semble is not installed).
4. Exact text/file search: fff MCP tools (`mcp__fff__grep`, `mcp__fff__find_files`, `mcp__fff__multi_grep`). Never shell `fff`. Not exposed: Grep, `rg`, or `find`; state reason.
5. Code structure (callers, callees, routes, types) where the `codebase-memory` MCP is connected: its graph tools before multi-file reads. Repo root missing from `list_projects`: in a linked git worktree (`git rev-parse --git-dir` differs from `--git-common-dir`), query the main checkout's project and read the branch's changed files directly (`git diff --name-only <base>...HEAD`), never index the worktree; otherwise run `index_repository` once.
6. Hover, types, and call hierarchy in Go, Rust, C/C++, Java, and Kotlin: the `LSP` tool where a language server is connected (gopls, rust-analyzer, clangd, jdtls, kotlin-lsp). For call sites and references, text search finds the same at lower cost, and in a fresh session the server returns nothing until it has finished indexing.

Preferred tool missing, failing, or lacking capability: use regular tools, state reason. `grep`/`find` fine for logs and configs.
Subagent prompts repeat this block: memory recall, search order, fff MCP tool names, no shell fff, fallback rule.

# Language Rules

Before editing Go, Rust, C/C++, Java, or Kotlin, and before any `go`, `cargo`, or `cmake` command, load skill `golang` / `rust` / `cpp` / `java` / `kotlin` (`agent-playbook:<name>` in Claude Code) and follow its routing table into `references/`. Java and Kotlin also load skill `jvm` for builds, tests, frameworks, and navigation; JVM build files and any `gradle`/`mvn` command (wrappers `./gradlew` and `./mvnw` included) load `jvm`. Run the post-write gate before reporting done; reading and reviewing do not need them (`docs/benchmarks.md`), as they left review answers unchanged and added about 70% to cost.

Hot-path code (per-message receive loops, decoders, order books, queues between threads, latency benchmarks): load skill `low-latency` (`agent-playbook:low-latency`) alongside the language skill. In Claude Code the language hook names it when a Rust repo's `Cargo.toml` depends on a latency crate.

Naming, function size, module boundaries, and architecture (SOLID, layered, MVC, hexagonal, DDD, CQRS): load skill `software-design` (`agent-playbook:software-design`) alongside the language skill when designing a module or service, naming new types or APIs, splitting code, or reviewing a design.

# Supply Chain and Outward Actions

- Before adding a dependency, confirm the exact package name in the official registry and the project's docs; typosquats are common. Pin versions.
- Never pipe a downloaded script into a shell or interpreter. Download it, read it, then run it.
- Vet skills, plugins, and MCP servers before installing them: read the source, or scan it with SkillSpector.
- Never commit secrets; keep them in environment variables or a secret store.
- Push, publish, deploy, and apply commands need the user's go-ahead in this conversation.
- Destructive database commands (`DROP`, `TRUNCATE`, `DELETE` or `UPDATE` without `WHERE`, a migration reset or rollback) and writes to a database that is not local need the same go-ahead. Reach production through a read-only role.

In Claude Code, hooks back these with a permission prompt. `dep-guard` checks each new dependency and the packages it pulls in for OSV advisories, install scripts, and versions published less than 7 days ago (`AGENT_PLAYBOOK_MIN_AGE_DAYS`). `security-guard` runs SkillSpector on skills and plugins, gitleaks before commits, and zizmor on workflow edits, and asks before every push, publish, or deploy. `db-guard` asks before the database commands above, in shell commands and in database MCP tools.

# Commits and Pull Requests

Before writing a commit message, a PR title, or a PR body, load skill `conventional-commits` (`agent-playbook:conventional-commits` in Claude Code): Conventional Commits headers, one-line commits with no AI attribution, and a Summary, Changes, Testing PR body. The repository's commitlint config, PR template, and commit history override it.

A feature that would put more than about 400 changed lines (lockfiles not counted) or more than one concern into one PR is split into stacked PRs, planned before the first edit: `references/stacked-prs.md` in that skill. Every PR in a stack keeps the usual names: the repo's branch pattern (default `<type>/<slug>`), a Conventional Commits title for its own change, and no stack position such as `[2/3]` in a title or branch. In Claude Code the `pr-guard` hook asks before a `gh pr create` or `gh stack` command that goes over the size limit, breaks these names, or would open PRs with generated titles.

# Worktree Commit Handoff

Work in a git worktree or on a branch other than the user's workspace branch:

- Track source branch and target workspace branch when known.
- Uncommitted: give exact proposed commit message; say no hash exists yet.
- Committed: give hash, source branch, full commit message, `git cherry-pick <hash>`.
- Include at each work-unit pause and at final completion.

# Agents and Orchestration (Claude Code)

Full ladder, composition, parallel fan-out rules, and tier table: skill `agent-playbook:orchestration-layers`. Load it before subagent fan-out or Workflow. Always on:

- Non-trivial multi-step task: classify the ask, define done and how to check it, read the evidence, make the smallest change, verify by running it, then check every claim against the diff and the output before reporting.
- Cheapest mechanism that fits: inline, then subagents dispatched from the main thread (shape found while working), then Workflow (shape known, user opted in).
- Parallel fan-out (Agent calls, Workflow `parallel()` or `pipeline()`, headless or eval batches): start one agent first and the rest after it responds (in Workflow, `await` one `agent()` before the fan-out stage). The rest then read the shared prompt cache instead of each writing it.
- Workflow() only on explicit opt-in: `ultracode`, "use a workflow", "orchestrate this with subagents", or a skill calls it. Otherwise offer.
- Subagent types use the plugin prefix: `agent-playbook:planning-subagent`, `agent-playbook:implement-subagent`. Never a guessed name.
- Code review: the built-in `code-review` skill (`/code-review <level>`, low for one task, medium for a feature, high before a release). It found every planted bug at a fraction of a review subagent's cost (`docs/benchmarks.md`).
- Hand off at the tier the work needs (table in `agent-playbook:orchestration-layers`). Disclose every spawn at dispatch as `<label> -> <alias> <version>`, with the version taken from an env pin or the session's model list, never from memory. No silent spawns.
- Relay packets include the standing protocols: memory recall, comment rules, Code Simplicity Discipline, search order.

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
- Duplicate coverage: branch already covered; cite the covering test and skip.
- Mock-call-count-only asserts with no observable output checked.
- False confidence: assertion weaker than the test name claims. Verify the actual contract or delete the test.
- Copy-pasted test doubles/encoders: one shared `tests/support` module per crate.
- Re-proving a generic contract per implementation: write one generic assert helper, call it per impl.

Exception: wire/on-disk layout pins (size, alignment, discriminant, padding, format magic) are contract gates. Keep those.

# Code Simplicity Discipline (all projects)

Pre-write gates, same standing as Code Growth Discipline. Apply before writing, not during review.

- No overcomplicated or overlong code. Smallest change that meets the ask. No speculative abstraction: no trait for one impl, generic for one type, builder for two fields, config knob for one value, indirection layer "for later". One concern per fn; if it needs section comments, split it. Plain `match`/`if`/iterator chain beats layered helpers.
- No backwards compatibility unless user asks. Rename or change signature and fix every call site. No `#[deprecated]` shims, `_v2` twins, old-name re-exports, dual code paths, "legacy" flags, or migration adapters. Breaking inside workspace is fine; git history holds old versions.
- Readable layout. Put one blank line between the steps of a function (setup, the work, the result), as paragraph breaks, not after every statement. No nested ternaries: use `if`/`else`, a `switch`/`match`, or a small named function. A formatter keeps the blank lines you write and adds none, and leaves a ternary chain on one line when it fits the width.
- Avoid slop and anti-patterns. Slop: dead code, unused params/imports, `#[allow]` to silence instead of fix, `.clone()` to dodge borrow, `unwrap()`/`expect()` on lib path, stringly-typed state, bool-param flags, `Box<dyn>` where generic fits, newtype with no invariant, re-validating already-typed input, comment narrating code, TODO placeholder instead of finishing, catch-all error swallow. Delete on sight in touched code.

In review, any of above in diff = NEEDS_REVISION. Relay packets include this section.
