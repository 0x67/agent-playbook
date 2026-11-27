---
name: migrations
description: >
  Rules for changes that running code or other teams still depend on:
  database schema migrations (adding, renaming, or dropping a column, table,
  index, or constraint), backfills and data fixes on large tables, API
  versioning and deprecation, breaking changes for external or partner
  callers, and event or message schema changes (Protocol Buffers, Avro, JSON
  Schema). Use when writing or reviewing a migration file, an ALTER TABLE, a
  backfill script, a change to an API response or request that others call,
  or a message format change, above all before a deploy. Covers expand and
  contract, rolling deploys where old and new code run together, locks on
  large tables, and where the AGENTS.md rule against backwards compatibility
  stops; loads alongside the language skill.
---

# Migrations skill

Inside the workspace, AGENTS.md drops backwards compatibility: rename, then fix every call site. During a rolling deploy, old and new code read the same database, and partners, other teams' services, and queued messages keep using the old format after the change merges. This skill covers changes that cross that line.

## Routing table (mandatory)

Read matching reference BEFORE designing or writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| schema migrations, renames, drops, constraints, indexes on large tables, backfills, API versioning and deprecation, event and message schema changes, data stored by old versions | `references/expand-contract.md` |

## Before writing

1. Read the repo's migration tool and history (`migrations/`, Flyway, Liquibase, Alembic, `sqlx migrate`, Atlas, Prisma) and follow its conventions, including whether it writes down migrations.
2. Find out how the deploy runs: does a rolling deploy run old and new code at once, and do migrations run before or after the new code starts?
3. List who reads or writes the thing being changed: running instances, other services, partner APIs, queues holding old messages, stored JSON or files. Each one needs to keep working at every step.
4. Check the table sizes and the database version before choosing a locking strategy.

## Core rules

- Expand, migrate, contract: add the new form, write both, backfill, switch reads, then remove the old form in a later release.
- A rename is add, copy, switch, drop. `RENAME COLUMN`, `DROP`, or a type change while old code still runs breaks it.
- Large tables get operations that avoid long locks and rewrites, a `lock_timeout`, and batched backfills outside the migration transaction.
- Destructive steps need the user's go-ahead (AGENTS.md), a backup, and a way back.
- An API or message format that others consume changes additively. Release a breaking change as a new version with a deprecation notice and an agreed removal date.
- Readers tolerate unknown fields and enum values; data written by old versions still parses.

## Review checklist

Flag in a diff:

- `RENAME COLUMN`, `DROP COLUMN`, or a narrowing type change in the same release as the code that stops using the old column.
- An index built without `CONCURRENTLY`, or a `NOT NULL` or foreign key added in one step, on a large table.
- Backfills written as one `UPDATE` over the whole table, run inside the migration transaction, or unsafe to rerun.
- Removing, renaming, retyping, or requiring a field in an API or event that other teams consume, with no new version or deprecation notice.
- A Protocol Buffers field number reused or changed; a removed field not marked `reserved`.
- A migration with no `lock_timeout` on a busy table.

## Tool preference

- Every reader of a column, field, or message type: the `codebase-memory` graph or `LSP` references where connected; fff MCP tools for the column and field names in SQL, JSON, and config, which a language server does not see.
- Global rules still apply: Code Simplicity Discipline, Useless Test Ban, and the destructive database command rule in Supply Chain and Outward Actions. Ledger data: skill `money`. Status changes and the outbox: skill `services`.
