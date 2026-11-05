# Naming

Loaded via `software-design` SKILL.md routing table. Sources: A Philosophy of Software Design, John Ousterhout; Clean Code, Robert C. Martin; Domain-Driven Design, Eric Evans; Refactoring and Patterns of Enterprise Application Architecture, Martin Fowler; Rust API Guidelines.

Casing, initialisms, and getter style come from the language skill (`golang`, `rust`, `cpp`, `java`, `kotlin`). This file covers what a name says.

## General

- A name says what the thing is or does, in the domain's words. If two readers would guess different behavior from it, rename it.
- Length grows with scope: `i` in a three-line loop, full words for anything exported or package-level.
- One word per concept, one concept per word, per bounded context. Pick `customer` or `client` and use it in code, tests, API fields, tables, and logs. `fetch`, `retrieve`, and `load` for one operation across modules is three words for one idea. Keep `user` (logs in) and `customer` (buys) apart when the domain does.
- Use the words domain experts use (Evans: ubiquitous language). Code saying `Shipment` while the business says `Consignment` needs translating in every conversation.
- Abbreviate only what nobody has to decode: `id`, `url`, `http`, `db`, `ctx`, `err`. No dropped vowels (`usrCnt`, `mgr`, `calcAmt`).
- No type in the name (`orderList`, `strName`, `iCount`) unless two forms of one value sit side by side (`rawBody`, `body`).
- Terminology guard (AGENTS.md): no `semantic`, `facade`, `golden`, `canonical` in project-authored identifiers, test names, or file names. Use `normalized`, `contract`, `boundary`, `adapter`, `expected`, `reference`, `snapshot`.

## Functions and methods

- Commands are imperative verb phrases: `placeOrder`, `sendInvoice`, `releaseLock`. Queries are nouns or questions: `total()`, `isExpired()`, `ordersFor(customer)`. Queries change nothing (command-query separation, `functions.md`).
- The verb tells the caller the cost and the failure mode. Give each verb one meaning repo-wide:

| Verb | Promises |
|---|---|
| plain accessor (`name()`; `getName()` where JavaBeans require it) | cheap, no I/O, cannot fail |
| `find` | lookup that may return nothing (`Optional`, nullable, `Option`, `(T, bool)`) |
| `get` by key | lookup that fails loudly when absent, in repos that split `get`/`find` this way |
| `load`, `fetch` | I/O: database, network, disk |
| `compute`, `calculate` | noticeable CPU work the caller may want to cache |
| `create`, `build`, `new` | returns a new object |
| `ensure` | idempotent: acts only when the state is missing |
| `try` prefix | fallible twin of a throwing call (`tryParse`, Rust `try_new`) |

- No `get` on computed or expensive work: a `getTotal()` that calls a service hides its cost. Go and Rust drop `get` on plain accessors too (`Owner()`, `name()`).
- Conversions (casing per language):

| Prefix | Meaning | Examples |
|---|---|---|
| `asX` | cheap view of the same data, no copy | Rust `as_bytes`, Java `Arrays.asList`, Kotlin `asSequence` |
| `toX` | new value, may copy or allocate | `toString`, Kotlin `toList`, Rust `to_vec` |
| `intoX` | consumes the source (Rust) | `into_inner`, `into_bytes` |
| `fromX` | constructor on the target type | Rust `From::from`, `Instant.from`, `Money.fromCents` |
| `parseX`, `X.parse` | from text; can fail | `Integer.parseInt`, `LocalDate.parse`, Go `strconv.ParseInt` |

- A name with `And` (`saveAndNotify`) describes two jobs; split. `validate`, `check`, `is`/`has`, `find`, and accessors never write.

## Booleans

- Prefix with `is`, `has`, `can`, `should` in the language's form (`isActive`, Rust `is_empty`). `enabled` and `visible` read fine as fields.
- Name the positive state: `isReady`, never `notReady` or `isNotReady`. `if (!notReady)` makes every reader undo a double negative. `disabled` becomes `enabled`.
- A boolean that grows a third state, or two booleans that must never both be true, is an enum: `Status { Pending, Paid, Failed }`. Stringly-typed state is slop under Code Simplicity Discipline.

## Types, classes, and objects

- Nouns for what the type is: `Invoice`, `RetryPolicy`, `ConnectionPool`, `RateLimiter`.
- Vague suffixes hide the job: `Manager`, `Helper`, `Util`, `Processor`, `Handler`, `Data`, `Info`, `Base`. Keep one only when it is the precise term (Go's `http.Handler`; a card payment processor). A class that cannot be named without one usually holds several concerns; split until each part has a real name.
- Singletons and objects (Kotlin `object`, Rust unit struct, module-level instance) are named for what they are: `SystemClock`, `NoopMetrics`. No `Singleton`, `Instance`, or `Global` suffix. A mutable singleton is a global; pass it in.
- Interfaces by role, from the caller's side: `Clock`, `PaymentGateway`, `Orders`, Go single-method `Notifier`. No `I` prefix (C# is the exception, where it is the platform convention). Implementations say what makes them different: `PostgresOrders`, `InMemoryOrders`, `StripeGateway`, `FixedClock`. `OrderRepositoryImpl` says nothing; if it is the only implementation, the interface should not exist yet (`architecture.md`).

## Data shapes

| Shape | What it is | Name like | Own type when |
|---|---|---|---|
| domain model | business concept with rules and invariants | `Order`, `Money` | the code has rules about it |
| request / response payload | wire contract of one endpoint or RPC | `CreateOrderRequest`, `OrderResponse` | the API is public or versioned |
| DTO | flat carrier across a process or layer boundary (Fowler, PoEAA) | a specific name (`OrderSummary`); `Dto` suffix only if the repo uses it | a boundary needs a shape the domain type lacks |
| persistence entity / row | mirrors a table or document | `OrderRow`, `OrderRecord`, JPA `OrderEntity` | columns, nullability, or ORM annotations would weaken domain invariants |
| view model | state shaped for one screen or template | `CheckoutViewModel`, `OrderCardState` | the screen needs formatted, combined, or UI-only fields |
| command | request to change state; may be rejected | imperative: `PlaceOrder`, `CancelSubscription` | the change crosses a queue, bus, or API |
| event | fact that already happened; immutable | past tense: `OrderPlaced`, `PaymentFailed` | other parts react to it |

- A type per layer by reflex is mapping boilerplate. In small internal CRUD where row, domain type, and payload share a shape, one type is fine; split when the first real difference appears.
- Public APIs get their own request and response types; an entity bound straight to a request invites mass assignment and leaks columns.
- Mapping lives in the outer layer so the domain never imports a payload or row: `OrderResponse.from(order)`, `row.toDomain()`.
- An event carries what consumers need without calling back: ID, occurrence time, changed values. `UpdateInventoryEvent` is a command in an event's name; publish `OrderPlaced` and let consumers decide.

## Errors

- Name what went wrong from the caller's view: `OrderNotFound`, `InsufficientFunds`, `PaymentDeclined`. Never `GeneralError`, `ServiceException`, `ErrorOccurred`.
- Follow the language: Java and Kotlin `...Exception`; Go `ErrNotFound` sentinels and `NotFoundError` types; Rust an `OrderError` enum whose variants do not repeat `Error`.

## Modules and packages

- Package by feature: `billing`, `orders/checkout`, `shipping`.
- No `utils`, `common`, `shared`, `helpers`, `misc`, `models`, `types` dumping grounds. A shared module earns its place with a precise name: `money`, `retry`, `pagination`.
- Where callers qualify names with the module, do not repeat it: Go `order.New`, never `order.NewOrder`.

## Variables, collections, units

- Collections plural: `orders`, `pendingInvoices`. Maps name key and value: `ordersById`, `priceBySku` (Go `ordersByID`). A count is `orderCount`.
- Units belong in the type: `Duration`, `Instant`, `Money`. Where the value must be a bare number (config, env var, JSON field, metric), the name carries the unit: `timeoutMs`, `maxBodyBytes`, `ttl_seconds`.
- A newtype pays when it holds an invariant or stops a real mix-up (`OrderId` and `CustomerId` passed side by side). A wrapper that only renames a primitive is slop under Code Simplicity Discipline.
- Constants named for meaning: `MAX_RETRIES`, never `FIVE`.

## Tests

- The name states behavior and condition: `rejectsOrderWhenStockIsZero`, Go `TestPlaceOrder_OutOfStock`, Rust `rejects_order_when_out_of_stock`, Kotlin `` `rejects order when out of stock` ``. Never `test1`, `testPlaceOrder`, `itWorks`.
- Doubles named by kind: `fakeOrders`, `stubClock`, `spyNotifier`. `Mock...` only for generated mocks. Expected-output files are `expected` or `snapshot`.

## Good and weak names

| Weak | Better | Why |
|---|---|---|
| `processData(d)` | `importBankStatement(file)` | says which data and what happens |
| `OrderManager` | `Checkout`, `OrderRepository` | "manager" hides several jobs; split by job |
| `UserHelper.format(u)` | `user.displayName()` | behavior sits on the type that owns the data |
| `getTotal()` running a query | `loadTotal()` | the verb shows I/O |
| `IOrderRepo`, `OrderRepoImpl` | `Orders`, `PostgresOrders` | role for the interface, difference for the implementation |
| `OrderUpdated` with a status field | `OrderShipped`, `OrderCancelled` | one fact per event |
| `utils/strings.ts` | `slug.ts` | module named for its job |
| `render(doc, true)` | `renderDraft(doc)` | a flag argument hides two functions |

## Renaming

- When a name stops matching what the code does, rename it in the change that changed the behavior.
- Rename everywhere at once: declarations, call sites, tests, docs, log text. Language server rename first, then text search for strings and config it misses. No old-name aliases, re-exports, or deprecated shims (Code Simplicity Discipline).
- Names stored or sent outside the repo are contracts: database columns, JSON fields, event type names, metric names, public API paths. Changing one needs a migration and the user's call.
