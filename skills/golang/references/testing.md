# Go Testing

Loaded via `golang` SKILL.md routing table. Sources: Go Code Review Comments, Google Go Style (tests), `testing` docs, go.dev/blog/subtests, go.dev/blog/fuzz-beta, `testing/synctest` docs.

## Framework

- `testing` stdlib default. `testify` only when module already imports it; then `testifylint` on, `require` for fatal, `assert` for continue.
- Diffs: `github.com/google/go-cmp/cmp` (`cmp.Diff(want, got)`, `cmpopts.IgnoreFields`, `cmpopts.EquateApproxTime`). Not `reflect.DeepEqual` for unexported fields, times, floats.
- No assertion frameworks that hide `t`. Test body reads top-to-bottom.
- Fakes hand-written at consumer's interface. Generated mocks (`mockgen`, `mockery`) only when repo already uses them.

## Table tests

```go
func TestParse(t *testing.T) {
	t.Parallel()
	tests := []struct {
		name    string
		in      string
		want    Config
		wantErr error
	}{
		{name: "empty input", in: "", wantErr: ErrEmpty},
		{name: "single key", in: "a=1", want: Config{A: 1}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			got, err := Parse(tt.in)
			if tt.wantErr != nil {
				if !errors.Is(err, tt.wantErr) {
					t.Fatalf("Parse(%q) err = %v, want %v", tt.in, err, tt.wantErr)
				}
				return
			}
			if err != nil {
				t.Fatalf("Parse(%q) unexpected err: %v", tt.in, err)
			}
			if diff := cmp.Diff(tt.want, got); diff != "" {
				t.Errorf("Parse(%q) mismatch (-want +got):\n%s", tt.in, diff)
			}
		})
	}
}
```

- Field names in every case. `name` first. Descriptive: `"trailing comma rejected"`, not `"case 3"`.
- `t.Run` per case. `t.Parallel()` inside when cases share no state. go.mod >= 1.22: no `tt := tt`.
- Case order: zero/empty, typical, boundary, error.
- Past ~15 cases or per-case setup: split into multiple test funcs.
- Cases needing different assertions: separate tests, not table.

## T helpers

- `t.Context()` (1.24+): cancelled after test. Never `context.Background()` in tests on >= 1.24. `testingcontext` modernizer rewrites.
- `t.Cleanup(f)` over `defer`: runs after parallel subtests finish.
- `t.TempDir()`, `t.Chdir(dir)` (1.24+), `t.Setenv(k, v)`. `Setenv` and `Chdir` panic with `t.Parallel()`.
- `t.Helper()` first line of every helper that calls `t.Error/Fatal`. Failure lines point at caller.
- `t.Skip` with reason. `testing.Short()` guards slow tests.
- `t.Output()` (1.25+) as `io.Writer` for logs. `t.Attr(key, val)` (1.25+) structured metadata. `t.ArtifactDir()` (1.26+) for files kept after run.
- Never `t.Fatal` from goroutine other than test's own (`testinggoroutine` vet). `t.Error` or send error on channel.

## Fatal vs Error

- `t.Fatal`: setup failed, cannot continue, nil deref would follow.
- `t.Error`: check failed, remaining checks still meaningful.
- Inside `t.Run`, `t.Fatal` stops only that subtest.

## Failure messages

- Form: `Func(input) = got, want want`. Include input. Diff for structs.
- `%q` strings, `%v` errors, `%#v` when type matters.
- No prefix like `"Error:"`, `"FAIL"`. `go test` adds file:line.

## Test doubles

- Interface at consumer, 1-3 methods. Fake in `_test.go` or `internal/testutil`.
- Fake holds state, returns canned values. Assert on outcome (stored rows, sent requests), not call count.
- Stub clock: `now func() time.Time` field, default `time.Now`.
- One `internal/testutil` per module. No copy-pasted fakes across packages.
- Real transports with fake backends: `httptest.NewServer` + real `http.Client`, `net.Pipe`, SQLite when driver-compatible.

## Package placement

- White-box `package foo` for unexported internals.
- Black-box `package foo_test` for public API. Preferred: reads like usage, exposes API smells.
- `export_test.go` exposes internals to black-box tests when needed.
- `testdata/` for fixtures via `filepath.Join("testdata", name)`.

## Examples

- `func ExampleParse()` with `// Output:` comment. Compiled, run, shown in godoc.
- One example per exported type or key func in library packages.
- Errors in examples: `if err != nil { fmt.Println(err); return }`.

## Benchmarks

```go
func BenchmarkParse(b *testing.B) {
	in := loadFixture(b)
	b.ReportAllocs()
	for b.Loop() {
		_, _ = Parse(in)
	}
}
```

- `for b.Loop()` (1.24+). Before: `b.ResetTimer(); for i := 0; i < b.N; i++`.
- `b.ReportAllocs()` always. `-benchmem` on CLI.
- Compare: `go test -bench=. -count=10 -run=^$ > old.txt`, change, `> new.txt`, `benchstat old.txt new.txt`.
- Sub-benchmarks by size: `b.Run(fmt.Sprintf("n=%d", n), ...)`.
- `B.Loop` prevents dead-code elimination since 1.24. Older: assign to package-level sink.

## Fuzz

- `func FuzzParse(f *testing.F)`, `f.Add(seed)` per seed, `f.Fuzz(func(t *testing.T, in string) {...})`.
- Property: no panic, round-trip equality, invariant holds. Not exact outputs.
- Seed corpus committed in `testdata/fuzz/FuzzParse/`. `go test -fuzz=FuzzParse -fuzztime=30s` locally; CI runs seeds only.

## Concurrency and time

- `testing/synctest` (1.25+): `synctest.Test(t, func(t *testing.T) { ... })`. Fake clock, `synctest.Wait()` for idle, `synctest.Sleep` (1.27+). Deterministic timeouts, tickers, debouncers.
- Before 1.25: inject `now`/`after` funcs. Never `time.Sleep` to wait for goroutine.
- `t.Parallel()` + `-race` finds shared-state bugs.
- Leak check: `runtime.NumGoroutine` delta or `goleak.VerifyNone(t)` when present.

## HTTP

- Handlers: `httptest.NewRecorder()` + `http.NewRequestWithContext(t.Context(), ...)`. Assert status, headers, decoded body.
- Clients: `httptest.NewServer(handler)`, `t.Cleanup(srv.Close)`, client at `srv.URL`.
- Middleware: wrap recording handler, assert it saw modified request.
- Route table through real `http.ServeMux` in a test: mux panics on conflicting patterns at registration.

## Integration tests

- Unit: no network, no DB, no filesystem outside `t.TempDir`, no real time. `-short` passes in seconds.
- Integration: `//go:build integration` tag or `if testing.Short() { t.Skip() }`. Separate `make test-integration`.
- Containers: `testcontainers-go` when repo uses it. Else `TEST_DATABASE_URL` env, skip when unset.
- Each test owns its data: unique schema, table prefix, or tx rolled back in `t.Cleanup`.

## Commands

```sh
go test ./...                         # unit
go test -race -shuffle=on ./...       # concurrency + order independence
go test -count=1 ./...                # bypass cache
go test -run 'TestParse/empty' ./pkg  # one subtest
go test -cover -coverprofile=c.out ./... && go tool cover -html=c.out
go test -bench=. -benchmem -run=^$ ./pkg
go test -fuzz=FuzzParse -fuzztime=30s ./pkg
go test -json ./...                   # machine output; OutputType field on 1.27+
go vet ./...                          # tests analyzer catches malformed Test/Benchmark/Example signatures
```

- >= 1.27 `go test` also runs `stdversion` vet: too-new stdlib API fails the run.

## Useless tests to reject

Test must fail from project bug. Do not write, delete on sight:

- stdlib restatement: `len(append(...))`, `strings.Contains`, `json.Marshal` of plain struct without custom marshaler, `time.Duration` math.
- Field echo: constructor stores arg, struct literal readback, constant equals itself.
- Getter/setter tests.
- `err != nil` only, when kind matters.
- Mock call count without observable output.
- Whole-string snapshot of big JSON/SQL where nothing is contract. Field assertions instead. Full-string pins only for wire formats, migrations, public API responses.
- Branch already covered by named existing test.
- Test named for behavior but asserting weaker thing.
- Copy-pasted fakes/encoders across packages.

Keep: wire/on-disk layout pins (encoding size, magic bytes, schema hash), migration idempotence, exhaustive enum switches.

## Avoid

- `init()` in test files.
- Global state mutated without `t.Cleanup` restore.
- `os.Chdir` (use `t.Chdir`), `os.Setenv` (use `t.Setenv`).
- Sleeping for timing.
- Asserting log text unless logs are contract.
- Testing private funcs through reflection or `linkname`.
- `//nolint` in tests to silence `errcheck`. Handle or `_ =` with reason.
