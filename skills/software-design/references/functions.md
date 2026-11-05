# Functions and Modules

Loaded via `software-design` SKILL.md routing table. Sources: A Philosophy of Software Design, John Ousterhout; Refactoring, Martin Fowler; Object-Oriented Software Construction, Bertrand Meyer; On the Criteria To Be Used in Decomposing Systems into Modules, David Parnas; Structured Design, Edward Yourdon and Larry Constantine; Gary Bernhardt's Boundaries talk; Parse, Don't Validate, Alexis King; The Wrong Abstraction, Sandi Metz; The Pragmatic Programmer, Andrew Hunt and David Thomas.

## Function size: signals

Line count alone decides nothing. A flat 60-line `match` over one enum is one concern. These signals mean a function does more than one thing:

| Signal | Usually means | Move |
|---|---|---|
| needs section comments (`// validate`, `// persist`) | several concerns | extract each section into a named function (Code Simplicity Discipline) |
| nesting deeper than about 3 levels | edge cases tangled with the main path | guard clauses; extract the loop body; match on a type |
| more than about 3 or 4 parameters | a missing type | a parameter object or an existing value type (`DateRange`, `Address`, `Money`) |
| boolean flag parameter | two functions in one; banned as slop | split (`renderDraft`, `renderFinal`); an enum when the mode is data from outside |
| the same values passed together through layers | a data clump (Fowler) | make it a type |
| name needs `And`, or only fits `handle`, `process`, `manage` | two jobs, or no clear job | split until each part has an honest name |
| unit test needs five fakes | I/O mixed into logic | pull the logic into a pure function |

## One level of abstraction

A function either coordinates steps or does one low-level step. Mixing both makes the reader change altitude every line.

```ts
async function placeOrder(cmd: PlaceOrder): Promise<OrderId> {
  const cart = await carts.load(cmd.cartId);
  const order = Order.fromCart(cart, clock.now());
  await orders.save(order);
  await events.publish(orderPlaced(order));
  return order.id;
}
```

Pricing math, SQL, and serialization live in the functions it calls.

## Guard clauses

Handle bad input and edge cases first and return. The main path then reads at one indent.

```go
func (s *Service) Ship(ctx context.Context, id OrderID) error {
	o, err := s.orders.ByID(ctx, id)
	if err != nil {
		return fmt.Errorf("load order %s: %w", id, err)
	}
	if o.Status != StatusPaid {
		return ErrNotPaid
	}
	return s.carrier.Book(ctx, o)
}
```

## Command-query separation

- A query returns a value and changes nothing observable. A command changes state and returns nothing, or only what the caller needs next: an ID or a result type (Meyer).
- Combine the two only where the combination is the point and the name says so: `pop`, `getAndIncrement`, `putIfAbsent`.
- A query that fills a private cache is fine when callers cannot observe the write and it is thread-safe.

## Pure core, I/O at the edges

- Business rules are pure functions over values: inputs in, decision out. A thin shell loads data, calls the core, and writes the result (Bernhardt: functional core, imperative shell).
- Time, randomness, and generated IDs come in as arguments, so the core is deterministic and tests need no fakes.

```rust
pub fn late_fee(invoice: &Invoice, today: Date) -> Money {
    if invoice.is_paid() || today <= invoice.due_date() {
        return Money::zero(invoice.currency());
    }
    invoice.amount().percent(2)
}
```

- Parse at the boundary: turn raw input into typed values once (`EmailAddress::parse`, `OrderId.from(raw)`), then pass the types inward. Re-validating already-typed input is slop under Code Simplicity Discipline.

## Side effects in names and signatures

- The name says it writes or sends: `saveOrder`, `sendReceipt`, `publishOrderPlaced`.
- The signature shows what the language can express: `context.Context` first in Go, `suspend` or `async`, `Result` or `throws` for failure, `&mut self` in Rust, a repository or `Clock` parameter where a global would hide the dependency.
- Constructors assign and validate. No I/O, no thread start, no handing out `this`.
- No hidden mutation of arguments. Return a new value, or name the mutation (`sortInPlace`, a `&mut` parameter).

## When not to extract

- A one-use wrapper that only forwards (`fun save(o: Order) = repo.save(o)`) adds a hop and hides nothing. Inline it.
- Three lines used once, extracted only to shorten a function, make the reader jump. Extract when the piece names a domain concept, is reused, or isolates a concern worth testing alone.
- A plain `match`, `if`, or iterator chain beats a stack of tiny helpers (Code Simplicity Discipline).

## Deep modules

Ousterhout: a module is worth the functionality it hides minus the interface it makes callers learn.

- Deep: small interface, much behind it. A blob store with `put`, `get`, `delete` that hides retries, sharding, and encryption.
- Shallow: interface about as complex as the body. Getter and setter bags, pass-through methods that repeat a lower layer's signature, a class per three-line step ("classitis").
- Hide decisions likely to change: storage format, wire protocol, retry policy, third-party SDK types (Parnas: information hiding). Two modules that both know one file format leak it; give it one owner.
- Pull complexity down. A module that handles defaults, retries, and partial reads itself spares every caller from doing it.

## Cohesion and coupling

- High cohesion: what changes together lives together. A feature change that touches eight folders is a cohesion problem.
- Low coupling: modules meet through small public APIs. Never through internals, shared mutable state, or each other's tables.
- Temporal coupling (`init()` before `use()`) gets designed out: a constructor that leaves the object ready, or a type that only exists after setup.
- Dependencies point toward the domain. Transport and persistence import the domain; the domain imports neither. Volatile, concrete code (UI, frameworks, SDKs) depends on stable code, never the reverse.
- No import cycles. A cycle means a wrong boundary: move the shared type down into a module both use, merge the two modules, or declare an interface at the consumer when it meets the port rule in `architecture.md`. Enforce with what the stack has: Go and Cargo reject package and crate cycles; ArchUnit or Spring Modulith tests on the JVM; dependency-cruiser or eslint `import/no-cycle` in TypeScript.

## Public surface

- Narrowest visibility by default: Go unexported or `internal/`, Rust private or `pub(crate)`, Java package-private, Kotlin `internal`, TypeScript unexported.
- Export what a caller needs today. Every public item is a contract someone will lean on. Helpers, mappers, and row types stay inside.

## Package by feature

```
by layer (avoid at app scale)     by feature
controllers/                      orders/     handler, use cases, store, rows
services/                         billing/
repositories/                     shipping/
models/
```

A feature change lands in one directory. Inside a large feature, layers are fine (`orders/http`, `orders/store`).

## File and module size

Code Growth Discipline (AGENTS.md) sets the thresholds; this skill adds none:

- Sketch the module layout before writing. One concern per file.
- Projected over 600 non-test LOC, or a second concern: start as a module directory with children; never "split later".
- A change that would push a file past about 800 non-test LOC, or couple it further: split first as its own commit (pure moves, external paths kept by re-exports, gates green), then implement on the clean layout.
- A cohesive single implementation block is fine at any size; the split trigger is mixed concerns.
- Test code over 40% of a file moves to a sibling test file.

## Duplication

- Rule of three (Fowler, credited to Don Roberts): live with the second copy, extract on the third, once you can see what varies.
- The wrong abstraction costs more than duplication (Metz). When a shared function grows flags and per-caller branches, inline it back into the callers and extract again from what they really share.
- Remove duplicated knowledge: a business rule, a validation, or a format spelled out twice (DRY in The Pragmatic Programmer). Code that looks alike but changes for different reasons is two things; leave it apart.
- Test doubles and fixtures live in one shared support module per crate or package (Useless Test Ban).
