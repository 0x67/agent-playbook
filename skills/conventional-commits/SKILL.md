---
name: conventional-commits
description: >
  Commit messages, PR titles, and PR bodies in Conventional Commits form. Use
  before `git commit`, `gh pr create`, or `gh pr edit`, and whenever writing or
  rewording a commit message, a pull request title, or a pull request
  description, choosing a type or scope (feat, fix, perf, refactor, test, docs,
  build, ci, chore, revert), or marking a breaking change.
---

# Commits and pull requests

The repository's own rules come first. Before writing, check:

1. A commitlint config (`commitlint.config.*`, `.commitlintrc*`, or a `commitlint` key in `package.json`) and `CONTRIBUTING.md`. Their types, scopes, and length limits replace the ones below.
2. A PR template (`.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE/`, or `docs/pull_request_template.md`). Fill its sections instead of the layout under PR body.
3. `git log --format=%s -30` on the target branch. Reuse the scopes it already uses and copy how it titles releases.

## Header

`type(scope)!: subject` is the whole commit message and also the PR title.

| Type | Use for |
| --- | --- |
| `feat` | New behavior a user, caller, or operator can see |
| `fix` | Wrong behavior made right |
| `perf` | Faster or smaller, same behavior |
| `refactor` | Structure changes, behavior stays |
| `test` | Tests only |
| `docs` | Documentation and comments only |
| `build` | Build system, dependencies, packaging |
| `ci` | CI configuration and workflows |
| `chore` | Maintenance that fits nothing above, including release commits |
| `revert` | Undoing an earlier commit; the subject is the reverted header |
| `style` | Formatting only |

When a change spans types, pick the one that matters to someone reading the changelog. A fix that needed a refactor is `fix`.

- **Scope** is the module, package, crate, or app the change lives in, lowercase and spelled as the repo spells it (`session`, `core`, `driver-web`). Leave it out when the change has no single home.
- **`!`** after the scope marks a breaking change: a public API, CLI flag, config key, wire format, or schema that existing callers must change for. The PR body says what breaks and how to migrate.
- **Subject** is imperative, starts lowercase unless the first word is a name or identifier, has no trailing period, and names the effect: `keep mdf trades out of bars and vwap`, not `fix bug`. Keep the whole header under about 72 characters and never wrap it.

## Commit message

1. One header line. No body, no footers, no trailers; detail goes in the PR body.
2. No AI attribution: no `Co-Authored-By`, `Claude-Session`, or "Generated with" lines, whatever the tool's default.
3. One logical change per commit. If the subject needs "and" to join two unrelated changes, split the commit.
4. Release commits copy the repo's pattern, such as `chore(release): <package> <version>` or `chore: release <version>`.

## PR title

Same header format. A squash merge turns the title into the commit on the main branch, so it names the whole change, not the last commit. A draft that collects a phase of commits takes the type of its main change, as in `feat: interop phase`.

## PR body

Prose follows the humanizer rules; load `humanizer:humanizer` in embedded mode when it is installed. Without a template, use bold section headings with numbered lists:

```markdown
**Summary**

1. What changed and why, readable without the diff.

**Changes**

1. One item per notable change, naming the file, module, or commit header.

**Screenshots**

| Before | After |
| --- | --- |
| ![Login error, before](./before-login-error.png) | ![Login error, after](./after-login-error.png) |

**Testing**

1. Each command run and its result, with counts: `cargo nextest run`: 412 passed.

**Breaking changes**

1. What callers must change, and how.
```

1. Drop a section that would be empty, and add one the PR needs, such as setup steps before the first release.
2. Report only results you observed. A check you did not run is listed as not run.
3. Link the issue when one exists: `Closes #123`.
4. No AI attribution lines and no "Generated with" footer.

### UI changes

A PR that changes what a screen looks like or how it behaves carries the Screenshots section.

1. Capture each affected screen on the base branch and on the PR branch, at the same viewport, data, and state, for example with Playwright's `page.screenshot({ path, fullPage: true })` or a browser tool. Cover each state the change touches: empty, error, loading, a phone width, and the dark theme when the app has one. Record a short video or GIF for motion, such as an animation or drag and drop.
2. Use test or seed data. Crop or blur names, emails, account numbers, tokens, and anything copied from production.
3. Keep the images out of the repo. Save them in a scratch folder, reference them in the body as `![alt](./after-login-error.png)`, and pass each one with `--attach`: `gh pr create --body-file body.md --attach './after-login-error.png#Login error, after'`. gh uploads the files and rewrites the references; `gh pr edit` and `gh pr comment` take `--attach` too. With a gh that has no `--attach`, drag the images into the PR in the browser.
4. Alt text says what the image shows, not the file name.

## Before you finish

| Detection | Fix |
| --- | --- |
| Header longer than about 72 characters | Cut the subject down to the effect |
| Subject ends with a period, or starts with a capitalized common word | Drop the period, lowercase the word |
| Subject is only `update`, `changes`, `misc`, or `fix bug` | Name what changed |
| Commit message with a body or trailers | Move the detail into the PR body |
| `!` with no breaking-change note in the PR body | Add the note, or drop the `!` |
| PR title that only describes the last commit | Retitle for the whole change |
| UI change with no before and after images | Capture them and attach with `--attach` |
| Screenshot showing real names, emails, or tokens | Recapture with test data, or crop and blur |
