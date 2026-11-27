# Data and API Changes

Loaded via `migrations` SKILL.md routing table. Sources: Refactoring Databases, Scott Ambler and Pramod Sadalage; Parallel Change, Danilo Sato, martinfowler.com; PostgreSQL docs (`ALTER TABLE` locking, `CREATE INDEX CONCURRENTLY`, `NOT VALID` constraints); Protocol Buffers docs (updating a message type); Semantic Versioning 2.0.0; RFC 9745 (`Deprecation` header); RFC 8594 (`Sunset` header).

AGENTS.md drops backwards compatibility inside the workspace: rename, then fix every call site. That rule ends where code outside the workspace or an older running version still reads or writes the thing being changed: the database schema during a rolling deploy, a public or partner API, a message format other services consume, and data that old versions stored. Changes there go through the steps below.

## Schema migrations: expand and contract

1. Expand: add the new column, table, or index in a form old code ignores (nullable, or with a default).
2. Deploy code that writes both the old and the new columns and still reads the old ones.
3. Backfill existing rows (below).
4. Switch reads to the new columns.
5. Contract: stop writing the old columns, then drop them in a later release, once no running version uses them.

- Each step is its own migration and deploy. A rename is add, copy, switch, drop; `RENAME COLUMN` while old code still runs breaks every instance that has not restarted yet.
- Migrations run before the code that needs them, so the code deployed before the contract step works with both schemas.
- On a large table, use operations that avoid a long lock or a rewrite. In PostgreSQL: `CREATE INDEX CONCURRENTLY`; a new constraint added as `NOT VALID` and then checked with `VALIDATE CONSTRAINT`; for `NOT NULL`, a validated `CHECK (col IS NOT NULL)` first, which `SET NOT NULL` then uses to skip the table scan (PostgreSQL 12+). Set a `lock_timeout` on migrations so a blocked one fails instead of queuing every query behind it.
- A migration that destroys data (`DROP`, a type change that loses precision) needs the user's go-ahead (AGENTS.md), a backup, and a way back.
- Follow the repo on down migrations; many teams only roll forward.

## Backfills

- Run in batches by primary key range, outside the migration transaction, with a pause between batches.
- Make each batch safe to rerun (`WHERE new_col IS NULL`), and record the last key so a stopped backfill resumes where it stopped.
- Try it on a copy of production-sized data first, log progress, and compare counts when it finishes.
- A backfill never rewrites posted ledger entries. It adds derived data, or a correction goes through reversing entries (skill `money`).

## APIs other people call

- Additive changes are compatible: a new optional field, a new endpoint, a new enum value when clients were told to ignore unknown ones.
- These break callers: removing or renaming a field, changing its type or meaning, making an optional field required, tightening validation, changing an error code.
- Release a breaking change as a new version next to the old one (`/v2`, a versioned media type, or a new field), with a deprecation notice (the `Deprecation` header, RFC 9745, and `Sunset`, RFC 8594) and a removal date agreed with the callers.
- Clients read tolerantly: unknown fields are ignored, and an unknown enum value is a handled case.
- Libraries published for others follow Semantic Versioning; the Rust skill's `references/api-design.md` covers crates.

## Events and messages

- During a rollout, old and new producers and consumers run at once, and queues still hold messages written by the old version. Each version must read what the other writes.
- Protocol Buffers: never reuse or change a field number; mark removed numbers and names `reserved`. With Avro or JSON Schema and a schema registry, check compatibility in CI.
- An event payload states its schema version when its fields can change.

## Stored data

- Data that old code wrote (JSON columns, cached blobs, files, queued jobs) still has to parse after the change, unless a migration rewrites it first.
