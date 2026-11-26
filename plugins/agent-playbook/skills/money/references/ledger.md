# Ledger

Loaded via `money` SKILL.md routing table. Sources: Analysis Patterns, Martin Fowler (inventory and accounting chapter); Accounting for Developers, Modern Treasury; Books: An Immutable Double-Entry Accounting Database Service, Square Engineering blog; TigerBeetle documentation (transfers, pending and two-phase transfers).

## Model

- Account: an id, an owner, an instrument (a currency or an asset), and a type that says what the account is for and whether it may go negative.
- Transaction (journal entry): an id, an effective date, a description, a unique external id, and two or more postings.
- Posting (leg): an account, an instrument, and an amount.
- Balance: derived from the postings. A stored balance is a cache of that sum.
- Pick one sign convention and write it down: debit and credit sides with a normal balance per account type (the accounting convention), or signed amounts where a positive posting increases the balance. Code that mixes the two flips signs.

## Invariants

1. A transaction's postings sum to zero per instrument. The one function that writes transactions checks this and rejects anything else; a database constraint or trigger is a second guard where the repo wants one.
2. Posted entries never change. A correction is a reversing transaction plus a new one, both linked to the original. The application does not issue `UPDATE` or `DELETE` on postings, and its database role should not be allowed to (`audit.md`).
3. A balance equals the sum of its postings. A stored balance (a running total per posting with a version, or a cached column) is written in the same transaction as the posting, and a reconciliation job compares it with the sum.
4. Each transaction has a unique external id taken from the operation that caused it (`<kind>:<source id>:<step>`). A retry then finds the existing transaction and posts nothing new. Store the transaction id on the business row as well.
5. Postings commit in the same database transaction as the business state they belong to: the order becomes filled and its postings exist, or neither happens.

## Concurrency and limits

- Check overdrafts and limits inside the write. Options: a conditional update (`UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1`, then check the rows affected), a row lock (`SELECT ... FOR UPDATE`), or an append with a unique `(account_id, version)` that turns a concurrent writer into a conflict error instead of a lost update.
- Which account types may go negative is configured per type and tested. Clearing, suspense, or fee accounts may be allowed to; customer accounts usually are not.
- Holds: while an asynchronous operation runs, move the funds into a hold (reserve) account or record a pending transfer, so the same funds cannot be spent twice. A hold is settled, released, or expired when the operation ends, and a sweeper finds holds past their deadline.

## Time and periods

- Store the effective date (value or booking date) of each transaction next to the time it was recorded. Period reports use the effective date.
- Back-dated entries go only into open periods. After a period closes, a correction is posted in the current period with a reference to the original.
- Inputs to a computation (rates, prices, FX) are effective-dated or stored in the transaction's metadata, so recomputing it gives the same result.

## Recognition and status

- Post revenue, fees, and profit when the business operation moves to a status that cannot be undone (filled, settled, delivered). Earlier, a cancel or refund would need a reversal.
- Tie each posting to the status transition that causes it, inside the guarded transition (skill `services`, `references/resilience.md`, level 3).

## Money outside the ledger

- Payouts, refunds, and deposits sent to a bank or payment provider are instructions. The zero-sum check never sees their amounts.
- Keep a record per instruction: amount, currency, scale, idempotency key, status, and the provider's reference.
- Before sending, check the amount against its source (the order or settlement it pays) with the same function that built it on the normal path.
- Reconcile against the provider's statement or report by reference. Unmatched items and amount differences are breaks for a person to resolve; the code reports them and never adjusts balances to make them match.

## Testing

- Property tests: every generated transaction sums to zero; after any sequence of operations, each balance equals the sum of its postings; a reversal restores the balances; posting the same external id twice leaves every balance as it was.
- Concurrency: start two withdrawals together that each fit the balance alone; exactly one succeeds.
- Recovery: run the retry, resume, and fallback paths for a payout and assert they send the amount the normal path would have sent.
