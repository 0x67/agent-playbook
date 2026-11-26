---
name: money
description: >
  Rules for code that computes, stores, or moves money: amounts, prices,
  currencies, minor units, decimals, rounding, FX conversion, fees, interest,
  accruals, splits and allocations, balances, holds, invoices, payments,
  payouts, refunds, ledgers, double-entry, journal entries, postings,
  reversals, accounting periods, reconciliation, and audit trails. Use when
  writing or reviewing such code, choosing a money type or column, a
  rounding rule, or a ledger schema, or when a balance or payout comes out
  wrong. Loads alongside the language skill and skill services; the
  project's own money and ledger docs win where they differ.
---

# Money skill

Money bugs rarely crash. They post a wrong number that someone finds weeks later in a reconciliation report or a customer complaint. This skill lists the rules that apply in any language and any company. Rounding rules, accounting conventions, and audit requirements differ between companies; the project's documents and its finance or compliance team decide those.

## Routing table (mandatory)

Read matching reference BEFORE designing or writing code. Paths are relative to this skill's directory: `references/`.

| Task touches | Read |
|---|---|
| money types, minor units, decimals, scale, currencies, database columns and JSON for amounts, rounding, FX, rates, fees, interest, accruals, splitting an amount | `references/amounts.md` |
| ledgers, accounts, double-entry, journal entries, postings, balances, holds and reserves, overdraft checks, reversals, accounting periods, payouts and refunds, reconciliation | `references/ledger.md` |
| audit trails, history tables, who changed what, immutability of records, retention and erasure | `references/audit.md` |

Multiple matches: read all matched.

## Before writing

1. Load the language skill, and skill `services` when the code calls a bank or payment provider.
2. Read the repo's own money and ledger docs (`lat.md/`, `docs/`, the money type, the ledger schema) and follow them. Their conventions win over this skill.
3. Find where the repo states the business parameters this change depends on: rounding mode, rounding points and direction, day-count basis, which accounts may go negative, and retention. They come from a contract, prospectus, tariff, regulation, or the finance team, and when the repo does not state one, you ask the user for it rather than pick a value.

## Core rules

- No binary floating point for amounts, in code, database columns, or JSON.
- An amount includes its currency and scale. Scale changes only in one named function at each system boundary.
- Round only where the business rules say, in the mode and direction they say. Intermediate values keep full precision.
- When splitting an amount, hand out the remainder. The parts must add up to the whole.
- A transaction's postings sum to zero per instrument. Posted entries never change; a correction is a reversing entry plus a new one.
- A balance is the sum of its postings. Balance and limit checks happen inside the write, never as read, check, then write.
- Each posting transaction has a unique external id, and it commits in the same database transaction as the business state it belongs to.
- Money that leaves through a bank or provider has an instruction record, an amount check before sending, and reconciliation against the provider.
- The audit trail mechanism is the project's choice. Find it and follow it, or ask.

## Review checklist

Flag in a diff:

- `float`, `double`, or a JavaScript `number` with fractions holding an amount; a `FLOAT`, `REAL`, or `DOUBLE PRECISION` column; an amount sent as a JSON number with a fraction.
- An integer amount passed between code that uses different scales without going through a conversion function; a scale of 2 hard-coded for every currency.
- Arithmetic across two currencies; an FX conversion with no stored rate, source, and time.
- A rounding mode, rounding direction, or day-count basis chosen in code with no cited source; rounding after every step; a division with no explicit scale and mode.
- A split whose parts do not add up to the total.
- An `UPDATE` or `DELETE` on posted entries; a correction made by editing an entry.
- Transaction legs that do not sum to zero, or a write path that skips that check.
- Reading a balance, comparing it, then writing it back.
- A posting with no unique external id, or committed outside the business transaction.
- A payout or refund amount built differently on the retry, resume, or fallback path than on the normal path.
- An audit mechanism added without the user's agreement, or an audit record written after the change commits.

## Tool preference

- Every place that builds an outbound amount, converts scale, or writes a posting: the `codebase-memory` graph or `LSP` references where connected; fff MCP tools for exact text such as the scale constant or the posting function.
- Global rules still apply: Code Simplicity Discipline, Useless Test Ban, Bugs and Design Friction (a wrong amount means checking every path that builds that amount). Value types and construction: skill `software-design`. Retries, idempotency keys, and the outbox: skill `services`.
