#!/bin/sh
set -e
git init -q -b main
git config user.email eval@example.com
git config user.name eval
mkdir -p shop
: > shop/__init__.py

cat > shop/order.py <<'X'
from dataclasses import dataclass, field


@dataclass
class Item:
    name: str
    qty: int
    price: float


@dataclass
class Order:
    items: list = field(default_factory=list)
    total: float = 0.0
    currency: str = "USD"
X

cat > shop/receipt.py <<'X'
def email_receipt(order):
    lines = [f"{item.name:<20}{item.qty:>3} x {item.price:>8.2f}" for item in order.items]
    return "\n".join(lines + [f"{'Total':<20}{order.total:>15.2f}"])


def print_receipt(order):
    lines = [f"{item.name:<20}{item.qty:>3} x {item.price:>8.2f}" for item in order.items]
    return "\n".join(lines + [f"{'Total':<20}{order.total:>15.2f}"])


def sms_receipt(order):
    lines = [f"{item.name:<20}{item.qty:>3} x {item.price:>8.2f}" for item in order.items]
    return "\n".join(lines + [f"{'Total':<20}{order.total:>15.2f}"])
X

git add -A
git commit -qm "feat(shop): add email, print, and SMS receipts"
