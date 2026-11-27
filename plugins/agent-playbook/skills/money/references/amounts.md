# Amounts

Loaded via `money` SKILL.md routing table. Sources: ISO 4217 currency codes and minor units; Patterns of Enterprise Application Architecture, Martin Fowler (Money); Java `BigDecimal` and `RoundingMode` docs; Python `decimal` docs; PostgreSQL numeric and monetary type docs.

## Representation

| Option | Use when | Watch |
|---|---|---|
| integer minor units (`int64` cents) | one fixed scale per currency; sums and comparisons | the scale lives outside the number, so the type or the name must state it |
| decimal type (Java `BigDecimal`, Python `Decimal`, C# `decimal`, Rust `rust_decimal`, Go `shopspring/decimal`) | rates, ratios, division, or several scales in one system | every division needs an explicit scale and rounding mode; Java `BigDecimal.equals` compares scale (`2.0` is not `2.00`) |
| binary float (`float`, `double`, a JavaScript `number` with fractions) | never for amounts | `0.1 + 0.2` is not `0.3` |

- Use the repo's existing money type. Without one, a small value type (`Money`, `software-design` `references/types.md`) wraps the amount and its currency, and every operation goes through it.
- Database: `NUMERIC(p, s)` or `DECIMAL(p, s)` with the scale the amount needs, or `BIGINT` minor units with the scale in the column name or comment. Never `FLOAT`, `REAL`, or `DOUBLE PRECISION`. Avoid PostgreSQL `money`: its fraction digits and output format follow the database's `lc_monetary` setting.
- JSON and other wire formats: a string (`"12.30"`) or integer minor units, always with the currency. A JSON number with a fraction is read into a binary float by many parsers, JavaScript's `JSON.parse` among them.
- A bare integer amount names its scale: `amount_cents`, `price_minor`, `fee_bps`.

## Currency and scale

- An amount includes its currency. Adding or comparing two currencies is an error, raised by the money type.
- The scale of a currency comes from ISO 4217 minor units (JPY 0, USD 2, KWD 3, BHD 3) or from the provider's API, never a hard-coded 2. Assets outside ISO 4217 (tokens, metals by weight) have a scale the product defines; store it with the instrument.
- Systems that exchange amounts often disagree on scale: the app keeps 4 decimals, the bank takes 2, a token uses 7. Convert at each boundary in one named function (`to_bank_minor`), and let the type say which scale an amount is in. A bare integer handed from one scale to another is off by a power of ten.
- An FX conversion stores the rate, its source, the time it was quoted, and the direction. The converted amount keeps the rate's precision until the final rounding.

## Rounding

- The rounding mode (`HALF_EVEN`, `HALF_UP`, down), the points where rounding happens, and the direction are business rules from the contract, prospectus, tariff, or regulator. Ask for them; never pick one yourself.
- Round at those points only. Intermediate results keep full precision, so the order of operations does not change the answer.
- Direction can depend on the side. A rule might round what the business receives up and what it pays out down. Write the rule once, next to the operation that uses it.
- Every division states its scale and mode. Java `BigDecimal.divide(divisor)` without them throws `ArithmeticException` on a result like 1 / 3.

## Rates, fees, and accruals

- Rates and ratios need more precision than amounts. Store them as decimals, or as integer basis points with the unit in the name (`fee_bps`).
- Rates and other inputs are effective-dated (`valid_from`), or stored with the transaction they priced, so recomputing a past period uses the rate that applied then.
- A daily accrual is the base amount times the annual rate divided by the day-count basis. The basis (actual/365, actual/360, 30/360) and when the accrued amount is rounded come from the governing documents; ask.

## Splitting an amount

Rounding each share on its own loses or invents minor units: 100.00 split three ways rounds to 33.33 each, which adds up to 99.99. Hand out the remainder instead (Fowler's Money allocation):

```python
def allocate(total_minor: int, weights: list[int]) -> list[int]:
    """Split a non-negative total by weight so the shares add up to it."""
    whole = sum(weights)
    shares = [total_minor * w // whole for w in weights]

    leftover = total_minor - sum(shares)
    by_remainder = sorted(
        range(len(weights)),
        key=lambda i: total_minor * weights[i] % whole,
        reverse=True,
    )
    for i in by_remainder[:leftover]:
        shares[i] += 1

    return shares
```

`allocate(10000, [1, 1, 1])` returns `[3334, 3333, 3333]`. Which share takes the extra unit when remainders tie (the first, the largest holder, a fixed order) is a business rule; ask when the repo does not say.

## Testing

- Property tests: allocated shares add up to the total; converting to another scale and back loses at most the documented rounding; adding then subtracting an amount returns the original.
- Amounts at the edges: zero, one minor unit, the largest supported amount, and currencies with 0 and 3 decimals.
- Assert each path that produces the same outbound amount (normal, retry, resume, fallback) against one expected value.
