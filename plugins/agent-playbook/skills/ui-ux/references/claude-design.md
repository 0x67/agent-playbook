# Laying out a Claude Design canvas

A Claude Design canvas is an artifact made from the Design type: artboards placed on a canvas, grouped into pages. This page covers how to organize one. The canvas's own `SKILL.md` and its `artifact-type/reference/` pages (`format.md`, `diagrams.md`, `craft.md`, `design-system-components.md`) define the file format and change with each release of the type. Read them from the canvas before writing, and follow them where they differ from this page.

## The pieces

| Piece | What it is | Where it is declared |
|---|---|---|
| Canvas | one design artifact | created once from the Design type; never create a second for the same work |
| Page | a named group of artboards | `pages` in `project/canvas.json`, up to 40 |
| Artboard | one frame, one `.dc.html` file | a `boards` entry with `x`, `y`, `w`, `h`, optional `title` and `page` |
| Note | a title or sticky on the canvas | `notes` in `project/canvas.json`; an agent writes only `kind: "title1"` and stickies (no `kind`) |
| Shared component | a `.dc.html` mounted by other artboards | `<dc-import name="Card">` mounts `Card.dc.html` |
| Component sheet | an artboard that mounts one component in each variant and state | `Card.sheet.dc.html` |
| Flow map | an artboard that diagrams one flow: a box per screen, a labelled arrow per transition | `Flow-Invite.dc.html`, built as the type's `diagrams.md` describes |
| System component | a real component from an installed design system | `<x-import component-from-global-scope="Ns.Button">` |
| Tweak | a control in the Tweaks tab | `data-props` on the artboard's script tag |

Notes of kind `rect`, `oval`, `pen`, `line`, `arrow`, and `image` are drawn by people. Keep them as they are, and draw arrows inside artboards instead (Flow maps, below).

## Pages

Use pages to separate kinds of work. A layout that holds up for a product feature:

| Page | Holds | Fidelity |
|---|---|---|
| `Flows` | each flow's map, then its screens in order, ideal state | high |
| `States` | per screen: empty, loading, error, partial, and the edge cases | high |
| `Components` | shared components, each beside its sheet | high |
| `Explorations` | direction options and wireframes | low |

1. Create a page only when it has artboards. One screen with three states needs one page.
2. Give pages short ids and plain names. The first listed page is the default for an artboard with no `page`.
3. Keep explorations apart from agreed work, so a reader does not mistake an option for the design.
4. A large product gets a page per area (`Billing`, `Onboarding`) with flows and states together in rows, plus one shared `Components` page.
5. For a product that already exists in code, a screen's as-is row sits directly above its to-be row on the same page (`references/existing-product.md`).
6. Never move or resize an artboard from memory. People rearrange the canvas by hand; read `project/canvas.json` again before placing anything, and put new frames in free space.

## Rows and placement

1. One row per flow on `Flows`: its flow map first, then the screens left to right in the order the user meets them.
2. One row per screen on `States`: ideal first as the reference, then empty, loading, error, partial, then edge cases.
3. Leave 80px between frames in a row and 120px between rows. A row with change notes under it gets the extra room those notes need (Marking changes, below).
4. A row of several artboards gets a title note (`kind: "title1"`) above it, at least 223px above the row. One artboard alone does not need a title note; its name strip shows its `title`.
5. Use a sticky note for a reviewer's question, a constraint, or a change note. Rationale and option trade-offs go in your reply and stay off the artboards.
6. Frames never overlap. A frame that grows shifts its neighbours along.

## Naming

1. The first artboard is `Main.dc.html`. Other file names are unique stems made of letters, digits, `_`, `.`, and `-`.
2. Name files so they sort and read: `Members.dc.html`, `Members-empty.dc.html`, `Members-error.dc.html`, `InviteDialog.dc.html`. A component's sheet adds `.sheet` to its stem (`MemberRow.sheet.dc.html`), and a flow map starts with `Flow-` (`Flow-Invite.dc.html`).
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
| Hover, focus, pressed, disabled of one component | its sheet artboard, `<Comp>.sheet.dc.html` (Component separation) |

1. Tweaks are levers. Declare few of them, for behavior and for values used in many places. Write copy as literal text so a viewer can retype it in place, and a color used once is edited in the properties panel.
2. A tweak hides the other values from a reviewer who does not open the panel. When the states must be seen side by side, use artboards.
3. Only artboards whose controls work get `"is_interactive": true`.

## Component separation

1. With a design system installed that has a bundle, mount its real components with `<x-import>`. Do not rebuild them as markup, and do not define your own components in a script (`window.X`): people cannot select or edit what those draw.
2. Screens, layout, and copy stay artboard markup.
3. Structure the system lacks becomes its own `.dc.html`, mounted with `<dc-import>`, when the screen inventory lists it on two or more screens or when it turns up a third time while drawing.
4. Each `.dc.html` outside `project/ds/` shows on the canvas as an artboard, imported ones included. List each in `boards` and place the shared ones on the `Components` page.
5. A component file draws one instance from its props, because `<dc-import>` mounts the whole file. Editing it updates every artboard on the canvas that mounts it.
6. Declare each variant axis as an `enum` prop in the component's `data-props`, with the values its code uses (`kind`, `size`, `tone`). A static canvas cannot hover or focus, so add a `previewState` enum (`default`, `hover`, `focus`, `active`, `disabled`, `loading`) that forces the look; an artboard sets it as `preview-state="hover"`.
7. The grid of variants and states is a separate sheet artboard, `<Comp>.sheet.dc.html`, that mounts the component once per cell and labels rows and columns with the code's names (`references/components.md`, The state sheet). Place the component, sized by its `$preview`, and its sheet side by side on the `Components` page.
8. Pass data to a child through attributes, declared in the child's `data-props` (`"editor": null` for objects and callbacks). Give `hint-size` the child's root size.
9. A component that is reused on the canvas and belongs to the product goes into the design system (its guidelines, preview, and tokens), and the canvas then mounts it from there. An installed system is copied into each canvas, and that copy changes only when the system is installed again.

## Flow maps

People draw arrows between artboards; an agent's arrows go inside an artboard.

1. Each flow with more than two screens, or with any branch, gets a map artboard at the start of its row. Read the type's `diagrams.md` before writing one: it is a diagram host with each element placed in px, and the canvas's flex and grid rule does not apply to it.
2. One box per screen, labelled with that screen's board title. One arrow per transition, labelled with what triggers it: "tap Invite", "email already invited", "server error".
3. Boxes hold text and inline tags only. The map gives each screen's title, and the screens themselves sit to its right in the same row.
4. Each arrow's `aria-label` says what it joins and when: "From Members to Invite dialog, on tap Invite".
5. Arrows do not follow boxes, so moving a box means working out every arrow it touches again. Keep the main path on one line and the branches below it.
6. Prototype links (`<a href>`) make a flow clickable in Play and draw nothing on the canvas. A flow asked for as a prototype gets both the links and its map.
7. A person's arrow note stays where it was drawn when frames move. Place new frames in free space, and say in the reply when a move leaves such an arrow pointing at the wrong place.

## Marking changes

On a revision, and on the to-be row of an existing product, each frame that changed gets a change note: a sticky under the frame.

1. Use `fill` `green` for a new frame and `orange` for a changed one.
2. The text says what changed and what it replaced: "Changed: Save moves to the footer (was in the header)." Keep one note per frame with a few lines; a longer list goes in the reply.
3. Put the notes in a strip under the row, each one at most its frame's width. A sticky can grow to 4/3 of its `w` in height, so leave that much clear below the row before the next one starts.
4. Change notes belong to one review round. Remove them when the user accepts the change.

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

1. Inventory (`references/screens.md`, and `references/existing-product.md` when the product exists in code), then the design system decision.
2. Direction options on `Explorations`, when the look is open, drawn as plain markup. Wait for the choice.
3. The `Components` page: each component the inventory lists on two or more screens that the system lacks, with its sheet.
4. The main flow at high fidelity, ideal states, on `Flows`, built from those components, with its flow map.
5. State rows on `States`.
6. Move any other structure that turns up a third time into a component.
7. Links between screens when a prototype was asked for.
8. Change notes, on a revision or a to-be row.
9. Report: the link, what was made and assumed, and which inventory items remain.

On a revision, change only what was asked, read the index again before any layout change, and send only the files that changed.

## Sources

The Design artifact type's `SKILL.md`, `format.md`, `diagrams.md`, `craft.md`, and `design-system-components.md`, read from the type on claude.ai (release 1795031767-284a, contract 0.2.47). The page layout, row order, naming scheme, sheet artboards, flow maps, and change note colors above are this skill's conventions; the type does not prescribe them.
