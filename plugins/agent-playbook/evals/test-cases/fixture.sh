#!/bin/sh
set -e
cat > requirement.md <<'X'
# PRD-7 Buy tokens from a bank account

As a retail customer, I want to buy TER tokens from my bank account, so that I can hold gold without visiting a branch.

- The system shall quote a unit price, a fee of 0.25% of the order value, and a total, and shall lock the quote for 15 seconds.
- The minimum order shall be 5 TER. An order below the minimum shall be rejected with reason code `MIN-ORDER`.
- The system shall reject an order when the account's available balance is below the quoted total, with reason code `INSUFFICIENT-BALANCE`.
- An order confirmed after the lock expires shall be rejected with reason code `QUOTE-EXPIRED` and shall not debit the account.
- On confirmation the system shall place a hold for the quoted total, debit the account once, keyed by the order reference, and only then place the gold order.
- The customer's TER holding shall increase by the ordered quantity, and the order shall appear in transaction history as Completed.
X
