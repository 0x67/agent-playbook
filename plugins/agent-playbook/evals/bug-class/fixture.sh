#!/bin/sh
set -e
git init -q -b main
git config user.email eval@example.com
git config user.name eval
mkdir -p shop
: > shop/__init__.py

cat > shop/invoice.py <<'X'
def line_total(price, qty):
    """Invoice line amount in dollars."""
    return round(price * qty, 2)
X

cat > shop/refund.py <<'X'
def refund_amount(paid, fraction):
    """Partial refund in dollars."""
    return round(paid * fraction, 2)
X

cat > shop/tax.py <<'X'
def sales_tax(amount, rate):
    """Sales tax in dollars."""
    return round(amount * rate, 2)
X

cat > shop/stats.py <<'X'
def average_rating(ratings):
    """Mean star rating shown on product pages, to one decimal place."""
    avg = sum(ratings) / len(ratings)
    return round(avg, 1)
X

cat > ISSUE.md <<'X'
# Invoice line rounds half a cent down

`line_total(1.005, 1)` returns `1.0`. Finance rounds money half up to the cent, so this line should be `1.01`.
X

git add -A
git commit -qm "feat(shop): add invoice, refund, and tax amounts"
