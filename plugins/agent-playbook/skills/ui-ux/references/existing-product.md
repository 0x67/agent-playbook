# Starting from an existing product

Use this page when the repository has UI code and is missing a design system, screen designs, or designs for some of its screens. The code is what users run, so it is the first record of the product's tokens, components, and screens.

## Pick the starting point

| The repository has | Do |
|---|---|
| UI code only | every section below |
| UI code and a system, no designs | Screens from code, then As-is and to-be |
| UI code and designs for some screens | every section below, plus Coverage |
| no UI code | `references/design-system.md` (no source at all), then `references/screens.md`; this page does not apply |

## Tokens from code

1. Read the config sources first: `tailwind.config.*`, CSS custom properties, a theme object, token JSON. Values defined there are primitives already.
2. When there are none, collect the raw values from stylesheets and component styles: colors, font families, font sizes with their line heights, spacing, radii, shadows. Record how often each value is used and in which files.
3. The values used most become primitives. Give each use a role from its job (body text, muted text, page background, action, danger), and point the role at a primitive.
4. Everything left over goes on a drift list: the value, its uses, its files, and the nearest primitive. Propose merges in the reply and wait for approval. Do not snap values in the system or in the code (`references/design-system.md`, Start from what exists).
5. Until the user approves the system, check new work against the proposed roles. Raw values already in the code are drift list entries, and a screen that uses them is not a finding on its own.

## Components from code

1. List the component folder. For each component the screen inventory needs, record its props, which props are variant axes (`variant`, `size`, `tone`), and which states its code handles (disabled, loading, error branches).
2. A state the code lacks is a finding: a button on an asynchronous action with no loading state, an input with no invalid style.
3. Components that do the same job under different names (`PrimaryButton` and `Button kind="primary"`) go on the drift list with their consumers.
4. Use the code's names for components, props, and values in the design.
5. Write the system as a Design System artifact (`references/design-system.md`, As a Claude Design System artifact). A system with no bundle has its components rebuilt on the canvas as `.dc.html` files (`references/claude-design.md`, Component separation), and each board `title` gives the file it mirrors, such as `src/components/Button.tsx`.

## Screens from code

1. Read the router: the route table, the `pages/` or `app/` directory, the navigation config. Each route is a screen, and so is each dialog, drawer, or wizard step opened from it.
2. For each screen, record the states its code handles (loading, empty, error branches) and the ones it lacks. A missing state is a finding.
3. The task decides what is drawn: the screens it changes and the screens a user passes through to reach them. List the other screens in the inventory without drawing them.

## As-is and to-be

1. A screen that exists in code is drawn as it is first, from the code and from a screenshot when there is one, using the system's components. Its title says so: "Members: as-is".
2. The proposed design goes in a to-be row under it, frames in the same order. Each frame that changes gets a change note (`references/claude-design.md`, Marking changes).
3. A new screen has only a to-be frame.

## Coverage

When designs exist for some screens (a Figma file, a canvas, screenshots in tickets), add a Design source column to the screen inventory with one of three values: designed, code only, none.

1. Where a design and the code disagree, list each difference and ask which one to follow. Without an answer, draw the as-is frame from the code and treat the design as the intended to-be.
2. Link a designed screen from the inventory instead of redrawing it, unless the task changes it.
