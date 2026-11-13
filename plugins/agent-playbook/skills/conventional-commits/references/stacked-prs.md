# Stacked pull requests

Split a large feature into a chain of small PRs, each based on the branch below it. Reviewers read one concern at a time, and the bottom of the stack can merge while the top is still in review.

**When to stack**

1. The feature would put more than about 400 changed lines in one PR. Lockfiles do not count, and a renamed file counts only the lines it edits. The `pr-guard` hook uses the same count; `AGENT_PLAYBOOK_PR_MAX_LINES` changes the limit, and `0` turns the size check off.
2. It mixes concerns, for example a refactor or file split plus new behavior, a schema change plus the code that reads it, or a new API plus its first caller in another module.
3. A spec with more than one group: one PR per group, in group order. Adjacent small groups can share a PR while it stays under the limit.
4. A change under the limit with one concern goes in one PR.

**Plan the stack before writing code**

1. List the PRs from the bottom up before the first edit, one concern each. A usual order is moves and refactors with no behavior change (the split-first commit from Code Growth Discipline), then types, schema, or migrations, then the behavior, then wiring, UI, and docs.
2. Each PR builds and passes its tests on its own. If a PR compiles only after the next one is merged, the split is in the wrong place.
3. A new function goes in the same PR as its first caller or its tests.
4. Show the user the plan as a list of branch names, bases, and PR titles before pushing or opening anything.

**Naming**

Each PR in a stack is named the way a standalone PR would be.

1. Name the branch after the repo's own pattern, read from `git branch -r` and recent PR heads. Without one, use `<type>/<slug>`, with the PR title's type and a short kebab-case slug: `refactor/orders-pricing-module`, `feat/orders-discount-codes`. When a stack tool generates names from dates, numbers, or commit hashes, pass the branch name to it explicitly.
2. Title each PR with a Conventional Commits header for its own change, following the Header rules in `SKILL.md`. A squash merge turns each title into a commit on the main branch, and that commit contains only this PR's change.
3. Keep the stack position out of titles and branch names: no `[2/3]`, `(2/3)`, `Part 2`, or `stack-2`. The position belongs in the PR body.
4. Commits inside each PR follow the commit rules in `SKILL.md`.

**PR body**

Put a Stack section above Summary. It lists every PR in the chain from the bottom and marks the current one:

```markdown
**Stack**

1. #101 refactor(orders): move pricing into its own module
2. #102 feat(orders): add discount codes (this PR)
3. #103 feat(checkout): accept discount codes at checkout
```

When a PR is added, merged, or dropped, update the list on every open PR in the chain. A stack linked with `gh stack link` (below) can leave the section out, because GitHub then shows the stack on every PR.

**Commands with git and gh**

1. Create each branch from the one below it: `git switch -c feat/orders-discount-codes refactor/orders-pricing-module`.
2. Open each PR against the branch below it: `gh pr create --base refactor/orders-pricing-module --title "feat(orders): add discount codes" --body-file body.md`. The bottom PR's base is the main branch.
3. After you commit a fix to a lower branch, check out the top branch and run `git rebase --update-refs <fixed-branch>`. Git replays the branches above the fix and moves each of their refs. Push every moved branch with `--force-with-lease`.
4. After the bottom PR is squash-merged, its old commits are still in the branches above it. Fetch, check out the top branch, and run `git rebase --update-refs --onto origin/main <merged-branch>` while the merged branch still exists locally. When the merged branch is deleted on GitHub, GitHub moves the next PR's base to the main branch; otherwise run `gh pr edit <number> --base main`.
5. Merge from the bottom up. A PR whose base is another branch merges into that branch.
6. Graphite (`gt`), git-town, and similar tools are fine in a repo that already uses one, and their branches still follow the Naming rules above. spr and ghstack pick their own branch names, so they do not fit.

**With gh stack**

GitHub's `gh stack` extension (`github/gh-stack`) links the PRs into a stack on GitHub. Each PR then shows a map of the stack, and one command merges a PR together with every PR below it. Use it when `gh extension list` shows `github/gh-stack`. Do not install it yourself; suggest `gh extension install github/gh-stack` to the user.

1. Create the bottom branch with `gh stack init refactor/orders-pricing-module` and each branch above it with `gh stack add feat/orders-discount-codes`, always with a name. Without one, `gh stack add -m` names the branch `MM-DD-slug`, and a bare `init` or `add` waits for input.
2. Commit in each branch, following the commit rules in `SKILL.md`.
3. Push every branch with `gh stack push`.
4. Open each PR from the bottom up with `gh pr create --base <branch below> --head <branch>`, as in the commands above. Avoid `gh stack submit` for new PRs, because it titles them from the commit subject or the branch name and appends a "Stack created with GitHub Stacks CLI" footer to each body.
5. Link the PRs into a stack, listed from the bottom: `gh stack link 101 102 103`. With PR numbers as arguments, `link` uses those PRs and opens none.
6. To fix a lower branch, check it out with `gh stack checkout <branch>`, commit, replay the branches above it with `gh stack rebase --upstack`, and run `gh stack push`.
7. After a PR merges, `gh stack sync` fetches, rebases the remaining branches onto the new base, and pushes them. `--prune` also deletes the merged local branches.
8. Merge with `gh stack merge <PR number> --yes`. It merges that PR and every unmerged PR below it, all or none. `gh pr merge` cannot merge a PR that belongs to a stack.
9. Read the stack with `gh stack view --json`.
10. A command that waits for input or opens a full-screen view hangs an agent. Run `gh stack view` only with `--json`, `submit` only with `--auto`, and `checkout` only with a branch name, and never run `switch` or `modify`. In a repo with more than one remote, pass `--remote <name>` to `push`, `submit`, `sync`, `rebase`, and `link`, or set `git config remote.pushDefault origin`.
11. Skip GitHub's agent skill for the extension (`gh skill install github/gh-stack`), because its examples name branches `auth` and `api` and break the Naming rules above.

Pushes, force pushes, new PRs, and merges are outward actions and need the user's go-ahead (`AGENTS.md`).
