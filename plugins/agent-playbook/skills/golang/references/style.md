# Go Style

Loaded via `golang` SKILL.md routing table. Sources: Effective Go, Go Code Review Comments, Google Go Style, Uber Go Style, go.dev/doc/modules/layout.

## Naming

- MixedCaps only. Underscores only in test names (`TestParse_EmptyInput`) and generated code.
- Initialisms keep case: `userID`, `HTTPServer`, `parseURL`, `xmlHTTPRequest`. Never `Id`, `Url`, `Http`.
- Package names: short, lowercase, singular, no underscores (`user` not `users`). No `util`, `common`, `helpers`, `base`, `misc`, `types`, `models`. Name says what package provides.
- Do not repeat package name in identifiers: `http.Server` not `http.HTTPServer`, `user.New` not `user.NewUser`.
- Getters: `Owner()` not `GetOwner()`. Setters: `SetOwner()`.
- Receivers: 1-2 letters, same name across all methods of type (`s *Server`). Never `this`, `self`.
- Locals: short in small scope (`i`, `n`, `buf`, `err`), longer as scope grows. Name length grows with distance from declaration to use.
- Interfaces: single-method gets `-er` suffix (`Reader`, `Flusher`). Multi-method: noun (`Store`, `Client`).
- Errors: sentinels `ErrNotFound`, types `NotFoundError` / `*ValidationError`.
- Constants: MixedCaps (`MaxRetries`), never `MAX_RETRIES`.
- Test doubles: `fakeStore`, `stubClock`, `spyNotifier`. `MockX` only when generated.
- Never shadow builtins or imports: no `len`, `new`, `error`, `string`, `url`, `json` as variable names.
- Printf-style funcs end in `f`: `Logf`, `Errorf`.

## Package layout

```
go.mod
cmd/<app>/main.go        thin: signal ctx, config, call run(ctx) error
internal/<domain>/       business logic, not importable outside module
internal/<transport>/    http, grpc, cli adapters
<pkg>/                   only packages intended as public API of module
```

- `internal/` is default. Public package only when external consumers exist.
- No `pkg/` dumping ground. No `src/`.
- One concern per package. Too big when reader scrolls unrelated types. Too small when caller imports three packages for one operation.
- Circular import means wrong boundary. Move shared types down, or define interface at consumer.
- Package `main` holds no logic. Everything testable lives in importable package.
- Separate module only when subtree needs independent versioning or external reuse.
- Test files beside code. Black-box tests use `package foo_test`.
- Fixtures in `testdata/` (ignored by `go build`). Generated code carries `// Code generated ... DO NOT EDIT.`

## Imports

- Three groups, blank line between: stdlib, third-party, module-local. `goimports` enforces.
- Alias only on collision or when package name differs from path tail (`pb`, `v1`).
- No `import .`. `import _` only in `main` or tests (driver registration).

## Declarations

- `var x T` for zero value. `x := value` when initial value matters. `var x = expr` at package level.
- Nil slice: `var s []T`. Not `s := []T{}` unless JSON must encode `[]`.
- `make([]T, 0, n)` and `make(map[K]V, n)` when n known.
- Composite literals with field names. Omit zero-value fields.
- Pointer to struct: `&T{...}`. `new(T)` for scalars; `new(expr)` (1.26+) for optional pointer fields.
- Group related `const`/`var` in one block. Separate unrelated groups.
- Declare at first use, smallest scope. `if v, ok := m[k]; ok {` idiom.
- Raw strings (backticks) for regex, JSON, SQL, multi-line.
- Format strings as named `const` when reused.
- Exported package-level vars: only sentinel errors and true constants. Everything else injected.

## Control flow

- Handle error, return early. Happy path at minimum indent.
- No `else` after `return`, `break`, `continue`, `panic`.
- Nesting depth 3 max. Extract function past that.
- `switch` over if-else chain with 3+ branches. `switch { case cond: }` for conditions.
- `for i := range n` (1.22+), `for range n` when index unused.
- No `goto`. Labeled `break` only for nested `select`/`for` that needs it.
- `defer` right after acquire: `f, err := os.Open(p); if err != nil {...}; defer f.Close()`.
- `defer` inside loop body: wrap iteration in func so cleanup runs per iteration.

## Functions and parameters

- Small. One concern. Name says what it returns or does.
- `ctx` first, options last. No bare `bool` params (`NewServer(addr, true)` unreadable): named type or option.
- Optional params, most callers set some: options struct as last param. Most callers set none: functional options.

```go
type Option func(*Server)

func WithTimeout(d time.Duration) Option { return func(s *Server) { s.timeout = d } }

func New(addr string, opts ...Option) *Server {
	s := &Server{addr: addr, timeout: 30 * time.Second}
	for _, o := range opts {
		o(s)
	}
	return s
}
```

- Return concrete types. Return interface only when factory hides several implementations on purpose.
- Named results only when they clarify (two same-typed returns) or `defer` must modify. Naked return only in tiny funcs.
- Do not return `(T, bool, error)`. Pick `error` or `bool`.
- Variadic `...T` only for true lists. Not for optional single param.
- Copy slices/maps at API boundary when either side may mutate later.
- Synchronous by default. No goroutines inside library funcs; caller decides.

## Receivers and embedding

- Pointer receiver when method mutates, struct holds mutex, struct is large, or any other method needs pointer. Value receiver for small immutable values.
- Never mix pointer and value receivers on one type.
- Compile-time interface check: `var _ Store = (*memStore)(nil)`.
- Embed only for is-a and interface satisfaction by delegation. Never embed in exported struct to save typing: leaks methods, freezes API.
- Mutex as named field `mu`, not embedded. Never copy struct holding mutex (`copylocks` vet).

## Enums

```go
type State int

const (
	StateUnknown State = iota // zero value stays invalid
	StateRunning
	StateStopped
)

func (s State) String() string { ... } // or go:generate stringer
```

- Zero value meaningful only when it is a valid default. Otherwise explicit `Unknown` first or `iota + 1`.
- Typed, never bare `int`/`string`. `String()` method. `exhaustive` linter on switches.
- String-backed enums (`type Level string`) when value crosses wire and readability matters.

## Comments and docs

- Doc comment on every exported identifier. Full sentence starting with the name: `// Server serves HTTP requests.`
- Package comment in one file, `// Package foo ...` directly above `package foo`. Long ones in `doc.go`.
- Comment explains why, invariants, concurrency guarantees, ownership of returned resources, error kinds. Not what code does.
- Delete comments that restate code. No commented-out code.
- Deprecation: `// Deprecated: use X instead.` paragraph.
- Directives `//go:generate`, `//go:build`, `//go:embed`: no space after `//`.
- Global comment rules apply: plain humanizer prose, no em dash, no plan/task IDs.

## Generics

- Use when: same func needed for second type, type-safe container, or replacing `any` + type assertion.
- Do not when: function operates on struct with named fields (interface or plain type instead), single call site, or constraint longer than body.
- Constraints narrow: `comparable`, `cmp.Ordered`, small interface. Never hand-roll `Ordered`. `~T` for named types.
- Functions over generic types. Generic type only for containers.
- Omit explicit type args when compiler infers (1.21+ inference covers most).
- Generic methods (1.27+): only when type param belongs to method, not type. Do not retrofit.
- Generic type aliases (1.24+) for renaming generic types.

## Iterators (1.23+)

- Collections expose `All() iter.Seq2[K, V]`, `Keys() iter.Seq[K]`, `Values() iter.Seq[V]`.
- Return `iter.Seq` instead of slice when caller may stop early or data is large.
- Consume with `slices.Collect`, `slices.Sorted`, `maps.Collect`.
- `strings.SplitSeq`, `strings.Lines`, `strings.FieldsSeq` (1.24+) over `strings.Split` in loops.
- `iter.Pull` rarely: merging two sequences. Always call stop.
- Yield loop must return when `yield` returns false.

```go
func (l *List[T]) All() iter.Seq[T] {
	return func(yield func(T) bool) {
		for n := l.head; n != nil; n = n.next {
			if !yield(n.val) {
				return
			}
		}
	}
}
```

## Avoid

- `interface{}`: use `any`.
- Interface with one implementation "for testing". Test with real type or small fake at consumer.
- Getter/setter pair on every field. Export field or give behavior.
- `init()` for anything but stdlib registration.
- Package-level `var log`, `var db`. Inject.
- `panic` for expected failures.
- Reflection when generics or interfaces fit.
- `time.Now()` deep in logic when tests need control. Inject `now func() time.Time`.
- Stringly-typed state. Use enums.
- Returning `nil, nil`.
- Ignoring `Close()` errors on writers.
