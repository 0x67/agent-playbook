---
name: cpp-tools
description: >
  Use when reading, writing, refactoring, or reviewing C/C++ code (.cpp, .h,
  .hpp, .cc, .cxx, .c). Covers symbol lookup, find references, call hierarchy,
  rename, signature changes. Prefer language-server-backed tooling (clangd
  MCP, ctags) over text grep. Trigger on any C++ file edit or any task that
  needs to find ALL usages of a C++ symbol.
---

# C++ Tools Instructions

Use language-server-backed tools whenever available to analyze C/C++ code. Text search misses overloads, templates, namespaces, and preprocessor-conditional code.

> Note: original Copilot version targeted `GetSymbolInfo_CppTools`, `GetSymbolReferences_CppTools`, `GetSymbolCallHierarchy_CppTools` (Copilot VS Code extension). Those tools are NOT exposed in Claude Code. Substitute equivalents below.

## Equivalent Tools in Claude Code

If a clangd MCP server is exposed, prefer its tools. Otherwise fall back:

| Need | Preferred | Fallback |
|------|-----------|----------|
| Find symbol definition | clangd MCP definition | `fff-grep` for `^\s*(class\|struct\|void\|int\|.*)\s*<sym>\s*[({]` then `Read` |
| Find ALL symbol references | clangd MCP references | `fff-grep "<sym>"` plus visual filter for false positives |
| Call hierarchy (callers / callees) | clangd MCP callHierarchy | grep call sites manually |
| Type info / hover | clangd MCP hover | `Read` definition |
| Rename | clangd MCP rename | grep + Edit per file (high risk) |

## Mandatory Rules

### Rule 1: Use Language Server for Symbol Usages

NEVER rely on manual code inspection or plain `grep` to find where a symbol is used when a language server is available.

ALWAYS call language-server "find references" when:

- Renaming any symbol (function, variable, class, method)
- Changing function signatures
- Refactoring code
- Understanding symbol impact
- Finding all call sites
- Identifying usage patterns
- Any task involving "find all uses/usages/references/calls"

Why: language server understands overloaded functions, template instantiations, qualified vs unqualified names, member function calls, inherited member usage, preprocessor-conditional code. Text search will miss these or produce false positives.

### Rule 2: Use Call Hierarchy for Function Changes

Before modifying any function signature, call hierarchy (incoming callers) to find all callers.

Examples: adding/removing parameters, changing parameter types, changing return types, making functions virtual, converting to template functions.

Why: ensures you update ALL call sites, not just visible ones.

### Rule 3: Use Symbol Info to Understand Symbols

Before working with unfamiliar code, query symbol info to:

- Find where a symbol is defined
- Understand class/struct memory layout
- Get type information
- Locate declarations

NEVER assume you know what a symbol is without checking.

## Parameter Usage Guidelines

### Symbol Names

- Provide symbol name (required).
- Can be unqualified (`MyFunction`), partially qualified (`MyClass::MyMethod`), or fully qualified (`MyNamespace::MyClass::MyMethod`).
- If you have line number, symbol should match what appears on that line.

### File Paths

- Always provide absolute file paths when available.
  - Good: `/home/you/project/src/main.cpp`
  - Avoid: `src/main.cpp` (requires resolution, may fail)

### Line Numbers

- Line numbers are 1-based, NOT 0-based.
- Mandatory workflow when you need a line number:
  1. Call `Read` to view the file.
  2. Locate the symbol in output.
  3. Note the EXACT line number from output.
  4. VERIFY the line contains the symbol.
  5. Only then call language-server tool with that line number.
- NEVER guess line numbers.
- If you do not have a line number, omit it. Tools will find symbol.

### Minimal Information Strategy

Start with minimal information and add more only if needed:

1. **First attempt**: Symbol name only
2. **If ambiguous**: Symbol name + file path
3. **If still ambiguous**: Symbol name + file path + line number (after `Read`)

## Common Workflows

### Renaming a Symbol

Correct:

1. Call "find references" with symbol name (and file path if available).
2. Review ALL references returned.
3. Update symbol at definition location.
4. Update symbol at ALL reference locations.

Incorrect:

- Using plain `grep` to find usages.
- Manually inspecting a few files.
- Assuming you know all usages.

### Changing a Function Signature

Correct:

1. Call "symbol info" to locate function definition.
2. Call "call hierarchy (incoming)" to find all callers.
3. Call "find references" to catch any additional references (function pointers, etc.).
4. Update function definition.
5. Update ALL call sites with new signature.

Incorrect:

- Changing function without finding callers.
- Only updating visible call sites.
- Using text search to find calls.

### Understanding Unfamiliar Code

Correct:

1. Call "symbol info" on key types/functions.
2. Call "call hierarchy (outgoing)" to understand what function does.
3. Call "call hierarchy (incoming)" to understand where function is used.

Incorrect:

- Reading code manually without tool assistance.
- Making assumptions about symbol meanings.
- Skipping hierarchy analysis.

### Analyzing Function Dependencies

Correct:

1. Call hierarchy outgoing to see what function calls.
2. Call hierarchy incoming to see what calls function.
3. Use this to understand code flow and dependencies.

Incorrect:

- Manually reading through function body.
- Guessing at call patterns.

## Tool Selection Decision Tree

- Find where a symbol is used/called/referenced? -> "find references"
- Changing function signature or analyzing function calls? -> "call hierarchy"
  - Finding callers? -> incoming
  - Finding what it calls? -> outgoing
- Find a definition or understand a type? -> "symbol info" / hover
- None of the above? -> may not need language-server tool

## DO and DO NOT

DO:

- Call "find references" for ANY symbol usage search.
- Call "call hierarchy" before function signature changes.
- Use `Read` to find line numbers before specifying them.
- Provide absolute file paths when available.
- Trust tool results over manual inspection.
- Use minimal parameters first, add more if needed.
- Remember line numbers are 1-based.

DO NOT:

- Use plain `grep` or `Read` to find symbol usages when language server is available.
- Manually inspect code to find references.
- Guess line numbers.
- Assume symbol uniqueness without checking.
- Skip tool usage to save time.
- Use 0-based line numbers.
- Batch multiple unrelated symbol operations.
- Make changes without finding all affected locations.

## Performance and Best Practices

- Call tools in parallel when analyzing multiple independent symbols.
- Use file paths to speed up symbol resolution.
- Empty results are valid: "no references" means symbol has none.
- Multiple results are common: C++ has overloading, templates, namespaces.

## Integration with Other Tools

### When to use `Read`

- ONLY for finding line numbers before calling language-server tools.
- ONLY for reading implementation details after locating symbols.
- NEVER for finding symbol usages.

### When to use `fff-grep` / `rg`

- Finding string literals or comments.
- Searching non-C++ files.
- Pattern matching in configuration files.
- NEVER for finding C++ symbol usages.

## Summary

Golden rule: when working with C++ code, think "tool first, manual inspection later."

1. **Symbol usages?** -> find references
2. **Function calls?** -> call hierarchy
3. **Symbol definition?** -> symbol info / hover

These are your primary interface to C++ code understanding. Use them liberally.
