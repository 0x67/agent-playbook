# Types and Construction

Loaded via `software-design` SKILL.md routing table. Sources: Effective Java (3rd edition), Joshua Bloch, items 1, 2, 17, 18, and 19; Design Patterns, Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides; Refactoring (2nd edition), Martin Fowler; Rust API Guidelines (C-CTOR, C-BUILDER); Functional Options for Friendly APIs, Dave Cheney; Yaron Minsky on making illegal states unrepresentable; Designing with Types, Scott Wlaschin.

The language skill picks the concrete form (Java `record`, Kotlin `data class`, Go options, Rust builders). This page picks which kind of type to use and how to construct it, in every language, including those without a skill here (TypeScript, Python, C#, Swift).

## Choosing the kind of type

| Kind | Use when | Forms |
|---|---|---|
| plain data | fields with no rule tying them together: a payload, a row, parsed config | Java `record`, Kotlin `data class`, Go or Rust `struct` with public fields, C++ aggregate `struct`, TypeScript `type`, Python `@dataclass(frozen=True)` |
| value type | a value with a rule (`Money`, `EmailAddress`, `DateRange`) | the same forms, built only through a constructor or parse function that checks the rule |
| class with behavior | identity and state that change through methods that keep invariants (an entity, a connection pool) | `final class`; a Rust or Go struct with private fields and methods |
| closed set of variants | a fixed list of cases, each with its own data | Rust `enum`, Java and Kotlin `sealed interface`, TypeScript discriminated union, C++ `std::variant` |
| module functions | nothing to hold between calls | package or module functions; a Java `final class` with a private constructor only when the function belongs on no type |
| interface | a second implementation exists now | the port rule in `architecture.md` |

- Start with plain data. Add a validating constructor when a rule appears, and methods when behavior belongs with the data.
- A class with private fields, a getter and setter for each, and no rule is plain data written the long way. Use the language's data form.
- A value type cannot exist in an invalid state. It checks once, when built, and code that receives it trusts it (parse at the boundary, `functions.md`).

## Construction

Use the first row that fits.

| Need | Form | Example |
|---|---|---|
| few fields, all required | constructor or literal | `Point{X: 1, Y: 2}`, `DateRange(start, end)` |
| some fields optional, in a language with default and named arguments (Kotlin, Python, C#, Swift), a TypeScript options object, or C++20 designated initializers | defaults and named arguments | `connect(host, timeout = 5.seconds)`, `Options{.timeout = 5s}` |
| construction needs a name, can fail validation, caches, or returns a subtype | named factory | `Money.of(amount, currency)`, `Duration::from_secs(5)`, `EmailAddress.parse(raw)` returning a result |
| more than about 3 or 4 parameters | parameter object or an existing value type | `book(slot: DateRange)` over `book(startDate, startTime, endDate, endTime)` |
| many optional parts in a language without default arguments, or a build in several steps checked as a whole | builder whose `build()` reports an invalid combination | `HttpRequest.newBuilder()`, `reqwest::ClientBuilder` |
| Go, optional settings | options struct, or functional options when most callers set none | `golang` skill |
| config or input picks the implementation at runtime | factory function returning the interface | `storage.Open(cfg)` returning a local or S3 store |

- A builder needs about four or more optional parts and a language without default and named arguments. A builder for two or three fields, or one in Kotlin or Python, is slop under Code Simplicity Discipline.
- Telescoping constructors (`Pizza(size)`, `Pizza(size, cheese)`, `Pizza(size, cheese, ham)`) call for defaults, a parameter object, or a builder (Bloch, item 2).
- Construction that needs I/O (open a file, dial a connection, read config) is a named function that returns a ready object or an error: `Open`, `connect`, `load`. Constructors only assign and validate (`functions.md`).
- A factory class (`ParserFactory`) or abstract factory needs two or more products that exist now. With one product, call the constructor.
- Singleton: create one instance at startup and pass it to whatever needs it (dependency injection, `architecture.md`). A global that any code can read hides the dependency and blocks test doubles. A stateless namespace (Kotlin `object`, a module) is fine.

## Composition and inheritance

- Compose by default: hold the other object in a field and call it (Bloch, item 18).
- Inherit only from a type built and documented for extension (item 19), and only where the subtype works anywhere the parent does (Liskov, `architecture.md`).
- Inheriting to reuse a few methods puts every parent method on the child. A `ShipmentStore extends HashMap` offers `clear()` and `putAll()` to every caller. Hold the map in a field.
- A base class is for state or a template method that its subclasses share. Unrelated types that share behavior use an interface or trait with default methods, or a plain function over the data.
- Merge a base class that has one subclass into it; that is speculative generality (Fowler).

## Mutability

- Fields are immutable by default (`final`, `val`, `readonly`, no `mut`). Operations return a new value (Bloch, item 17).
- Only objects whose identity follows changing state (an entity, a buffer, a cache) hold mutable state, and it changes only through methods that keep the invariants.
- A value type copies the collections it receives, or wraps them read-only, so callers cannot change it afterwards (Java `List.copyOf`).
- Immutable values cross threads without locks; the language skill's concurrency page covers the rest.

## State and lifecycle

A thing with a lifecycle (an order, an invoice, a job) is a state machine whether or not the code calls it one. Pick the lowest level that covers the pressure.

| Level | Shape | Use when |
|---|---|---|
| 0 | a plain field | the value has no lifecycle |
| 1 | a status enum and one transition function that checks the allowed from and to pairs | the default for anything with a lifecycle |
| 2 | one type per state: a sum type whose variants each hold their own data, or typestate in Rust (`Order<Draft>`) | states hold different data, or a call in the wrong state should not compile |

Level 1:

```go
var allowed = map[Status][]Status{
	StatusPending: {StatusPaid, StatusCancelled},
	StatusPaid:    {StatusShipped, StatusRefunded},
}

func (o *Order) Transition(to Status) error {
	if !slices.Contains(allowed[o.Status], to) {
		return fmt.Errorf("order %s: %s to %s: %w", o.ID, o.Status, to, ErrInvalidTransition)
	}
	o.Status = to
	return nil
}
```

Level 2:

```kotlin
sealed interface Invoice {
    data class Draft(val lines: List<Line>) : Invoice
    data class Sent(val lines: List<Line>, val sentAt: Instant) : Invoice
    data class Paid(val lines: List<Line>, val sentAt: Instant, val receipt: ReceiptId) : Invoice
}

fun Invoice.Sent.markPaid(receipt: ReceiptId) = Invoice.Paid(lines, sentAt, receipt)
```

`markPaid` exists only on `Sent`, so paying a draft does not compile.

- Several booleans that together describe one lifecycle (`isSubmitted`, `isApproved`, `isRejected`) allow combinations that cannot happen. Replace them with a status (level 1).
- Nullable fields filled in only in some states (`paidAt`, `receipt`) mean the states hold different data (level 2).
- `status = X` assigned in several places scatters the allowed transitions. Route every change through the transition function.
- A state machine library or framework only where the repo already uses one, or with the user's agreement, like any new layer.
- State stored in a database with concurrent writers or retries also guards the transition in the database, with a conditional update on the current status (`WHERE status = 'pending'`) or a version column.

## Classic patterns

Every entry in Design Patterns has a plainer form. Use the pattern once the plain form stops working.

| Pattern | Plain form first | Use the pattern when |
|---|---|---|
| Strategy | pass a function; `match` over an enum for a closed set | implementations hold their own state or config and are chosen at runtime |
| Factory, abstract factory | constructor or named factory | two or more implementations exist and config or input picks one |
| Builder | constructor, defaults, parameter object | the construction table above says so |
| Singleton | one instance made at startup and passed in | never as a global |
| Observer | a direct call or a callback parameter | several subscribers the publisher must not know about |
| Decorator | a wrapping function, or the framework's middleware | stacking cross-cutting behavior (retry, cache, logging) on one interface |
| Adapter | call the library directly inside one module | a third-party API must stay out of the domain (driven adapters, `architecture.md`) |
| State | status enum and transition function (above) | per-state behavior grows until every method is a `match` on status; then one type per state |
| Template method | a function that takes the varying step as a parameter | the framework's base class is built for it |
| Visitor | exhaustive `match` over a sum type | the language has no sum types and operations grow faster than types |
| Command | a function value, or the request as plain data | undo, queueing, or a log of requests needs each request as an object |

Name types by their domain role (`ShippingRate`, `RetryPolicy`). Leave the pattern out of the name unless callers use the type as that pattern (`HttpClientBuilder` is fine); see `naming.md`.
