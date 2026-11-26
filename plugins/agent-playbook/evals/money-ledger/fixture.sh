#!/bin/sh
set -e
cat > wallet.py <<'X'
FEE_RATE = 0.015
APP_SCALE = 4   # settlement amounts are stored as integers with 4 decimal places
BANK_SCALE = 2  # the bank API takes cents


def fee_for(amount):
    return round(amount * FEE_RATE, 2)


def withdraw(db, account_id, amount):
    balance = db.execute(
        "select balance from accounts where id = ?", (account_id,)
    ).fetchone()[0]
    if balance < amount:
        raise ValueError("insufficient funds")
    fee = fee_for(amount)
    db.execute(
        "update accounts set balance = ? where id = ?",
        (balance - amount - fee, account_id),
    )
    db.execute("update accounts set balance = balance + ? where id = 'fees'", (fee,))
    db.commit()


def correct_fee(db, entry_id, new_fee):
    db.execute("update ledger_entries set amount = ? where id = ?", (new_fee, entry_id))
    db.commit()


def split_refund(amount, parts):
    return [round(amount / parts, 2)] * parts


def send_payout(bank, order):
    amount = order["settlement_minor"] // 10 ** (APP_SCALE - BANK_SCALE)
    bank.pay(order["iban"], amount, key=order["payout_key"])


def resend_failed_payout(bank, order):
    bank.pay(order["iban"], order["settlement_minor"], key=order["payout_key"])
X
