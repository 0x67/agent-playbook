# Design system

A design system is the set of decisions a product reuses: tokens, components, and the rules for using both. Build it from the product's real sources, with no more tokens and components than the product uses.

## Start from what exists

1. List the sources: stylesheets and custom properties, a theme object, `tailwind.config.*`, token JSON, the component folder, stories, brand guidelines, the design tool library.
2. Write the full inventory first (tokens per family, themes, text styles, fonts, components, assets) and track progress against it.
3. Copy values exactly. A 5px padding stays 5px; do not snap values to a 4 or 8 grid or to a framework default.
4. Copy logos, icons, and fonts as files. Never redraw a mark from memory.
5. Include the components the source defines and no "usual" extras. Additions go in their own list with a reason.
6. With no source at all, start small: 6 to 10 colors in one theme, 5 to 7 text styles, 4 spacing steps, 3 radii, and no components until a screen needs them.

## Token layers

| Layer | Also called | Holds | Example |
|---|---|---|---|
| Primitive | reference, base, global | raw values that say what a thing is | `blue-600`, `space-4`, `radius-2` |
| Role | semantic, alias, decision | intent, pointing at a primitive | `color-action-primary`, `color-text-muted` |
| Component | contextual | one component's own override points | `button-primary-bg` |

1. Components read role tokens. Role tokens point at primitives.
2. A component token points at a role token, never straight at a primitive.
3. Themes (light, dark, high contrast, a brand) swap the role-to-primitive mapping. Component code does not change per theme.
4. Add the component layer only when a component must differ from the roles. A product with one theme and a small component set can stop at two layers.
5. Deciding which roles exist is design work. A role per component consolidates nothing; the goal is a few roles that all components share.

## Naming

1. Pick one pattern and apply it everywhere; which pattern matters less than applying it consistently.
2. Order from broad to specific: category, property, role, then variant, state, mode. Example: `color-bg-danger-hover`.
3. Variant comes before state, and state before mode. Keep the mode in the same position in every name, or out of names and in themes.
4. Pick a token by its job. The same step number means different things across hues: one published comparison measured step 600 at 1.85:1 contrast in yellow and 10.83:1 in purple, so `yellow-600` and `purple-600` cannot be swapped for text.
5. A role's name says why it exists: `color-text-danger`. A name that describes appearance (`color-text-red`) breaks when the theme changes.
6. Prefer a clear long name to a short cryptic one.
7. Scales use one scheme across the system (`sm`, `md`, `lg`, or numeric steps such as `space-100`, `space-200`) and leave room to grow in both directions.
8. Match token names to the names in code, so a designer and an engineer search for the same string.

## State values

A role that changes with interaction (hover, pressed, disabled) gets its state values in one of two ways:

| Approach | Tokens | Fits |
|---|---|---|
| Per-state tokens | `color-bg-action-primary-hover`, `-pressed`, `-disabled`, each with its own value | one brand and one theme, a small team, a first system |
| Base plus state layer | `color-bg-action-primary` and a few overlay opacities that every component shares (one published set: hover 0.08, pressed 0.12, disabled 0.38) | two or more brands or themes, or dark mode on the roadmap |

1. Per-state tokens are easy to read and map one to one to CSS, but each theme or brand added multiplies them.
2. A state layer is a translucent overlay on the control, often a pseudo-element. Adding a theme then changes only the base colors. Engineers meeting it for the first time need it explained in the README.
3. An overlay changes contrast. A lighter base color in a new brand under a white hover layer can drop text below 4.5:1, so check each base color with each layer.
4. A system can mix the two: per-state tokens for its core components, and state layers for components built outside the library.

## Families to cover

1. Color: surfaces, text, borders, action, status (success, warning, danger, info), focus ring. Each text color's note lists the backgrounds it is used on.
2. Type: families, then named text styles with size, line height, and weight together.
3. Spacing and sizing scales.
4. Radius, border width, shadow or elevation.
5. Motion: a few duration and easing tokens (`references/components.md`, Motion), and z-index layers when the product uses them.
6. Breakpoints and container widths.
7. Locale formats, for a product in more than one market: dates, including partial ones (day and month, month and year) in short, medium, and long forms; times with their time zone; numbers; and currency per market (£1,250.50, $1,250.50, 1.250,50 €). Values stay structured and the application formats them. The system documents the rule and one example per market. `09/06` reads as 9 June in one market and 6 September in another, so use a month name where markets mix.

Each token gets a usage note that says where it applies. A token nobody can place is a candidate for removal.

## Contrast and themes

1. Text holds 4.5:1 against the backgrounds its note lists, in each theme. Large text (24px and up, or bold 19px and up), control borders, focus rings, and icons that convey meaning hold 3:1.
2. Check the values of the later themes as well as the first.
3. A filled accent gets an `on-` token for the text placed on it, so a dark theme can flip the text.
4. Status colors differ in lightness as well as hue, and each status also has a word or an icon.
5. Do not re-tint a source color pair that fails; record the failure in its usage note.
6. A control's boundary (an input border, an outline button, a checkbox) has its own role token, separate from the decorative divider, at 3:1 against the background behind the control. In one system an outline button used the divider token at 1.23:1, and a control border token mapped to an existing ink value raised it to 3.30:1.

## Component inventory

Per component, the system records:

1. Purpose in one sentence, and when to use something else.
2. Anatomy: its parts, each with a name.
3. Variant axes and their values.
4. States it supports.
5. Consumer inputs: props, children, data, the container it expects.
6. Do and do not, with real examples from the product.
7. A live preview that shows the main variants and states.
8. Owner: the person or team who approves changes to it.
9. Status: proposed, in progress, ready, or deprecated, with the state of its design, code, and docs.

`references/components.md` has the rules for each of these.

## Documentation

1. The system's README is usage rules for whoever builds with it, written as instructions that name tokens: "Set body copy in `body`. Use `color-text-danger` only for errors."
2. It covers content basics (tone, casing, how the product addresses the user), visual foundations, and iconography, with examples taken from the product.
3. Its length follows the source. A system of a few tokens needs only a few bullets.
4. Build notes, provenance, and next steps go in your reply to the user, outside the README.

## Changing the system

1. Each layer has a stated rule for who may change it. A new screen may consume tokens and components freely; adding or changing a role token or a component is authorship and needs the owner's approval.
2. Approval belongs to a role with the authority to say no. A pull request records who approved; the system's own rules say who is allowed to.
3. Record each request: what was proposed, what was checked, who approved or declined it, and why. A declined variant with its reason answers the next team that asks for it.
4. Before adding a pattern or variant for one request, ask whether it solves a user problem the existing parts cannot, whether the context really differs, what happens without it, and whether another team would ask for it. Write the cost beside each option. A request for a different look alone can be declined: one email template that existing modules already supported cost about 5 to 6 extra days of design and development, plus another QA and compliance cycle.
5. Before changing a token or component, find all of its consumers. A border token that looks decorative may be the only sign that a control is clickable. When fixing a shared token, list every consumer, local overrides included, as fixed now, fixed later, or exempt.
6. A component in use is never renamed or removed silently. Deprecate it first, give the migration path, and list the change in the release notes under added, changed, fixed, deprecated, or action required.
7. Keep a register of deliberate exceptions (a screen that breaks the grid on purpose), so a later cleanup or an agent does not "fix" them.
8. A correction made twice becomes a written rule or an automated check.
9. An agent working on a product uses the system. It proposes changes to the system and does not make them in passing. When a role token is in the way, the agent either gets the look it needs from a component token that points at another existing role, or reports the role change it needs with that role's consumers and waits for approval. A screenshot of the one screen it fixed says nothing about the other screens that use the role.

## Approval tiers

Match the review to how many components and products a change affects, whatever its size in lines. A one-line change that breaks a shared contract is major.

| Tier | Covers | Example | Approved by |
|---|---|---|---|
| Minor | no change to behavior, props, visual meaning, or compatibility | a typo or a usage example in a component's docs | the component's owner |
| Standard | new behavior or a new variant that keeps the component's API compatible | a loading state on an existing button | the owner, after design and engineering check the interaction and accessibility |
| Major | shared foundations, breaking changes, a changed interaction pattern, or a change many products depend on | remapping role tokens across products | the system lead or governance group, with an impact assessment, a migration plan, and a coordinated release |

Adapt the tiers to the team's size and release process. A system with one maintainer can run all three through that person and still does the impact assessment for a major change.

## Protecting tokens in a repository

Written rules guide people and agents but do not stop a merge. Where tokens live in code, checks enforce the layer rules as well.

1. Primitive and role tokens are protected: an ordinary feature task does not add, change, or remove them. Component tokens may change inside their own component's namespace (`button-*` for a Button task).
2. Keep the token rules in one document in the repository, and point agent instruction files (`AGENTS.md`, `CLAUDE.md`) at it instead of copying it into each.
3. Assign the token directories in `CODEOWNERS` (primitives and roles to the system team, component tokens to component owners) and require code-owner approval in branch protection.
4. A CI check diffs the tokens against the base branch, sorts each added, changed, renamed, or deleted token by layer, and fails a protected change made outside the approval process. The same check confirms that every reference resolves, no alias chain loops, and component tokens point at role tokens.
5. Keep a list of foreground and background token pairs, each with its minimum ratio, for every theme. Start with body and muted text on the page background and on each raised background (cards, table rows, code blocks), button labels on their fills, links, and input borders and the focus ring at 3:1, then add hover and selected states. Placeholder text counts as text. The build fails when a pair measures under its minimum, with no rounding up (4.49:1 fails 4.5:1), and the message gives the pair and the ratio. One team found that lightening `--text-muted` by 4% had dropped it to 4.39:1.
6. Size visual testing by the dependency graph: visual regression on the Button's variants and states for a Button token change, and for a role color change, contrast checks on its documented backgrounds and visual regression on every component and screen that uses it.
7. The pull request lists old and new values, changed aliases, and the affected consumers.

## As a Claude Design System artifact

The Design System artifact type holds a system as files that the Design canvas and other agents read. The type's own `SKILL.md` and `artifact-type/reference/` pages define the format and take precedence; read them from the artifact before writing. What to know when planning:

| Path under `project/` | Holds |
|---|---|
| `README.md` | the usage rules; readers start here |
| `tokens.json` | all tokens |
| `components/<Comp>/README.md` | guidelines for one component |
| `components/<Comp>/preview.html` | its live preview |
| `components/bundle.js`, `bundle.css`, `index.d.ts` | the real components, when the system has a library |
| `assets/<Group>/<file>` | logos, icons, images |
| `fonts/<file>` | font files |
| `design-system.json` | the index, written last |

1. `tokens.json` uses lists: each family is `{"tokens": [{"name", "value", "usage"}]}`, and `color` also has `themes`. The W3C/DTCG name-to-value map is valid JSON that the page cannot read, so convert a DTCG source into lists first.
2. Color values are hex, a color function with plain numbers, or an alias `"{other-token}"`. Named colors, `var()`, and `color-mix()` are dropped.
3. Put the primary theme first. A token with no value for a later theme inherits the first theme's value.
4. Type is shaped differently: `fonts`, `families`, and `groups` of named styles.
5. Each component preview starts with a `<!-- @dsCard group="..." height=N -->` line and renders one component in a few states.
6. A system built from a repository records its source, and a later sync merges into it file by file. A system kept in sync by Claude Code's `/design-sync` is read-only on the page: change the code and sync again. `/design-sync` writes to design-system projects on standalone Claude Design (claude.ai/design), which closes by December 14, 2026; check where the project is stored before relying on it.
7. Before using a system in a design, read its `project/README.md` and `project/tokens.json`. Use real components from its bundle where it has them, and never draw look-alikes.

## Sources

- Always Twisted, "Design token naming conventions": https://www.alwaystwisted.com/articles/design-token-naming-conventions
- Design Systems Collective newsletter, "Picking a token by its job, or by its number": https://designsystemscollective.substack.com/p/picking-a-token-by-its-job-or-by
- Design Systems Collective newsletter, "The approve button needs an owner": https://designsystemscollective.substack.com/p/the-approve-button-needs-an-owner
- Design Systems Collective newsletter, "Some mistakes are on purpose": https://designsystemscollective.substack.com/p/some-mistakes-are-on-purpose
- Design Systems Collective, "Design System Governance: One Framework, Every Component" (approval tiers, decision records): https://www.designsystemscollective.com/design-system-governance-one-framework-every-component-37cb8bd4a84d
- Design Systems Collective, "Design Token Governance: Protecting Tokens from AI Agents" (protected layers, `CODEOWNERS`, CI token checks): https://www.designsystemscollective.com/protecting-design-tokens-in-ai-development-2da25a0595f1
- Design Systems Collective, "The Story of Design Tokens: Stateful vs. Composable Tokens" (per-state tokens and state layers): https://www.designsystemscollective.com/the-story-of-design-tokens-stateful-vs-composable-tokens-4f8a3f736932
- Design Systems Collective, "When Your Design System Should Say No" (exception test, cost of a variation): https://www.designsystemscollective.com/when-your-design-system-should-say-no-834236cba193
- Design Systems Collective, "One border, five components" (control boundary token): https://www.designsystemscollective.com/one-border-five-components-6a78dda5f26d
- Design Systems Collective, "Fail the Build When a Design Token Breaks WCAG AA" (contrast pairs in CI): https://www.designsystemscollective.com/fail-the-build-when-a-design-token-breaks-wcag-aa-a9b703c04e8e
- Design Systems Collective, "Localisation is a design-system problem" (locale formats): https://www.designsystemscollective.com/localisation-is-a-design-system-problem-1d0a922d007d
- Design Systems Collective, "Shape to System: A Practical Figma File Structure for Building a Design System from Scratch" (component status, deprecation): https://www.designsystemscollective.com/shape-to-system-a-practical-figma-file-structure-for-building-a-design-system-from-scratch-63e1f1b72369
- Collective Kit, a Figma UI kit whose docs show one layout for a system and its component pages: https://collectivekit.co/
- The Design System artifact type's `SKILL.md`, `craft.md`, and `format.md`, read from a Design System artifact on claude.ai.
