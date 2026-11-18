---
name: ui-ux
description: >
  Interface design structure: design systems (tokens, themes, component
  inventory), component separation, variants and states, screen and flow
  inventories, and how to lay out a Claude Design canvas or Design System
  artifact (pages, artboards, state rows, shared components). Use when
  designing or reviewing a screen, flow, page, component, or design system;
  on "design system", "design tokens", "component library", "variants",
  "button states", "empty state", "loading state", "wireframe", "mockup",
  "prototype", "user flow", "Claude Design", "design canvas", "artboard", or
  "Figma file structure"; and before building UI from a PRD. Works without a
  PRD; when the prd skill wrote one, its Experience section is the screen
  inventory. Covers structure and completeness. Visual polish, color,
  typography, layout, copy, and accessibility detail belong to the better-*
  and ui skills when installed.
---

# UI/UX skill

Design an interface as a system: decisions held in tokens, components with a declared set of variants and states, screens that account for more than the ideal case, and a design file in which a second person can locate each screen and component. This skill covers that structure and leaves the choice of look to the user and the visual skills.

## Routing table (mandatory)

Read the matching reference before designing. Paths are relative to this skill's directory.

| Task touches | Read |
|---|---|
| tokens, themes, naming, component inventory, documenting a system, a Design System artifact, syncing a system from code | `references/design-system.md` |
| deciding what is a component, anatomy, variant axes, interactive states, props, composition | `references/components.md` |
| screen inventory, flows, screen states (ideal, empty, loading, error, partial), responsive behavior, handoff | `references/screens.md` |
| a Claude Design canvas: pages, artboards, rows, state variants, shared components, tweaks, prototypes | `references/claude-design.md` |

When several rows match, read all of them. A new feature usually needs `screens.md` and `components.md`.

## Before designing

1. Look for a PRD: `specs/<slug>/prd.md` or wherever the repo keeps them. When one exists, its Experience section and user stories are the starting inventory, and its out of scope table bounds the design. When none exists, carry on: write the inventory yourself from the request and the code, and say which parts you assumed.
2. Find the existing system before inventing one. Look for a design system artifact or Figma library, token files, a theme object, `tailwind.config.*`, CSS custom properties, the component folder. Follow it. A new token, component, or pattern needs a reason the existing ones cannot serve.
3. Read one finished screen of the product end to end (markup, styles, states) to learn its vocabulary.
4. Settle the direction with the user when no system or reference sets the look. Two to four low-fidelity options that differ on an axis you can state serve better than one polished guess.
5. Write the inventory before drawing: flows, screens per flow, states per screen, components needed and which already exist.

## Core rules

- Values come from tokens. A raw hex, pixel size, or font name in a component is a finding unless the source system has no token for it.
- Components reference role tokens (`color-text-danger`), and role tokens reference primitives (`red-600`). Themes change the mapping between those two layers and nothing else.
- A component exists when the same structure appears a third time or when the system already defines it. Before that, it is markup on a screen.
- A variant is a choice the designer makes (kind, size, tone, density), while a state is a condition at run time (hover, focus, disabled, loading, error). Keep the two on separate axes and declare both lists per component.
- Interactive components show default, hover, focus-visible, active, disabled, and loading where the action is asynchronous. Inputs add filled, read-only, and invalid.
- A data-backed screen is designed in five states: ideal, empty, loading, error, partial. The ideal state comes first and the rest are designed against it.
- Empty has three causes that need different content: first use, the user cleared it, and no results.
- An error keeps what the user typed, says what happened in plain words, and offers the next action.
- Screens for the web work at phone width. State what stacks, wraps, scrolls, or hides.
- Use real content. Missing facts become visible placeholders such as `[PLAN PRICE]`; filler text and invented numbers hide layout problems.
- Real elements even in a mockup: `<button>`, `<a href>`, `<input>` with a `<label>`. Text contrast at least 4.5:1, and 3:1 for large text and for borders or icons that convey meaning.
- A change to scope found while designing (a new flow, a state missing from the PRD, or a requirement that cannot fit) goes back to the PRD or the requester before it is drawn as if agreed.

## Working with the prd skill

| PRD section | Becomes in the design |
|---|---|
| User stories (the role and outcome) | who each flow is for, the order of flows |
| Requirement bullets | what must be visible or operable on a screen |
| Failure bullets and reason codes | error states and their messages |
| Experience (flows, screens, states) | the canvas pages and state rows |
| Non-functional requirements (accessibility, localisation, compatibility) | contrast, keyboard paths, text expansion, supported sizes |
| Out of scope | what is left off the screens |
| Rollout plan (off switch) | the disabled state and its notice |

After designing, give the PRD's Experience table a link per flow, and raise each gap you found as an open question. The screen inventory and state rows are also the input for the `test-cases` skill: one case per screen state, with how to reach it.

## Other skills

When they are installed, hand detail to them: `better-colors` for palettes and contrast, `better-typography` for the type scale, `better-layout` for grouping and responsive structure, `better-writing` for interface copy, `better-accessibility` for keyboard, focus, and ARIA, `better-ui` for radius, shadow, and motion values, `ui` for building the page in code, `modern-web-guidance` before HTML or CSS work. `software-design` covers the code side of component boundaries.

## Review checklist

Flag in a design or a UI diff:

- Raw color, spacing, radius, or font values where a token exists; a component that references a primitive token directly.
- A new token or component that duplicates an existing one under another name.
- A component with variants mixed into states (`primary-hover` as a variant), or with states missing from its sheet.
- Focus not visible, or hover as the only sign that something is interactive.
- A disabled control with no explanation nearby when the reason is not obvious.
- A screen drawn only in its ideal state; an empty state that says "No data" and offers nothing to do.
- A loading state that is a blank area or a spinner over content whose shape is known.
- An error that clears the form, blames the user, or shows a raw code.
- A fixed-width page with no statement of phone behavior.
- Filler text, invented statistics, or sample names that hide real lengths.
- Controls drawn as styled `div`s; icon-only buttons with no accessible name.
- A design file with screens and components mixed on one page, unnamed artboards, or options renamed between rounds.
- Scope in the design that the PRD or request does not contain.

Report each finding with where it is and a concrete fix.
