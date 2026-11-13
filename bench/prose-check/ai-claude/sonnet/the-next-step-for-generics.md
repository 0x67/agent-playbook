# The Next Step for Generics

Generics are one of those features that feel finished until you try to build something ambitious with them. Over the past year, our platform team has been pushing our shared libraries toward more expressive, reusable abstractions, and we've repeatedly hit the same wall: generics get us most of the way there, but the last stretch is awkward. This post covers where we've landed, what still hurts, and where we think the next step lies.

## Where Generics Serve Us Well

For most of our codebase, basic parametric polymorphism is exactly right. Collections, result types, retry wrappers, and typed clients all benefit from a simple `T`. A function like this is easy to read, easy to test, and hard to misuse:

```ts
function firstOr<T>(items: readonly T[], fallback: T): T {
  return items.length > 0 ? items[0] : fallback;
}
```

The compiler proves what we mean, and callers get precise types without ceremony. This is the 80% case, and it works.

## Where They Start to Strain

The trouble begins when abstractions need to say more than "some type." We've run into three recurring problems.

**1. Constraint sprawl.** As functions grow more general, their type signatures accumulate bounds. A pipeline stage that is generic over input, output, error, and context can end up with a signature longer than its body. Readers skim past it, and that defeats the purpose of having types document intent.

**2. Poor inference at boundaries.** Inference works well within a function but degrades across composition. When we chain generic stages, the compiler often asks us to annotate types it "should" be able to deduce. Each annotation is small, but together they create friction and make refactors noisy.

**3. Errors that describe the mechanism, not the mistake.** A misuse of a deeply generic API often produces an error mentioning an unresolved type parameter three layers down. Engineers new to the codebase can't map that message back to what they did wrong.

None of these are fatal. But they tax every person who touches generic-heavy code, and that tax compounds.

## The Next Step: Named, Composable Type Contracts

Our proposal, which we've been prototyping internally, is to treat constraints as first-class, named contracts rather than inline bounds. Instead of repeating a cluster of requirements on every signature, you define the contract once and reference it by name:

```ts
contract Stage<In, Out> {
  run(input: In): Promise<Out>;
  readonly name: string;
}

function compose<A, B, C>(
  first: Stage<A, B>,
  second: Stage<B, C>,
): Stage<A, C> {
  // ...
}
```

The idea isn't novel in isolation; traits, protocols, and type classes all point in this direction. What we care about is the combination of three properties:

- **Named intent.** A contract carries a name and documentation, so a signature reads like a sentence rather than an equation.
- **Composition by default.** Contracts can be combined and narrowed, and inference flows through the combination instead of resetting at each boundary.
- **Diagnostics tied to the contract.** When a type fails to satisfy a contract, the error says which contract and which member, not which internal parameter failed to unify.

In our prototype, the third property turned out to matter most. Engineers told us the improved messages did more for adoption than any added expressiveness.

## What We Learned Prototyping

We migrated a few of our internal pipeline libraries to the contract style and measured what we could. Signature length dropped noticeably, and explicit type annotations at call sites fell by roughly a third. Just as important, code review conversations shifted from "what does this type mean?" to "is this the right contract?", which is a far better use of everyone's time.

We also learned some cautions. Contracts invite over-abstraction; teams were tempted to define one for every shape. We now apply a rule of thumb: introduce a contract only when at least two independent implementations exist or are clearly planned. We also found that naming matters enormously. A vague contract name is worse than an inline bound, because it hides requirements instead of surfacing them.

## What's Next

We're hardening the prototype, writing migration guides, and gathering feedback from teams outside platform. In the coming months we plan to open-source the tooling and publish a more detailed design document, including the trade-offs we haven't resolved, such as how contracts interact with variance and how to keep compile times predictable.

Generics gave us reuse. The next step is making that reuse legible. If you're wrestling with similar problems, we'd love to hear how you're solving them.
