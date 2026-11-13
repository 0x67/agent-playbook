# Debugging Go programs with the GNU Debugger

Go ships with excellent tooling: `go test`, `go vet`, the race detector, and `pprof` cover a large share of day-to-day problems. But sometimes you need to stop a running program, look at its memory, and step through it line by line. That's where a real debugger comes in. In this post, we'll look at how to use GDB, the GNU Debugger, with Go programs, where it shines, and where you should reach for something else.

## Why GDB for Go?

Go's compiler emits DWARF debugging information, which GDB understands. That means you can set breakpoints by function name, inspect variables, and walk stack traces on any machine that has GDB installed. This is particularly useful when:

- You're debugging a production binary or core dump on a server where you can't install other tools.
- You need to inspect a process that is already running.
- You want to debug cgo code, where Go and C frames are mixed together.

For most interactive Go debugging, [Delve](https://github.com/go-delve/delve) is the better choice because it understands goroutines, channels, and Go's type system natively. GDB is the fallback that's often already there.

## Building for debugging

The Go compiler optimizes and inlines aggressively, which makes stepping confusing: variables disappear, and lines execute out of order. Disable both when debugging:

```bash
go build -gcflags="all=-N -l" -o myapp ./cmd/myapp
```

`-N` disables optimizations and `-l` disables inlining. The `all=` prefix applies the flags to the standard library and dependencies too, not just your package.

Avoid stripping the binary (`-ldflags="-s -w"`), since that removes the symbol table and DWARF data GDB depends on.

## A small example

Consider this program with a subtle bug:

```go
package main

import "fmt"

type Order struct {
    ID    int
    Items []string
    Total float64
}

func applyDiscount(o *Order, pct float64) {
    o.Total = o.Total * (1 - pct)
}

func main() {
    o := &Order{ID: 42, Items: []string{"book", "pen"}, Total: 100}
    applyDiscount(o, 15) // oops: meant 0.15
    fmt.Println(o.Total)
}
```

The output is `-1400`, which is clearly wrong. Let's find out why.

## Starting a session

```bash
gdb ./myapp
```

Set a breakpoint and run:

```
(gdb) break main.applyDiscount
Breakpoint 1 at 0x...: file main.go, line 12.
(gdb) run
```

Note that Go function names are qualified with the package: `main.applyDiscount`, not `applyDiscount`.

Once stopped, inspect values:

```
(gdb) info args
o = 0xc000012345
pct = 15
(gdb) print *o
$1 = {ID = 42, Items = {array = 0xc000014000, len = 2, cap = 2}, Total = 100}
(gdb) print o.Total
$2 = 100
```

There's the bug: `pct` is `15`, not `0.15`. Step through to confirm:

```
(gdb) next
(gdb) print o.Total
$3 = -1400
```

## Essential commands

| Command | What it does |
|---|---|
| `break file.go:line` | Break at a specific line |
| `next` / `step` | Step over / into |
| `continue` | Resume execution |
| `bt` | Print the stack trace |
| `up` / `down` | Move between stack frames |
| `info locals` | Show local variables |
| `watch expr` | Break when a value changes |

## Working with goroutines

Go's runtime ships a GDB helper script, `runtime-gdb.py`, that adds Go-aware commands. GDB loads it automatically only if the path is trusted, so you may need to add this to `~/.gdbinit`:

```
add-auto-load-safe-path /usr/local/go/src/runtime/runtime-gdb.py
```

Adjust the path to match your `GOROOT`. Then you can use:

```
(gdb) info goroutines
(gdb) goroutine 5 bt
```

This is handy for finding where a deadlocked program is stuck. Be aware that the support is limited compared to Delve, and GDB's notion of "thread" doesn't map neatly onto goroutines, which are multiplexed over OS threads.

## Debugging core dumps

If a Go program crashes, you can have it produce a core dump by setting `GOTRACEBACK=crash` and enabling core files with `ulimit -c unlimited`. Then load it:

```bash
gdb ./myapp core
(gdb) bt
```

This gives you the state of the program at the moment of failure, which you can examine at leisure.

## Caveats

- **Optimized builds are hard to debug.** If you must debug a release binary, expect missing variables.
- **Goroutine stacks move.** Go grows stacks by copying them, so pointers to stack addresses can become stale.
- **Garbage collection and scheduling** can make timing-dependent bugs behave differently under a debugger.
- **Expression evaluation is limited.** You can't call Go methods or work easily with maps, interfaces, and channels.

## Conclusion

GDB isn't the first tool most Go developers reach for, but it's a capable one, especially for core dumps, running processes, and environments where Delve isn't available. Build with `-gcflags="all=-N -l"`, load the runtime helper script, and you'll have enough to track down many bugs. For everyday work, pair it with Delve and the Go toolchain's built-in diagnostics, and you'll be well equipped for whatever your programs throw at you.
