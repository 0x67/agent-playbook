# Go Error Handling

Loaded via `golang` SKILL.md routing table. Sources: Go Code Review Comments, Google Go Style, Uber Go Style, go.dev/blog/go1.13-errors, `errors` package docs.

## Pick error kind

| Caller need | Use |
|---|---|
| Propagate with context, no matching | `fmt.Errorf("op: %w", err)` |
| Static message, caller never matches | `errors.New("parse header: empty")` |
| Caller matches identity | sentinel `var ErrNotFound = errors.New("not found")` + `errors.Is` |
| Caller needs data (field, code, retry hint) | custom type + `errors.As` / `errors.AsType` |
| Multiple independent failures | `errors.Join(errs...)` |
| Hide internals at public/RPC boundary | `fmt.Errorf("op: %v", err)` (no `%w`), documented |

- Sentinels: package-level `var Err...`, exported only when callers need them. Lowercase, no punctuation.
- Custom types: pointer receiver `func (e *NotFoundError) Error() string`. Add `Unwrap() error` when wrapping. `Is(target error) bool` only for identity semantics on value types.
- Do not export error type that only carries a message. Sentinel suffices.

## Wrapping

- Wrap where context is lost: I/O, network, database, parsing, external service, user input. Not at every call level.
- Context adds what inner error lacks: `fmt.Errorf("open config %q: %w", path, err)`. Never repeat what wrapped error already says.
- Form: `"<operation> <subject>: %w"`. Lowercase, no `error:` prefix, no trailing period, no `failed to` stacking.
- One `%w` per Errorf normally. Multiple `%w` (1.20+) only when both chains matter to caller.
- `%v` deliberately at public API boundary where internal type is not contract. Comment why.
- Never `err.Error()` into new error. Loses chain.
- Never wrap nil. Check first.

## Matching

- `errors.Is(err, ErrNotFound)`. Never `err == ErrNotFound` on anything possibly wrapped.
- `e, ok := errors.AsType[*NotFoundError](err)` (1.26+). Before: `var e *NotFoundError; errors.As(err, &e)`. Never type switch on wrapped error.
- `errorsas` vet catches non-pointer target.
- `context.Canceled`, `context.DeadlineExceeded` via `errors.Is`. `context.Cause(ctx)` when cause set.
- `io.EOF` compared with `==` only directly from `Read`; `errors.Is` elsewhere.
- Unsupported operation: `errors.ErrUnsupported` (1.21+).

## Handle once

- Error goes one way: return it, or log it and stop it. Never both.
- Log at top of chain (handler, worker loop, `main`) with full chain and structured fields. Inner layers wrap and return.
- Wrapping is not handling. Retrying, degrading, mapping to status, logging is handling.
- Swallow deliberately, with comment: `_ = f.Close() // read-only, close error irrelevant`. Never bare `_ =` on writes.
- `errcheck` enforces. No `//nolint:errcheck` without reason.

## Cleanup errors

```go
func write(path string, data []byte) (err error) {
	f, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("create %q: %w", path, err)
	}
	defer func() { err = errors.Join(err, f.Close()) }()

	if _, err := f.Write(data); err != nil {
		return fmt.Errorf("write %q: %w", path, err)
	}
	return nil
}
```

- Named result only for this pattern. Close errors matter on writers, sync, commit, flush.
- `errors.Join` returns nil when all nil.

## main and exit

```go
func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	if err := run(ctx, os.Args[1:], os.Stdout, os.Stderr); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(ctx context.Context, args []string, stdout, stderr io.Writer) error { ... }
```

- `os.Exit`, `log.Fatal*` only inside `main`. Defers do not run on exit.
- One exit point. `run` returns error, `main` prints and exits.
- `run` takes ctx, args, writers: testable without process control.
- Exit codes: 1 generic, 2 usage. Map specific errors only when scripts depend on them.

## Panics

- Panic only for programmer bugs: impossible state, broken invariant, nil dependency at construction. Message names invariant.
- Never panic on user input, I/O, network, config.
- `Must*` helpers only for package-level init of compile-time constants (`regexp.MustCompile`, `template.Must`).
- `recover` only at goroutine top-level with policy: convert to error, log with `debug.Stack()`, re-panic if unknown. `net/http` recovers per request; worker pools add their own.
- Unrecovered panic in any goroutine kills process. Every spawned goroutine either cannot panic or recovers.

## Context errors

- `context.Canceled` and `DeadlineExceeded` are expected. Not logged as errors at request layer; map to 499/504 or drop.
- `context.WithCancelCause` + `context.Cause(ctx)` when callers need reason.
- Check `ctx.Err()` before expensive work in long loops.

## Transport boundaries

Domain errors stay domain. Status mapping lives in transport layer, one switch:

```go
func status(err error) int {
	switch {
	case errors.Is(err, ErrNotFound):
		return http.StatusNotFound
	case errors.As(err, new(*ValidationError)): // AsType on 1.26+
		return http.StatusBadRequest
	default:
		return http.StatusInternalServerError
	}
}
```

- Never leak internal messages to clients on 5xx. Log internally, return generic body.
- Never leak secrets, tokens, connection strings, SQL with params in messages.

## Naming and docs

- Sentinels `ErrX`. Types `XError`. Unexported `errX`, `xError`.
- Doc comment on every exported sentinel and error type: when returned, whether wrapped.
- Function doc lists notable error kinds: `// Returns ErrNotFound when id is unknown.`

## Test assertions

- Assert kind: `errors.Is`, `errors.As`, or typed field. Not `err != nil` alone when kind matters. Not `err.Error() == "..."` unless message is public contract.
- `if err == nil { t.Fatal("want error") }` then match kind.

## Avoid

- `panic(err)` in library. `log.Fatal` outside `main`.
- `err.Error()` string matching.
- `errors.New` with dynamic text in hot loops: allocate once or use type.
- Wrapping at every layer: `"a: b: c: d: open file: no such file"`.
- Returning `error` from funcs that cannot fail.
- `if err != nil { return err }` at boundaries that lose info.
- `pkg/errors`, `go.uber.org/multierr` in new code. stdlib covers both.
- Custom `Result[T]` types. Two return values is the idiom.
