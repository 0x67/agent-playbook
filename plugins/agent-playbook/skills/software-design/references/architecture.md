# Architecture

Loaded via `software-design` SKILL.md routing table. Sources: Clean Architecture, Robert C. Martin; Alistair Cockburn's hexagonal architecture article; Jeffrey Palermo on onion architecture; Domain-Driven Design, Eric Evans; Implementing Domain-Driven Design, Vaughn Vernon; Patterns of Enterprise Application Architecture and the CQRS, Event Sourcing, Anemic Domain Model, and MonolithFirst articles, Martin Fowler; Building Microservices, Sam Newman.

## Ground rules

- Follow the repo's existing architecture, even where you would pick another; read how one recent feature was built (and `lat.md/`) first.
- A new style, layer, service, or module boundary needs the user's agreement. Propose it with its cost, outside a feature change.
- One style applied consistently beats two half applied.
- Structure answers a pressure that exists now: team count, domain rules, deploy cadence, load.

## SOLID, read practically

| Principle | Practical reading | Overused when |
|---|---|---|
| Single responsibility | a module answers to one group of people who request changes (Martin: one actor) | every class holds one method; a feature spans twelve files |
| Open/closed | adding a variant does not mean editing unrelated code | plugin points and strategies for variants nobody asked for |
| Liskov substitution | a subtype works wherever its parent does: accepts at least as much, promises at least as much, throws nothing new | seldom; inheritance for reuse is the failure (`Stack extends Vector`) |
| Interface segregation | callers depend only on methods they use; small role interfaces declared by the consumer | an interface per method, one caller |
| Dependency inversion | policy does not import mechanism; the domain owns the abstraction it needs | an interface per class; a DI container for three objects |

### Where SOLID meets Code Simplicity Discipline

AGENTS.md bans a trait for one implementation and indirection "for later". So:

- Ports and dependency inversion: an interface exists only when a second implementation exists now. A fake that tests actually use counts. A planned second backend does not, nor do tests that hit a real database through the concrete adapter. Until then the use case calls the concrete adapter and the domain stays free of I/O, so it needs no port and imports nothing outward. Extract the interface in the consumer's module when the second implementation lands.
- Open/closed: no extension point before the second variant. For a closed set, a sum type with exhaustive matching (Rust `enum`, Java and Kotlin `sealed`, TypeScript discriminated union) beats an open interface: a new case makes the compiler list every site to update.
- Single responsibility: split on mixed concerns, never on line count (Code Growth Discipline).
- Dependency injection is passing dependencies through constructors or parameters, concrete classes included; a container only where the repo has one.

## Styles

| Style | Use when | Cost | Signals it is wrong |
|---|---|---|---|
| Layered | CRUD, forms over data, small team | features cut through every layer; rules drift into controllers or SQL | layers that only forward calls; a lower layer importing an upper one |
| MVC, MVP, MVVM | the web or UI framework picks one | the controller or view model collects every rule | rules in controllers, views, templates |
| Hexagonal | real domain rules; several drivers or backends | an adapter and mapping per boundary | one-implementation ports everywhere; domain importing a framework |
| Clean / onion | long-lived domain; hexagonal with more named rings | the most types and mapping | a new column touches six mappers in a CRUD app |
| Vertical slices | many independent features, little shared logic | duplication across slices | slices calling each other; one rule copied into five slices |
| CQRS | reads differ from writes in shape or load | two models; separate stores add sync and eventual consistency | identical read and write models; CRUD behind a command bus |
| Event sourcing | history is the product (ledgers, audit) | event versioning, projection rebuilds, erasure in an append-only log | adopted only for an audit trail a history table would give |
| Event-driven messaging | consumers may lag; the producer should not know them | at-least-once delivery, idempotency, ordering, tracing across hops | request/reply over a queue; event chains hiding a workflow |
| Modular monolith | one deployable, several teams or bounded contexts | boundary tooling (ArchUnit, Spring Modulith) | modules reading each other's tables or internals |
| Microservices | teams need independent deploys; parts scale or fail differently | network failure, sagas, observability, contract versioning | lockstep deploys; a shared database; more services than teams |

## Hexagonal in practice

Cockburn: the application meets the outside only through ports; each adapter connects one port to one technology.

- Driving (primary) side: what the application offers. The driving port is the use-case API, usually a plain class (`OrderService.placeOrder`) with no interface; HTTP handlers, consumers, CLIs, and tests drive it.
- Driven (secondary) side: what the application needs (storage, payment gateway, clock, publisher), implemented by driven adapters such as Postgres or a Kafka producer.
- The domain sits in the center and imports no framework, driver, HTTP, or serialization types.
- Use cases load, call the domain, save, publish, and own the transaction. Adapters map payloads and rows, so SDK types stay out of the domain.

Layout: `orders/domain` (pure rules), `orders/app` (use cases, ports), `orders/adapters/{http,postgres}`.

```go
// package app: declared by its consumer; a fake backs the use-case tests
type Orders interface {
	ByID(ctx context.Context, id domain.OrderID) (domain.Order, error)
	Save(ctx context.Context, o domain.Order) error
}
```

- Test use cases through the driving port, fakes behind driven ports. Assert on return values, fake state, and published events; call-count-only asserts are banned (Useless Test Ban).
- One shared contract-test helper runs against the fake and the real adapter so the fake cannot drift.

## MVC in web frameworks

- Thin controllers: parse the request into typed input, call one use case, map the result or error to a response. No rules, no transactions.
- Application services own use cases and transaction boundaries; rules live on domain types or in domain services.
- Views and templates only render: no queries, no rules.
- ORM entities map data, unless the repo chose active record (Rails, Laravel Eloquent, Django models): then model methods hold rules about their own row, and a rule spanning models moves to a service.
- MVP and MVVM: the presenter or view model holds screen state, calls use cases, owns no rules, and is tested without the UI.

## DDD tactical patterns

| Pattern | What it is | Rules |
|---|---|---|
| Entity | identity that persists while attributes change (`Order`) | equality by ID; state changes through methods that keep invariants |
| Value object | defined by its values, immutable (`Money`, `DateRange`) | equality by value; validated in the constructor |
| Aggregate | entities and values under one root that guards invariants; the consistency boundary | one aggregate per transaction; reference others by ID; keep it small (Vernon); cross-aggregate consistency is eventual |
| Repository | collection-like access to whole aggregates | one per aggregate root, never per table |
| Domain service | rule spanning aggregates or owned by none | stateless, no I/O, named in domain words |
| Domain event | fact the domain records (`OrderPlaced`) | past tense; raised by the aggregate; published after commit (transactional outbox) |

Tactical DDD is overkill for CRUD, reporting, and rules that fit in validation and constraints. Strategic DDD is cheap anywhere: a shared vocabulary (`naming.md`) and bounded contexts, each with its own model.

## Choosing a style

Team size, domain complexity, and change rate decide. Conway's law: structure follows team communication; one team seldom gains from more deployables than it can run.

| Situation | Start with | Revisit when |
|---|---|---|
| one small team, thin rules, fast change | layered or the framework's MVC, by feature | rules pile up in controllers or SQL |
| rich rules, long-lived domain, several drivers or backends | hexagonal around a pure domain; DDD where invariants are nontrivial | adapters outnumber rules |
| many independent features | vertical slices | slices copy one rule |
| several teams, one product | modular monolith with enforced boundaries | a module needs its own deploys or scaling |
| a module with proven boundaries blocks other teams' releases | extract it as a service (MonolithFirst) | services deploy together |
| reads dominate and differ from writes | a separate query path on the same database | reads need their own store |
| history is a requirement | event sourcing for that bounded context only | projections cost more than the history earns |

## Anti-patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| God class | a class every feature edits | split by use case or concern |
| Anemic domain where rules matter (Fowler) | entities are field bags; services hold the rules | move each rule onto the type that owns the data |
| Distributed monolith | lockstep deploys, shared domain library, synchronous call chains | redraw boundaries around data ownership, or merge |
| Shared database between services | two services write the same tables | one owner per table; others use its API or events |
| Speculative generality (Fowler) | one-implementation interfaces, unused hooks | delete; extract when the second case arrives |
| Layer for the sake of layers | services that only forward; mapping between identical types | collapse the layer |
| Circular dependencies | modules import each other | move shared types down, merge, or put an interface at the consumer |
