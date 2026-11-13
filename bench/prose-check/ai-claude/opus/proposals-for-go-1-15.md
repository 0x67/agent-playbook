# Proposals for Go 1.15

Go 1.14 is on track to ship in February, and the Go team is already lining up the next release. Go 1.15, due around August, has a short list of proposed changes. Most of our backend services run on Go, so we follow these early discussions closely. It's easier to give feedback on a proposal than to adapt to a decision after it ships.

This cycle's list is deliberately modest. Larger efforts like generics are still in the design phase, so the Go team has framed Go 1.15 as a cleanup release: fix rough edges, catch common bugs earlier, and avoid churn. Here's what's proposed and what it means for us.

## How the proposal process works

The Go team picks a few proposals at the start of each release cycle. When the development tree opens, prototype implementations land so people can try them against real code. Feedback over the following months determines whether each change stays. The team makes a final decision before the release freeze and removes anything that doesn't hold up.

So none of the changes below are guaranteed. They are candidates, and the early prototypes exist to find problems.

## 1. A vet check for `string(int)` conversions

([#32479](https://golang.org/issue/32479))

In Go, converting an integer to a string produces the UTF-8 encoding of the matching Unicode code point. It does not produce the decimal representation:

```go
n := 65
s := string(n) // "A", not "65"
```

This behavior is well defined, but it's a classic trap. People new to Go, and plenty of experienced developers, write `string(n)` expecting `"65"`. The result is a bug that compiles cleanly and can slip past tests.

The proposal adds a `go vet` check that flags `string(x)` when `x` is an integer type other than `rune` or `byte`. The fix is to say what you mean:

```go
s := strconv.Itoa(n) // "65"
r := string(rune(n)) // "A", explicitly
```

Longer term, a future version of the language could remove the conversion entirely. A vet warning is the low-risk first step.

## 2. Flagging impossible interface type assertions

([#4483](https://golang.org/issue/4483))

Today the compiler accepts any type assertion from one interface type to another, even when the assertion can never succeed:

```go
var r io.Reader
_ = r.(interface{ Read(p []byte) int })
```

The `Read` method on `io.Reader` returns `(int, error)`. No type can have both `Read` signatures, so this assertion always fails at runtime. It's almost certainly a mistake, usually caused by a method signature drifting out of sync.

The proposal has `go vet` report these impossible assertions. A later release might have the compiler reject them outright. The issue has been open since 2012, so it's good to see it get attention.

## 3. Constant evaluation of indexing and slicing on constant strings

([#28591](https://golang.org/issue/28591))

The length of a constant string is already a constant, but indexing or slicing one is not:

```go
const greeting = "hello"
const n = len(greeting)   // OK today
const c = greeting[0]     // not a constant today
const sub = greeting[1:3] // not a constant today
```

Under the proposal, when both the string and the indices are constant, the result would also be a constant: a `byte` for an index and a string for a slice. The compiler already bounds-checks constant indices into constant strings, so this mainly removes an inconsistency.

One subtlety is worth watching in the prototype. Expressions that become constant are evaluated under constant rules. For example, `"\xff"[0] + 1` currently wraps around to zero at runtime. As a constant expression, it would be a compile-time overflow error. That's arguably an improvement, but it's the kind of edge case early testing should surface.

## What we're doing

We plan to take three steps before the decision:

- **Run the prototype vet checks against our repositories** once they land on tip, and fix whatever they find. The `string(int)` pattern is easy to miss in code review.
- **Build our services against the development branch in CI** so that compile-level changes like constant evaluation show up early.
- **Report findings upstream.** If a check produces false positives or a change breaks reasonable code, the proposal issue is the place to say so.

None of these changes require action today. Still, the vet checks are worth adopting early, because the code they catch is buggy no matter what the proposal process decides.

## Get involved

Each proposal has its own GitHub issue, linked above. The Go team actively asks for experience reports, and feedback from teams running Go in production carries real weight. If you have a case where one of these proposals would help or hurt, share it on the issue.
