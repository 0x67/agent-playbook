---
name: software-design
description: >
  Language-agnostic software design: naming, function and module size,
  modularity, and architecture. Use when naming or renaming functions,
  variables, booleans, classes, interfaces, DTOs, request and response
  payloads, entities, view models, events, commands, errors, or packages;
  on "what should I call this", "is this function too big", "too many
  parameters", "split this module", "refactor for modularity", "where should
  this logic live", or "circular dependency"; and when designing or
  reviewing a module, service, or architecture: SOLID, layered, MVC, MVP,
  MVVM, hexagonal, ports and adapters, clean or onion architecture, vertical
  slices, DDD, aggregates, CQRS, event sourcing, event-driven, modular
  monolith, microservices. Loads alongside the language skill (golang, rust,
  cpp, java, kotlin), whose idioms win where they differ. Core rules inline;
  specialist rules live in references/ and load through the routing table
  below.
---

# Software design skill

Design code a new teammate can change safely in their first week: names in the domain's words, functions that do one thing at one level, modules that hide decisions behind small interfaces, dependencies that point toward the domain, and no more architecture than current pressure demands. This skill holds the cross-language rules; the language skill holds casing, idioms, and the post-write gate.

## Routing table (mandatory)

Read matching reference BEFORE designing or writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| naming or renaming functions, variables, booleans, types, interfaces, singletons, DTOs, payloads, entities, view models, events, commands, errors, modules, test names | `references/naming.md` |
| function size, parameters, flag arguments, nesting, extraction, side effects, pure core, module depth, cohesion, coupling, dependency direction, import cycles, public surface, file size, duplication | `references/functions.md` |
| SOLID, layers, MVC/MVP/MVVM, hexagonal, ports and adapters, clean/onion, vertical slices, DDD, aggregates, CQRS, event sourcing, messaging, modular monolith, microservices, choosing or reviewing an architecture | `references/architecture.md` |

Multiple matches: read all matched. Unsure: read `naming.md` and `functions.md`.

## Before designing

1. Load the language skill for the files involved. Its naming and layout rules (casing, initialisms, getter style, where interfaces live) override the general ones here.
2. Read the repo's existing structure: top-level layout, how one recent feature was built end to end, `lat.md/` when present. Follow it. A new style, layer, service, or module boundary needs the user's agreement first.
3. Collect the domain's words from tickets, docs, the API, and existing code before naming anything new.
4. Sketch the module layout before writing (Code Growth Discipline).

## Core rules

- Names say what a thing is or does in the domain's words. One term per concept across code, API, storage, and logs.
- One concern per function and per file. Section comments, a name with `And`, or nesting past about 3 levels mean split.
- More than about 3 or 4 parameters means a missing type. Boolean flag parameters are banned.
- Business rules are pure functions over values. I/O, time, and randomness stay at the edges and come in as arguments.
- Queries change nothing; commands say in their name what they change.
- Modules are deep: small public surface, decisions hidden inside, narrowest visibility by default.
- Dependencies point toward the domain. No import cycles.
- Package by feature. No `utils`, `common`, `helpers`, or `models` dumping grounds.
- An interface (port) exists only when a second implementation exists now; a fake that tests use counts. Otherwise depend on the concrete type and extract the interface when the second one arrives. Open/closed extension points and dependency inversion follow the same rule (`references/architecture.md`).
- Duplication beats the wrong abstraction. Extract on the third copy.
- The simplest architecture that carries today's team, domain, and load; the repo's existing one first.
- Several approaches (2 to 5) still viable and the choice worth measuring: run the spec-driven approach trial (`spec-driven` skill, `trial.md`) instead of arguing from taste.

## Review checklist

Flag in a diff:

- Vague names (`Manager`, `Helper`, `Util`, `Data`, `Info`, `process`, `handle`) where a precise one exists; negative booleans; `get` on I/O or heavy work; bare numbers without a unit.
- A new synonym for an existing concept, or an old name kept as an alias after a rename.
- `I` prefix or `Impl` suffix; an interface, strategy, factory, or config knob with one implementation or one value (a fake that tests use counts as a second implementation).
- A function with section comments, nesting past about 3 levels, more than about 4 parameters, or a boolean flag argument.
- A query that writes; a side effect missing from the name or signature; I/O or clock reads inside business rules.
- Pass-through methods or layers; mapping between identical types.
- The domain importing HTTP, ORM, driver, or SDK types; a dependency pointing outward; a new import cycle.
- Business rules in controllers, views, templates, or ORM entities (outside an active record repo).
- A persistence entity used as a public request or response payload.
- A file pushed past the Code Growth Discipline thresholds, or a second concern added to a file.
- A new layer, style, service, or message queue the user did not agree to.
- One transaction changing several aggregates; a service writing another service's tables.
- An event named as a command (`SendEmailEvent`), or a command named in past tense.
- Tests named `test1` or `testX`; doubles that only assert call counts.

A Code Simplicity Discipline item in the diff is NEEDS_REVISION under AGENTS.md. Raise the rest as design findings, each with a concrete fix.

## Tool preference

- Callers, implementations, and dependency direction: the `LSP` tool (references, implementations, call hierarchy) or the `codebase-memory` graph where connected. Semble for "where does this concept live". Exact text: fff MCP tools.
- Renames: the language server's rename, then text search for strings, docs, and config it misses.
- Boundary checks: the stack's own tools (Go and Cargo cycle errors, ArchUnit, Spring Modulith, dependency-cruiser).
- Global rules still apply: Code Growth Discipline, Code Simplicity Discipline, Useless Test Ban, Project Terminology Guard, Code Comments.
