# Modern Go by Version

Loaded via `golang` SKILL.md routing table. Sources: go.dev/doc/go1.20 through go1.27 release notes, `go tool fix help` modernizer list.

## Rule

- go.mod `go` line is the ceiling. No API or syntax above it. `stdversion` vet (auto in `go test` on 1.27+) fails otherwise.
- Bumping `go` line changes semantics (loopvar 1.22, timers 1.23, map impl 1.24, GC 1.26). Ask before bumping someone else's module.
- New code uses newest idiom the module allows. Existing code: `go fix -diff ./...`, apply in separate commit.
- Third-party replaced by stdlib: switch in new code; migrate existing only when asked.

## Ladder

| go.mod | Unlocks |
|---|---|
| 1.20 | `errors.Join`, multiple `%w`, `context.WithCancelCause`, `bytes.Clone`, `unsafe.SliceData/String/StringData`, interfaces satisfy `comparable` |
| 1.21 | `min`, `max`, `clear` builtins; `slices`, `maps`, `cmp`; `log/slog`; `sync.OnceFunc/OnceValue/OnceValues`; `context.WithoutCancel`, `AfterFunc`, `WithDeadlineCause`; `errors.ErrUnsupported`; PGO GA (`default.pgo`); `toolchain` line |
| 1.22 | `for i := range 10`; per-iteration loop variables (no `i := i`); `net/http.ServeMux` methods + wildcards; `math/rand/v2`; `slices.Concat`; `reflect.TypeFor` |
| 1.23 | range-over-func iterators, `iter.Seq/Seq2/Pull`; `slices.All/Values/Collect/Sorted/Chunk`, `maps.Keys/Values/All/Collect`; `unique`; timers GC-safe with unbuffered channels; `structs.HostLayout`; `go telemetry` |
| 1.24 | generic type aliases; go.mod `tool` directive, `go get -tool`; `testing.T.Context`, `B.Loop`, `T.Chdir`; `os.Root`; `weak`; `runtime.AddCleanup`; `json:",omitzero"`; `strings.Lines/SplitSeq/FieldsSeq`; `encoding.TextAppender`; `crypto/mlkem`, `hkdf`, `pbkdf2`, `sha3`; Swiss-table maps; `slog.DiscardHandler`; `#cgo noescape/nocallback`; `printf` non-constant format vet; `tests` vet; `GOAUTH` |
| 1.25 | `sync.WaitGroup.Go`; `testing/synctest` (`Test`, `Wait`); `T.Output`, `T.Attr`; `encoding/json/v2` experimental (`GOEXPERIMENT=jsonv2`); `http.CrossOriginProtection`; `runtime/trace.FlightRecorder`; container-aware `GOMAXPROCS`; `waitgroup`, `hostport` vet; go.mod `ignore`; `go doc -http`; `go build -asan` leak detect; `reflect.TypeAssert`; `io/fs.ReadLinkFS`; `work` package pattern; DWARF5 |
| 1.26 | `new(expr)`; self-referential generic constraints; `errors.AsType[T]`; `go fix` modernizers + `//go:fix inline`; Green Tea GC default; `slog.NewMultiHandler`; `testing.T.ArtifactDir`; `crypto/hpke`; `bytes.Buffer.Peek`; `io.ReadAll` 2x faster; `httputil.ReverseProxy.Director` deprecated (use `Rewrite`); `net.Dialer.DialTCP` etc. with ctx; `reflect` iterator methods; goroutine leak profile experimental; `go mod init` defaults to previous minor; cgo calls 30% cheaper |
| 1.27 | generic methods; struct literal keys as field selectors; generalized func type inference; `encoding/json/v2` + `jsontext` stable; stdlib `uuid`; `crypto/mldsa`; `strings.CutLast`, `bytes.CutLast`; `math/big.Int.Divide`; `math/rand/v2` generic `N` method; `net/url.URL.Clone`, `Values.Clone`; `synctest.Sleep`; goroutine leak profile GA; `go test` runs `stdversion`; `go test -json` `OutputType`; `go doc pkg@version`, `-ex`; `go mod tidy` merges require blocks; modernizers `atomictypes`, `embedlit`, `slicesbackward`, `unsafefuncs`; macOS 13+ |

## Replacement table

| Old | New | Since |
|---|---|---|
| `interface{}` | `any` | 1.18 |
| `ioutil.ReadFile`, `ioutil.ReadAll`, `ioutil.TempDir` | `os.ReadFile`, `io.ReadAll`, `os.MkdirTemp` / `t.TempDir` | 1.16 |
| `golang.org/x/exp/slices`, `maps`, `constraints` | `slices`, `maps`, `cmp.Ordered` | 1.21 |
| `sort.Slice(s, less)` | `slices.SortFunc(s, cmp)` / `slices.Sort(s)` | 1.21 |
| hand loop for contains/index | `slices.Contains`, `slices.Index`, `slices.IndexFunc` | 1.21 |
| `if a < b { m = a } else { m = b }` | `min(a, b)` | 1.21 |
| `for k := range m { delete(m, k) }` | `clear(m)` | 1.21 |
| `logrus`, `zap`, `zerolog`, `log.Printf` in new code | `log/slog` | 1.21 |
| `for i := 0; i < n; i++` (index not used for indexing) | `for i := range n` | 1.22 |
| `i := i` in loop body | delete | 1.22 |
| `if r.Method != "GET"` in handler | `mux.HandleFunc("GET /path", ...)` | 1.22 |
| `gorilla/mux`, `httprouter` for plain routing | `net/http.ServeMux` | 1.22 |
| `math/rand` | `math/rand/v2` (`rand.IntN`, `rand.N`) | 1.22 |
| `reflect.TypeOf((*T)(nil)).Elem()` | `reflect.TypeFor[T]()` | 1.22 |
| `strings.Split` then range | `strings.SplitSeq` | 1.24 |
| `context.WithCancel(context.Background())` in tests | `t.Context()` | 1.24 |
| `for i := 0; i < b.N; i++` | `for b.Loop()` | 1.24 |
| `tools.go` blank imports | go.mod `tool` directive | 1.24 |
| `json:",omitempty"` on struct / `time.Time` | `json:",omitzero"` | 1.24 |
| `runtime.SetFinalizer` | `runtime.AddCleanup` | 1.24 |
| `os.Chdir` in tests | `t.Chdir` | 1.24 |
| `x/crypto/sha3`, `hkdf`, `pbkdf2` | `crypto/sha3`, `crypto/hkdf`, `crypto/pbkdf2` | 1.24 |
| `wg.Add(1); go func(){ defer wg.Done() ... }()` | `wg.Go(func(){ ... })` | 1.25 |
| clock injection only for timer tests | `testing/synctest` | 1.25 |
| `uber-go/automaxprocs` | built-in container-aware GOMAXPROCS | 1.25 |
| `var e *E; errors.As(err, &e)` | `e, ok := errors.AsType[*E](err)` | 1.26 |
| `p := new(T); *p = v` | `new(v)` | 1.26 |
| `httputil.ReverseProxy{Director: ...}` | `Rewrite: func(*ProxyRequest)` | 1.20 (Director deprecated 1.26) |
| `atomic.AddInt64(&n, 1)` | `atomic.Int64` methods | 1.19 (modernizer 1.27) |
| `github.com/google/uuid` | `uuid` stdlib | 1.27 |
| `encoding/json` for new hot JSON paths | `encoding/json/v2` | 1.27 |
| `pkg/errors`, `multierr` | `fmt.Errorf %w`, `errors.Join` | 1.13 / 1.20 |
| `go.uber.org/atomic` | `sync/atomic` typed | 1.19 |
| `golang.org/x/net/context` | `context` | 1.7 |

## Still third-party, still right

- `golang.org/x/sync/errgroup`, `semaphore`, `singleflight`.
- `github.com/google/go-cmp/cmp` for test diffs.
- `github.com/jackc/pgx/v5` for Postgres. `sqlc` for query codegen.
- `connectrpc.com/connect` + `buf` for RPC.
- `golang.org/x/time/rate` for rate limiting.
- `golang.org/x/text` for i18n, `golang.org/x/net/http2/h2c`.
- `testify`, `cobra`: only if repo already has them. Never add to a repo that lacks them.

## Detect version

```sh
grep -E '^go ' go.mod            # ceiling for language + stdlib
go version                       # installed toolchain
go list -m -f '{{.GoVersion}}'   # module's go line
```

- Toolchain newer than go.mod line is normal; API still capped by go.mod.
- go.mod line newer than toolchain: `GOTOOLCHAIN=auto` downloads. Hermetic CI needs matching install.
