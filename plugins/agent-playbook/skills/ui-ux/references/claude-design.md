# Laying out a Claude Design canvas

A Claude Design canvas is an artifact made from the Design type: artboards placed on a canvas, grouped into pages. This page covers how to organize one. The canvas's own `SKILL.md` and its `artifact-type/reference/` pages (`format.md`, `craft.md`, `design-system-components.md`) define the file format and change with each release of the type. Read them from the canvas before writing, and follow them where they differ from this page.

## The pieces

| Piece | What it is | Where it is declared |
|---|---|---|
| Canvas | one design artifact | created once from the Design type; never create a second for the same work |
| Page | a named group of artboards | `pages` in `project/canvas.json`, up to 40 |
| Artboard | one frame, one `.dc.html` file | a `boards` entry with `x`, `y`, `w`, `h`, optional `title` and `page` |
| Note | a title or sticky on the canvas | `notes` in `project/canvas.json` |
| Shared component | a `.dc.html` mounted by other artboards | `<dc-import name="Card">` mounts `Card.dc.html` |
| System component | a real component from an installed design system | `<x-import component-from-global-scope="Ns.Button">` |
| Tweak | a control in the Tweaks tab | `data-props` on the artboard's script tag |

## Pages

Use pages to separate kinds of work. A layout that holds up for a product feature:

| Page | Holds | Fidelity |
|---|---|---|
| `Flows` | each flow's screens in order, ideal state | high |
| `States` | per screen: empty, loading, error, partial, and the edge cases | high |
| `Components` | shared components, each with its variant and state sheet | high |
| `Explorations` | direction options and wireframes | low |

1. Create a page only when it has artboards. One screen with three states needs one page.
2. Give pages short ids and plain names. The first listed page is the default for an artboard with no `page`.
3. Keep explorations apart from agreed work, so a reader does not mistake an option for the design.
4. A large product gets a page per area (`Billing`, `Onboarding`) with flows and states together in rows, plus one shared `Components` page.
5. Never move or resize an artboard from memory. People rearrange the canvas by hand; read `project/canvas.json` again before placing anything, and put new frames in free space.

## Rows and placement

1. One row per flow on `Flows`: screens left to right in the order the user meets them.
2. One row per screen on `States`: ideal first as the reference, then empty, loading, error, partial, then edge cases.
3. Leave 80px between frames in a row and 120px between rows.
4. A row of several artboards gets a title note (`kind: "title1"`) above it, at least 223px above the row. One artboard alone does not need a title note; its name strip shows its `title`.
5. Use a sticky note for a reviewer's question or a constraint. Rationale and option trade-offs go in your reply and stay off the artboards.
6. Frames never overlap. A frame that grows shifts its neighbours along.

## Naming

1. The first artboard is `Main.dc.html`. Other file names are unique stems made of letters, digits, `_`, `.`, and `-`.
2. Name files so they sort and read: `Members.dc.html`, `Members-empty.dc.html`, `Members-error.dc.html`, `InviteDialog.dc.html`.
3. Give each board a `title` a reviewer would say aloud ("Members: empty, first use") and each file its own `<title>`.
4. Component files are named for the component as code names it (`MemberRow.dc.html`), since `<dc-import name="MemberRow">` uses the stem.
5. Do not rename options. "Option B" or "Dense table" keeps that name in later rounds.

## Screens and sizes

1. A web page, dashboard, or app screen is a page-type artboard: `"expand": "fill"` on its entry, a fluid root with a `max-width` container, and a width of 1280 to 1440. Its `h` is the page's height at that width; too tall is better than clipped.
2. A phone app screen is a fixed 390×844 root. Posters, social graphics, and print are fixed too.
3. Lay out sibling groups with flex or grid and `gap`, so edits made by dragging on the canvas keep their spacing.
4. Add layout guides to an entry only when a column grid helps, and then lay the content on them.

## State variants: artboard, tweak, or interaction

| The difference | Show it as |
|---|---|
| Screen states a reviewer compares (ideal, empty, loading, error, partial) | separate artboards in one row |
| Direction options | separate artboards on `Explorations` |
| A switch that cuts across the design (dark, density, accent, a variant enum, item count) | a tweak in `data-props` |
| States reached by acting (selected tab, open menu, valid form enabling submit) | `state` and handlers in one artboard, marked `"is_interactive": true` |
| Hover, focus, pressed, disabled of one component | a static state sheet on the component's artboard |

1. Tweaks are levers. Declare few of them, for behavior and for values used in many places. Write copy as literal text so a viewer can retype it in place, and a color used once is edited in the properties panel.
2. A tweak hides the other values from a reviewer who does not open the panel. When the states must be seen side by side, use artboards.
3. Only artboards whose controls work get `"is_interactive": true`.

## Component separation

1. With a design system installed that has a bundle, mount its real components with `<x-import>`. Do not rebuild them as markup, and do not define your own components in a script (`window.X`): people cannot select or edit what those draw.
2. Screens, layout, and copy stay artboard markup.
3. Structure reused across artboards that the system lacks becomes its own `.dc.html`, mounted with `<dc-import>`. Extract on the third use, as in code.
4. Each `.dc.html` outside `project/ds/` shows on the canvas as an artboard, imported ones included. List each in `boards` and place the shared ones on the `Components` page.
5. A shared component's artboard is also its state sheet: render it in its variants and states there, sized by its `$preview`.
6. Pass data to a child through attributes, declared in the child's `data-props` (`"editor": null` for objects and callbacks). Give `hint-size` the child's root size.
7. A component that is reused on the canvas and belongs to the product goes into the design system (its guidelines, preview, and tokens), and the canvas then mounts it from there.

## Design system on the canvas

1. Settle the system before any look: the one the user or the session names, else the account default, else ask which of the listed systems to use. With nobody to ask, build with your own look and say so.
2. Read the system's `project/README.md` and `project/tokens.json`, never its page.
3. Install it on the canvas (its `tokens.json` under `project/ds/<folder>/` plus a `designSystems` record in the index), or the editor's color and text-style menus show bare values.
4. Use its tokens and its icon component. Inline stroke SVG is for an icon the system lacks; emoji are never icons.

## Prototypes

1. A clickable prototype is one artboard per screen, joined by links: `<a href="Cart.dc.html">` moves Play to that artboard.
2. Style the `<a>` as the button. A `<button>` inside it swallows the click.
3. Each artboard has its own `state`. A flow that must share state across screens is one artboard with a state field and one `<sc-if>` per screen.
4. Set `launch` to the focused view of the first screen when the canvas is mainly a prototype.

## Order of work

1. Inventory (`references/screens.md`), then the design system decision.
2. Direction options on `Explorations`, when the look is open. Wait for the choice.
3. The main flow at high fidelity, ideal states, on `Flows`.
4. State rows on `States`.
5. Extract shared structure to the `Components` page on its third use.
6. Links between screens when a prototype was asked for.
7. Report: the link, what was made and assumed, and which inventory items remain.

On a revision, change only what was asked, read the index again before any layout change, and send only the files that changed.

## Sources

The Design artifact type's `SKILL.md`, `format.md`, `craft.md`, and `design-system-components.md`, read from the type on claude.ai (contract 0.2.47). The page layout, row order, and naming scheme above are this skill's conventions; the type does not prescribe them.
