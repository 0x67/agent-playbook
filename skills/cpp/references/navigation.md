# C/C++ Code Navigation

Loaded via `cpp` SKILL.md routing table. Text search misses overloads, template instantiations, namespaces, argument-dependent lookup, macros, and code behind `#if`; a language server resolves them. Sources: clangd docs (clangd.llvm.org), the Claude Code `LSP` tool's operation list.

## Setup

- clangd reads `compile_commands.json` from the source root or a parent `build/` dir, or the path in `.clangd` (`CompileFlags: CompilationDatabase: build/dev`).
- Generate it: CMake `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON` (then symlink `build/<preset>/compile_commands.json` to the repo root), Meson writes it to the build dir, Make via `bear -- make`, Bazel via `hedronvision/bazel-compile-commands-extractor`.
- Claude Code: the `clangd-lsp` plugin (`claude-plugins-official`) serves clangd through the `LSP` tool; clangd must be on `PATH`. Other agents: their clangd integration.
- No compilation database: clangd guesses flags and misses include paths and macros. Say so before trusting any result.

## Which operation

| Need | `LSP` operation | Fallback (state why) |
|---|---|---|
| where it is defined | `goToDefinition` | `fff-grep` the bare name, then `Read` |
| every use | `findReferences` | `fff-grep` the bare name, filter by hand |
| who calls this | `prepareCallHierarchy`, then `incomingCalls` | grep call sites |
| what this calls | `outgoingCalls` | read the body |
| type, signature, docs | `hover` | `Read` the declaration |
| overrides of a virtual | `goToImplementation` | grep `override` plus the name |
| symbols in a file | `documentSymbol` | `Read` |
| find a symbol by name across the project | `workspaceSymbol` with `query` | `fff-grep` |

Errors arrive as diagnostics after edits; the build is still the authority.

## Rules

1. `findReferences` before renaming, deleting, or changing what a symbol means. Grep is the fallback, never the plan.
2. Before changing a function signature (parameters, return type, `const`, `noexcept`, `virtual`, template parameters): `incomingCalls` for callers, then `findReferences` for the rest (function pointers, `std::function` bindings, friend declarations, overrides). Update every site.
3. `hover` or `goToDefinition` before using an unfamiliar symbol. Overload resolution and ADL pick by argument types; never assume which function a name resolves to.
4. Templates: references to the primary template do not list every instantiation's behavior. Check specializations, concept constraints, and `requires` clauses separately.
5. Macros and `#if`: clangd sees only the configuration in the database. Code for other platforms or feature flags needs a grep pass. Say which configurations you checked.
6. Header changes touch every includer. Search references across the whole database, not only open files.

## Positions

- `line` and `character` are 1-based. Take the line from `Read` output, confirm the symbol is on it, count the column. Never guess either.
- Absolute file paths.
- Empty result means no references, unless the file is missing from the database; check that first.
- Query independent symbols in parallel.

## When text search is right

String literals, comments, log messages, CMake and config files, target names, macro names across unbuilt configurations, non-C++ files.
