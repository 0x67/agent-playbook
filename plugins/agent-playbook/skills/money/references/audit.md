# Audit Trails

Loaded via `money` SKILL.md routing table. Sources: PostgreSQL docs (`SET LOCAL`, `current_setting`, triggers); SQL Server and MariaDB system-versioned temporal table docs; Debezium docs.

Companies record audit trails in different ways, and their auditors, regulators, and finance teams set different requirements. This page fixes only what has to hold under any mechanism. The mechanism itself is the repo's or the user's choice.

## Find the existing mechanism

Search before adding anything:

- an `audit` table, `*_history` or `*_versions` tables, or triggers that write to them;
- CDC configuration (Debezium, a stream from the database log);
- system-versioned temporal tables;
- an event store;
- an audit library or middleware (Hibernate Envers, `paper_trail`, `django-simple-history`).

Follow what you find, including its gaps, and report a gap to the user instead of building a second mechanism next to it.

## When there is none

Stop and ask the user. The choice lasts for years and is costly to change (Bugs and Design Friction in AGENTS.md).

| Option | Records | Cost |
|---|---|---|
| audit table written by the app in the same transaction | changes made through the app, with the actor and reason the app knows | misses writes made directly in the database or by other services |
| database triggers into history tables | every write to the table | knows only the database role unless the app sets the actor per transaction (PostgreSQL `SET LOCAL app.user_id = '...'`, read with `current_setting`); ties the trail to one database |
| system-versioned temporal tables (SQL Server, MariaDB; PostgreSQL needs triggers or an extension) | every row version with the time range it was current | the same actor gap as triggers |
| CDC from the database log into an append-only store | every committed change, outside the app | more infrastructure and some lag; the actor has to be a column in the row |
| event sourcing | the history is the data itself | only when history is the product (skill `software-design`, `references/architecture.md`) |

## What holds under any mechanism

1. The audit record commits with the change, in the same transaction or read from the commit log. An audit write that can fail after the change commits loses records.
2. It records who (the user, plus the service or admin acting for them), when (server time in UTC), what (entity, id, and the values before and after, or a diff), and why (a reason, ticket, or request id).
3. The application can only append. Its database role has no `UPDATE` or `DELETE` on audit tables. A rule enforced only in application code is weaker than grants or triggers; which one the project uses is its decision, and the decision is written down.
4. Retention, erasure (privacy law against an append-only history), and who may read the trail come from company policy. Ask for them. Secrets, passwords, and full card numbers stay out of the before and after values.
5. Manual changes get audited too: admin tools, back-office adjustments, data fixes run by hand, and changes to configuration, rates, and limits.

## Ledger and audit

The ledger already records how each balance changed: postings never change, and corrections are reversals (`ledger.md`). The audit trail covers who did what around it: manual adjustments, approvals, limit and rate changes, and account status changes.

Entities that matter, such as an order handed over or a payout released, get one history row per status transition with from, to, actor, time, and reason. That row is the level 3 history table in skill `services`, `references/resilience.md`.
