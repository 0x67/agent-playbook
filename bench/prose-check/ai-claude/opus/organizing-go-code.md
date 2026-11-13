# Organizing Go code

Every Go project starts the same way: a `go.mod`, a `main.go`, and good intentions. A few months later you might have forty files in one directory, a package called `utils` that everything imports, and a circular dependency you're avoiding with a carefully placed interface. We've been there. Here's what we've learned about structuring Go code so it stays easy to work with as it grows.

## Start flat, and stay flat longer than you think

The most common mistake we see is building structure before it's needed. A new service doesn't need `pkg/`, `internal/`, `domain/`, `adapters/`, and `infrastructure/` on day one. It needs a `main.go` and maybe a few other files in the same package.

Go packages are cheap to create but expensive to reorganize, because every split creates an API boundary. Once code lives in a separate package, its unexported identifiers become inaccessible, and you start exporting things just to make the compiler happy. Keep things in one package until you feel real friction, such as files that are hard to navigate or concepts that clearly don't belong together. Then split along the seam you've discovered instead of the one you predicted.

## Name packages for what they provide

A package name is part of every call site. When you write `http.Get` or `json.Marshal`, the package name does half the work of explaining what's happening. Good package names are short, lowercase, and describe what the package *provides*, not what it *contains*.

Avoid names like `utils`, `common`, `helpers`, `models`, and `types`. These describe a category of code, not a purpose, and they become dumping grounds. A `utils` package tends to import half your codebase and get imported by the other half, which is exactly how import cycles start.

If you have a function that formats currency, it doesn't belong in `utils`. It belongs in a package called `money` or `currency`, where `currency.Format(amount)` reads naturally.

Also watch for stutter. In a package called `user`, the type should be `user.Account` or just `user.User` if that's truly the clearest name, never `user.UserService`. The package name is already part of the identifier.

## Organize by responsibility, not by layer

Many developers arrive at Go from frameworks that organize code by technical layer: all controllers in one folder, all models in another, all repositories in a third. In Go this tends to work poorly. A single feature change touches four packages, and those packages end up tightly coupled anyway.

We prefer grouping code by what it does in the business. A billing service might have packages like `invoice`, `payment`, and `subscription`, each containing its own types, logic, and storage code. When someone needs to change how invoices work, they open one directory.

This isn't absolute. Truly shared infrastructure, like a database connection pool or a logging setup, can reasonably live in its own package. But your default should be cohesion around a concept.

## Use `internal/` to protect your boundaries

Go has one built-in visibility mechanism above the package level: the `internal` directory. Code under `internal/` can only be imported by code rooted at the parent of that directory. This makes it easy to tell other teams and repositories that something is an implementation detail.

For applications, putting most of your packages under `internal/` is a reasonable default. It costs nothing and keeps you free to refactor without worrying about who might depend on your code. For libraries, it lets you share code between your own packages without making it part of your public API.

## Keep `main` thin

We put executables in `cmd/<name>/main.go`, and we keep those files small. A `main` function should parse configuration, wire dependencies together, and start the program. Business logic doesn't belong there because `main` packages can't be imported, which means that logic can't be tested or reused.

A useful pattern is for `main` to call a `run` function that returns an error:

```go
func main() {
    if err := run(os.Args, os.Getenv); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}
```

This makes the startup path testable and keeps `os.Exit` in exactly one place.

## Define interfaces where they're used

In Go, interfaces are satisfied implicitly, so the consumer, not the producer, should usually define them. If your `invoice` package needs to send email, it should declare a small `Mailer` interface with just the method it needs. The concrete email client doesn't need to know that interface exists.

This keeps dependencies pointing in the right direction and keeps interfaces small, which makes them easy to fake in tests.

## The real rule

No layout is correct for every project, and the popular "standard Go project layout" repositories are not an official standard. The goal is code that a new teammate can navigate on their first day. Start simple, split when it hurts, and name things so the call sites read clearly.
