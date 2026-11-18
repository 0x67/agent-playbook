# Screens, flows, and screen states

## Inventory first

Before drawing, write a table and show it to the user:

| Flow | Step | Screen | States | Components needed | New or existing |
|---|---|---|---|---|---|
| Invite a member | 1 | Members list | ideal, empty (first use), loading, error | Table, Button, Empty block | existing |
| Invite a member | 2 | Invite dialog | default, invalid email, sending, sent, failed | Dialog, Field, Button | existing |

1. With a PRD, copy its Experience table and add the component columns. Without one, derive flows from the request and the current product, and mark what you assumed.
2. A flow starts where the user is and ends when their goal is met or abandoned. Include the way in (a link, a notification, a deep link) and the way out.
3. One screen can serve several flows. List it once per flow, and design it once.
4. The inventory is also the scope. A screen that is not on it is not designed without asking.

## Flows

1. Design the main path first, end to end, at low fidelity.
2. Then the branches: validation failure, permission denied, cancel, back, timeout, the second visit.
3. Count the steps. Each one is a chance to drop out; remove a step when a sensible default can replace a question.
4. State where data comes from at each step and what is saved when the user leaves halfway.
5. A destructive action gets a confirmation that states what will be lost, or an undo. Prefer undo.

## Screen states

Each data-backed screen has up to five states. Design the ideal state first; the others lead to it.

| State | When | Must contain |
|---|---|---|
| Ideal | data present, nothing wrong | the content and the main action at their best |
| Empty | nothing to show | why it is empty and what to do next |
| Loading | waiting for data or an action | the layout of what is coming |
| Error | something failed | what happened, what is safe, the next action |
| Partial | some data, sparse or incomplete | the data there is, and a pull toward the ideal state |

### Empty

Each cause needs its own design:

1. First use: say what this screen is for and offer the first action. Sample content or a small example works better than "Nothing to see here".
2. Cleared by the user (an emptied inbox, all tasks done): confirm it and point to what comes next.
3. No results: repeat the query, suggest the closest match or a wider search, and offer to clear filters.

### Loading

1. Give immediate feedback on the control for a wait under about a second, with no looped animation. For a longer wait on content whose layout is known, use a skeleton that matches it. Past about 10 seconds, show percent done (thresholds in `references/components.md`, Motion).
2. A blank area or a full-screen spinner hides the structure the user is waiting for.
3. Keep what is already on screen while more loads. Do not replace a list with a spinner to fetch its next page.
4. Where the action nearly always succeeds, show the result at once and reconcile on failure.
5. Long work (seconds to minutes) needs progress and the option to leave and come back.

### Error

1. Keep what the user typed. Never clear a form on failure.
2. Say what happened and what to do in plain words, without codes or blame.
3. Put the message next to its cause. A field error goes at the field and a section failure in the section.
4. Offer the action: retry, edit, contact support with the reference.
5. Show errors in place, without a page reload.
6. Cover the kinds: validation, permission, not found, offline, server failure, and a conflict with someone else's change.
7. Match the presentation to the scope: a field error inline, a failed section inside that section, a toast only for brief feedback that does not block the user, a dialog only when the user must acknowledge or decide, a full page only when the main content cannot show. An error the user must understand stays until they dismiss it or fix the cause.
8. When a refresh fails and earlier data is on screen, keep the data and say it may be out of date: "Showing previously loaded data. We could not refresh it right now." No data, could not load, and may be out of date are three different messages.
9. Offer retry on a write (create an order, charge a card, send a message) only when repeating it is safe. Otherwise show a pending state until the outcome is known.
10. Never show a stack trace. Give a request reference the user can quote to support, such as `req_9f82a1`.

### Success

1. Show success only after the system that stores the record confirms it. A success badge shown when a request is sent reports something nobody has checked yet.
2. An action that is sent now and checked later has four states: Requested, Confirmed, Could not check, and Failed. Could not check is the one teams forget.
3. Show on the screen which system confirmed it. With no confirming system, the screen says Requested.

### Partial

1. One item in a layout built for many should still look intended.
2. Show progress toward the ideal state when the user controls it (profile completeness, setup steps).
3. A screen with several sections handles each section's loading, error, and empty state separately. One failed panel does not blank the page.

### Transitions

Decide how the screen moves between states: what appears, what holds its position, and what gains focus. Content that jumps when loading ends is a defect.

## Other conditions

Walk these for each screen and draw the ones that change the layout:

1. Permissions: a viewer who cannot act (the action is replaced by who can, as in the Blocked state in `references/components.md`), a feature switched off (the page stays reachable, the action is disabled, a notice explains).
2. Limits: the longest name, the largest number, 0 and 1 and 10,000 items, quota reached.
3. Offline or stale data.
4. Locale: text about 30% longer, right-to-left, other date and number formats (the system's locale formats in `references/design-system.md`).
5. Accessibility settings: 200% zoom, reduced motion, high contrast.
6. First run versus returning user.

## Responsive behavior

1. A web page is fluid: a `max-width` container, grids that collapse to one column, tables that scroll inside their own box.
2. For each screen, state what happens to navigation, toolbars, tables, and side panels at phone width: stack, wrap, scroll, or move behind a control.
3. Design at phone width as you go. Headlines that break badly and grids squeezed to unreadable columns show up early there.
4. Fixed sizes are for fixed formats: device mockups (a phone app at 390×844), posters, print, social graphics.
5. Do not draw fake device chrome (status bar, keyboard) in a mobile mockup.
6. Check each stated width in a rendered capture, side by side. When two widths look the same, suspect the harness before the component. A component inside a fixed-width wrapper still responds to the viewport's media queries, and its demo needs container queries to respond to the wrapper.
7. Keep the reading order the same at every width. Reordering with CSS `order` makes keyboard focus and screen readers follow a different sequence from the eye.

## Fidelity

| Stage | Use | Looks like |
|---|---|---|
| Wireframe | choosing structure and flow | boxes, real labels, little color, 3 to 5 distinct approaches |
| Direction options | choosing the look | 2 to 4 low-fidelity boards that differ on a stated axis |
| High fidelity | agreeing the design | real tokens, real components, real content |
| Prototype | testing the flow | screens joined by links, working controls where they matter |

1. Settle direction at low fidelity before building the whole deliverable.
2. Give each option its reasoning and its main cost in your reply. Keep option names fixed across rounds.
3. High-fidelity work starts from the product's real context: its code, its system, screenshots. A mockup from nothing is the last resort.
4. A small requested change stays small. Finish it, then suggest wider changes separately.
5. Approve type, color, and icons on one or two pilot screens before drawing the rest. One team picked colors after nearly 150 screens and repainted them four times.
6. Draw wireframes in greyscale with every fill bound to a role token. A theme then supplies the colors later and changes every screen at once.
7. Use one filled button per screen, the action color only on things that can be pressed, and the alert color only for errors and live status.

## Handoff

1. Per screen: the states designed, the components and variants used by their code names, the tokens for anything not covered by a component.
2. Behavior that a picture cannot show: focus order, keyboard actions, what is announced, timings, validation rules.
3. Content rules: maximum lengths, truncation, pluralization, empty values.
4. What is out of scope, and which open questions remain, linked to the PRD when there is one.

## Sources

- Scott Hurff, "Why your user interface is awkward: you're ignoring the UI stack": https://www.scotthurff.com/posts/why-your-user-interface-is-awkward-youre-ignoring-the-ui-stack/
- The Design artifact type's `craft.md`, read from the type on claude.ai.
- Design Systems Collective, "Design Error States Before They Break Your App" (scope, stale data, safe retry): https://www.designsystemscollective.com/design-error-states-before-they-break-your-app-b0603eaa120e
- Design Systems Collective, "Sometimes the missing component is a missing pattern" (confirmed success): https://www.designsystemscollective.com/the-missing-component-might-be-a-missing-pattern-b1df373acfd2
- Design Systems Collective, "Three widths, two identical screenshots": https://www.designsystemscollective.com/three-widths-two-identical-screenshots-c4e09238bf3b
- Design Systems Collective, "Designing in pairs: a PM, Claude and Figma" (pilot screens, greyscale wireframes, visual budget): https://www.designsystemscollective.com/designing-in-pairs-a-pm-claude-and-figma-0ebc8ca8f1ba
