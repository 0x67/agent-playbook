# Components, variants, and states

## What becomes a component

1. The system already defines it: use that one.
2. The screen inventory lists it on two or more screens: build it before the screens that use it.
3. The same structure with the same behavior turns up a third time while drawing: extract it. Before that it is markup on the screen. Things that look alike today and will change for different reasons are separate components.
4. A screen is not a component. Layout and copy that belong to one screen stay there.
5. Split a component when its variants stop sharing structure (a "card" whose variants have different parts is several components).

## Levels

| Level | Examples | Knows about |
|---|---|---|
| Primitive | Button, Input, Checkbox, Badge, Icon | tokens only |
| Composite | Field (label, input, hint, error), Menu, Dialog, Table row | primitives |
| Pattern | Sign-in form, Filter bar, Empty state block | composites and product copy |
| Screen | Billing, Project list | patterns and data |

Dependencies point down the table. A primitive that reads product data or another product's copy has been placed at the wrong level.

## Anatomy

1. List the parts by name (container, label, leading icon, trailing icon, helper text) before listing variants.
2. Mark each part required or optional.
3. State what the consumer fills (label text, icon choice, children) and what the component controls (spacing, focus ring, loading spinner).
4. Give sizes for the parts that affect touch: interactive targets are at least 44px on touch screens.

## Variants

A variant is a choice made at design time. Keep each kind of choice on its own axis:

| Axis | Typical values |
|---|---|
| Kind or emphasis | primary, secondary, ghost, destructive |
| Size | sm, md, lg |
| Tone | neutral, success, warning, danger |
| Shape or content | with icon, icon only, full width |
| Density | comfortable, compact |

1. Use the same axis names and values across components (`size: sm | md | lg` on Button, Input, and Select alike).
2. Name variants as the code does, so the design property and the prop match.
3. An axis with one value is not an axis. An axis used once in the product may be a one-off style.
4. Cap the kinds. Three or four emphasis levels cover most products; a fifth usually duplicates one.
5. Combinations that do not make sense are stated as unsupported (a destructive ghost icon-only button, for example) so nobody draws or builds them.
6. When one component serves different tasks on different surfaces, the product picks the variant by task, and the viewport width does not switch it. An approval component, for example, has a row for reviewing many in a queue (32px actions), a detail view for working on one (44px), and a focus view for deciding one on a phone, with status first and the actions stacked (44px). On a desktop, a narrow side panel still shows the row. Inside each variant the layout wraps and stays fluid down to 320px, without horizontal scroll.
7. Count the cells before adding an axis: 4 kinds × 3 sizes × 5 states × 2 icon positions × 2 themes × 2 loading values make 480. Add a variant only when a real use case needs it and it changes meaning, hierarchy, or structure. A boolean prop, a slot, or a theme covers the rest.

## States

A state is a condition at run time. It applies on top of any variant.

| State | Applies to | Shows |
|---|---|---|
| Default | all | resting appearance |
| Hover | pointer devices | a pointer is over it; never the only sign of interactivity |
| Focus-visible | all interactive | a ring at 3:1 against what is behind it |
| Active / pressed | all interactive | the press itself |
| Disabled | all interactive | not available until something on the screen changes (a required field, a save in progress); say why nearby when the reason is not obvious |
| Blocked | actions the viewer may not take | the action replaced by who can take it, in visible text, with the item still in view |
| Loading | async actions | work in progress, with the control's size unchanged |
| Selected / checked / on | toggles, tabs, options | the current choice |
| Invalid | inputs | the error and its message |
| Warning | inputs | a value that is allowed but questionable, and its message |
| Read-only | inputs | a value that can be copied but not edited |
| Filled / empty | inputs | with and without a value, placeholder included |
| Expanded / collapsed | disclosures, menus | open and closed |
| Dragging / drop target | sortable items | the lift and the landing spot |

1. Touch screens have no hover. A design that hides an action behind hover needs another way to reach it there.
2. Disabled and loading both block the action, but they read differently: loading promises a result.
3. Success is usually feedback on the screen (a notice, a changed value) and not a lasting state of the control.
4. Decide what wins when states meet: disabled over everything, then loading, then invalid, then focus and hover. Write the order down per component.
5. Draw the transitions a user must notice. A submit button goes from disabled to enabled when the form is valid, then to loading, then back with the result.
6. Disabled clears when something on the screen changes. Blocked means the viewer is not allowed to decide: remove the action, say who can ("Needs a regional manager"), offer the step that sends it there ("Send to regional manager"), and keep the item and its summary in view. Show the reason as text beside a neutral badge or lock icon, and hide the icon from assistive technology.

### Selected styles

Pick the selected style by what the choice does, and use the same style for that kind of choice across the product. One product settled on these five:

| Choice | Does | Selected style |
|---|---|---|
| Tab | moves to different content | a filled container in the brand color |
| View switch | shows the same content another way | a raised white pill on a grey rail |
| Filter | narrows the list in view | text weight and color |
| Picture choice | picks an image or option card | a brand-colored border |
| Menu item | sets an option | a checkmark |

1. Give a filter or a view switch a button group or radio group role. Built from a tabs primitive, it announces a tab list that goes nowhere.
2. The chosen option differs from its neighbors in brightness, or has a border or shadow. A tint close in brightness to its background flickers at the edge and is easy to miss.
3. Write the rule down. In that product, 34 single-choice controls showed the chosen option 8 different ways while the brand guide said nothing, and each screen or agent filled the gap its own way.

## The state sheet

Per component, lay the states out as a grid: one row per variant, one column per state. On a Claude Design canvas the grid is its own artboard (`references/claude-design.md`, Component separation).

1. List the combinations before drawing. An input's value, interaction, status, and validation states multiply into dozens of combinations. Draw the ones people will see, and let the precedence order under States settle the rest.
2. For a button with 4 kinds and 3 sizes, show all kinds at one size across the states, then the sizes once in the default state.
3. Label rows and columns with the variant and state names used in code.
4. Add the content cases that break layouts: the longest label, a translated label about 30% longer, no icon, a two-line value, right-to-left.
5. Show each theme.
6. For an input, the critical cells are: empty, filled, focused while empty, focused while filled, invalid with message, disabled, read-only, loading.

## Motion

Start with the essentials, which every product needs. Add the overlay level when the screen inventory has menus, dialogs, drawers, or toasts, and the navigation level only when views animate into each other or motion is part of the brand.

### Essentials: every product

| Moment | Duration | Source |
|---|---|---|
| Toggle, checkbox, switch | about 100 ms (Carbon uses 70 ms, Material 3 uses 200 ms for selection controls) | NN/g; Material 2 speed; Carbon; Material 3 tokens |
| Hover, press | 150 ms or less, or instant | The State Problem; `better-ui` |
| Focus ring | instant | The State Problem |

1. Animate color, opacity, and transform. Animating width, height, or position in the layout makes content jump and forces the browser to recalculate the layout.
2. Loading feedback follows the wait (NN/g): under about 1 second, no looped animation; about 2 to 10 seconds, a looped indicator or a skeleton; 10 seconds or more, percent done and an estimate of the finish time.
3. Every animated change also leaves a static cue (a color, an icon, a label). A status message such as "Saved" or "Copied" is announced to assistive technology without moving focus (WCAG 4.1.3, Level AA): `role="status"` for results, `role="alert"` for errors.
4. Respect the reduced-motion setting (`prefers-reduced-motion`). WCAG 2.3.3 (Level AAA) asks that motion triggered by interaction can be turned off unless it is essential. Under Reduce Motion, Apple's guidelines replace movement along x, y, and z with fades, avoid animating blur and depth, and cut automatic and repeating animation. Keep indicators that show information, such as progress.
5. Anything that starts moving on its own and lasts more than five seconds (a carousel, a ticker) gets a pause, stop, or hide control (WCAG 2.2.2, Level A).
6. Skip animation in rapid sequences and frequent interactions: arrow keys through a menu, a value that updates several times a second (Apple Motion guidelines; Motion Belongs in the Design System).
7. Show text that already exists all at once. A typewriter effect on stored text slows reading; stream text only as the system produces it, as with a chat reply that is still being written. This rule is this skill's own and has no published source.

### Overlays: menus, dialogs, drawers, toasts

| Moment | Duration | Source |
|---|---|---|
| Tooltip | about 300 ms delay, then a 150 ms fade | The State Problem |
| Small element appearing or expanding a short distance (menu, popover, disclosure) | 150 ms (Carbon `moderate-01`) to 200 ms (Material 3, small area) | Carbon; Material 3 applying |
| Larger expansion, toast entering and leaving | about 240 ms (Carbon `moderate-02`) | Carbon |
| Dialog | 200 to 300 ms | NN/g |
| Drawer or sheet from an edge | enter 250 ms, exit 200 ms (a persistent sheet 300 and 250 ms) | Material 2 speed; Material 3 applying |

1. Keep most transitions between 100 and 500 ms. Duration grows with the size of the change and the distance travelled, and 500 ms already feels slow to users (NN/g, Material 3, Carbon).
2. Exits are shorter than enters, because the user's attention has moved on. Material 3 pairs a 500 ms enter with a 200 ms exit, and in Material 2 a drawer opens in 250 ms and closes in 200 ms. Enters use decelerating easing and exits accelerating easing.
3. Store motion as a few tokens: three or four durations and standard, enter, and exit easings, taken from the product's own set or a published one (below).
4. A toast that disappears on its own may only show information the user can find elsewhere (WCAG 2.2.1). One with an action stays until the user acts or dismisses it. Material 3 lets an action-free snackbar dismiss after 4 to 10 seconds depending on platform, and advises against auto-dismiss on the web without inline feedback. Apple's guidelines ask to minimize time-boxed elements.

### Navigation and motion-led products

| Moment | Duration | Source |
|---|---|---|
| Card growing into a full-screen view | 300 ms (Material 2) to 500 ms (Material 3, emphasized easing) | Material 2 speed; Material 3 tokens |

1. Material 2's motion system picks the navigation transition by how the two views relate. A card or list item growing into its detail uses a container transform; forward and back between steps, or between parent and child, use a shared axis; a switch between unrelated destinations uses a fade through; dialogs, menus, and snackbars inside the screen use a plain fade. On the web, the View Transition API animates between views (`document.startViewTransition()`, `view-transition-name`).
2. A full token scale, from the product or from a published set:
   - Material 3: durations `short1` to `extra-long4`, 50 to 1000 ms; easing standard `cubic-bezier(0.2, 0, 0, 1)`, decelerate `cubic-bezier(0, 0, 0, 1)`, accelerate `cubic-bezier(0.3, 0, 1, 1)`. Material 3 marks this set as no longer maintained since its Expressive update and still uses it for transitions.
   - Carbon: `fast-01` 70 ms, `fast-02` 110 ms, `moderate-01` 150 ms, `moderate-02` 240 ms, `slow-01` 400 ms, `slow-02` 700 ms; productive easings for everyday interface motion and expressive easings for occasional important moments.
3. A product built around motion (a game, an onboarding sequence, a brand site) also names its patterns, documents each one, and gives motion an owner.

Exact curves and recipes come from `better-ui`, and the accessibility requirements from `better-accessibility`.

## Props and composition

1. One prop per variant axis, as an enum. Boolean props are for real on/off conditions (`disabled`, `loading`). A choice between kinds is an enum.
2. Do not add a prop for a difference that appears once. Style that one place.
3. Prefer composition to configuration when contents vary: a Dialog with header, body, and footer slots outlasts a Dialog with twelve props.
4. A composite connects its own parts (the Field links label, input, hint, and error message for assistive technology). The consumer should not have to repeat it.
5. A component does not set its own outer margin. The parent's layout and `gap` place it.
6. State that the consumer controls (selected value, open or closed) is passed in. State that is purely visual (hover, press) stays inside.

## Guidelines per component

Write, in this order: what it is for, when to use something else, anatomy, variants, states, what the consumer supplies, do and do not with real examples, accessibility notes (role, keyboard, accessible name).

Published kits follow a similar page: Collective Kit's button page has When to use, Variants (types, sizes), Interaction states, Accessibility considerations for design and for code, and Best practices. Two details from it are worth copying: a disabled control is still visible and perceivable (`aria-disabled="true"` when it must remain discoverable), and hover and focus states exist on the quietest variants too. One detail is worth avoiding: it lists success, error, and warning under "States". Those are tones chosen at design time, so they are a variant axis.

## Sources

- Scott Hurff, "Why your user interface is awkward: you're ignoring the UI stack" (the disabled, enabled, sending, failed sequence): https://www.scotthurff.com/posts/why-your-user-interface-is-awkward-youre-ignoring-the-ui-stack/
- Always Twisted, "Design token naming conventions" (variant, state, mode order): https://www.alwaystwisted.com/articles/design-token-naming-conventions
- Collective Kit docs, Button: https://collectivekit.co/Docs/button
- Design Systems Collective, "The State Problem: How to Design (and Build) Components That Change" (state combinations, critical input cells, transition timings): https://www.designsystemscollective.com/the-state-problem-how-to-design-and-build-components-that-change-3a0e49e8a0a0
- Design Systems Collective, "Blocked is not disabled": https://www.designsystemscollective.com/blocked-is-not-disabled-0bf68aeaa6c1
- Design Systems Collective, "The Control Nobody Wrote Down" (selected styles): https://www.designsystemscollective.com/the-control-nobody-wrote-down-ed75152bf5e6
- Design Systems Collective, "Choose the variant by task, not by breakpoint": https://www.designsystemscollective.com/choose-the-variant-by-task-not-by-breakpoint-8a94f093873d
- Design Systems Collective, "Shape to System: A Practical Figma File Structure for Building a Design System from Scratch" (variant count): https://www.designsystemscollective.com/shape-to-system-a-practical-figma-file-structure-for-building-a-design-system-from-scratch-63e1f1b72369
- Design Systems Collective, "Motion Belongs in the Design System" (motion tokens, rapid sequences): https://www.designsystemscollective.com/motion-belongs-in-the-design-system-cfc8d27dd962
- W3C, Understanding WCAG 2.2, Success Criterion 2.2.2 Pause, Stop, Hide: https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html
- W3C, Understanding WCAG 2.2: 2.2.1 Timing Adjustable https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html, 2.3.3 Animation from Interactions https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html, 4.1.3 Status Messages https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html
- Nielsen Norman Group, "Executing UX Animations: Duration and Motion Characteristics": https://www.nngroup.com/articles/animation-duration/
- Nielsen Norman Group, "Progress Indicators Make a Slow System Less Insufferable": https://www.nngroup.com/articles/progress-indicators/
- Material Design 3, easing and duration tokens: https://m3.material.io/styles/motion/easing-and-duration/tokens-specs, and applying them: https://m3.material.io/styles/motion/easing-and-duration/applying-easing-and-duration
- Material Design 3, snackbar guidelines: https://m3.material.io/components/snackbar/guidelines
- Material Design 2 (legacy), speed: https://m2.material.io/design/motion/speed.html, and the motion system: https://m2.material.io/design/motion/the-motion-system.html
- Carbon Design System, motion: https://carbondesignsystem.com/elements/motion/overview/
- Apple Human Interface Guidelines, Motion: https://developer.apple.com/design/human-interface-guidelines/motion, and Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- MDN, `prefers-reduced-motion`: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion, and the View Transition API: https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API
