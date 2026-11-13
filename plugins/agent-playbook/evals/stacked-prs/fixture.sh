#!/bin/sh
set -e
git init -q -b main
git config user.email eval@example.com
git config user.name eval
mkdir -p orders cli tests

cat > orders/service.py <<'X'
class OrderService:
    def __init__(self, repo):
        self.repo = repo

    def total(self, order):
        subtotal = sum(line.price * line.qty for line in order.lines)
        tax = round(subtotal * 0.08, 2)
        return subtotal + tax
X
git add -A
git commit -qm "feat(orders): add order service"

git switch -qc feat/orders

cat > orders/pricing.py <<'X'
TAX_RATE = 0.08


def subtotal(lines):
    return sum(line.price * line.qty for line in lines)


def tax(amount):
    return round(amount * TAX_RATE, 2)
X

cat > orders/service.py <<'X'
from orders import discounts, pricing


class OrderService:
    def __init__(self, repo):
        self.repo = repo

    def total(self, order, code=None):
        amount = pricing.subtotal(order.lines)
        if code:
            amount -= discounts.amount_off(code, amount)
        return amount + pricing.tax(amount)
X

{
    echo 'PERCENT_OFF = {'
    for i in $(seq 1 120); do printf '    "SAVE%03d": %d,\n' "$i" $((i % 40 + 5)); done
    echo '}'
    echo
    echo
    echo 'def amount_off(code, amount):'
    echo '    percent = PERCENT_OFF.get(code)'
    echo '    if percent is None:'
    echo '        raise ValueError(f"unknown discount code {code}")'
    echo '    return round(amount * percent / 100, 2)'
} > orders/discounts.py

{
    echo 'import pytest'
    echo
    echo 'from orders import discounts'
    echo
    echo
    echo '@pytest.mark.parametrize("code,amount,expected", ['
    for i in $(seq 1 120); do printf '    ("SAVE%03d", 100.0, %d.0),\n' "$i" $((i % 40 + 5)); done
    echo '])'
    echo 'def test_amount_off(code, amount, expected):'
    echo '    assert discounts.amount_off(code, amount) == expected'
    echo
    echo
    echo 'def test_unknown_code():'
    echo '    with pytest.raises(ValueError):'
    echo '        discounts.amount_off("NOPE", 10.0)'
} > tests/test_discounts.py

{
    echo 'import argparse'
    echo
    echo 'from orders.service import OrderService'
    echo
    echo
    echo 'def main(argv=None):'
    echo '    parser = argparse.ArgumentParser(prog="checkout")'
    echo '    parser.add_argument("order_id")'
    echo '    parser.add_argument("--code")'
    echo '    args = parser.parse_args(argv)'
    echo '    service = OrderService(repo=None)'
    echo '    order = service.repo.get(args.order_id)'
    echo '    print(service.total(order, code=args.code))'
    for i in $(seq 1 60); do
        echo
        echo
        printf 'def render_line_%d(line):\n' "$i"
        printf '    return f"{line.sku:<12} {line.qty:>3} x {line.price:>8.2f} (col %d)"\n' "$i"
    done
} > cli/checkout.py

git add -A
git commit -qm "feat(orders): add discount codes and checkout command"
