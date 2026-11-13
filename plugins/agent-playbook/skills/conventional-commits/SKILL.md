---
name: conventional-commits
description: >
  Commit messages, PR titles, and PR bodies in Conventional Commits form. Use
  before `git commit`, `gh pr create`, or `gh pr edit`, and whenever writing or
  rewording a commit message, a pull request title, or a pull request
  description, choosing a type or scope (feat, fix, perf, refactor, test, docs,
  build, ci, chore, revert), marking a breaking change, naming a branch, or
  splitting a large feature into stacked PRs.
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

- **Scope** is the module, package, crate, or app the change belongs to, lowercase and spelled as the repo spells it (`session`, `core`, `driver-web`). Leave it out when the change has no one home.
- **`!`** after the scope marks a breaking change: a public API, CLI flag, config key, wire format, or schema that existing callers must change for. The PR body says what breaks and how to migrate.
- **Subject** is imperative, starts lowercase unless the first word is a name or identifier, has no trailing period, and names the effect: `keep mdf trades out of bars and vwap`, not `fix bug`. The whole header stays under about 72 characters and is never wrapped.

## Commit message

1. One header line, with no body, footers, or trailers. Detail goes in the PR body.
2. No AI attribution: no `Co-Authored-By`, `Claude-Session`, or "Generated with" lines, whatever the tool's default.
3. One logical change per commit. If the subject needs "and" to join two unrelated changes, split the commit.
4. Release commits copy the repo's pattern, such as `chore(release): <package> <version>` or `chore: release <version>`.

## PR title

Same header format. A squash merge turns the title into the commit on the main branch, so it describes the whole change, not the last commit. A draft that collects a phase of commits takes the type of its main change, as in `feat: interop phase`.

## Branch name

Copy the repo's pattern from `git branch -r` and recent PR heads (`gh pr list --state all --limit 20 --json headRefName`). Without one, use `<type>/<slug>`: the PR title's type and a short lowercase kebab-case slug, as in `fix/cache-expiry`. Keep stack positions such as `part-2` out of branch names.

## Stacked PRs

A feature over about 400 changed lines (lockfiles not counted), or one that mixes concerns, goes out as a stack of PRs, one concern each, every PR named by the rules above. Read `references/stacked-prs.md` before the first edit of such a feature. It has the size rule, how to plan the stack, the Stack section for the PR body, and the git and gh commands. When `gh extension list` shows GitHub's `github/gh-stack`, follow its gh stack section.

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
| Subject is only `update`, `changes`, `misc`, or `fix bug` | State what changed |
| Commit message with a body or trailers | Move the detail into the PR body |
| `!` with no breaking-change note in the PR body | Add the note, or drop the `!` |
| PR title that only describes the last commit | Retitle for the whole change |
| PR over about 400 changed lines, or mixing concerns | Split it into stacked PRs (`references/stacked-prs.md`) |
| Stack position (`[2/3]`, `Part 2`, `part-2`) in a PR title or branch name | Move it to the PR body's Stack section |
| Branch name outside the repo's pattern | Rename it with `git branch -m <new-name>` before pushing |
| UI change with no before and after images | Capture them and attach with `--attach` |
| Screenshot showing real names, emails, or tokens | Recapture with test data, or crop and blur |
