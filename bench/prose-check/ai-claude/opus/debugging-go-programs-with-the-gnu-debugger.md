# Debugging Go programs with the GNU Debugger

Most Go developers reach for [Delve](https://github.com/go-delve/delve), and the Go team recommends it for good reason. Still, GDB comes up more often than you might expect. It may be the only debugger installed on a locked-down production host. You may need to step from Go into C through cgo. You may want to analyze a core dump with the same tools your team already uses for its C and C++ services.

This post covers how to make GDB useful with Go: building a debuggable binary, loading Go's runtime extensions, and working around the rough edges.

## Build a debuggable binary

By default, the Go compiler optimizes aggressively and inlines small functions. That is great for production but frustrating in a debugger. Variables show up as `<optimized out>`, and the current line jumps around unpredictably. For a debugging session, turn both off:

```sh
go build -gcflags=all="-N -l" -o server ./cmd/server
```

`-N` disables optimizations and `-l` disables inlining. The `all=` prefix applies the flags to every package in the build, including your dependencies, not just the main package.

Two more things to check:

- **Don't strip the binary.** Release pipelines often pass `-ldflags="-s -w"`, and `-w` removes DWARF debug information entirely.
- **Watch for compressed DWARF.** The Go linker compresses debug sections by default. If an older GDB reports that it can't find debugging symbols, rebuild with `-ldflags=-compressdwarf=false`.

GDB works best on Linux. On macOS it requires code signing and has poor support for Apple silicon, so most of what follows assumes a Linux host or container.

## Load the Go runtime extensions

Go ships a Python script, `runtime-gdb.py`, that teaches GDB about goroutines and adds pretty-printers for strings, slices, maps, and channels. The linker records the script's path in the binary, but GDB refuses to auto-load it unless the path is trusted. Add this to your `~/.gdbinit`:

```
add-auto-load-safe-path /usr/local/go/src/runtime/runtime-gdb.py
```

If your Go installation lives elsewhere, run `go env GOROOT` to find it. You can also load the script by hand inside a session with `source <GOROOT>/src/runtime/runtime-gdb.py`.

## A basic session

Take a small function from an order-processing service:

```go
type Order struct {
	ID    int
	Items []string
	Meta  map[string]string
}

func process(o *Order) int {
	total := 0
	for _, item := range o.Items {
		total += len(item)
	}
	return total
}
```

A typical session looks like this:

```
$ gdb ./server
(gdb) break main.process
(gdb) run
(gdb) info args            # show function arguments
(gdb) print *o             # dereference the struct
(gdb) print o.Meta         # pretty-printed map
(gdb) print $len(o.Items)  # helper from runtime-gdb.py
(gdb) next
(gdb) info locals
```

Go symbol names need some care. To break on a method with a pointer receiver, quote the name so GDB doesn't misread the parentheses and asterisk:

```
(gdb) break 'main.(*Server).handleOrder'
```

You can also set breakpoints by file and line (`break orders.go:42`) or make them conditional:

```
(gdb) break main.process if o.ID == 1234
```

Conditional breakpoints matter more in Go than in many languages, for reasons covered in the next section.

## Working with goroutines

The runtime script adds a few goroutine-aware commands:

```
(gdb) info goroutines      # list all goroutines and their state
(gdb) goroutine 7 bt       # backtrace for goroutine 7
(gdb) goroutine all bt     # backtraces for every goroutine
```

For interface values, `$dtype(x)` prints the dynamic type behind the interface.

Expect some friction here. GDB thinks in OS threads, while the Go scheduler multiplexes many goroutines onto a few threads and moves them between threads freely. As a result, stepping can feel erratic. A `next` might stop inside a *different* goroutine that happened to hit the same breakpoint. In a busy server, conditional breakpoints keyed on a request ID or similar value are the most reliable way to follow a single flow of execution.

## Post-mortem debugging with core dumps

GDB is especially useful for crashes you can't reproduce. To get a core dump from a Go program, enable cores in your shell and tell the runtime to abort on a fatal error:

```sh
ulimit -c unlimited
GOTRACEBACK=crash ./server
```

You can also set this from code with `debug.SetTraceback("crash")`. After a crash, open the binary and the core file together:

```sh
gdb ./server core.12345
```

Then use `bt`, `info goroutines`, and `print` as before. On systems running `systemd-coredump`, cores are captured automatically, and `coredumpctl gdb` opens the most recent one directly.

## Knowing when to switch

GDB doesn't natively understand deferred calls, panics, channel internals, or Go's growable stacks. It also has limited support for calling Go functions from the prompt. Delve handles all of these, and `dlv core` reads the same core files. Our team's rule of thumb is to use Delve by default and use GDB for cgo-heavy code, mixed-language core dumps, and hosts where it's the only debugger available.

When those situations come up, a binary built with `-N -l`, a trusted `runtime-gdb.py`, and a few well-placed conditional breakpoints make GDB a capable tool for Go.
