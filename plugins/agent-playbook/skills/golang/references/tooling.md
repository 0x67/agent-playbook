# Go Tooling

Loaded via `golang` SKILL.md routing table. Sources: `go` command docs, `go vet` docs, golangci-lint.run, staticcheck.dev, go.dev/doc/tutorial/govulncheck, go.dev/doc/modules.

## Gate (run in order, after every change)

```sh
gofmt -l .                       # prints files needing format; must be empty
go vet ./...
go build ./...
go test -race ./...
staticcheck ./...                # or golangci-lint run, when .golangci.yml present
```

- Any red: fix, rerun whole gate. Report failures verbatim.
- Gate must compile what it validates: `go vet -tags=integration ./...` when tagged files changed.
- Multi-module (`go.work`): gate per module, or `work` pattern (1.25+) from workspace root.

## Formatting

- `gofmt` mandatory. `goimports` (`golang.org/x/tools/cmd/goimports`) groups imports; `-local <module>` for local group.
- `gofumpt` (`mvdan.cc/gofumpt`) stricter superset; only when repo config enables it. Never mix within repo.
- `golines` only with repo config. Go has no line limit; wrap for meaning.
- v2 golangci-lint runs formatters via `golangci-lint fmt`.

## go vet

Runs registered analyzers; `go test` runs a subset automatically (plus `stdversion` since 1.27). Highlights:

| Analyzer | Catches |
|---|---|
| `printf` | format/arg mismatch, non-constant format string (1.24+) |
| `lostcancel` | `WithCancel` cancel func not called |
| `copylocks` | mutex copied by value, range over `sync.Locker` |
| `waitgroup` | `wg.Add` inside goroutine (1.25+) |
| `hostport` | `fmt.Sprintf("%s:%d")` instead of `net.JoinHostPort` (1.25+) |
| `slog` | key without value in slog call |
| `errorsas` | non-pointer target to `errors.As` |
| `httpresponse` | body use before error check |
| `testinggoroutine` | `t.Fatal` from goroutine |
| `tests` | malformed `TestX`/`BenchmarkX`/`ExampleX` signatures |
| `stdversion` | stdlib symbol newer than go.mod `go` line |
| `unusedresult` | ignored `fmt.Errorf`, `errors.New` results |
| `cgocall` | cgo pointer-passing violations |
| `structtag`, `unmarshal`, `nilfunc`, `unreachable`, `shift`, `stringintconv`, `timeformat`, `directive`, `appends`, `defers`, `sigchanyzer`, `atomic`, `bools`, `composites` | as named |

Extra analyzers from `golang.org/x/tools/go/analysis/passes` via `go vet -vettool=$(which fieldalignment)`.

## staticcheck

- `go install honnef.co/go/tools/cmd/staticcheck@latest`. `staticcheck ./...`.
- Config `staticcheck.conf` at module root: `checks = ["all", "-ST1000"]` style. Default set fine.
- Bundled inside golangci-lint; standalone when no golangci config.

## golangci-lint v2

- Install: `go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest`, or release binary. Pin version in CI.
- v2 config differs from v1: `version: "2"`, formatters separate section, `linters.default` replaces enable-all. `golangci-lint migrate` converts v1.
- Standard default set: `errcheck`, `govet`, `ineffassign`, `staticcheck`, `unused`.

```yaml
version: "2"

run:
  timeout: 5m

linters:
  default: standard
  enable:
    - errorlint        # %w, errors.Is/As instead of == and type switch
    - bodyclose
    - noctx
    - sqlclosecheck
    - rowserrcheck
    - copyloopvar
    - intrange
    - perfsprint
    - prealloc
    - exhaustive
    - gosec
    - revive
    - sloglint
    - thelper
    - tparallel
    - usestdlibvars
    - unconvert
    - unparam
    - nolintlint
    - misspell
    # - testifylint    # only when testify present
    # - wrapcheck      # noisy; only if team wants every boundary wrapped
  settings:
    errcheck:
      check-type-assertions: true
    revive:
      rules:
        - name: exported
          arguments: [checkPrivateReceivers, disableStutteringCheck]
    exhaustive:
      default-signifies-exhaustive: true
  exclusions:
    presets:
      - std-error-handling
      - common-false-positives
    paths:
      - gen/
      - .*\.pb\.go$

formatters:
  enable:
    - gofmt
    - goimports
  settings:
    goimports:
      local-prefixes:
        - github.com/acme/app
```

- `golangci-lint run ./...`, `golangci-lint fmt`, `--fix` for auto-fixable.
- `//nolint:errcheck // reason` only with reason, only on the line. `nolintlint` enforces. Never file-level nolint.
- Never `default: all`. Noise kills signal.

## govulncheck

- `go install golang.org/x/vuln/cmd/govulncheck@latest`. `govulncheck ./...`.
- Reports vulns on reachable call paths; informational for imported-but-unused.
- Run when `go.mod` changes and weekly in CI. Fix: `go get module@fixed`, rerun.
- `govulncheck -mode=binary ./bin/app` for shipped binaries.

## go fix modernizers (1.26+)

- `go fix -diff ./...` shows rewrites; `go fix ./...` applies. Review diff, run gate. Separate commit from feature work.
- Modernizers: `any`, `forvar`, `rangeint`, `minmax`, `mapsloop`, `slicescontains`, `slicessort`, `slicesbackward`, `stringsseq`, `stringscut`, `stringscutprefix`, `stringsbuilder`, `waitgroupgo`, `testingcontext`, `errorsastype`, `newexpr`, `omitzero`, `atomictypes`, `embedlit`, `stditerators`, `reflecttypefor`, `unsafefuncs`, `inline` (`//go:fix inline` directive), `plusbuild`, `buildtag`.
- Rewrites respect go.mod version: no `errors.AsType` suggested on 1.25 module.
- gopls surfaces same fixes as quick fixes.

## Modules

- `go mod tidy` after every dependency change. `go mod verify` in CI. Commit `go.sum`.
- `go` line: language + stdlib ceiling, controls semantics (loopvar 1.22, timers 1.23, maps 1.24, GC 1.26). Bump deliberately. `go mod init` defaults to previous minor since 1.26.
- `toolchain` line not auto-added since 1.25. `GOTOOLCHAIN=auto` (default) downloads newer toolchain when go.mod demands; `GOTOOLCHAIN=local` in hermetic CI.
- Tools (1.24+): `go get -tool golang.org/x/tools/cmd/stringer@latest` adds `tool` directive; run `go tool stringer`. Replaces `tools.go` blank-import hack. `go install tool` installs all.
- `ignore` directive (1.25+) in go.mod excludes dirs from `./...`.
- `godebug` directive pins runtime behavior across upgrades.
- `replace` for local dev only; never commit absolute paths. `go.work` for multi-module local dev, usually gitignored.
- Private modules: `GOPRIVATE=github.com/acme/*`, `GONOSUMDB`, `GOAUTH` (1.24+).
- Vendoring: `go mod vendor` + `-mod=vendor` only when repo policy requires.
- Major versions: `/v2` path suffix.
- Duplicate `require` blocks auto-merged by `go mod tidy` on 1.27+.

## Build

```sh
CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o bin/app ./cmd/app
go build -race ./...           # race-enabled binary for staging
go build -asan ./...           # leak detection on by default 1.25+
go build -json ./...           # structured output 1.24+
GOOS=linux GOARCH=arm64 go build ./cmd/app
go version -m bin/app          # embedded module + VCS info; -json 1.25+
```

- `-buildvcs` on by default: binary carries revision, time, dirty flag. `debug.ReadBuildInfo()` reads it. Main module version set from VCS tag since 1.24; prefer over `-X main.version`.
- `CGO_ENABLED=0` for static binaries unless cgo needed. Check `go env CGO_ENABLED`.
- Dockerfile: multi-stage, `golang:1.27` builder, `gcr.io/distroless/static` or `scratch` runtime, non-root user, copy binary only.
- `go generate ./...` in CI only when generated output not committed; else verify `git diff --exit-code` after generate.
- Build tags: `//go:build integration`, `//go:build linux && amd64`. `buildtag` vet validates.

## Docs and inspection

- `go doc <pkg>`, `go doc <pkg>.<Sym>`, `go doc -all <pkg>`, `go doc pkg@version` (1.27+), `go doc -http` (1.25+) local server.
- `go list -m all`, `go list -deps ./...`, `go mod graph`, `go mod why <module>`.
- `go env`, `go version`, `go tool dist list`.
- LSP: `gopls` via `LSP` tool when exposed: definition, references, rename, diagnostics. Else `go doc` + `mcp__fff__grep`/`rg`.
- `go tool trace -http` localhost-only by default (1.27+).

## CI

- Matrix `go-version: [stable, oldstable]` with `actions/setup-go` and cache.
- Steps: `go mod tidy && git diff --exit-code go.mod go.sum`, `gofmt -l`, `go vet`, `golangci-lint`, `go test -race -shuffle=on -coverprofile`, `govulncheck`, `go build` per target.
- Pin linter versions. Fail on new warnings; do not baseline forever.
- `go test -json` piped to `gotestsum` for readable CI output when available.

## Install missing tools

```sh
go install golang.org/x/tools/cmd/goimports@latest
go install mvdan.cc/gofumpt@latest
go install honnef.co/go/tools/cmd/staticcheck@latest
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest
go install golang.org/x/vuln/cmd/govulncheck@latest
go install golang.org/x/perf/cmd/benchstat@latest
go install golang.org/x/tools/gopls@latest
```

Inside a module prefer `go get -tool` + `tool` directive so versions pin in go.mod.
